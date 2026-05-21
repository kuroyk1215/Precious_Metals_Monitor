#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 145-152 IBKR one-shot read-only connection preflight check"

required_files=(
  "docs/IBKR_ONESHOT_READONLY_CONNECTION_PREFLIGHT.md"
  "scripts/ibkr_oneshot_readonly_connection_preflight.sh"
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

echo "[INFO] Run preflight without --execute"
./scripts/ibkr_oneshot_readonly_connection_preflight.sh

echo "[INFO] Required output check"
required_outputs=(
  "ibkr_oneshot_readonly_connection_preflight.csv"
  "reports/ibkr_oneshot_readonly_connection_preflight_report.md"
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

path = Path("ibkr_oneshot_readonly_connection_preflight.csv")
required_header = [
    "run_id",
    "run_timestamp",
    "timezone",
    "branch",
    "commit",
    "workflow",
    "decision",
    "execute_requested",
    "read_only_required",
    "real_connection_allowed",
    "contract_qualification_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "trading_actions_allowed",
    "connection_attempted",
    "connection_succeeded",
    "market_data_request_triggered",
    "historical_data_request_triggered",
    "contract_qualification_triggered",
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

if len(rows) != 1:
    raise SystemExit(f"[FAIL] Expected 1 row, got {len(rows)}")

row = rows[0]
checks = {
    "timezone": "Asia/Tokyo",
    "workflow": "ibkr_oneshot_readonly_connection_preflight",
    "decision": "NO_GO",
    "execute_requested": "false",
    "read_only_required": "true",
    "real_connection_allowed": "false",
    "contract_qualification_allowed": "false",
    "market_data_request_allowed": "false",
    "historical_data_request_allowed": "false",
    "trading_actions_allowed": "false",
    "connection_attempted": "false",
    "connection_succeeded": "false",
    "market_data_request_triggered": "false",
    "historical_data_request_triggered": "false",
    "contract_qualification_triggered": "false",
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

print("[PASS] IBKR one-shot preflight CSV is valid")
PY

echo "[INFO] Markdown safety check"
grep -q "decision | NO_GO" reports/ibkr_oneshot_readonly_connection_preflight_report.md
grep -q "connection_attempted | false" reports/ibkr_oneshot_readonly_connection_preflight_report.md
grep -q "market_data_request_triggered=false" reports/ibkr_oneshot_readonly_connection_preflight_report.md
grep -q "historical_data_request_triggered=false" reports/ibkr_oneshot_readonly_connection_preflight_report.md
grep -q "contract_qualification_triggered=false" reports/ibkr_oneshot_readonly_connection_preflight_report.md
grep -q "broker_execution_triggered=false" reports/ibkr_oneshot_readonly_connection_preflight_report.md
grep -q "action_allowed=false" reports/ibkr_oneshot_readonly_connection_preflight_report.md

echo "[INFO] Forbidden active runtime API guard"
if grep -R "reqMktData\|reqHistoricalData\|reqContractDetails\|placeOrder\|cancelOrder\|bracketOrder\|whatIfOrder\|exerciseOptions" main.py src --include="*.py" >/dev/null 2>&1; then
  echo "[FAIL] Forbidden IBKR API keyword found in active runtime code"
  exit 1
fi

echo "[INFO] Runtime output git hygiene check"
if git status --short | grep -E "ibkr_oneshot_readonly_connection_preflight.csv|reports/ibkr_oneshot_readonly_connection_preflight_report.md" >/dev/null 2>&1; then
  echo "[FAIL] IBKR one-shot preflight runtime output appears in git status"
  git status --short
  exit 1
fi

echo "[INFO] Config staging guard"
if git diff --cached --name-only | grep -q "^config.yaml$"; then
  echo "[FAIL] config.yaml is staged"
  exit 1
fi

echo "[PASS] IBKR one-shot preflight generated"
echo "[PASS] Default run is NO_GO with no connection attempt"
echo "[PASS] No market data request triggered"
echo "[PASS] No historical data request triggered"
echo "[PASS] No contract qualification triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Runtime outputs do not pollute git status"
echo "[PASS] config.yaml is not staged"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
