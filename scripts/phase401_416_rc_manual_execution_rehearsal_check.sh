#!/usr/bin/env bash
set -euo pipefail

DEFAULT_OUT="/tmp/phase401_416_rc_manual_execution_rehearsal.out"
rm -f "$DEFAULT_OUT"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/phase401_416_pycache}"
mkdir -p "$PYTHONPYCACHEPREFIX"

PATH=.venv/bin:$PATH python -m py_compile main.py src/*.py
PATH=.venv/bin:$PATH PYTHONPATH=. python -m pytest -q
PATH=.venv/bin:$PATH bash scripts/rc_manual_execution_rehearsal.sh > "$DEFAULT_OUT"

if [[ ! -f rc_manual_execution_rehearsal_packet.csv ]]; then
  echo "[FAIL] missing rc_manual_execution_rehearsal_packet.csv"
  exit 1
fi

if [[ ! -f reports/rc_manual_execution_rehearsal_report.md ]]; then
  echo "[FAIL] missing reports/rc_manual_execution_rehearsal_report.md"
  exit 1
fi

if [[ ! -f reports/rc_execution_c_command_preview.md ]]; then
  echo "[FAIL] missing reports/rc_execution_c_command_preview.md"
  exit 1
fi

for marker in \
  "RC_REHEARSAL_READY" \
  "USER_WATCHLIST_ONLY" \
  "GLD_SLV" \
  "1540_1542_OPTIONAL" \
  "518880_EXCLUDED_FROM_IBKR" \
  "READY_FOR_MANUAL_EXECUTION_C" \
  "action_allowed=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false" \
  "telegram_send_triggered=false"; do
  if ! rg -n "$marker" "$DEFAULT_OUT" rc_manual_execution_rehearsal_packet.csv reports/rc_manual_execution_rehearsal_report.md reports/rc_execution_c_command_preview.md >/dev/null 2>&1; then
    echo "[FAIL] missing RC rehearsal marker: $marker"
    exit 1
  fi
done

if ! rg -n -- "--execute-market-data" reports/rc_execution_c_command_preview.md >/dev/null 2>&1; then
  echo "[FAIL] command preview missing manual Execution C flag"
  exit 1
fi

SCAN_FILES=(
  src/rc_manual_execution_rehearsal.py
  src/release_hardening_audit.py
  src/ibkr_execution_c_validation.py
  src/ibkr_local_daily_runner.py
  src/ibkr_daily_marketdata_integration.py
  src/ibkr_daily_operator_packet.py
  src/ibkr_telegram_notification_packet.py
  src/ibkr_telegram_send_gate.py
  scripts/rc_manual_execution_rehearsal.sh
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

PHASE_SCRIPT_COMMANDS="$(mktemp)"
trap 'rm -f "$PHASE_SCRIPT_COMMANDS"' EXIT
sed '/if ! rg -n -- "--execute-market-data"/,/fi/d' scripts/phase401_416_rc_manual_execution_rehearsal_check.sh > "$PHASE_SCRIPT_COMMANDS"
if rg -n -- "--execute-market-data" "$PHASE_SCRIPT_COMMANDS" >/dev/null 2>&1; then
  echo "[FAIL] phase check script contains executable --execute-market-data usage"
  exit 1
fi

if git diff --name-only --cached -- config.yaml | rg -n "config.yaml" >/dev/null 2>&1; then
  echo "[FAIL] config.yaml is staged"
  exit 1
fi

echo "[PASS] Phase 401-416 RC manual execution rehearsal check completed"
