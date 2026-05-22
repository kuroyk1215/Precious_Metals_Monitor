#!/usr/bin/env bash
set -euo pipefail

OPERATOR_PACKET_CSV="ibkr_daily_operator_packet.csv"
PIPELINE_SUMMARY_CSV="ibkr_daily_research_pipeline_summary.csv"
RUNNER_SUMMARY_CSV="ibkr_local_daily_runner_summary.csv"
OUTPUT_CSV="ibkr_telegram_notification_packet.csv"
OUTPUT_REPORT="reports/ibkr_telegram_notification_packet_report.md"
MESSAGE_PREVIEW="reports/ibkr_telegram_message_preview.md"

for arg in "$@"; do
  case "$arg" in
    --operator-packet=*)
      OPERATOR_PACKET_CSV="${arg#--operator-packet=}"
      ;;
    --pipeline-summary=*)
      PIPELINE_SUMMARY_CSV="${arg#--pipeline-summary=}"
      ;;
    --runner-summary=*)
      RUNNER_SUMMARY_CSV="${arg#--runner-summary=}"
      ;;
    --output-csv=*)
      OUTPUT_CSV="${arg#--output-csv=}"
      ;;
    --output-report=*)
      OUTPUT_REPORT="${arg#--output-report=}"
      ;;
    --message-preview=*)
      MESSAGE_PREVIEW="${arg#--message-preview=}"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

export OPERATOR_PACKET_CSV PIPELINE_SUMMARY_CSV RUNNER_SUMMARY_CSV OUTPUT_CSV OUTPUT_REPORT MESSAGE_PREVIEW
export RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"

mkdir -p "$(dirname "$OUTPUT_REPORT")" "$(dirname "$MESSAGE_PREVIEW")"

echo "[INFO] IBKR Telegram notification packet dry-run started: ${RUN_TS}"

python3 - <<'PY'
from pathlib import Path
import os

from src.ibkr_telegram_notification_packet import (
    build_notification_rows,
    missing_operator_packet_row,
    read_csv_rows,
    summarize_statuses,
    write_message_preview,
    write_notification_csv,
    write_notification_report,
)

operator_path = Path(os.environ["OPERATOR_PACKET_CSV"])
pipeline_summary_path = Path(os.environ["PIPELINE_SUMMARY_CSV"])
runner_summary_path = Path(os.environ["RUNNER_SUMMARY_CSV"])
output_csv = Path(os.environ["OUTPUT_CSV"])
output_report = Path(os.environ["OUTPUT_REPORT"])
message_preview = Path(os.environ["MESSAGE_PREVIEW"])

operator_status, operator_rows = read_csv_rows(operator_path)
pipeline_status, _ = read_csv_rows(pipeline_summary_path)
runner_status, _ = read_csv_rows(runner_summary_path)

if operator_rows:
    rows = build_notification_rows(operator_rows)
else:
    rows = [missing_operator_packet_row(str(operator_path))]

write_notification_csv(output_csv, rows)
write_message_preview(message_preview, rows)
write_notification_report(
    output_report,
    rows,
    str(operator_path),
    operator_status,
    str(pipeline_summary_path),
    pipeline_status,
    str(runner_summary_path),
    runner_status,
    str(message_preview),
)

statuses = sorted({row.notification_status for row in rows})
severities = sorted({row.notification_severity for row in rows})
status_counts = summarize_statuses(rows)

print("[PASS] IBKR Telegram notification packet dry-run generated")
print("notification_packet_status=NO_GO")
print("telegram_send_triggered=false")
print("action_allowed=false")
print("broker_execution_triggered=false")
print("historical_data_request_triggered=false")
print("account_read_triggered=false")
print("position_read_triggered=false")
print("manual_review_required=true")
print(f"operator_packet_input_status={operator_status}")
print("notification_statuses=" + ",".join(statuses))
print("notification_severities=" + ",".join(severities))
print("notification_counts=" + ",".join(f"{k}:{v}" for k, v in sorted(status_counts.items())))
print(f"csv={output_csv}")
print(f"report={output_report}")
print(f"message_preview={message_preview}")
PY
