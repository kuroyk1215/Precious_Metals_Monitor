#!/usr/bin/env bash
set -euo pipefail

TIMEZONE="Asia/Tokyo"
HOUR="16"
MINUTE="10"
LOG_ROOT="logs/ibkr_daily"
REPORT_PATH="reports/ibkr_scheduler_plan_report.md"
PLIST_PATH="docs/examples/com.kuroyk.ibkr-daily-runner.plist.example"
CRON_PATH="docs/examples/ibkr_daily_runner_cron.example"

for arg in "$@"; do
  case "$arg" in
    --timezone=*)
      TIMEZONE="${arg#--timezone=}"
      ;;
    --hour=*)
      HOUR="${arg#--hour=}"
      ;;
    --minute=*)
      MINUTE="${arg#--minute=}"
      ;;
    --log-root=*)
      LOG_ROOT="${arg#--log-root=}"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

export TIMEZONE HOUR MINUTE LOG_ROOT REPORT_PATH PLIST_PATH CRON_PATH
mkdir -p reports docs/examples

python3 - <<'PY'
from pathlib import Path
import os

timezone = os.environ["TIMEZONE"]
hour = os.environ["HOUR"]
minute = os.environ["MINUTE"]
log_root = os.environ["LOG_ROOT"]
plist_path = Path(os.environ["PLIST_PATH"])
cron_path = Path(os.environ["CRON_PATH"])
report_path = Path(os.environ["REPORT_PATH"])

plist_path.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.kuroyk.ibkr-daily-runner</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>PLACEHOLDER_PROJECT_ROOT/scripts/ibkr_local_daily_runner.sh</string>
    <string>--log-root={log_root}</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>{hour}</integer>
    <key>Minute</key>
    <integer>{minute}</integer>
  </dict>
  <key>WorkingDirectory</key>
  <string>PLACEHOLDER_PROJECT_ROOT</string>
  <key>Disabled</key>
  <true/>
</dict>
</plist>
""", encoding="utf-8")

cron_path.write_text(
    f"# Example only. Do not install automatically.\n"
    f"# Timezone target: {timezone}\n"
    f"{minute} {hour} * * 1-5 cd PLACEHOLDER_PROJECT_ROOT && /bin/bash scripts/ibkr_local_daily_runner.sh --log-root={log_root}\n",
    encoding="utf-8",
)

report_path.write_text(
    "\n".join(
        [
            "# IBKR Scheduler Plan",
            "",
            "## Scheduler Decision",
            "",
            "| field | value |",
            "|---|---|",
            "| scheduler_install_triggered | false |",
            "| launchctl_triggered | false |",
            "| crontab_modified | false |",
            "| action_allowed | false |",
            f"| timezone | {timezone} |",
            f"| hour | {hour} |",
            f"| minute | {minute} |",
            f"| log_root | {log_root} |",
            "",
            "## Generated Examples",
            "",
            f"- launchd_example={plist_path}",
            f"- cron_example={cron_path}",
            "",
            "## Manual Installation Notes",
            "",
            "Review examples manually before installing. This script does not call launchctl and does not modify crontab.",
            "",
            "## Safety Confirmation",
            "",
            "- scheduler_install_triggered=false",
            "- launchctl_triggered=false",
            "- crontab_modified=false",
            "- action_allowed=false",
            "- broker_execution_triggered=false",
            "- historical_data_request_triggered=false",
            "- account_read_triggered=false",
            "- position_read_triggered=false",
        ]
    )
    + "\n",
    encoding="utf-8",
)
PY

echo "[PASS] IBKR scheduler plan generated"
echo "scheduler_install_triggered=false"
echo "launchctl_triggered=false"
echo "crontab_modified=false"
echo "action_allowed=false"
echo "report=${REPORT_PATH}"
echo "launchd_example=${PLIST_PATH}"
echo "cron_example=${CRON_PATH}"
