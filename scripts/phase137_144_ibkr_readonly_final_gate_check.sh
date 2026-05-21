#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 137-144 IBKR read-only final gate dry-run check"

required_files=(
  "docs/IBKR_READONLY_FINAL_GATE_DRYRUN.md"
  "examples/ibkr_readonly_final_gate_decision.sample.yaml"
  "scripts/ibkr_readonly_final_gate_plan.sh"
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

echo "[INFO] Generate IBKR read-only final gate dry-run"
./scripts/ibkr_readonly_final_gate_plan.sh

echo "[INFO] Required output check"
required_outputs=(
  "ibkr_readonly_final_gate_plan.csv"
  "reports/ibkr_readonly_final_gate_report.md"
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

path = Path("ibkr_readonly_final_gate_plan.csv")
required_header = [
    "run_id",
    "run_timestamp",
    "timezone",
    "branch",
    "commit",
    "workflow",
    "decision",
    "operator_approval_required",
    "config_scan_status",
    "real_connection_allowed",
    "contract_qualification_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "trading_actions_allowed",
    "ibkr_connection_triggered",
    "market_data_request_triggered",
    "historical_data_request_triggered",
    "contract_qualification_triggered",
    "broker_execution_triggered",
    "manual_review_required",
    "action_allowed",
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
    "workflow": "ibkr_readonly_final_gate_dryrun",
    "decision": "NO_GO",
    "operator_approval_required": "true",
    "config_scan_status": "PASS",
    "real_connection_allowed": "false",
    "contract_qualification_allowed": "false",
    "market_data_request_allowed": "false",
    "historical_data_request_allowed": "false",
    "trading_actions_allowed": "false",
    "ibkr_connection_triggered": "false",
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

for key in ("run_id", "run_timestamp", "branch", "commit"):
    if not row.get(key):
        raise SystemExit(f"[FAIL] Missing value: {key}")

print("[PASS] IBKR read-only final gate CSV is valid")
PY

echo "[INFO] Markdown safety check"
grep -q "decision | NO_GO" reports/ibkr_readonly_final_gate_report.md
grep -q "ibkr_connection_triggered=false" reports/ibkr_readonly_final_gate_report.md
grep -q "market_data_request_triggered=false" reports/ibkr_readonly_final_gate_report.md
grep -q "historical_data_request_triggered=false" reports/ibkr_readonly_final_gate_report.md
grep -q "contract_qualification_triggered=false" reports/ibkr_readonly_final_gate_report.md
grep -q "broker_execution_triggered=false" reports/ibkr_readonly_final_gate_report.md
grep -q "action_allowed=false" reports/ibkr_readonly_final_gate_report.md
grep -q "manual_review_required=true" reports/ibkr_readonly_final_gate_report.md

echo "[INFO] Active runtime trading API guard"
if grep -R "placeOrder\|cancelOrder\|bracketOrder\|whatIfOrder\|exerciseOptions" main.py src --include="*.py" >/dev/null 2>&1; then
  echo "[FAIL] Trading API keyword found in active runtime code"
  exit 1
fi

echo "[INFO] Runtime output git hygiene check"
if git status --short | grep -E "ibkr_readonly_final_gate_plan.csv|reports/ibkr_readonly_final_gate_report.md" >/dev/null 2>&1; then
  echo "[FAIL] IBKR final gate runtime output appears in git status"
  git status --short
  exit 1
fi

echo "[INFO] Config staging guard"
if git diff --cached --name-only | grep -q "^config.yaml$"; then
  echo "[FAIL] config.yaml is staged"
  exit 1
fi

echo "[PASS] IBKR read-only final gate dry-run generated"
echo "[PASS] CSV schema and safety flags are valid"
echo "[PASS] Markdown safety assertions are valid"
echo "[PASS] No active Python trading API keyword found"
echo "[PASS] Runtime outputs do not pollute git status"
echo "[PASS] config.yaml is not staged"
echo "[PASS] No IBKR connection triggered"
echo "[PASS] No market data request triggered"
echo "[PASS] No historical data request triggered"
echo "[PASS] No contract qualification triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
