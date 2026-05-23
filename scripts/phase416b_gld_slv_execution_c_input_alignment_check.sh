#!/usr/bin/env bash
set -euo pipefail

OUT="/tmp/phase416b_gld_slv_execution_c_input_alignment.out"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/private/tmp/phase416b_pycache}"

PATH=.venv/bin:$PATH python -m py_compile main.py src/*.py
PATH=.venv/bin:$PATH PYTHONPATH=. python -m pytest -q
PATH=.venv/bin:$PATH bash scripts/prepare_gld_slv_contract_map.sh
PATH=.venv/bin:$PATH bash scripts/rc_manual_execution_rehearsal.sh --first-validation-contract-map=ibkr_verified_contract_map_gld_slv.csv > "$OUT"

for marker in \
  "READY_FOR_MANUAL_EXECUTION_C" \
  "GLD_SLV" \
  "ibkr_verified_contract_map_gld_slv.csv" \
  "518880_EXCLUDED_FROM_IBKR" \
  "action_allowed=false"; do
  if ! grep -q "$marker" "$OUT" rc_manual_execution_rehearsal_packet.csv reports/rc_manual_execution_rehearsal_report.md reports/rc_execution_c_command_preview.md ibkr_verified_contract_map_gld_slv.csv; then
    echo "[FAIL] Missing marker: $marker"
    exit 1
  fi
done

FORBIDDEN_EXECUTION_C_CALL="bash scripts/ibkr_execution_c_pipeline_validation.sh --execute""-market-data"
if grep -q "$FORBIDDEN_EXECUTION_C_CALL" "$0"; then
  echo "[FAIL] Phase 416B check must not execute market data"
  exit 1
fi

SCAN_FILES=(
  scripts/ibkr_market_data_snapshot_oneshot.sh
  scripts/prepare_gld_slv_contract_map.sh
  scripts/rc_manual_execution_rehearsal.sh
  src/ibkr_market_data_contract_builder.py
  src/rc_manual_execution_rehearsal.py
)

if grep -nE "placeOrder|cancelOrder|whatIfOrder|bracketOrder|exerciseOptions|reqGlobalCancel" "${SCAN_FILES[@]}" >/dev/null; then
  echo "[FAIL] Forbidden trading function reference found"
  exit 1
fi

if grep -nE "reqAccount|reqPositions|accountSummary|managedAccounts" "${SCAN_FILES[@]}" >/dev/null; then
  echo "[FAIL] Forbidden account/position read reference found"
  exit 1
fi

echo "[PASS] Phase 416B GLD/SLV Execution C input alignment check completed"
