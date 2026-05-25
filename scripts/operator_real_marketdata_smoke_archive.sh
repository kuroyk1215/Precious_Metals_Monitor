#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
SOURCE_SUMMARY_FILE="operator_real_marketdata_smoke_summary.csv"
SOURCE_REPORT_FILE="reports/operator_real_marketdata_smoke_report.md"
OUTPUT_CSV="operator_real_marketdata_smoke_archive.csv"
OUTPUT_REPORT="reports/operator_real_marketdata_smoke_archive_report.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-summary-file=*) SOURCE_SUMMARY_FILE="${1#--source-summary-file=}"; shift ;;
    --source-summary-file) SOURCE_SUMMARY_FILE="${2:?--source-summary-file requires a path}"; shift 2 ;;
    --source-report-file=*) SOURCE_REPORT_FILE="${1#--source-report-file=}"; shift ;;
    --source-report-file) SOURCE_REPORT_FILE="${2:?--source-report-file requires a path}"; shift 2 ;;
    --output-csv=*) OUTPUT_CSV="${1#--output-csv=}"; shift ;;
    --output-csv) OUTPUT_CSV="${2:?--output-csv requires a path}"; shift 2 ;;
    --output-report=*) OUTPUT_REPORT="${1#--output-report=}"; shift ;;
    --output-report) OUTPUT_REPORT="${2:?--output-report requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m src.operator_real_marketdata_smoke_archive \
  --source-summary-file "$SOURCE_SUMMARY_FILE" \
  --source-report-file "$SOURCE_REPORT_FILE" \
  --output-csv "$OUTPUT_CSV" \
  --output-report "$OUTPUT_REPORT"
