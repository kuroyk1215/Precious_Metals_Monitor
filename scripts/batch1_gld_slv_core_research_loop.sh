#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
QUOTE_CSV="operator_real_quote_normalization.csv"
OUTPUT_REPORT="reports/latest_gld_slv_research.md"
OUTPUT_CSV="logs/research_log_US.csv"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --quote-csv=*) QUOTE_CSV="${1#--quote-csv=}"; shift ;;
    --quote-csv) QUOTE_CSV="${2:?--quote-csv requires a path}"; shift 2 ;;
    --output-report=*) OUTPUT_REPORT="${1#--output-report=}"; shift ;;
    --output-report) OUTPUT_REPORT="${2:?--output-report requires a path}"; shift 2 ;;
    --output-csv=*) OUTPUT_CSV="${1#--output-csv=}"; shift ;;
    --output-csv) OUTPUT_CSV="${2:?--output-csv requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m src.batch1_gld_slv_core_research_loop \
  --quote-csv "$QUOTE_CSV" \
  --output-report "$OUTPUT_REPORT" \
  --output-csv "$OUTPUT_CSV"
