#!/usr/bin/env bash
set -u -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
SMOKE_SUMMARY_CSV="operator_real_marketdata_smoke_summary.csv"
SMOKE_REPORT="reports/operator_real_marketdata_smoke_report.md"
SNAPSHOT_CSV="ibkr_market_data_snapshot.csv"
ARCHIVE_CSV="operator_real_marketdata_smoke_archive.csv"
ARCHIVE_REPORT="reports/operator_real_marketdata_smoke_archive_report.md"
DECISION_CSV="operator_real_marketdata_decision_gate.csv"
DECISION_REPORT="reports/operator_real_marketdata_decision_gate_report.md"
LATEST_CSV="operator_real_marketdata_latest.csv"
LATEST_REPORT="reports/operator_real_marketdata_latest_report.md"
SUMMARY_CSV="operator_real_marketdata_daily_run_summary.csv"
SUMMARY_REPORT="reports/operator_real_marketdata_daily_run_report.md"
SMOKE_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --smoke-summary-csv=*) SMOKE_SUMMARY_CSV="${1#--smoke-summary-csv=}"; shift ;;
    --smoke-summary-csv) SMOKE_SUMMARY_CSV="${2:?--smoke-summary-csv requires a path}"; shift 2 ;;
    --smoke-report=*) SMOKE_REPORT="${1#--smoke-report=}"; shift ;;
    --smoke-report) SMOKE_REPORT="${2:?--smoke-report requires a path}"; shift 2 ;;
    --snapshot-csv=*) SNAPSHOT_CSV="${1#--snapshot-csv=}"; shift ;;
    --snapshot-csv) SNAPSHOT_CSV="${2:?--snapshot-csv requires a path}"; shift 2 ;;
    --archive-csv=*) ARCHIVE_CSV="${1#--archive-csv=}"; shift ;;
    --archive-csv) ARCHIVE_CSV="${2:?--archive-csv requires a path}"; shift 2 ;;
    --archive-report=*) ARCHIVE_REPORT="${1#--archive-report=}"; shift ;;
    --archive-report) ARCHIVE_REPORT="${2:?--archive-report requires a path}"; shift 2 ;;
    --decision-csv=*) DECISION_CSV="${1#--decision-csv=}"; shift ;;
    --decision-csv) DECISION_CSV="${2:?--decision-csv requires a path}"; shift 2 ;;
    --decision-report=*) DECISION_REPORT="${1#--decision-report=}"; shift ;;
    --decision-report) DECISION_REPORT="${2:?--decision-report requires a path}"; shift 2 ;;
    --latest-csv=*) LATEST_CSV="${1#--latest-csv=}"; shift ;;
    --latest-csv) LATEST_CSV="${2:?--latest-csv requires a path}"; shift 2 ;;
    --latest-report=*) LATEST_REPORT="${1#--latest-report=}"; shift ;;
    --latest-report) LATEST_REPORT="${2:?--latest-report requires a path}"; shift 2 ;;
    --summary-csv=*) SUMMARY_CSV="${1#--summary-csv=}"; shift ;;
    --summary-csv) SUMMARY_CSV="${2:?--summary-csv requires a path}"; shift 2 ;;
    --summary-report=*) SUMMARY_REPORT="${1#--summary-report=}"; shift ;;
    --summary-report) SUMMARY_REPORT="${2:?--summary-report requires a path}"; shift 2 ;;
    *) SMOKE_ARGS+=("$1"); shift ;;
  esac
done

SMOKE_EXIT_CODE=0
ARCHIVE_EXIT_CODE=0
DECISION_EXIT_CODE=0
LATEST_EXIT_CODE=0

echo "[INFO] Phase 446 daily real marketdata operator chain started"

bash scripts/operator_real_marketdata_smoke.sh \
  --output-csv "$SMOKE_SUMMARY_CSV" \
  --output-report "$SMOKE_REPORT" \
  --snapshot-csv "$SNAPSHOT_CSV" \
  ${SMOKE_ARGS[@]+"${SMOKE_ARGS[@]}"}
SMOKE_EXIT_CODE=$?
echo "[INFO] smoke_exit_code=${SMOKE_EXIT_CODE}"

bash scripts/operator_real_marketdata_smoke_archive.sh \
  --source-summary-file "$SMOKE_SUMMARY_CSV" \
  --source-report-file "$SMOKE_REPORT" \
  --output-csv "$ARCHIVE_CSV" \
  --output-report "$ARCHIVE_REPORT"
ARCHIVE_EXIT_CODE=$?
echo "[INFO] archive_exit_code=${ARCHIVE_EXIT_CODE}"

bash scripts/operator_real_marketdata_decision_gate.sh \
  --source-archive-file "$ARCHIVE_CSV" \
  --output-csv "$DECISION_CSV" \
  --output-report "$DECISION_REPORT"
DECISION_EXIT_CODE=$?
echo "[INFO] decision_exit_code=${DECISION_EXIT_CODE}"

bash scripts/operator_real_marketdata_latest.sh \
  --source-summary-file "$SMOKE_SUMMARY_CSV" \
  --source-archive-file "$ARCHIVE_CSV" \
  --source-decision-file "$DECISION_CSV" \
  --output-csv "$LATEST_CSV" \
  --output-report "$LATEST_REPORT"
LATEST_EXIT_CODE=$?
echo "[INFO] latest_exit_code=${LATEST_EXIT_CODE}"

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m src.operator_real_marketdata_daily_run \
  --smoke-exit-code "$SMOKE_EXIT_CODE" \
  --archive-exit-code "$ARCHIVE_EXIT_CODE" \
  --decision-exit-code "$DECISION_EXIT_CODE" \
  --latest-exit-code "$LATEST_EXIT_CODE" \
  --latest-csv "$LATEST_CSV" \
  --output-csv "$SUMMARY_CSV" \
  --output-report "$SUMMARY_REPORT"
SUMMARY_EXIT_CODE=$?

if [[ "$SUMMARY_EXIT_CODE" -ne 0 ]]; then
  exit "$SUMMARY_EXIT_CODE"
fi

if [[ "$ARCHIVE_EXIT_CODE" -ne 0 || "$LATEST_EXIT_CODE" -ne 0 ]]; then
  exit 1
fi

exit 0
