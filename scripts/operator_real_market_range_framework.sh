#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
NORMALIZATION_CSV="operator_real_quote_normalization.csv"
SPREAD_FRAMEWORK_CSV="operator_gld_slv_spread_framework.csv"
THRESHOLD_EXPLAINER_CSV="operator_signal_threshold_explainer.csv"
RESEARCH_PLAN_CSV="research_trading_plan.csv"
OUTPUT_CSV="operator_real_market_range_framework.csv"
OUTPUT_REPORT="reports/operator_real_market_range_framework_report.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --normalization-csv=*) NORMALIZATION_CSV="${1#--normalization-csv=}"; shift ;;
    --normalization-csv) NORMALIZATION_CSV="${2:?--normalization-csv requires a path}"; shift 2 ;;
    --spread-framework-csv=*) SPREAD_FRAMEWORK_CSV="${1#--spread-framework-csv=}"; shift ;;
    --spread-framework-csv) SPREAD_FRAMEWORK_CSV="${2:?--spread-framework-csv requires a path}"; shift 2 ;;
    --threshold-explainer-csv=*) THRESHOLD_EXPLAINER_CSV="${1#--threshold-explainer-csv=}"; shift ;;
    --threshold-explainer-csv) THRESHOLD_EXPLAINER_CSV="${2:?--threshold-explainer-csv requires a path}"; shift 2 ;;
    --research-plan-csv=*) RESEARCH_PLAN_CSV="${1#--research-plan-csv=}"; shift ;;
    --research-plan-csv) RESEARCH_PLAN_CSV="${2:?--research-plan-csv requires a path}"; shift 2 ;;
    --output-csv=*) OUTPUT_CSV="${1#--output-csv=}"; shift ;;
    --output-csv) OUTPUT_CSV="${2:?--output-csv requires a path}"; shift 2 ;;
    --output-report=*) OUTPUT_REPORT="${1#--output-report=}"; shift ;;
    --output-report) OUTPUT_REPORT="${2:?--output-report requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m src.operator_real_market_range_framework \
  --normalization-csv "$NORMALIZATION_CSV" \
  --spread-framework-csv "$SPREAD_FRAMEWORK_CSV" \
  --threshold-explainer-csv "$THRESHOLD_EXPLAINER_CSV" \
  --research-plan-csv "$RESEARCH_PLAN_CSV" \
  --output-csv "$OUTPUT_CSV" \
  --output-report "$OUTPUT_REPORT"
