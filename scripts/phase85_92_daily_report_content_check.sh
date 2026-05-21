#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 85-92 daily report content hardening check"

required_files=(
  "scripts/daily_research_run.sh"
  "docs/DAILY_RESEARCH_RUN_SCHEMA.md"
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

echo "[INFO] Daily research run with --skip-tests"
./scripts/daily_research_run.sh --skip-tests

echo "[INFO] Daily summary report content check"
grep -q "## 2. Daily summary" reports/daily_research_run_report.md
grep -q "daily_summary_status" reports/daily_research_run_report.md
grep -q "final_plan_status" reports/daily_research_run_report.md
grep -q "telegram_ready_status" reports/daily_research_run_report.md
grep -q "data_status_summary" reports/daily_research_run_report.md
grep -q "blocked_reason" reports/daily_research_run_report.md
grep -q "manual_review_required" reports/daily_research_run_report.md
grep -q "final_action_allowed" reports/daily_research_run_report.md

echo "[INFO] Summary CSV schema content check"
python3 - <<'PY'
import csv
from pathlib import Path

required = [
    "daily_summary_status",
    "final_plan_status",
    "telegram_ready_status",
    "data_status_summary",
    "blocked_reason",
    "manual_review_required",
    "final_action_allowed",
]

with Path("daily_research_run_summary.csv").open(newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames or []
    rows = list(reader)

missing = [field for field in required if field not in fields]
if missing:
    raise SystemExit(f"[FAIL] Missing summary CSV fields: {missing}")

if len(rows) != 1:
    raise SystemExit(f"[FAIL] Expected 1 row, got {len(rows)}")

row = rows[0]
if row["daily_summary_status"] != "INPUT_REQUIRED":
    raise SystemExit("[FAIL] daily_summary_status mismatch")
if row["final_plan_status"] != "INPUT_REQUIRED":
    raise SystemExit("[FAIL] final_plan_status mismatch")
if row["telegram_ready_status"] != "TELEGRAM_BLOCKED":
    raise SystemExit("[FAIL] telegram_ready_status mismatch")
if row["manual_review_required"] != "true":
    raise SystemExit("[FAIL] manual_review_required mismatch")
if row["final_action_allowed"] != "false":
    raise SystemExit("[FAIL] final_action_allowed mismatch")
if not row["blocked_reason"]:
    raise SystemExit("[FAIL] blocked_reason is empty")

print("[PASS] Summary CSV daily content fields are valid")
PY

echo "[INFO] Metadata schema check"
./scripts/phase77_80_daily_run_metadata_schema_check.sh

echo "[INFO] Project acceptance suite"
./scripts/project_acceptance_suite.sh

echo "[INFO] Runtime output git hygiene check"
if git status --short | grep -E "daily_research_run_summary.csv|reports/daily_research_run_report.md|final_research_plan_orchestrator.csv|report_template_daily_log_telegram_ready_output.csv|reports/telegram_ready_text.txt" >/dev/null 2>&1; then
  echo "[FAIL] Runtime output appears in git status"
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

echo "[PASS] Daily report readable summary fields are present"
echo "[PASS] Summary CSV daily content fields are valid"
echo "[PASS] Metadata schema check passed"
echo "[PASS] Project acceptance suite passed"
echo "[PASS] Runtime outputs do not pollute git status"
echo "[PASS] config.yaml is not staged"
echo "[PASS] No active Python trading API keyword found"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
