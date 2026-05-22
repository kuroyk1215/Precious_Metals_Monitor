#!/usr/bin/env bash
set -euo pipefail

python3 -m py_compile main.py src/*.py
PYTHONPATH=. pytest -q
bash scripts/ibkr_market_data_snapshot_oneshot.sh

if rg -nE "\.(placeOrder|cancelOrder|whatIfOrder|bracketOrder|exerciseOptions|reqGlobalCancel)\s*\(" scripts src main.py >/dev/null 2>&1; then
  echo "[FAIL] Forbidden broker trading call found"
  exit 1
fi

python3 - <<'PY'
import csv
rows=list(csv.DictReader(open('ibkr_market_data_snapshot.csv', newline='')))
if not rows:
    raise SystemExit('[FAIL] snapshot csv empty')
for r in rows:
    if r['execute_requested'] != 'false' or r['decision'] != 'NO_GO':
        raise SystemExit('[FAIL] default run must remain NO_GO with execute_requested=false')
    if r['ibkr_connection_triggered'] != 'false':
        raise SystemExit('[FAIL] default run must not trigger IBKR connection')
print('[PASS] default no --execute keeps connection disabled')
PY

echo "[PASS] Phase 241-256 delayed/frozen fallback check completed"
