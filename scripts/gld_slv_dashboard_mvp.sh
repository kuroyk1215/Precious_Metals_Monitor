#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
CSV_PATH="logs/research_log_US.csv"
REPORT_PATH="reports/latest_gld_slv_research.md"
OUTPUT_HTML="dashboard/index.html"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --csv-path=*) CSV_PATH="${1#--csv-path=}"; shift ;;
    --csv-path) CSV_PATH="${2:?--csv-path requires a path}"; shift 2 ;;
    --report-path=*) REPORT_PATH="${1#--report-path=}"; shift ;;
    --report-path) REPORT_PATH="${2:?--report-path requires a path}"; shift 2 ;;
    --output-html=*) OUTPUT_HTML="${1#--output-html=}"; shift ;;
    --output-html) OUTPUT_HTML="${2:?--output-html requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m src.gld_slv_dashboard_mvp \
  --csv-path "$CSV_PATH" \
  --report-path "$REPORT_PATH" \
  --output-html "$OUTPUT_HTML"
