#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 161-168 IBKR contract qualification one-shot preflight check"

required_files=(
  "docs/IBKR_CONTRACT_QUALIFICATION_ONESHOT_PREFLIGHT.md"
  "scripts/ibkr_contract_qualification_oneshot.sh"
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

echo "[INFO] Run one-shot script without --execute"
./scripts/ibkr_contract_qualification_oneshot.sh

echo "[INFO] Required output check"
required_outputs=(
  "ibkr_contract_qualification_oneshot.csv"
  "reports/ibkr_contract_qualification_oneshot_report.md"
)

for file in "${required_outputs[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing generated output: $file"
    exit 1
  fi
done

echo "[INFO] CSV schema and default NO_GO safety check"
python3 - <<'PY'
import csv
from pathlib import Path

path = Path("ibkr_contract_qualification_oneshot.csv")
required_header = [
    "run_id",
    "run_timestamp",
    "timezone",
    "branch",
    "commit",
    "workflow",
    "decision",
    "execute_requested",
    "display_symbol",
    "symbol",
    "exchange",
    "currency",
    "sec_type",
    "primary_exchange",
    "market",
    "instrument_type",
    "read_only_required",
    "real_connection_allowed",
    "contract_qualification_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "trading_actions_allowed",
    "ibkr_connection_triggered",
    "connection_succeeded",
    "contract_qualification_triggered",
    "contract_details_count",
    "conid",
    "local_symbol",
    "trading_class",
    "market_name",
    "min_tick",
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

if len(rows) != 3:
    raise SystemExit(f"[FAIL] Expected 3 rows, got {len(rows)}")

expected_symbols = {"1540.T", "1542.T", "518880.SH"}
actual_symbols = {row["display_symbol"] for row in rows}
if actual_symbols != expected_symbols:
    raise SystemExit(f"[FAIL] Unexpected target symbols: {actual_symbols}")

for row in rows:
    checks = {
        "timezone": "Asia/Tokyo",
        "workflow": "ibkr_contract_qualification_oneshot",
        "decision": "NO_GO",
        "execute_requested": "false",
        "read_only_required": "true",
        "real_connection_allowed": "false",
        "contract_qualification_allowed": "false",
        "market_data_request_allowed": "false",
        "historical_data_request_allowed": "false",
        "trading_actions_allowed": "false",
        "ibkr_connection_triggered": "false",
        "connection_succeeded": "false",
        "contract_qualification_triggered": "false",
        "contract_details_count": "0",
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
    if not row.get("notes"):
        raise SystemExit("[FAIL] notes should explain NO_GO reason")

print("[PASS] IBKR contract qualification one-shot default CSV is valid")
PY

echo "[INFO] Markdown safety check"
grep -q "decision | NO_GO" reports/ibkr_contract_qualification_oneshot_report.md
grep -q "ibkr_connection_triggered | false" reports/ibkr_contract_qualification_oneshot_report.md
grep -q "contract_qualification_triggered | false" reports/ibkr_contract_qualification_oneshot_report.md
grep -q "market_data_request_triggered=false" reports/ibkr_contract_qualification_oneshot_report.md
grep -q "historical_data_request_triggered=false" reports/ibkr_contract_qualification_oneshot_report.md
grep -q "broker_execution_triggered=false" reports/ibkr_contract_qualification_oneshot_report.md
grep -q "action_allowed=false" reports/ibkr_contract_qualification_oneshot_report.md

echo "[INFO] Active runtime trading API guard"
if grep -R "placeOrder\|cancelOrder\|bracketOrder\|whatIfOrder\|exerciseOptions" main.py src --include="*.py" >/dev/null 2>&1; then
  echo "[FAIL] Trading API keyword found in active runtime code"
  exit 1
fi

echo "[INFO] One-shot direct forbidden request guard"
if grep -nE "\.(reqMktData|reqHistoricalData|placeOrder|cancelOrder|bracketOrder|whatIfOrder|exerciseOptions)\s*\(" scripts/ibkr_contract_qualification_oneshot.sh >/dev/null 2>&1; then
  echo "[FAIL] One-shot contract qualification script contains forbidden direct API call"
  exit 1
fi

echo "[INFO] reqContractDetails presence check"
if ! grep -q "reqContractDetails" scripts/ibkr_contract_qualification_oneshot.sh; then
  echo "[FAIL] One-shot contract qualification script does not contain reqContractDetails execution path"
  exit 1
fi

echo "[INFO] Runtime output git hygiene check"
if git status --short | grep -E "ibkr_contract_qualification_oneshot.csv|reports/ibkr_contract_qualification_oneshot_report.md" >/dev/null 2>&1; then
  echo "[FAIL] Contract qualification one-shot runtime output appears in git status"
  git status --short
  exit 1
fi

echo "[INFO] Config staging guard"
if git diff --cached --name-only | grep -q "^config.yaml$"; then
  echo "[FAIL] config.yaml is staged"
  exit 1
fi

echo "[PASS] IBKR contract qualification one-shot preflight generated"
echo "[PASS] Default gate remains NO_GO"
echo "[PASS] No IBKR connection triggered by default"
echo "[PASS] No contract qualification triggered by default"
echo "[PASS] No market data request triggered"
echo "[PASS] No historical data request triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Runtime outputs do not pollute git status"
echo "[PASS] config.yaml is not staged"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
