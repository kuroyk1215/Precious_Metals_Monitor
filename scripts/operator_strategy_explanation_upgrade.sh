#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
SPREAD_FRAMEWORK_CSV="operator_gld_slv_spread_framework.csv"
RANGE_FRAMEWORK_CSV="operator_real_market_range_framework.csv"
STRATEGY_QUALITY_CSV="operator_strategy_quality_report.csv"
MVP_READINESS_CSV="operator_mvp_readiness_report.csv"
OUTPUT_CSV="operator_strategy_explanation_upgrade.csv"
OUTPUT_REPORT="reports/operator_strategy_explanation_upgrade_report.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --spread-framework-csv=*) SPREAD_FRAMEWORK_CSV="${1#--spread-framework-csv=}"; shift ;;
    --spread-framework-csv) SPREAD_FRAMEWORK_CSV="${2:?--spread-framework-csv requires a path}"; shift 2 ;;
    --range-framework-csv=*) RANGE_FRAMEWORK_CSV="${1#--range-framework-csv=}"; shift ;;
    --range-framework-csv) RANGE_FRAMEWORK_CSV="${2:?--range-framework-csv requires a path}"; shift 2 ;;
    --strategy-quality-csv=*) STRATEGY_QUALITY_CSV="${1#--strategy-quality-csv=}"; shift ;;
    --strategy-quality-csv) STRATEGY_QUALITY_CSV="${2:?--strategy-quality-csv requires a path}"; shift 2 ;;
    --mvp-readiness-csv=*) MVP_READINESS_CSV="${1#--mvp-readiness-csv=}"; shift ;;
    --mvp-readiness-csv) MVP_READINESS_CSV="${2:?--mvp-readiness-csv requires a path}"; shift 2 ;;
    --output-csv=*) OUTPUT_CSV="${1#--output-csv=}"; shift ;;
    --output-csv) OUTPUT_CSV="${2:?--output-csv requires a path}"; shift 2 ;;
    --output-report=*) OUTPUT_REPORT="${1#--output-report=}"; shift ;;
    --output-report) OUTPUT_REPORT="${2:?--output-report requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m src.operator_strategy_explanation_upgrade \
  --spread-framework-csv "$SPREAD_FRAMEWORK_CSV" \
  --range-framework-csv "$RANGE_FRAMEWORK_CSV" \
  --strategy-quality-csv "$STRATEGY_QUALITY_CSV" \
  --mvp-readiness-csv "$MVP_READINESS_CSV" \
  --output-csv "$OUTPUT_CSV" \
  --output-report "$OUTPUT_REPORT"
