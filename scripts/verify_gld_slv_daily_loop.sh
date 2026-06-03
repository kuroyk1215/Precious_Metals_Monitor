#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
REPORT_PATH="runtime/reports/latest_gld_slv_research.md"
CSV_PATH="logs/research_log_US.csv"
DASHBOARD_PATH="runtime/dashboard/index.html"

mkdir -p runtime/reports runtime/dashboard logs

bash scripts/batch1_gld_slv_core_research_loop.sh \
  --output-report "$REPORT_PATH" \
  --output-csv "$CSV_PATH"

bash scripts/gld_slv_dashboard_mvp.sh \
  --csv-path "$CSV_PATH" \
  --report-path "$REPORT_PATH" \
  --output-html "$DASHBOARD_PATH"

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m src.gld_slv_daily_loop_verifier \
  --report-path "$REPORT_PATH" \
  --csv-path "$CSV_PATH" \
  --dashboard-path "$DASHBOARD_PATH"
