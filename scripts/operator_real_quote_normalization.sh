#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
LATEST_CSV="operator_real_marketdata_latest.csv"
DAILY_SUMMARY_CSV="operator_real_marketdata_daily_run_summary.csv"
DECISION_GATE_CSV="operator_real_marketdata_decision_gate.csv"
OUTPUT_CSV="operator_real_quote_normalization.csv"
OUTPUT_REPORT="reports/operator_real_quote_normalization_report.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --latest-csv=*) LATEST_CSV="${1#--latest-csv=}"; shift ;;
    --latest-csv) LATEST_CSV="${2:?--latest-csv requires a path}"; shift 2 ;;
    --daily-summary-csv=*) DAILY_SUMMARY_CSV="${1#--daily-summary-csv=}"; shift ;;
    --daily-summary-csv) DAILY_SUMMARY_CSV="${2:?--daily-summary-csv requires a path}"; shift 2 ;;
    --decision-gate-csv=*) DECISION_GATE_CSV="${1#--decision-gate-csv=}"; shift ;;
    --decision-gate-csv) DECISION_GATE_CSV="${2:?--decision-gate-csv requires a path}"; shift 2 ;;
    --output-csv=*) OUTPUT_CSV="${1#--output-csv=}"; shift ;;
    --output-csv) OUTPUT_CSV="${2:?--output-csv requires a path}"; shift 2 ;;
    --output-report=*) OUTPUT_REPORT="${1#--output-report=}"; shift ;;
    --output-report) OUTPUT_REPORT="${2:?--output-report requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m src.operator_real_quote_normalization \
  --latest-csv "$LATEST_CSV" \
  --daily-summary-csv "$DAILY_SUMMARY_CSV" \
  --decision-gate-csv "$DECISION_GATE_CSV" \
  --output-csv "$OUTPUT_CSV" \
  --output-report "$OUTPUT_REPORT"
