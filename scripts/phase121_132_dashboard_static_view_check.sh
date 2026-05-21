#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 121-132 dashboard local static view check"

required_files=(
  "docs/DASHBOARD_LOCAL_STATIC_VIEW_PLAN.md"
  "examples/dashboard_manifest.sample.json"
  "scripts/dashboard_static_view_generate.sh"
  "scripts/daily_research_run.sh"
  "scripts/data_source_status_report.sh"
  "scripts/telegram_ready_digest.sh"
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

echo "[INFO] Generate dashboard local static view"
./scripts/dashboard_static_view_generate.sh

echo "[INFO] Required output check"
required_outputs=(
  "dashboard_static_view_summary.csv"
  "reports/dashboard_static_view_report.md"
  "reports/dashboard/index.html"
)

for file in "${required_outputs[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing generated output: $file"
    exit 1
  fi
done

echo "[INFO] Dashboard summary CSV schema check"
python3 - <<'PY'
import csv
from pathlib import Path

path = Path("dashboard_static_view_summary.csv")
required_header = [
    "run_id",
    "run_timestamp",
    "timezone",
    "branch",
    "commit",
    "workflow",
    "dashboard_status",
    "daily_summary_status",
    "data_source_status",
    "telegram_ready_status",
    "scheduler_status",
    "blocked_reason",
    "manual_review_required",
    "action_allowed",
    "broker_execution_triggered",
    "telegram_api_called",
    "scheduler_deployed",
    "auto_trade_allowed",
    "safety_boundary",
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
    "workflow": "dashboard_static_view",
    "dashboard_status": "STATIC_VIEW_READY",
    "telegram_ready_status": "TELEGRAM_BLOCKED",
    "scheduler_status": "DRY_RUN_ONLY",
    "manual_review_required": "true",
    "action_allowed": "false",
    "broker_execution_triggered": "false",
    "telegram_api_called": "false",
    "scheduler_deployed": "false",
    "auto_trade_allowed": "false",
    "safety_boundary": "research-only/read-only/manual-only/no-auto-trade",
}

for key, expected in checks.items():
    actual = row.get(key)
    if actual != expected:
        raise SystemExit(f"[FAIL] {key}: expected {expected}, got {actual}")

for key in ("run_id", "run_timestamp", "branch", "commit", "blocked_reason"):
    if not row.get(key):
        raise SystemExit(f"[FAIL] Missing value: {key}")

print("[PASS] Dashboard summary CSV is valid")
PY

echo "[INFO] Dashboard HTML safety check"
grep -q "Local Static Dashboard" reports/dashboard/index.html
grep -q "broker_execution_triggered=false" reports/dashboard/index.html
grep -q "telegram_api_called=false" reports/dashboard/index.html
grep -q "scheduler_deployed=false" reports/dashboard/index.html
grep -q "auto_trade_allowed=false" reports/dashboard/index.html
grep -q "action_allowed=false" reports/dashboard/index.html
grep -q "manual_review_required=true" reports/dashboard/index.html

echo "[INFO] Dashboard must not contain execution controls"
if grep -E "placeOrder|cancelOrder|bracketOrder|whatIfOrder|exerciseOptions|sendMessage|launchctl load|launchctl bootstrap" reports/dashboard/index.html >/dev/null 2>&1; then
  echo "[FAIL] Dashboard contains forbidden execution phrase"
  exit 1
fi

echo "[INFO] Runtime output git hygiene check"
if git status --short | grep -E "dashboard_static_view_summary.csv|reports/dashboard_static_view_report.md|reports/dashboard/|daily_research_run_summary.csv|data_source_status.csv|telegram_ready_summary.csv|scheduler_dryrun_plan.csv" >/dev/null 2>&1; then
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

echo "[PASS] Dashboard local static view generated"
echo "[PASS] Dashboard summary CSV is valid"
echo "[PASS] Dashboard HTML safety assertions are valid"
echo "[PASS] Dashboard contains no execution controls"
echo "[PASS] Runtime outputs do not pollute git status"
echo "[PASS] config.yaml is not staged"
echo "[PASS] No active Python trading API keyword found"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
