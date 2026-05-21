#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 93-100 data source status check"

required_files=(
  "docs/DATA_SOURCE_STATUS_REPORT.md"
  "scripts/data_source_status_report.sh"
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

echo "[INFO] Generate data source status report"
./scripts/data_source_status_report.sh

echo "[INFO] Required output check"
required_outputs=(
  "data_source_status.csv"
  "reports/data_source_status_report.md"
)

for file in "${required_outputs[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing generated output: $file"
    exit 1
  fi
done

echo "[INFO] CSV schema check"
python3 - <<'PY'
import csv
from pathlib import Path

path = Path("data_source_status.csv")
required_header = [
    "source_name",
    "market",
    "instrument",
    "source_type",
    "data_status",
    "license_required",
    "subscription_required",
    "fallback_priority",
    "manual_review_required",
    "action_allowed",
    "notes",
]

with path.open(newline="") as f:
    reader = csv.DictReader(f)
    if reader.fieldnames != required_header:
        raise SystemExit(f"[FAIL] Unexpected header: {reader.fieldnames}")
    rows = list(reader)

if len(rows) < 4:
    raise SystemExit(f"[FAIL] Expected at least 4 rows, got {len(rows)}")

allowed_status = {
    "manual_csv",
    "mock",
    "synthetic_sample",
    "unavailable",
    "inferred",
    "delayed",
    "real_time",
}

for row in rows:
    if row["data_status"] not in allowed_status:
        raise SystemExit(f"[FAIL] Invalid data_status: {row}")
    if row["manual_review_required"] != "true":
        raise SystemExit(f"[FAIL] manual_review_required must be true: {row}")
    if row["action_allowed"] != "false":
        raise SystemExit(f"[FAIL] action_allowed must be false: {row}")

print("[PASS] Data source status CSV schema is valid")
PY

echo "[INFO] Markdown safety check"
grep -q "ibkr_connection_triggered=false" reports/data_source_status_report.md
grep -q "market_data_request_triggered=false" reports/data_source_status_report.md
grep -q "historical_data_request_triggered=false" reports/data_source_status_report.md
grep -q "contract_qualification_triggered=false" reports/data_source_status_report.md
grep -q "telegram_api_called=false" reports/data_source_status_report.md
grep -q "scheduler_deployed=false" reports/data_source_status_report.md
grep -q "broker_execution_triggered=false" reports/data_source_status_report.md
grep -q "action_allowed=false" reports/data_source_status_report.md
grep -q "manual_review_required=true" reports/data_source_status_report.md

echo "[INFO] Runtime output git hygiene check"
if git status --short | grep -E "data_source_status.csv|reports/data_source_status_report.md" >/dev/null 2>&1; then
  echo "[FAIL] Data source status runtime output appears in git status"
  git status --short
  exit 1
fi

echo "[INFO] Config staging guard"
if git diff --cached --name-only | grep -q "^config.yaml$"; then
  echo "[FAIL] config.yaml is staged"
  exit 1
fi

echo "[INFO] Active runtime trading API guard"
if grep -R "placeOrder\|cancelOrder\|bracketOrder\|whatIfOrder\|exerciseOptions" main.py src --include="*.py" >/dev/null 2>&1; then
  echo "[FAIL] Trading API keyword found in active runtime code"
  exit 1
fi

echo "[PASS] Data source status report generated"
echo "[PASS] Data source status CSV schema is valid"
echo "[PASS] Data source status report safety assertions are valid"
echo "[PASS] Data source status outputs do not pollute git status"
echo "[PASS] config.yaml is not staged"
echo "[PASS] No active Python trading API keyword found"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
