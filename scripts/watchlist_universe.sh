#!/usr/bin/env bash
set -euo pipefail

ROOT="."
OUTPUT_CSV="watchlist_universe.csv"
OUTPUT_REPORT="reports/watchlist_universe_report.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root=*) ROOT="${1#--root=}"; shift ;;
    --root) ROOT="${2:?--root requires a path}"; shift 2 ;;
    --output-csv=*) OUTPUT_CSV="${1#--output-csv=}"; shift ;;
    --output-csv) OUTPUT_CSV="${2:?--output-csv requires a path}"; shift 2 ;;
    --output-report=*) OUTPUT_REPORT="${1#--output-report=}"; shift ;;
    --output-report) OUTPUT_REPORT="${2:?--output-report requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

python3 -m src.watchlist_universe \
  --root "$ROOT" \
  --output-csv "$OUTPUT_CSV" \
  --output-report "$OUTPUT_REPORT"
