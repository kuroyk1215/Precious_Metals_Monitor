#!/usr/bin/env bash
set -euo pipefail

EXECUTION_C_PACKET="ibkr_execution_c_validation_packet.csv"
SNAPSHOT_CSV="ibkr_market_data_snapshot.csv"
SNAPSHOT_REPORT="reports/ibkr_market_data_snapshot_report.md"
API_ERRORS_CSV=""
OPERATOR_PACKET="ibkr_daily_operator_packet.csv"
TELEGRAM_NOTIFICATION_PACKET="ibkr_telegram_notification_packet.csv"
OUTPUT_CSV="first_operator_run_post_analysis.csv"
OUTPUT_REPORT="reports/first_operator_run_post_analysis_report.md"
SUMMARY_MD="reports/first_operator_run_summary.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execution-c-packet=*)
      EXECUTION_C_PACKET="${1#--execution-c-packet=}"
      shift
      ;;
    --execution-c-packet)
      EXECUTION_C_PACKET="${2:?--execution-c-packet requires a path}"
      shift 2
      ;;
    --snapshot-csv=*)
      SNAPSHOT_CSV="${1#--snapshot-csv=}"
      shift
      ;;
    --snapshot-csv)
      SNAPSHOT_CSV="${2:?--snapshot-csv requires a path}"
      shift 2
      ;;
    --snapshot-report=*)
      SNAPSHOT_REPORT="${1#--snapshot-report=}"
      shift
      ;;
    --snapshot-report)
      SNAPSHOT_REPORT="${2:?--snapshot-report requires a path}"
      shift 2
      ;;
    --api-errors-csv=*)
      API_ERRORS_CSV="${1#--api-errors-csv=}"
      shift
      ;;
    --api-errors-csv)
      API_ERRORS_CSV="${2:?--api-errors-csv requires a path}"
      shift 2
      ;;
    --operator-packet=*)
      OPERATOR_PACKET="${1#--operator-packet=}"
      shift
      ;;
    --operator-packet)
      OPERATOR_PACKET="${2:?--operator-packet requires a path}"
      shift 2
      ;;
    --telegram-notification-packet=*)
      TELEGRAM_NOTIFICATION_PACKET="${1#--telegram-notification-packet=}"
      shift
      ;;
    --telegram-notification-packet)
      TELEGRAM_NOTIFICATION_PACKET="${2:?--telegram-notification-packet requires a path}"
      shift 2
      ;;
    --output-csv=*)
      OUTPUT_CSV="${1#--output-csv=}"
      shift
      ;;
    --output-csv)
      OUTPUT_CSV="${2:?--output-csv requires a path}"
      shift 2
      ;;
    --output-report=*)
      OUTPUT_REPORT="${1#--output-report=}"
      shift
      ;;
    --output-report)
      OUTPUT_REPORT="${2:?--output-report requires a path}"
      shift 2
      ;;
    --summary-md=*)
      SUMMARY_MD="${1#--summary-md=}"
      shift
      ;;
    --summary-md)
      SUMMARY_MD="${2:?--summary-md requires a path}"
      shift 2
      ;;
    *)
      echo "[FAIL] Unknown argument: $1"
      exit 2
      ;;
  esac
done

ARGS=(
  -m src.first_operator_run_post_analysis
  --execution-c-packet "$EXECUTION_C_PACKET"
  --snapshot-csv "$SNAPSHOT_CSV"
  --snapshot-report "$SNAPSHOT_REPORT"
  --operator-packet "$OPERATOR_PACKET"
  --telegram-notification-packet "$TELEGRAM_NOTIFICATION_PACKET"
  --output-csv "$OUTPUT_CSV"
  --output-report "$OUTPUT_REPORT"
  --summary-md "$SUMMARY_MD"
)

if [[ -n "$API_ERRORS_CSV" ]]; then
  ARGS+=(--api-errors-csv "$API_ERRORS_CSV")
fi

python3 "${ARGS[@]}"
