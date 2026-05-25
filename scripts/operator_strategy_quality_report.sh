#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
ARCHIVE_COMPARE_CSV="operator_real_market_archive_compare.csv"
THRESHOLD_EXPLAINER_CSV="operator_signal_threshold_explainer.csv"
MVP_STATUS_CSV="operator_real_market_mvp_status.csv"
DAILY_REPORT_CSV="operator_daily_real_market_report.csv"
OUTPUT_CSV="operator_strategy_quality_report.csv"
OUTPUT_REPORT="reports/operator_strategy_quality_report.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive-compare-csv=*) ARCHIVE_COMPARE_CSV="${1#--archive-compare-csv=}"; shift ;;
    --archive-compare-csv) ARCHIVE_COMPARE_CSV="${2:?--archive-compare-csv requires a path}"; shift 2 ;;
    --threshold-explainer-csv=*) THRESHOLD_EXPLAINER_CSV="${1#--threshold-explainer-csv=}"; shift ;;
    --threshold-explainer-csv) THRESHOLD_EXPLAINER_CSV="${2:?--threshold-explainer-csv requires a path}"; shift 2 ;;
    --mvp-status-csv=*) MVP_STATUS_CSV="${1#--mvp-status-csv=}"; shift ;;
    --mvp-status-csv) MVP_STATUS_CSV="${2:?--mvp-status-csv requires a path}"; shift 2 ;;
    --daily-report-csv=*) DAILY_REPORT_CSV="${1#--daily-report-csv=}"; shift ;;
    --daily-report-csv) DAILY_REPORT_CSV="${2:?--daily-report-csv requires a path}"; shift 2 ;;
    --output-csv=*) OUTPUT_CSV="${1#--output-csv=}"; shift ;;
    --output-csv) OUTPUT_CSV="${2:?--output-csv requires a path}"; shift 2 ;;
    --output-report=*) OUTPUT_REPORT="${1#--output-report=}"; shift ;;
    --output-report) OUTPUT_REPORT="${2:?--output-report requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m src.operator_strategy_quality_report \
  --archive-compare-csv "$ARCHIVE_COMPARE_CSV" \
  --threshold-explainer-csv "$THRESHOLD_EXPLAINER_CSV" \
  --mvp-status-csv "$MVP_STATUS_CSV" \
  --daily-report-csv "$DAILY_REPORT_CSV" \
  --output-csv "$OUTPUT_CSV" \
  --output-report "$OUTPUT_REPORT"
