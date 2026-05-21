#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 153-160 IBKR contract qualification dry-run final gate check"

required_files=(
  "docs/IBKR_CONTRACT_QUALIFICATION_DRYRUN_FINAL_GATE.md"
  "examples/ibkr_contract_qualification_targets.sample.csv"
  "scripts/ibkr_contract_qualification_final_gate.sh"
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

echo "[INFO] Run contract qualification dry-run final gate"
./scripts/ibkr_contract_qualification_final_gate.sh

echo "[INFO] Required output check"
required_outputs=(
  "ibkr_contract_qualification_final_gate.csv"
  "reports/ibkr_contract_qualification_final_gate_report.md"
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

path = Path("ibkr_contract_qualification_final_gate.csv")
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

if len(rows) != 3:
    raise SystemExit(f"[FAIL] Expected 3 rows, got {len(rows)}")

expected_symbols = {"1540.T", "1542.T", "518880.SH"}
actual_symbols = {row["display_symbol"] for row in rows}
if actual_symbols != expected_symbols:
    raise SystemExit(f"[FAIL] Unexpected target symbols: {actual_symbols}")

for row in rows:
    checks = {
        "timezone": "Asia/Tokyo",
        "workflow": "ibkr_contract_qualification_dryrun_final_gate",
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

print("[PASS] IBKR contract qualification dry-run CSV is valid")
PY

echo "[INFO] Markdown safety check"
grep -q "decision | NO_GO" reports/ibkr_contract_qualification_final_gate_report.md
grep -q "gate_status | PASS" reports/ibkr_contract_qualification_final_gate_report.md
grep -q "1540.T" reports/ibkr_contract_qualification_final_gate_report.md
grep -q "1542.T" reports/ibkr_contract_qualification_final_gate_report.md
grep -q "518880.SH" reports/ibkr_contract_qualification_final_gate_report.md
grep -q "ibkr_connection_triggered=false" reports/ibkr_contract_qualification_final_gate_report.md
grep -q "contract_qualification_triggered=false" reports/ibkr_contract_qualification_final_gate_report.md
grep -q "market_data_request_triggered=false" reports/ibkr_contract_qualification_final_gate_report.md
grep -q "historical_data_request_triggered=false" reports/ibkr_contract_qualification_final_gate_report.md
grep -q "broker_execution_triggered=false" reports/ibkr_contract_qualification_final_gate_report.md
grep -q "action_allowed=false" reports/ibkr_contract_qualification_final_gate_report.md

echo "[INFO] Active runtime trading API guard"
if grep -R "placeOrder\|cancelOrder\|bracketOrder\|whatIfOrder\|exerciseOptions" main.py src --include="*.py" >/dev/null 2>&1; then
  echo "[FAIL] Trading API keyword found in active runtime code"
  exit 1
fi

echo "[INFO] Contract dry-run direct IBKR request guard"
if grep -nE "\.(reqContractDetails|reqMktData|reqHistoricalData|placeOrder|cancelOrder|bracketOrder|whatIfOrder|exerciseOptions)\s*\(" scripts/ibkr_contract_qualification_final_gate.sh >/dev/null 2>&1; then
  echo "[FAIL] Contract qualification dry-run script contains direct forbidden IBKR request or trading call"
  exit 1
fi

echo "[INFO] Runtime output git hygiene check"
if git status --short | grep -E "ibkr_contract_qualification_final_gate.csv|reports/ibkr_contract_qualification_final_gate_report.md" >/dev/null 2>&1; then
  echo "[FAIL] Contract qualification runtime output appears in git status"
  git status --short
  exit 1
fi

echo "[INFO] Config staging guard"
if git diff --cached --name-only | grep -q "^config.yaml$"; then
  echo "[FAIL] config.yaml is staged"
  exit 1
fi

echo "[PASS] IBKR contract qualification dry-run final gate generated"
echo "[PASS] Default gate remains NO_GO"
echo "[PASS] No IBKR connection triggered"
echo "[PASS] No contract qualification triggered"
echo "[PASS] No market data request triggered"
echo "[PASS] No historical data request triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Runtime outputs do not pollute git status"
echo "[PASS] config.yaml is not staged"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
