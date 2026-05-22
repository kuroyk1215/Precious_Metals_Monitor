#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 321-336 IBKR local daily runner scheduler plan check"

CHECK_LOG_ROOT="/tmp/ibkr_daily_runner_check_logs"
rm -rf "$CHECK_LOG_ROOT"

PATH=.venv/bin:$PATH python -m py_compile main.py src/*.py
PATH=.venv/bin:$PATH PYTHONPATH=. python -m pytest -q

PATH=.venv/bin:$PATH bash scripts/ibkr_local_daily_runner.sh --log-root="$CHECK_LOG_ROOT" --retention-days=7 | tee /tmp/phase321_336_local_runner_check.out
PATH=.venv/bin:$PATH bash scripts/ibkr_scheduler_plan.sh --hour=16 --minute=10 | tee /tmp/phase321_336_scheduler_plan_check.out

if grep -q "execution_c_mode=execute_market_data" /tmp/phase321_336_local_runner_check.out; then
  echo "[FAIL] Default local runner must not trigger execute_market_data mode"
  exit 1
fi

for required in \
  "runner_status=NO_GO" \
  "execution_c_mode=dry_run" \
  "action_allowed=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false"; do
  if ! grep -q "$required" /tmp/phase321_336_local_runner_check.out; then
    echo "[FAIL] Local runner output missing $required"
    exit 1
  fi
done

if ! grep -q "scheduler_install_triggered=false" /tmp/phase321_336_scheduler_plan_check.out; then
  echo "[FAIL] Scheduler plan must not install scheduler"
  exit 1
fi
if ! grep -q "launchctl_triggered=false" /tmp/phase321_336_scheduler_plan_check.out; then
  echo "[FAIL] Scheduler plan must not trigger launchctl"
  exit 1
fi
if ! grep -q "crontab_modified=false" /tmp/phase321_336_scheduler_plan_check.out; then
  echo "[FAIL] Scheduler plan must not modify crontab"
  exit 1
fi

python - <<'PY'
import csv
from pathlib import Path

root = Path("/tmp/ibkr_daily_runner_check_logs")
summaries = sorted(root.glob("*/*/ibkr_local_daily_runner_summary.csv"))
reports = sorted(root.glob("*/*/ibkr_local_daily_runner_report.md"))
if not summaries:
    raise SystemExit("[FAIL] Local runner summary not found")
if not reports:
    raise SystemExit("[FAIL] Local runner report not found")

rows = list(csv.DictReader(summaries[-1].open(newline="", encoding="utf-8")))
if len(rows) != 1:
    raise SystemExit("[FAIL] Local runner summary must contain one row")
row = rows[0]
if row["execution_c_mode"] != "dry_run":
    raise SystemExit("[FAIL] Local runner summary must remain dry_run")
if row["pipeline_exit_code"] != "0":
    raise SystemExit("[FAIL] Default local runner pipeline must exit 0")
for key in (
    "action_allowed",
    "broker_execution_triggered",
    "historical_data_request_triggered",
    "account_read_triggered",
    "position_read_triggered",
):
    if row[key] != "false":
        raise SystemExit(f"[FAIL] Local runner {key} must be false")
if row["manual_review_required"] != "true":
    raise SystemExit("[FAIL] Local runner manual_review_required must be true")
if int(row["copied_file_count"]) < 1:
    raise SystemExit("[FAIL] Local runner should archive at least one output file")

scheduler_report = Path("reports/ibkr_scheduler_plan_report.md").read_text(encoding="utf-8")
for required in (
    "scheduler_install_triggered | false",
    "launchctl_triggered | false",
    "crontab_modified | false",
    "action_allowed | false",
):
    if required not in scheduler_report:
        raise SystemExit(f"[FAIL] Scheduler report missing {required}")
for example in (
    Path("docs/examples/com.kuroyk.ibkr-daily-runner.plist.example"),
    Path("docs/examples/ibkr_daily_runner_cron.example"),
):
    if not example.exists():
        raise SystemExit(f"[FAIL] Missing scheduler example: {example}")

print("[PASS] Local runner and scheduler outputs validated")
PY

if rg -nE "\.(placeOrder|cancelOrder|whatIfOrder|bracketOrder|exerciseOptions|reqGlobalCancel)\s*\(" src/ibkr_local_daily_runner.py scripts/ibkr_local_daily_runner.sh scripts/ibkr_scheduler_plan.sh >/dev/null 2>&1; then
  echo "[FAIL] Forbidden broker trading call found"
  exit 1
fi

if rg -nE "\.(reqAccount|reqPositions|accountSummary|managedAccounts)\s*\(" src/ibkr_local_daily_runner.py scripts/ibkr_local_daily_runner.sh scripts/ibkr_scheduler_plan.sh >/dev/null 2>&1; then
  echo "[FAIL] Forbidden account or position read found"
  exit 1
fi

echo "[PASS] Phase 321-336 local daily runner scheduler plan check completed"
