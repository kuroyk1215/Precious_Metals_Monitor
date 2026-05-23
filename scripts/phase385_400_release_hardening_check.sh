#!/usr/bin/env bash
set -euo pipefail

DEFAULT_OUT="/tmp/phase385_400_release_hardening_audit.out"
rm -f "$DEFAULT_OUT"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/phase385_400_pycache}"
mkdir -p "$PYTHONPYCACHEPREFIX"

PATH=.venv/bin:$PATH python -m py_compile main.py src/*.py
PATH=.venv/bin:$PATH PYTHONPATH=. python -m pytest -q
PATH=.venv/bin:$PATH bash scripts/release_hardening_audit.sh > "$DEFAULT_OUT"

if [[ ! -f release_hardening_audit.csv ]]; then
  echo "[FAIL] missing release_hardening_audit.csv"
  exit 1
fi

if [[ ! -f reports/release_hardening_audit_report.md ]]; then
  echo "[FAIL] missing reports/release_hardening_audit_report.md"
  exit 1
fi

for marker in \
  "RELEASE_AUDIT_PASS" \
  "USER_WATCHLIST_ONLY" \
  "GLD_SLV_FIRST_TEST_UNIVERSE" \
  "JP_ETF_OPTIONAL" \
  "CN_ETF_EXCLUDED_FROM_IBKR" \
  "action_allowed=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false" \
  "telegram_send_triggered=false"; do
  if ! rg -n "$marker" "$DEFAULT_OUT" release_hardening_audit.csv reports/release_hardening_audit_report.md >/dev/null 2>&1; then
    echo "[FAIL] missing release audit marker: $marker"
    exit 1
  fi
done

SCAN_FILES=(
  src/release_hardening_audit.py
  src/ibkr_execution_c_validation.py
  src/ibkr_local_daily_runner.py
  src/ibkr_daily_marketdata_integration.py
  src/ibkr_daily_operator_packet.py
  src/ibkr_telegram_notification_packet.py
  src/ibkr_telegram_send_gate.py
  scripts/release_hardening_audit.sh
  scripts/ibkr_execution_c_pipeline_validation.sh
  scripts/ibkr_local_daily_runner.sh
  scripts/ibkr_daily_research_pipeline.sh
  scripts/ibkr_telegram_notification_packet.sh
  scripts/ibkr_telegram_send_gate.sh
)

if rg -n "\.(placeOrder|cancelOrder|whatIfOrder|bracketOrder|exerciseOptions|reqGlobalCancel)\s*\(" "${SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] forbidden trading call found in default executable path"
  exit 1
fi

if rg -n "\.(reqAccount|reqPositions|accountSummary|managedAccounts)\s*\(" "${SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] account or position read found in default executable path"
  exit 1
fi

if rg -n "\.reqHistoricalData\s*\(" "${SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] historical data request found in default executable path"
  exit 1
fi

if git diff --name-only --cached -- config.yaml | rg -n "config.yaml" >/dev/null 2>&1; then
  echo "[FAIL] config.yaml is staged"
  exit 1
fi

echo "[PASS] Phase 385-400 release hardening safety audit check completed"
