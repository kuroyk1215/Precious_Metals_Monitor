#!/usr/bin/env bash
set -euo pipefail

CONTRACT_MAP_CSV="ibkr_verified_contract_map_gld_slv.csv"
SNAPSHOT_CSV="ibkr_market_data_snapshot.csv"
API_ERRORS_CSV="ibkr_market_data_api_errors.csv"
EXECUTION_C_PACKET="ibkr_execution_c_validation_packet.csv"
OPERATOR_PACKET="ibkr_daily_operator_packet.csv"
POST_ANALYSIS_CSV="first_operator_run_post_analysis.csv"
TELEGRAM_NOTIFICATION_PACKET="ibkr_telegram_notification_packet.csv"
OUTPUT_CSV="daily_operator_handoff_summary.csv"
OUTPUT_REPORT="reports/daily_operator_handoff_summary.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --contract-map-csv=*) CONTRACT_MAP_CSV="${1#--contract-map-csv=}"; shift ;;
    --contract-map-csv) CONTRACT_MAP_CSV="${2:?--contract-map-csv requires a path}"; shift 2 ;;
    --snapshot-csv=*) SNAPSHOT_CSV="${1#--snapshot-csv=}"; shift ;;
    --snapshot-csv) SNAPSHOT_CSV="${2:?--snapshot-csv requires a path}"; shift 2 ;;
    --api-errors-csv=*) API_ERRORS_CSV="${1#--api-errors-csv=}"; shift ;;
    --api-errors-csv) API_ERRORS_CSV="${2:?--api-errors-csv requires a path}"; shift 2 ;;
    --execution-c-packet=*) EXECUTION_C_PACKET="${1#--execution-c-packet=}"; shift ;;
    --execution-c-packet) EXECUTION_C_PACKET="${2:?--execution-c-packet requires a path}"; shift 2 ;;
    --operator-packet=*) OPERATOR_PACKET="${1#--operator-packet=}"; shift ;;
    --operator-packet) OPERATOR_PACKET="${2:?--operator-packet requires a path}"; shift 2 ;;
    --post-analysis-csv=*) POST_ANALYSIS_CSV="${1#--post-analysis-csv=}"; shift ;;
    --post-analysis-csv) POST_ANALYSIS_CSV="${2:?--post-analysis-csv requires a path}"; shift 2 ;;
    --telegram-notification-packet=*) TELEGRAM_NOTIFICATION_PACKET="${1#--telegram-notification-packet=}"; shift ;;
    --telegram-notification-packet) TELEGRAM_NOTIFICATION_PACKET="${2:?--telegram-notification-packet requires a path}"; shift 2 ;;
    --output-csv=*) OUTPUT_CSV="${1#--output-csv=}"; shift ;;
    --output-csv) OUTPUT_CSV="${2:?--output-csv requires a path}"; shift 2 ;;
    --output-report=*) OUTPUT_REPORT="${1#--output-report=}"; shift ;;
    --output-report) OUTPUT_REPORT="${2:?--output-report requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

python3 -m src.daily_operator_handoff_summary \
  --contract-map-csv "$CONTRACT_MAP_CSV" \
  --snapshot-csv "$SNAPSHOT_CSV" \
  --api-errors-csv "$API_ERRORS_CSV" \
  --execution-c-packet "$EXECUTION_C_PACKET" \
  --operator-packet "$OPERATOR_PACKET" \
  --post-analysis-csv "$POST_ANALYSIS_CSV" \
  --telegram-notification-packet "$TELEGRAM_NOTIFICATION_PACKET" \
  --output-csv "$OUTPUT_CSV" \
  --output-report "$OUTPUT_REPORT"
