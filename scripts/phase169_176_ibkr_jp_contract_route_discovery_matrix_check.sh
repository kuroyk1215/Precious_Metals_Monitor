#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 169-176 IBKR JP contract route discovery matrix dry-run check"

required_files=(
  "docs/IBKR_JP_CONTRACT_ROUTE_DISCOVERY_MATRIX.md"
  "examples/ibkr_jp_contract_route_discovery_candidates.sample.csv"
  "scripts/ibkr_jp_contract_route_discovery_matrix.sh"
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

echo "[INFO] Generate JP contract route discovery matrix"
./scripts/ibkr_jp_contract_route_discovery_matrix.sh

echo "[INFO] Required output check"
required_outputs=(
  "ibkr_jp_contract_route_discovery_matrix.csv"
  "reports/ibkr_jp_contract_route_discovery_matrix_report.md"
)

for file in "${required_outputs[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing generated output: $file"
    exit 1
  fi
done

echo "[INFO] CSV schema and safety check"
python3 - <<'PY'
import csv
from pathlib import Path

path = Path("ibkr_jp_contract_route_discovery_matrix.csv")
required_header = [
    "run_id",
    "run_timestamp",
    "timezone",
    "branch",
    "commit",
    "workflow",
    "decision",
    "gate_status",
    "display_symbol",
    "symbol",
    "market",
    "instrument_type",
    "route_status",
    "candidate_priority",
    "route_family",
    "sec_type",
    "exchange",
    "primary_exchange",
    "currency",
    "local_symbol",
    "trading_class",
    "read_only_required",
    "real_connection_allowed",
    "contract_qualification_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "trading_actions_allowed",
    "ibkr_connection_triggered",
    "contract_qualification_triggered",
    "market_data_request_triggered",
    "historical_data_request_triggered",
    "broker_execution_triggered",
    "manual_review_required",
    "action_allowed",
    "notes",
]

with path.open(newline="") as f:
    reader = csv.DictReader(f)
    if reader.fieldnames != required_header:
        raise SystemExit(f"[FAIL] Unexpected header: {reader.fieldnames}")
    rows = list(reader)

if len(rows) != 9:
    raise SystemExit(f"[FAIL] Expected 9 rows, got {len(rows)}")

candidate_rows = [r for r in rows if r["route_status"] == "CANDIDATE"]
unsupported_rows = [r for r in rows if r["route_status"] == "IBKR_UNSUPPORTED"]

if len(candidate_rows) != 8:
    raise SystemExit(f"[FAIL] Expected 8 candidate rows, got {len(candidate_rows)}")

if len(unsupported_rows) != 1:
    raise SystemExit(f"[FAIL] Expected 1 unsupported row, got {len(unsupported_rows)}")

candidate_symbols = {r["display_symbol"] for r in candidate_rows}
if candidate_symbols != {"1540.T", "1542.T"}:
    raise SystemExit(f"[FAIL] Unexpected candidate symbols: {candidate_symbols}")

unsupported = unsupported_rows[0]
if unsupported["display_symbol"] != "518880.SH":
    raise SystemExit(f"[FAIL] Expected 518880.SH unsupported row, got {unsupported['display_symbol']}")

required_route_families = {
    "smart_tsej",
    "direct_tsej",
    "tse_primary_tsej",
    "smart_no_primary",
}
actual_route_families = {r["route_family"] for r in candidate_rows}
if actual_route_families != required_route_families:
    raise SystemExit(f"[FAIL] Unexpected route families: {actual_route_families}")

for row in rows:
    checks = {
        "timezone": "Asia/Tokyo",
        "workflow": "ibkr_jp_contract_route_discovery_matrix_dryrun",
        "decision": "NO_GO",
        "gate_status": "PASS",
        "read_only_required": "true",
        "real_connection_allowed": "false",
        "contract_qualification_allowed": "false",
        "market_data_request_allowed": "false",
        "historical_data_request_allowed": "false",
        "trading_actions_allowed": "false",
        "ibkr_connection_triggered": "false",
        "contract_qualification_triggered": "false",
        "market_data_request_triggered": "false",
        "historical_data_request_triggered": "false",
        "broker_execution_triggered": "false",
        "manual_review_required": "true",
        "action_allowed": "false",
    }
    for key, expected in checks.items():
        actual = row.get(key)
        if actual != expected:
            raise SystemExit(f"[FAIL] {key}: expected {expected}, got {actual}")

print("[PASS] IBKR JP contract route discovery matrix CSV is valid")
PY

echo "[INFO] Markdown safety and scope check"
grep -q "decision | NO_GO" reports/ibkr_jp_contract_route_discovery_matrix_report.md
grep -q "candidate_count | 8" reports/ibkr_jp_contract_route_discovery_matrix_report.md
grep -q "unsupported_count | 1" reports/ibkr_jp_contract_route_discovery_matrix_report.md
grep -q "1540.T" reports/ibkr_jp_contract_route_discovery_matrix_report.md
grep -q "1542.T" reports/ibkr_jp_contract_route_discovery_matrix_report.md
grep -q "518880.SH" reports/ibkr_jp_contract_route_discovery_matrix_report.md
grep -q "IBKR_UNSUPPORTED" reports/ibkr_jp_contract_route_discovery_matrix_report.md
grep -q "ibkr_connection_triggered=false" reports/ibkr_jp_contract_route_discovery_matrix_report.md
grep -q "contract_qualification_triggered=false" reports/ibkr_jp_contract_route_discovery_matrix_report.md
grep -q "market_data_request_triggered=false" reports/ibkr_jp_contract_route_discovery_matrix_report.md
grep -q "historical_data_request_triggered=false" reports/ibkr_jp_contract_route_discovery_matrix_report.md
grep -q "broker_execution_triggered=false" reports/ibkr_jp_contract_route_discovery_matrix_report.md
grep -q "action_allowed=false" reports/ibkr_jp_contract_route_discovery_matrix_report.md

echo "[INFO] Active runtime trading API guard"
if grep -R "placeOrder\|cancelOrder\|bracketOrder\|whatIfOrder\|exerciseOptions" main.py src --include="*.py" >/dev/null 2>&1; then
  echo "[FAIL] Trading API keyword found in active runtime code"
  exit 1
fi

echo "[INFO] Route discovery dry-run direct IBKR request guard"
if grep -nE "\.(reqContractDetails|reqMktData|reqHistoricalData|placeOrder|cancelOrder|bracketOrder|whatIfOrder|exerciseOptions)\s*\(" scripts/ibkr_jp_contract_route_discovery_matrix.sh >/dev/null 2>&1; then
  echo "[FAIL] Route discovery dry-run script contains direct forbidden IBKR request or trading call"
  exit 1
fi

echo "[INFO] Runtime output git hygiene check"
if git status --short | grep -E "ibkr_jp_contract_route_discovery_matrix.csv|reports/ibkr_jp_contract_route_discovery_matrix_report.md" >/dev/null 2>&1; then
  echo "[FAIL] Route discovery runtime output appears in git status"
  git status --short
  exit 1
fi

echo "[INFO] Config staging guard"
if git diff --cached --name-only | grep -q "^config.yaml$"; then
  echo "[FAIL] config.yaml is staged"
  exit 1
fi

echo "[PASS] IBKR JP contract route discovery matrix generated"
echo "[PASS] 1540.T and 1542.T are included as JP route candidates"
echo "[PASS] 518880.SH is marked as IBKR_UNSUPPORTED"
echo "[PASS] Default gate remains NO_GO"
echo "[PASS] No IBKR connection triggered"
echo "[PASS] No contract qualification triggered"
echo "[PASS] No market data request triggered"
echo "[PASS] No historical data request triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Runtime outputs do not pollute git status"
echo "[PASS] config.yaml is not staged"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
