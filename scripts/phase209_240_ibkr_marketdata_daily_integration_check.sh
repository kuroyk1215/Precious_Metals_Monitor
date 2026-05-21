#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 209-240 IBKR market data and daily integration preflight check"

required_files=(
  "docs/IBKR_MARKETDATA_DAILY_INTEGRATION_PREFLIGHT.md"
  "examples/ibkr_verified_contract_map.sample.csv"
  "scripts/ibkr_verified_contract_map_generate.sh"
  "scripts/ibkr_market_data_snapshot_oneshot.sh"
  "scripts/ibkr_daily_integration_preflight.sh"
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

echo "[INFO] Generate verified contract map"
./scripts/ibkr_verified_contract_map_generate.sh

echo "[INFO] Market data snapshot default NO_GO"
./scripts/ibkr_market_data_snapshot_oneshot.sh

echo "[INFO] Daily integration preflight"
./scripts/ibkr_daily_integration_preflight.sh

echo "[INFO] Required output check"
required_outputs=(
  "ibkr_verified_contract_map.csv"
  "reports/ibkr_verified_contract_map_report.md"
  "ibkr_market_data_snapshot.csv"
  "reports/ibkr_market_data_snapshot_report.md"
  "ibkr_daily_integration_preflight.csv"
  "reports/ibkr_daily_integration_preflight_report.md"
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

map_rows = list(csv.DictReader(Path("ibkr_verified_contract_map.csv").open()))
if len(map_rows) != 3:
    raise SystemExit(f"[FAIL] Expected 3 contract map rows, got {len(map_rows)}")

expected = {
    "1540.T": ("MAP_READY", "117595037"),
    "1542.T": ("MAP_READY", "121557296"),
    "518880.SH": ("IBKR_UNSUPPORTED", ""),
}
for row in map_rows:
    symbol = row["display_symbol"]
    if symbol not in expected:
        raise SystemExit(f"[FAIL] Unexpected map symbol: {symbol}")
    status, conid = expected[symbol]
    if row["status"] != status or row["conid"] != conid:
        raise SystemExit(f"[FAIL] Bad map row for {symbol}: {row}")

snap_rows = list(csv.DictReader(Path("ibkr_market_data_snapshot.csv").open()))
if len(snap_rows) != 3:
    raise SystemExit(f"[FAIL] Expected 3 snapshot rows, got {len(snap_rows)}")
for row in snap_rows:
    if row["decision"] != "NO_GO":
        raise SystemExit("[FAIL] Market data snapshot must be NO_GO by default")
    if row["execute_requested"] != "false":
        raise SystemExit("[FAIL] execute_requested must be false by default")
    for k in ("ibkr_connection_triggered", "connection_succeeded", "market_data_request_triggered", "historical_data_request_triggered", "broker_execution_triggered", "action_allowed"):
        if row[k] != "false":
            raise SystemExit(f"[FAIL] {k} must be false by default")

integration_rows = list(csv.DictReader(Path("ibkr_daily_integration_preflight.csv").open()))
if len(integration_rows) != 3:
    raise SystemExit(f"[FAIL] Expected 3 integration rows, got {len(integration_rows)}")
for row in integration_rows:
    if row["decision"] != "NO_GO":
        raise SystemExit("[FAIL] Daily integration must remain NO_GO")
    for k in ("daily_research_input_allowed", "telegram_send_allowed", "dashboard_publish_allowed", "broker_execution_allowed", "action_allowed"):
        if row[k] != "false":
            raise SystemExit(f"[FAIL] {k} must be false")

print("[PASS] Market data and daily integration CSVs are valid")
PY

echo "[INFO] Active runtime trading API guard"
if grep -R "placeOrder\|cancelOrder\|bracketOrder\|whatIfOrder\|exerciseOptions" main.py src --include="*.py" >/dev/null 2>&1; then
  echo "[FAIL] Trading API keyword found in active runtime code"
  exit 1
fi

echo "[INFO] Direct forbidden request guard"
if grep -nE "\.(reqHistoricalData|reqContractDetails|placeOrder|cancelOrder|bracketOrder|whatIfOrder|exerciseOptions|accountSummary|positions|reqPositions)\s*\(" scripts/ibkr_market_data_snapshot_oneshot.sh scripts/ibkr_verified_contract_map_generate.sh scripts/ibkr_daily_integration_preflight.sh >/dev/null 2>&1; then
  echo "[FAIL] Forbidden historical/account/contract/trading direct call found"
  exit 1
fi

echo "[INFO] reqMktData execution path check"
if ! grep -q "reqMktData" scripts/ibkr_market_data_snapshot_oneshot.sh; then
  echo "[FAIL] Market data snapshot script lacks reqMktData path"
  exit 1
fi

echo "[INFO] Runtime output git hygiene check"
if git status --short | grep -E "ibkr_verified_contract_map.csv|reports/ibkr_verified_contract_map_report.md|ibkr_market_data_snapshot.csv|reports/ibkr_market_data_snapshot_report.md|ibkr_daily_integration_preflight.csv|reports/ibkr_daily_integration_preflight_report.md" >/dev/null 2>&1; then
  echo "[FAIL] Runtime output appears in git status"
  git status --short
  exit 1
fi

echo "[INFO] Config staging guard"
if git diff --cached --name-only | grep -q "^config.yaml$"; then
  echo "[FAIL] config.yaml is staged"
  exit 1
fi

echo "[PASS] Phase 209-240 market data and daily integration preflight check passed"
echo "[PASS] Verified contract map generated"
echo "[PASS] Market data snapshot remains NO_GO by default"
echo "[PASS] Daily integration remains NO_GO by default"
echo "[PASS] No historical data request triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Runtime outputs do not pollute git status"
echo "[PASS] config.yaml is not staged"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
