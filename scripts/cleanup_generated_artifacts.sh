#!/usr/bin/env bash
set -euo pipefail

# Cleanup generated runtime artifacts for Precious_Metals_Monitor.
#
# Safety boundary:
# - Does not remove config.yaml
# - Does not remove .venv/
# - Does not change source code
# - Does not change trading logic
# - Does not execute trades

git restore reports/ibkr_smoke_report.md 2>/dev/null || true

rm -f conversion_factor_calibration_log.csv
rm -f historical_quality_gate_log.csv
rm -f ibkr_historical_fetch_log.csv
rm -f ibkr_smoke_log.csv
rm -f precious_metals_signal_log.csv
rm -f theoretical_price_snapshot.csv
rm -f upstream_factor_snapshot.csv

rm -f data/raw/ibkr_jp_etf_prices_candidate.csv

rm -f reports/conversion_factor_calibration_report.md
rm -f reports/historical_quality_gate_report.md
rm -f reports/ibkr_historical_fetch_report.md
rm -f reports/latest_report.md
rm -f reports/theoretical_price_report.md
rm -f reports/upstream_factor_report.md

git status --short
