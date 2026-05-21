#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 77-80 daily run metadata schema check"

required_files=(
  "docs/DAILY_RESEARCH_RUN_SCHEMA.md"
  "scripts/daily_research_run.sh"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing required file: $file"
    exit 1
  fi
done

echo "[INFO] Daily research run"
./scripts/daily_research_run.sh

echo "[INFO] Required runtime outputs"
required_outputs=(
  "daily_research_run_summary.csv"
  "reports/daily_research_run_report.md"
)

for file in "${required_outputs[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing runtime output: $file"
    exit 1
  fi
done

echo "[INFO] Summary CSV schema check"
python3 - <<'PY'
import csv
from pathlib import Path

path = Path("daily_research_run_summary.csv")
required_header = [
    "schema_version",
    "run_id",
    "run_timestamp",
    "timezone",
    "branch",
    "commit",
    "workflow",
    "python_compile_passed",
    "pytest_passed",
    "final_research_plan_orchestrator_run",
    "report_template_daily_log_telegram_ready_output_run",
    "telegram_api_called",
    "scheduler_deployed",
    "broker_execution_triggered",
    "final_action_allowed",
    "manual_review_required",
    "safety_boundary",
]

with path.open(newline="") as f:
    reader = csv.DictReader(f)
    if reader.fieldnames != required_header:
        raise SystemExit(f"[FAIL] Unexpected header: {reader.fieldnames}")
    rows = list(reader)

if len(rows) != 1:
    raise SystemExit(f"[FAIL] Expected 1 summary row, got {len(rows)}")

row = rows[0]
checks = {
    "schema_version": "daily_research_run.v1",
    "timezone": "Asia/Tokyo",
    "workflow": "daily_research_run",
    "python_compile_passed": "true",
    "pytest_passed": "true",
    "final_research_plan_orchestrator_run": "true",
    "report_template_daily_log_telegram_ready_output_run": "true",
    "telegram_api_called": "false",
    "scheduler_deployed": "false",
    "broker_execution_triggered": "false",
    "final_action_allowed": "false",
    "manual_review_required": "true",
    "safety_boundary": "research-only/read-only/manual-only/no-auto-trade",
}

for key, expected in checks.items():
    actual = row.get(key)
    if actual != expected:
        raise SystemExit(f"[FAIL] {key}: expected {expected}, got {actual}")

for key in ("run_id", "run_timestamp", "branch", "commit"):
    if not row.get(key):
        raise SystemExit(f"[FAIL] Missing metadata value: {key}")

if not row["run_id"].endswith("_JST"):
    raise SystemExit(f"[FAIL] run_id does not end with _JST: {row['run_id']}")

print("[PASS] Summary CSV schema and metadata are valid")
PY

echo "[INFO] Markdown report metadata check"
grep -q "schema_version: daily_research_run.v1" reports/daily_research_run_report.md
grep -q "timezone: Asia/Tokyo" reports/daily_research_run_report.md
grep -q "## 3. Artifact manifest" reports/daily_research_run_report.md
grep -q "telegram_api_called=false" reports/daily_research_run_report.md
grep -q "scheduler_deployed=false" reports/daily_research_run_report.md
grep -q "broker_execution_triggered=false" reports/daily_research_run_report.md
grep -q "final_action_allowed=false" reports/daily_research_run_report.md
grep -q "manual_review_required=true" reports/daily_research_run_report.md

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

echo "[PASS] Daily research run metadata schema is valid"
echo "[PASS] Markdown report contains artifact manifest"
echo "[PASS] Runtime outputs do not pollute git status"
echo "[PASS] config.yaml is not staged"
echo "[PASS] No active Python trading API keyword found"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
