#!/usr/bin/env bash
set -euo pipefail

DEFAULT_OUT="/tmp/phase369_384_execution_c_validation.out"
rm -f "$DEFAULT_OUT"

PATH=.venv/bin:$PATH python -m py_compile main.py src/*.py
PATH=.venv/bin:$PATH PYTHONPATH=. python -m pytest -q

PATH=.venv/bin:$PATH bash scripts/ibkr_execution_c_pipeline_validation.sh > "$DEFAULT_OUT"

for marker in \
  "execution_c_mode=dry_run" \
  "market_data_execution_requested=false" \
  "action_allowed=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false"; do
  if ! rg -n "$marker" "$DEFAULT_OUT" >/dev/null 2>&1; then
    echo "[FAIL] missing default output marker: $marker"
    exit 1
  fi
done

SCAN_FILES=(
  src/ibkr_execution_c_validation.py
  scripts/ibkr_execution_c_pipeline_validation.sh
)

if rg -n "\.(placeOrder|cancelOrder|whatIfOrder|bracketOrder|exerciseOptions|reqGlobalCancel)\s*\(" "${SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] broker execution function found in Execution C validation path"
  exit 1
fi

if rg -n "\.(reqAccount|reqPositions|accountSummary|managedAccounts)\s*\(" "${SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] account or position read found in Execution C validation path"
  exit 1
fi

EXEC_FLAG_PATTERN="--execute""-market-data"
if rg -n "$EXEC_FLAG_PATTERN" scripts/phase369_384_ibkr_execution_c_validation_check.sh >/dev/null 2>&1; then
  echo "[FAIL] phase check script contains real market data execution flag"
  exit 1
fi

echo "[PASS] Phase 369-384 IBKR Execution C validation check completed"
