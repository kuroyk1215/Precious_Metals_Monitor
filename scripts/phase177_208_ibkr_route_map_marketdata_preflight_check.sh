#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 177-208 IBKR route map and market data preflight check"

required_files=(
  "docs/IBKR_ROUTE_MAP_MARKETDATA_PREFLIGHT.md"
  "examples/ibkr_contract_map_lockin.sample.csv"
  "scripts/ibkr_jp_route_discovery_oneshot.sh"
  "scripts/ibkr_contract_map_lockin_builder.sh"
  "scripts/ibkr_market_data_snapshot_preflight.sh"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing required file: $file"
    exit 1
  fi
done

echo "[INFO] Python syntax check"
python3 -m py_compile main.py src/*.py

echo "[INFO] Unit tests"
python3 -m pytest -q

echo "[INFO] Route discovery default NO_GO"
./scripts/ibkr_jp_route_discovery_oneshot.sh

echo "[INFO] Contract map lock-in builder"
./scripts/ibkr_contract_map_lockin_builder.sh

echo "[INFO] Market data snapshot preflight"
./scripts/ibkr_market_data_snapshot_preflight.sh

echo "[INFO] Required output check"
required_outputs=(
  "ibkr_jp_route_discovery_oneshot.csv"
  "reports/ibkr_jp_route_discovery_oneshot_report.md"
  "ibkr_contract_map_lockin.csv"
  "reports/ibkr_contract_map_lockin_report.md"
  "ibkr_market_data_snapshot_preflight.csv"
  "reports/ibkr_market_data_snapshot_preflight_report.md"
)

for file in "${required_outputs[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing generated output: $file"
    exit 1
  fi
done

echo "[INFO] CSV validation"
python3 - <<'PY'
import csv
from pathlib import Path

route_rows = list(csv.DictReader(Path("ibkr_jp_route_discovery_oneshot.csv").open()))
if len(route_rows) != 9:
    raise SystemExit(f"[FAIL] Expected 9 route rows, got {len(route_rows)}")
if {r["display_symbol"] for r in route_rows if r["route_status"] == "CANDIDATE"} != {"1540.T", "1542.T"}:
    raise SystemExit("[FAIL] Route candidate symbols mismatch")
if [r for r in route_rows if r["display_symbol"] == "518880.SH"][0]["route_status"] != "IBKR_UNSUPPORTED":
    raise SystemExit("[FAIL] 518880.SH must be IBKR_UNSUPPORTED")
for r in route_rows:
    if r["decision"] != "NO_GO":
        raise SystemExit("[FAIL] default route discovery must be NO_GO")
    for k in ("ibkr_connection_triggered", "contract_qualification_triggered", "market_data_request_triggered", "historical_data_request_triggered", "broker_execution_triggered", "action_allowed"):
        if r[k] != "false":
            raise SystemExit(f"[FAIL] {k} must be false")

map_rows = list(csv.DictReader(Path("ibkr_contract_map_lockin.csv").open()))
if len(map_rows) != 3:
    raise SystemExit(f"[FAIL] Expected 3 map rows, got {len(map_rows)}")
statuses = {r["display_symbol"]: r["status"] for r in map_rows}
if statuses.get("518880.SH") != "IBKR_UNSUPPORTED":
    raise SystemExit("[FAIL] 518880.SH map status must be IBKR_UNSUPPORTED")
if statuses.get("1540.T") not in {"ROUTE_REQUIRED", "MAP_READY"}:
    raise SystemExit("[FAIL] 1540.T map status invalid")
if statuses.get("1542.T") not in {"ROUTE_REQUIRED", "MAP_READY"}:
    raise SystemExit("[FAIL] 1542.T map status invalid")

preflight_rows = list(csv.DictReader(Path("ibkr_market_data_snapshot_preflight.csv").open()))
if len(preflight_rows) != 3:
    raise SystemExit(f"[FAIL] Expected 3 preflight rows, got {len(preflight_rows)}")
for r in preflight_rows:
    if r["decision"] != "NO_GO":
        raise SystemExit("[FAIL] market data preflight must remain NO_GO")
    for k in ("market_data_request_allowed", "historical_data_request_allowed", "broker_execution_allowed", "market_data_request_triggered", "historical_data_request_triggered", "broker_execution_triggered", "action_allowed"):
        if r[k] != "false":
            raise SystemExit(f"[FAIL] {k} must be false")

print("[PASS] Route, map, and market data preflight CSVs are valid")
PY

echo "[INFO] Active runtime trading API guard"
if grep -R "placeOrder\|cancelOrder\|bracketOrder\|whatIfOrder\|exerciseOptions" main.py src --include="*.py" >/dev/null 2>&1; then
  echo "[FAIL] Trading API keyword found in active runtime code"
  exit 1
fi

echo "[INFO] Market data direct request guard"
if grep -nE "\.(reqMktData|reqHistoricalData|placeOrder|cancelOrder|bracketOrder|whatIfOrder|exerciseOptions)\s*\(" scripts/ibkr_jp_route_discovery_oneshot.sh scripts/ibkr_contract_map_lockin_builder.sh scripts/ibkr_market_data_snapshot_preflight.sh >/dev/null 2>&1; then
  echo "[FAIL] Forbidden market data / historical / trading direct call found"
  exit 1
fi

echo "[INFO] reqContractDetails execution path check"
if ! grep -q "reqContractDetails" scripts/ibkr_jp_route_discovery_oneshot.sh; then
  echo "[FAIL] Route discovery script lacks reqContractDetails path"
  exit 1
fi

echo "[INFO] Runtime output git hygiene check"
if git status --short | grep -E "ibkr_jp_route_discovery_oneshot.csv|reports/ibkr_jp_route_discovery_oneshot_report.md|ibkr_contract_map_lockin.csv|reports/ibkr_contract_map_lockin_report.md|ibkr_market_data_snapshot_preflight.csv|reports/ibkr_market_data_snapshot_preflight_report.md" >/dev/null 2>&1; then
  echo "[FAIL] Runtime output appears in git status"
  git status --short
  exit 1
fi

echo "[INFO] Config staging guard"
if git diff --cached --name-only | grep -q "^config.yaml$"; then
  echo "[FAIL] config.yaml is staged"
  exit 1
fi

echo "[PASS] Phase 177-208 mega batch check passed"
echo "[PASS] Default route discovery remains NO_GO"
echo "[PASS] Contract map lock-in builder generated"
echo "[PASS] Market data snapshot preflight generated"
echo "[PASS] No market data request triggered"
echo "[PASS] No historical data request triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Runtime outputs do not pollute git status"
echo "[PASS] config.yaml is not staged"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
