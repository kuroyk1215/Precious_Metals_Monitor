#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 109-120 scheduler dry-run check"

required_files=(
  "docs/SCHEDULER_DRY_RUN_PLAN.md"
  "examples/launchd_daily_research_run.sample.plist"
  "scripts/scheduler_dryrun_plan.sh"
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

echo "[INFO] Generate scheduler dry-run plan"
./scripts/scheduler_dryrun_plan.sh

echo "[INFO] Required output check"
required_outputs=(
  "scheduler_dryrun_plan.csv"
  "reports/scheduler_dryrun_report.md"
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

path = Path("scheduler_dryrun_plan.csv")
required_header = [
    "run_id",
    "run_timestamp",
    "timezone",
    "market",
    "time_jst",
    "workflow",
    "launchd_installed",
    "launchctl_called",
    "telegram_api_called",
    "broker_execution_triggered",
    "auto_trade_allowed",
    "manual_review_required",
    "action_allowed",
]

with path.open(newline="") as f:
    reader = csv.DictReader(f)
    if reader.fieldnames != required_header:
        raise SystemExit(f"[FAIL] Unexpected header: {reader.fieldnames}")
    rows = list(reader)

if len(rows) != 6:
    raise SystemExit(f"[FAIL] Expected 6 schedule rows, got {len(rows)}")

expected_times = {"08:30", "12:00", "16:00", "21:30", "01:00", "05:15"}
actual_times = {row["time_jst"] for row in rows}
if actual_times != expected_times:
    raise SystemExit(f"[FAIL] Unexpected schedule times: {actual_times}")

for row in rows:
    if row["timezone"] != "Asia/Tokyo":
        raise SystemExit(f"[FAIL] timezone mismatch: {row}")
    for key in (
        "launchd_installed",
        "launchctl_called",
        "telegram_api_called",
        "broker_execution_triggered",
        "auto_trade_allowed",
        "action_allowed",
    ):
        if row[key] != "false":
            raise SystemExit(f"[FAIL] {key} must be false: {row}")
    if row["manual_review_required"] != "true":
        raise SystemExit(f"[FAIL] manual_review_required must be true: {row}")

print("[PASS] Scheduler dry-run CSV schema and safety flags are valid")
PY

echo "[INFO] Launchd sample safety check"
grep -q "Disabled" examples/launchd_daily_research_run.sample.plist
grep -q "PLACEHOLDER_PROJECT_ROOT" examples/launchd_daily_research_run.sample.plist
grep -q -- "--skip-tests" examples/launchd_daily_research_run.sample.plist

echo "[INFO] Markdown safety check"
grep -q "launchd_installed=false" reports/scheduler_dryrun_report.md
grep -q "launchctl_called=false" reports/scheduler_dryrun_report.md
grep -q "telegram_api_called=false" reports/scheduler_dryrun_report.md
grep -q "broker_execution_triggered=false" reports/scheduler_dryrun_report.md
grep -q "auto_trade_allowed=false" reports/scheduler_dryrun_report.md
grep -q "manual_review_required=true" reports/scheduler_dryrun_report.md
grep -q "action_allowed=false" reports/scheduler_dryrun_report.md

echo "[INFO] No installed LaunchAgent check"
if [[ -f "$HOME/Library/LaunchAgents/com.precious-metals-monitor.daily-research-run.plist" ]]; then
  echo "[FAIL] Real LaunchAgent appears to exist"
  exit 1
fi

echo "[INFO] Runtime output git hygiene check"
if git status --short | grep -E "scheduler_dryrun_plan.csv|reports/scheduler_dryrun_report.md" >/dev/null 2>&1; then
  echo "[FAIL] Scheduler runtime output appears in git status"
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

echo "[PASS] Scheduler dry-run plan generated"
echo "[PASS] Scheduler CSV schema and safety flags are valid"
echo "[PASS] Launchd sample is disabled and placeholder-only"
echo "[PASS] No real LaunchAgent installed"
echo "[PASS] Runtime outputs do not pollute git status"
echo "[PASS] config.yaml is not staged"
echo "[PASS] No active Python trading API keyword found"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
