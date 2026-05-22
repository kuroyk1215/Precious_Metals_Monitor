#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 257-272 IBKR delayed/frozen daily integration check"

python -m py_compile main.py src/*.py
PYTHONPATH=. python -m pytest -q

missing_snapshot="$(mktemp /tmp/ibkr_missing_snapshot.XXXXXX.csv)"
rm -f "$missing_snapshot"

bash scripts/ibkr_daily_integration_preflight.sh --market-data-snapshot="$missing_snapshot" | tee /tmp/phase257_272_daily_integration_check.out

if ! grep -q "market_data_snapshot_status=missing" /tmp/phase257_272_daily_integration_check.out; then
  echo "[FAIL] Missing snapshot did not report market_data_snapshot_status=missing"
  exit 1
fi

if ! grep -q "daily_integration_status=NO_GO" /tmp/phase257_272_daily_integration_check.out; then
  echo "[FAIL] Missing snapshot did not report daily_integration_status=NO_GO"
  exit 1
fi

if ! grep -q "action_allowed=false" /tmp/phase257_272_daily_integration_check.out; then
  echo "[FAIL] Missing snapshot did not report action_allowed=false"
  exit 1
fi

python - <<'PY'
import csv
from pathlib import Path

rows = list(csv.DictReader(Path("ibkr_daily_integration_preflight.csv").open(newline="")))
if len(rows) != 1:
    raise SystemExit(f"[FAIL] Expected one missing-input row, got {len(rows)}")
row = rows[0]
if row["market_data_snapshot_status"] != "missing":
    raise SystemExit("[FAIL] CSV market_data_snapshot_status must be missing")
if row["daily_integration_status"] != "NO_GO" or row["integration_status"] != "NO_GO":
    raise SystemExit("[FAIL] Missing snapshot must remain NO_GO")
for key in (
    "action_allowed",
    "broker_execution_triggered",
    "historical_data_request_triggered",
    "account_read_triggered",
    "position_read_triggered",
):
    if row[key] != "false":
        raise SystemExit(f"[FAIL] {key} must be false")
if row["manual_review_required"] != "true":
    raise SystemExit("[FAIL] manual_review_required must be true")
print("[PASS] Missing snapshot NO_GO CSV validated")
PY

if rg -nE "\.(placeOrder|cancelOrder|whatIfOrder|bracketOrder|exerciseOptions|reqGlobalCancel)\s*\(" main.py src scripts/ibkr_daily_integration_preflight.sh scripts/ibkr_market_data_snapshot_oneshot.sh >/dev/null 2>&1; then
  echo "[FAIL] Forbidden broker trading call found"
  exit 1
fi

if rg -nE "\.(reqAccount|reqPositions|accountSummary|managedAccounts)\s*\(" main.py src scripts/ibkr_daily_integration_preflight.sh scripts/ibkr_market_data_snapshot_oneshot.sh >/dev/null 2>&1; then
  echo "[FAIL] Forbidden account or position read found"
  exit 1
fi

echo "[PASS] Phase 257-272 daily integration check completed"
