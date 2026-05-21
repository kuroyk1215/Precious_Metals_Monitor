#!/usr/bin/env bash
set -euo pipefail

RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"

CSV_PATH="ibkr_readonly_final_gate_plan.csv"
REPORT_PATH="reports/ibkr_readonly_final_gate_report.md"
CONFIG_PATH="config.yaml"

mkdir -p reports

echo "[INFO] IBKR read-only final gate dry-run started: ${RUN_TS}"

CONFIG_SCAN_STATUS="PASS"
CONFIG_SCAN_NOTES="config.yaml scanned for unsafe true flags"

python3 - <<'PY'
from pathlib import Path
import sys
import yaml

config_path = Path("config.yaml")
if not config_path.exists():
    raise SystemExit("[FAIL] config.yaml not found")

data = yaml.safe_load(config_path.read_text()) or {}

unsafe_true_keys = {
    "trading_actions_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "auto_trade_allowed",
    "place_order_allowed",
    "cancel_order_allowed",
    "what_if_order_allowed",
    "exercise_options_allowed",
}

soft_gate_keys = {
    "real_connection_allowed",
    "contract_qualification_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
}

hits = []

def walk(obj, path=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            full = f"{path}.{key}" if path else str(key)
            if key in unsafe_true_keys and value is True:
                hits.append((full, value))
            if key in soft_gate_keys and value is True:
                hits.append((full, value))
            walk(value, full)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            walk(value, f"{path}[{i}]")

walk(data)

if hits:
    for key, value in hits:
        print(f"[FAIL] Unsafe enabled config flag: {key}={value}", file=sys.stderr)
    raise SystemExit(1)

print("[PASS] config.yaml has no unsafe true gate flags")
PY

cat > "${CSV_PATH}" <<CSV
run_id,run_timestamp,timezone,branch,commit,workflow,decision,operator_approval_required,config_scan_status,real_connection_allowed,contract_qualification_allowed,market_data_request_allowed,historical_data_request_allowed,trading_actions_allowed,ibkr_connection_triggered,market_data_request_triggered,historical_data_request_triggered,contract_qualification_triggered,broker_execution_triggered,manual_review_required,action_allowed
${RUN_ID},${RUN_TS},Asia/Tokyo,${BRANCH},${COMMIT},ibkr_readonly_final_gate_dryrun,NO_GO,true,${CONFIG_SCAN_STATUS},false,false,false,false,false,false,false,false,false,false,true,false
CSV

cat > "${REPORT_PATH}" <<MD
# IBKR Read-only Final Gate Dry-run Report

## 1. Run metadata

- run_id: ${RUN_ID}
- run_timestamp: ${RUN_TS}
- timezone: Asia/Tokyo
- branch: ${BRANCH}
- commit: ${COMMIT}
- workflow: ibkr_readonly_final_gate_dryrun

## 2. Gate decision

| field | value |
|---|---|
| decision | NO_GO |
| operator_approval_required | true |
| config_scan_status | ${CONFIG_SCAN_STATUS} |
| config_scan_notes | ${CONFIG_SCAN_NOTES} |
| manual_review_required | true |
| action_allowed | false |

## 3. Current permission posture

| permission | value |
|---|---:|
| real_connection_allowed | false |
| contract_qualification_allowed | false |
| market_data_request_allowed | false |
| historical_data_request_allowed | false |
| trading_actions_allowed | false |

## 4. Safety assertions

- ibkr_connection_triggered=false
- market_data_request_triggered=false
- historical_data_request_triggered=false
- contract_qualification_triggered=false
- broker_execution_triggered=false
- action_allowed=false
- manual_review_required=true

## 5. Next allowed step

The next phase may prepare a one-shot read-only connection test only if the operator explicitly approves it.

That later phase must still prohibit:

- order placement
- order cancellation
- bracket orders
- what-if orders
- options exercise
- rebalance
- automatic trading

## 6. Final boundary

This phase did not connect to IBKR, did not request data, did not qualify contracts, and did not trigger broker execution.
MD

echo "[PASS] IBKR read-only final gate dry-run generated"
echo "csv=${CSV_PATH}"
echo "report=${REPORT_PATH}"
echo "[PASS] No IBKR connection triggered"
echo "[PASS] No market data request triggered"
echo "[PASS] No historical data request triggered"
echo "[PASS] No contract qualification triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
