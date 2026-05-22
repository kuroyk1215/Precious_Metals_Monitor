#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 289-304 IBKR final research review pack bridge check"

PATH=.venv/bin:$PATH python -m py_compile main.py src/*.py
PATH=.venv/bin:$PATH PYTHONPATH=. python -m pytest -q

missing_input="/tmp/nonexistent_phase289_review_pack.csv"
rm -f "$missing_input"

PATH=.venv/bin:$PATH bash scripts/ibkr_final_research_review_pack.sh --review-pack="$missing_input" | tee /tmp/phase289_304_final_review_pack_check.out

if ! grep -q "review_pack_input_status=missing" /tmp/phase289_304_final_review_pack_check.out; then
  echo "[FAIL] Missing review pack input did not report missing"
  exit 1
fi

if ! grep -q "final_research_review_status=NO_GO" /tmp/phase289_304_final_review_pack_check.out; then
  echo "[FAIL] Missing review pack input did not report NO_GO"
  exit 1
fi

if ! grep -q "action_allowed=false" /tmp/phase289_304_final_review_pack_check.out; then
  echo "[FAIL] Missing review pack input did not keep action_allowed=false"
  exit 1
fi

python - <<'PY'
import csv
from pathlib import Path

csv_path = Path("ibkr_final_research_review_pack.csv")
report_path = Path("reports/ibkr_final_research_review_pack_report.md")
if not csv_path.exists():
    raise SystemExit("[FAIL] Missing final research review pack CSV output")
if not report_path.exists():
    raise SystemExit("[FAIL] Missing final research review pack report output")

rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
if len(rows) != 1:
    raise SystemExit(f"[FAIL] Expected one missing-input final review row, got {len(rows)}")
row = rows[0]
if row["final_review_status"] != "FINAL_REVIEW_BLOCKED" or row["final_decision_label"] != "BLOCKED":
    raise SystemExit("[FAIL] Missing input row must be FINAL_REVIEW_BLOCKED / BLOCKED")
if row["final_research_bucket"] != "no_go":
    raise SystemExit("[FAIL] Missing input row must be no_go bucket")
for key in (
    "action_allowed",
    "broker_execution_triggered",
    "historical_data_request_triggered",
    "account_read_triggered",
    "position_read_triggered",
):
    if row[key] != "false":
        raise SystemExit(f"[FAIL] {key} must be false")
if row["manual_review_required"] != "true":
    raise SystemExit("[FAIL] manual_review_required must be true")

report_text = report_path.read_text(encoding="utf-8")
for required in (
    "Final Research Review Decision",
    "Input Review Pack Status",
    "Symbol Final Review Rows",
    "Research Bucket Summary",
    "Safety Confirmation",
    "Operator Handoff",
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

print("[PASS] Missing input NO_GO final research review pack validated")
PY

if rg -nE "\.(placeOrder|cancelOrder|whatIfOrder|bracketOrder|exerciseOptions|reqGlobalCancel)\s*\(" main.py src/ibkr_final_research_review_pack.py scripts/ibkr_final_research_review_pack.sh >/dev/null 2>&1; then
  echo "[FAIL] Forbidden broker trading call found"
  exit 1
fi

if rg -nE "\.(reqAccount|reqPositions|accountSummary|managedAccounts)\s*\(" main.py src/ibkr_final_research_review_pack.py scripts/ibkr_final_research_review_pack.sh >/dev/null 2>&1; then
  echo "[FAIL] Forbidden account or position read found"
  exit 1
fi

echo "[PASS] Phase 289-304 final research review pack bridge check completed"
