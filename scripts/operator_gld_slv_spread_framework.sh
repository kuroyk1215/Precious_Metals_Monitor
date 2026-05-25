#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
NORMALIZATION_CSV="operator_real_quote_normalization.csv"
SIGNAL_BRIDGE_CSV="operator_real_quote_signal_bridge.csv"
DAILY_REPORT_CSV="operator_daily_real_market_report.csv"
OUTPUT_CSV="operator_gld_slv_spread_framework.csv"
OUTPUT_REPORT="reports/operator_gld_slv_spread_framework_report.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --normalization-csv=*) NORMALIZATION_CSV="${1#--normalization-csv=}"; shift ;;
    --normalization-csv) NORMALIZATION_CSV="${2:?--normalization-csv requires a path}"; shift 2 ;;
    --signal-bridge-csv=*) SIGNAL_BRIDGE_CSV="${1#--signal-bridge-csv=}"; shift ;;
    --signal-bridge-csv) SIGNAL_BRIDGE_CSV="${2:?--signal-bridge-csv requires a path}"; shift 2 ;;
    --daily-report-csv=*) DAILY_REPORT_CSV="${1#--daily-report-csv=}"; shift ;;
    --daily-report-csv) DAILY_REPORT_CSV="${2:?--daily-report-csv requires a path}"; shift 2 ;;
    --output-csv=*) OUTPUT_CSV="${1#--output-csv=}"; shift ;;
    --output-csv) OUTPUT_CSV="${2:?--output-csv requires a path}"; shift 2 ;;
    --output-report=*) OUTPUT_REPORT="${1#--output-report=}"; shift ;;
    --output-report) OUTPUT_REPORT="${2:?--output-report requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m src.operator_gld_slv_spread_framework \
  --normalization-csv "$NORMALIZATION_CSV" \
  --signal-bridge-csv "$SIGNAL_BRIDGE_CSV" \
  --daily-report-csv "$DAILY_REPORT_CSV" \
  --output-csv "$OUTPUT_CSV" \
  --output-report "$OUTPUT_REPORT"
