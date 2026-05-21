#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="config.yaml"

for arg in "$@"; do
  case "$arg" in
    --config=*)
      CONFIG_PATH="${arg#--config=}"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"

CSV_PATH="ibkr_contract_qualification_final_gate.csv"
REPORT_PATH="reports/ibkr_contract_qualification_final_gate_report.md"

mkdir -p reports

echo "[INFO] IBKR contract qualification dry-run final gate started: ${RUN_TS}"

python3 - <<PY
from pathlib import Path
import csv
import yaml

config_path = Path("${CONFIG_PATH}")
csv_path = Path("${CSV_PATH}")
report_path = Path("${REPORT_PATH}")

if not config_path.exists():
    raise SystemExit("[FAIL] config file not found")

config = yaml.safe_load(config_path.read_text()) or {}
ibkr = config.get("ibkr", {}) or {}

read_only_required = ibkr.get("read_only_required") is True
real_connection_allowed = ibkr.get("real_connection_allowed") is True
contract_qualification_allowed = ibkr.get("contract_qualification_allowed") is True
market_data_request_allowed = ibkr.get("market_data_request_allowed") is True
historical_data_request_allowed = ibkr.get("historical_data_request_allowed") is True
trading_actions_allowed = ibkr.get("trading_actions_allowed") is True

gate_failures = []
if not read_only_required:
    gate_failures.append("read_only_required must be true")
if real_connection_allowed:
    gate_failures.append("real_connection_allowed must be false in dry-run")
if contract_qualification_allowed:
    gate_failures.append("contract_qualification_allowed must be false in dry-run")
if market_data_request_allowed:
    gate_failures.append("market_data_request_allowed must be false")
if historical_data_request_allowed:
    gate_failures.append("historical_data_request_allowed must be false")
if trading_actions_allowed:
    gate_failures.append("trading_actions_allowed must be false")

decision = "NO_GO"
gate_status = "PASS" if not gate_failures else "FAIL"
notes = "; ".join(gate_failures) if gate_failures else "Dry-run gate is safe. Real contract qualification remains disabled."

targets = [
    {
        "symbol": "1540",
        "display_symbol": "1540.T",
        "exchange": "TSE",
        "currency": "JPY",
        "sec_type": "STK",
        "primary_exchange": "TSE",
        "market": "JP",
        "instrument_type": "gold_etf",
    },
    {
        "symbol": "1542",
        "display_symbol": "1542.T",
        "exchange": "TSE",
        "currency": "JPY",
        "sec_type": "STK",
        "primary_exchange": "TSE",
        "market": "JP",
        "instrument_type": "silver_etf",
    },
    {
        "symbol": "518880",
        "display_symbol": "518880.SH",
        "exchange": "SEHK",
        "currency": "CNH",
        "sec_type": "STK",
        "primary_exchange": "SEHK",
        "market": "CN",
        "instrument_type": "gold_etf_placeholder",
    },
]

rows = []
for target in targets:
    rows.append({
        "run_id": "${RUN_ID}",
        "run_timestamp": "${RUN_TS}",
        "timezone": "Asia/Tokyo",
        "branch": "${BRANCH}",
        "commit": "${COMMIT}",
        "workflow": "ibkr_contract_qualification_dryrun_final_gate",
        "decision": decision,
        "gate_status": gate_status,
        "display_symbol": target["display_symbol"],
        "symbol": target["symbol"],
        "exchange": target["exchange"],
        "currency": target["currency"],
        "sec_type": target["sec_type"],
        "primary_exchange": target["primary_exchange"],
        "market": target["market"],
        "instrument_type": target["instrument_type"],
        "read_only_required": str(read_only_required).lower(),
        "real_connection_allowed": str(real_connection_allowed).lower(),
        "contract_qualification_allowed": str(contract_qualification_allowed).lower(),
        "market_data_request_allowed": str(market_data_request_allowed).lower(),
        "historical_data_request_allowed": str(historical_data_request_allowed).lower(),
        "trading_actions_allowed": str(trading_actions_allowed).lower(),
        "ibkr_connection_triggered": "false",
        "contract_qualification_triggered": "false",
        "market_data_request_triggered": "false",
        "historical_data_request_triggered": "false",
        "broker_execution_triggered": "false",
        "manual_review_required": "true",
        "action_allowed": "false",
        "notes": notes,
    })

header = list(rows[0].keys())

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()
    writer.writerows(rows)

target_lines = "\\n".join(
    f"| {r['display_symbol']} | {r['exchange']} | {r['currency']} | {r['sec_type']} | {r['contract_qualification_allowed']} |"
    for r in rows
)

report_path.write_text(f"""# IBKR Contract Qualification Dry-run Final Gate Report

## 1. Run metadata

- run_id: ${RUN_ID}
- run_timestamp: ${RUN_TS}
- timezone: Asia/Tokyo
- branch: ${BRANCH}
- commit: ${COMMIT}
- workflow: ibkr_contract_qualification_dryrun_final_gate

## 2. Gate decision

| field | value |
|---|---|
| decision | {decision} |
| gate_status | {gate_status} |
| notes | {notes} |
| manual_review_required | true |
| action_allowed | false |

## 3. Target contracts

| display_symbol | exchange | currency | sec_type | contract_qualification_allowed |
|---|---|---|---|---|
{target_lines}

## 4. Gate posture

| gate | value |
|---|---:|
| read_only_required | {str(read_only_required).lower()} |
| real_connection_allowed | {str(real_connection_allowed).lower()} |
| contract_qualification_allowed | {str(contract_qualification_allowed).lower()} |
| market_data_request_allowed | {str(market_data_request_allowed).lower()} |
| historical_data_request_allowed | {str(historical_data_request_allowed).lower()} |
| trading_actions_allowed | {str(trading_actions_allowed).lower()} |

## 5. Safety assertions

- ibkr_connection_triggered=false
- contract_qualification_triggered=false
- market_data_request_triggered=false
- historical_data_request_triggered=false
- broker_execution_triggered=false
- action_allowed=false
- manual_review_required=true

## 6. Final boundary

This phase generated a contract qualification dry-run plan only.

No IBKR connection occurred, no `reqContractDetails` call occurred, no market data or historical data was requested, and no broker execution occurred.
""")

print("[PASS] IBKR contract qualification dry-run final gate generated")
print(f"decision={decision}")
print(f"gate_status={gate_status}")
print(f"target_count={len(rows)}")
print(f"csv={csv_path}")
print(f"report={report_path}")
PY

echo "[PASS] No IBKR connection triggered"
echo "[PASS] No contract qualification triggered"
echo "[PASS] No market data request triggered"
echo "[PASS] No historical data request triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
