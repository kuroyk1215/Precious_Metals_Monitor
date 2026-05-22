#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 273-288 IBKR daily integration review pack bridge check"

PATH=.venv/bin:$PATH python -m py_compile main.py src/*.py
PATH=.venv/bin:$PATH PYTHONPATH=. python -m pytest -q

missing_input="/tmp/nonexistent_phase273_daily_integration.csv"
rm -f "$missing_input"

PATH=.venv/bin:$PATH bash scripts/ibkr_daily_integration_review_pack.sh --daily-integration="$missing_input" | tee /tmp/phase273_288_review_pack_check.out

if ! grep -q "daily_integration_input_status=missing" /tmp/phase273_288_review_pack_check.out; then
  echo "[FAIL] Missing daily integration input did not report missing"
  exit 1
fi

if ! grep -q "review_pack_status=NO_GO" /tmp/phase273_288_review_pack_check.out; then
  echo "[FAIL] Missing daily integration input did not report NO_GO"
  exit 1
fi

if ! grep -q "action_allowed=false" /tmp/phase273_288_review_pack_check.out; then
  echo "[FAIL] Missing daily integration input did not keep action_allowed=false"
  exit 1
fi

python - <<'PY'
import csv
from pathlib import Path

csv_path = Path("ibkr_daily_integration_review_pack.csv")
report_path = Path("reports/ibkr_daily_integration_review_pack_report.md")
if not csv_path.exists():
    raise SystemExit("[FAIL] Missing review pack CSV output")
if not report_path.exists():
    raise SystemExit("[FAIL] Missing review pack report output")

rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
if len(rows) != 1:
    raise SystemExit(f"[FAIL] Expected one missing-input review row, got {len(rows)}")
row = rows[0]
if row["integration_status"] != "MISSING_INPUT":
    raise SystemExit("[FAIL] Missing input row must carry MISSING_INPUT integration_status")
if row["review_status"] != "REVIEW_BLOCKED" or row["decision_label"] != "NO_GO":
    raise SystemExit("[FAIL] Missing input row must be REVIEW_BLOCKED / NO_GO")
if row["action_allowed"] != "false" or row["manual_review_required"] != "true":
    raise SystemExit("[FAIL] Review row must force action_allowed=false and manual_review_required=true")

report_text = report_path.read_text(encoding="utf-8")
for required in (
    "Review Pack Decision",
    "Input Daily Integration Status",
    "Symbol Review Rows",
    "Data Quality Tier Summary",
    "Safety Confirmation",
    "Next Phase Handoff",
    "action_allowed=false",
    "broker_execution_triggered=false",
    "historical_data_request_triggered=false",
    "account_read_triggered=false",
    "position_read_triggered=false",
    "manual_review_required=true",
):
    if required not in report_text:
        raise SystemExit(f"[FAIL] Report missing required text: {required}")

print("[PASS] Missing input NO_GO review pack validated")
PY

if rg -nE "\.(placeOrder|cancelOrder|whatIfOrder|bracketOrder|exerciseOptions|reqGlobalCancel)\s*\(" main.py src/ibkr_daily_integration_review_pack.py scripts/ibkr_daily_integration_review_pack.sh >/dev/null 2>&1; then
  echo "[FAIL] Forbidden broker trading call found"
  exit 1
fi

if rg -nE "\.(reqAccount|reqPositions|accountSummary|managedAccounts)\s*\(" main.py src/ibkr_daily_integration_review_pack.py scripts/ibkr_daily_integration_review_pack.sh >/dev/null 2>&1; then
  echo "[FAIL] Forbidden account or position read found"
  exit 1
fi

echo "[PASS] Phase 273-288 daily integration review pack bridge check completed"
