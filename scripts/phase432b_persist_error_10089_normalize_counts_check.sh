#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 432B persist Error 10089 normalize counts check started"

PATH=.venv/bin:$PATH python -m py_compile main.py src/*.py
PATH=.venv/bin:$PATH PYTHONPATH=. python -m pytest -q

POST_OUT="$(PATH=.venv/bin:$PATH bash scripts/first_operator_run_post_analysis.sh)"
printf '%s\n' "$POST_OUT"

for marker in \
  "action_allowed=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false" \
  "telegram_send_triggered=false"
do
  if ! grep -F "$marker" <<<"$POST_OUT" >/dev/null; then
    echo "[FAIL] Missing safety marker: $marker"
    exit 1
  fi
done

if ! rg -n "10089" tests/test_ibkr_market_data_fallback.py tests/test_first_operator_run_post_analysis.py >/dev/null; then
  echo "[FAIL] Missing Error 10089 test coverage"
  exit 1
fi

if ! rg -n "354" tests/test_ibkr_market_data_fallback.py tests/test_first_operator_run_post_analysis.py >/dev/null; then
  echo "[FAIL] Missing Error 354 test coverage"
  exit 1
fi

SCAN_FILES=(
  main.py
  src/ibkr_market_data_fallback.py
  src/ibkr_market_data_error_capture.py
  src/first_operator_run_post_analysis.py
  scripts/ibkr_market_data_snapshot_oneshot.sh
  scripts/first_operator_run_post_analysis.sh
  scripts/phase432b_persist_error_10089_normalize_counts_check.sh
)

if rg -n "\.(placeOrder|cancelOrder|whatIfOrder|bracketOrder|exerciseOptions|reqGlobalCancel)\s*\(" "${SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] Broker trading function call detected in Phase 432B execution path"
  exit 1
fi

if rg -n "\.(reqAccount|reqPositions|accountSummary|managedAccounts)\s*\(" "${SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] Account or position read call detected in Phase 432B execution path"
  exit 1
fi

needle_exec="--execute-market"
needle_exec="${needle_exec}-data"
needle_pipeline="ibkr_execution_c_pipeline_validation"
needle_pipeline="${needle_pipeline}.sh"

if rg -n -- "$needle_exec" scripts/phase432b_persist_error_10089_normalize_counts_check.sh >/dev/null 2>&1; then
  echo "[FAIL] Phase 432B check script contains real market-data execution flag"
  exit 1
fi

if rg -n -- "$needle_pipeline" scripts/phase432b_persist_error_10089_normalize_counts_check.sh >/dev/null 2>&1; then
  echo "[FAIL] Phase 432B check script references Execution C pipeline validation"
  exit 1
fi

echo "[PASS] Phase 432B persist Error 10089 normalize counts check completed"
