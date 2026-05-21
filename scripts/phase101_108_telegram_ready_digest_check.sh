#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 101-108 Telegram-ready readable digest check"

required_files=(
  "docs/TELEGRAM_READY_READABLE_DIGEST.md"
  "scripts/telegram_ready_digest.sh"
  "scripts/daily_research_run.sh"
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

echo "[INFO] Generate Telegram-ready readable digest"
./scripts/telegram_ready_digest.sh

echo "[INFO] Required output check"
required_outputs=(
  "telegram_ready_summary.csv"
  "reports/telegram_ready_report.md"
  "reports/telegram_ready_daily_digest.txt"
)

for file in "${required_outputs[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing generated output: $file"
    exit 1
  fi
done

echo "[INFO] Summary CSV schema check"
python3 - <<'PY'
import csv
from pathlib import Path

path = Path("telegram_ready_summary.csv")
required_header = [
    "run_id",
    "run_timestamp",
    "timezone",
    "branch",
    "commit",
    "workflow",
    "daily_summary_status",
    "final_plan_status",
    "telegram_ready_status",
    "data_source_status",
    "blocked_reason",
    "manual_review_required",
    "action_allowed",
    "telegram_api_called",
    "scheduler_deployed",
    "broker_execution_triggered",
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
    "workflow": "telegram_ready_digest",
    "daily_summary_status": "INPUT_REQUIRED",
    "final_plan_status": "INPUT_REQUIRED",
    "telegram_ready_status": "TELEGRAM_BLOCKED",
    "manual_review_required": "true",
    "action_allowed": "false",
    "telegram_api_called": "false",
    "scheduler_deployed": "false",
    "broker_execution_triggered": "false",
    "safety_boundary": "research-only/read-only/manual-only/no-auto-trade",
}

for key, expected in checks.items():
    actual = row.get(key)
    if actual != expected:
        raise SystemExit(f"[FAIL] {key}: expected {expected}, got {actual}")

for key in ("run_id", "run_timestamp", "branch", "commit", "blocked_reason"):
    if not row.get(key):
        raise SystemExit(f"[FAIL] Missing value: {key}")

print("[PASS] Telegram-ready summary CSV is valid")
PY

echo "[INFO] Digest content check"
grep -q "贵金属监控日报" reports/telegram_ready_daily_digest.txt
grep -q "telegram_ready_status: TELEGRAM_BLOCKED" reports/telegram_ready_daily_digest.txt
grep -q "manual_review_required: true" reports/telegram_ready_daily_digest.txt
grep -q "action_allowed: false" reports/telegram_ready_daily_digest.txt
grep -q "telegram_api_called: false" reports/telegram_ready_daily_digest.txt
grep -q "scheduler_deployed: false" reports/telegram_ready_daily_digest.txt
grep -q "broker_execution_triggered: false" reports/telegram_ready_daily_digest.txt
grep -q "未触发任何交易" reports/telegram_ready_daily_digest.txt

echo "[INFO] Markdown report safety check"
grep -q "telegram_api_called=false" reports/telegram_ready_report.md
grep -q "scheduler_deployed=false" reports/telegram_ready_report.md
grep -q "broker_execution_triggered=false" reports/telegram_ready_report.md
grep -q "action_allowed=false" reports/telegram_ready_report.md
grep -q "manual_review_required=true" reports/telegram_ready_report.md

echo "[INFO] Runtime output git hygiene check"
if git status --short | grep -E "telegram_ready_summary.csv|reports/telegram_ready_report.md|reports/telegram_ready_daily_digest.txt|data_source_status.csv|reports/data_source_status_report.md|daily_research_run_summary.csv|reports/daily_research_run_report.md" >/dev/null 2>&1; then
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

echo "[PASS] Telegram-ready readable digest generated"
echo "[PASS] Telegram-ready summary CSV is valid"
echo "[PASS] Digest content is readable"
echo "[PASS] Safety assertions are valid"
echo "[PASS] Runtime outputs do not pollute git status"
echo "[PASS] config.yaml is not staged"
echo "[PASS] No active Python trading API keyword found"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
