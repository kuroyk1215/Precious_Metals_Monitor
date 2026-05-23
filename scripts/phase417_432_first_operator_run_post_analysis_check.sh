#!/usr/bin/env bash
set -euo pipefail

DEFAULT_OUT="/tmp/phase417_432_first_operator_run_post_analysis.out"
rm -f "$DEFAULT_OUT"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/phase417_432_pycache}"
mkdir -p "$PYTHONPYCACHEPREFIX"

PATH=.venv/bin:$PATH python -m py_compile main.py src/*.py
PATH=.venv/bin:$PATH PYTHONPATH=. python -m pytest -q
PATH=.venv/bin:$PATH bash scripts/first_operator_run_post_analysis.sh > "$DEFAULT_OUT"

for path in \
  first_operator_run_post_analysis.csv \
  reports/first_operator_run_post_analysis_report.md \
  reports/first_operator_run_summary.md; do
  if [[ ! -f "$path" ]]; then
    echo "[FAIL] missing post-run analysis output: $path"
    exit 1
  fi
done

if ! rg -n "POST_RUN_REFERENCE_READY|POST_RUN_BLOCKED" "$DEFAULT_OUT" first_operator_run_post_analysis.csv reports/first_operator_run_post_analysis_report.md reports/first_operator_run_summary.md >/dev/null 2>&1; then
  echo "[FAIL] missing post-run status"
  exit 1
fi

for marker in \
  "action_allowed=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false" \
  "telegram_send_triggered=false"; do
  if ! rg -n "$marker" "$DEFAULT_OUT" reports/first_operator_run_post_analysis_report.md reports/first_operator_run_summary.md >/dev/null 2>&1; then
    echo "[FAIL] missing safety marker: $marker"
    exit 1
  fi
done

if rg -n "\.(placeOrder|cancelOrder|whatIfOrder|bracketOrder|exerciseOptions|reqGlobalCancel)\s*\(" src scripts >/dev/null 2>&1; then
  echo "[FAIL] forbidden trading call found in src/scripts executable path"
  exit 1
fi

if rg -n "\.(reqAccount|reqPositions|accountSummary|managedAccounts)\s*\(" src scripts >/dev/null 2>&1; then
  echo "[FAIL] account or position read found in src/scripts executable path"
  exit 1
fi

PHASE_SCRIPT="scripts/phase417_432_first_operator_run_post_analysis_check.sh"
EXEC_FLAG="--""execute-market-data"
EXEC_SCRIPT="ibkr_execution_c_pipeline_validation"".sh"
if rg -n -- "$EXEC_FLAG" "$PHASE_SCRIPT" >/dev/null 2>&1; then
  echo "[FAIL] phase check script contains executable market-data flag usage"
  exit 1
fi

if rg -n "$EXEC_SCRIPT" "$PHASE_SCRIPT" >/dev/null 2>&1; then
  echo "[FAIL] phase check script references Execution C pipeline validation"
  exit 1
fi

if git diff --name-only --cached -- config.yaml | rg -n "config.yaml" >/dev/null 2>&1; then
  echo "[FAIL] config.yaml is staged"
  exit 1
fi

echo "[PASS] Phase 417-432 first operator-run post analysis check completed"
