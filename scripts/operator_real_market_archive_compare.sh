#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
BASE_DIR="."
OUTPUT_CSV="operator_real_market_archive_compare.csv"
OUTPUT_REPORT="reports/operator_real_market_archive_compare_report.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-dir=*) BASE_DIR="${1#--base-dir=}"; shift ;;
    --base-dir) BASE_DIR="${2:?--base-dir requires a path}"; shift 2 ;;
    --output-csv=*) OUTPUT_CSV="${1#--output-csv=}"; shift ;;
    --output-csv) OUTPUT_CSV="${2:?--output-csv requires a path}"; shift 2 ;;
    --output-report=*) OUTPUT_REPORT="${1#--output-report=}"; shift ;;
    --output-report) OUTPUT_REPORT="${2:?--output-report requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m src.operator_real_market_archive_compare \
  --base-dir "$BASE_DIR" \
  --output-csv "$OUTPUT_CSV" \
  --output-report "$OUTPUT_REPORT"
