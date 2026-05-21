#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="config.yaml"
EXECUTE="false"

for arg in "$@"; do
  case "$arg" in
    --execute)
      EXECUTE="true"
      ;;
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

CSV_PATH="ibkr_contract_qualification_oneshot.csv"
REPORT_PATH="reports/ibkr_contract_qualification_oneshot_report.md"

mkdir -p reports

echo "[INFO] IBKR contract qualification one-shot preflight started: ${RUN_TS}"

python3 - <<PY
from pathlib import Path
import csv
import yaml

config_path = Path("${CONFIG_PATH}")
execute = "${EXECUTE}" == "true"
csv_path = Path("${CSV_PATH}")
report_path = Path("${REPORT_PATH}")

if not config_path.exists():
    raise SystemExit("[FAIL] config file not found")

config = yaml.safe_load(config_path.read_text()) or {}
ibkr_cfg = config.get("ibkr", {}) or {}

read_only_required = ibkr_cfg.get("read_only_required") is True
real_connection_allowed = ibkr_cfg.get("real_connection_allowed") is True
contract_qualification_allowed = ibkr_cfg.get("contract_qualification_allowed") is True
market_data_request_allowed = ibkr_cfg.get("market_data_request_allowed") is True
historical_data_request_allowed = ibkr_cfg.get("historical_data_request_allowed") is True
trading_actions_allowed = ibkr_cfg.get("trading_actions_allowed") is True

host = str(ibkr_cfg.get("host", "127.0.0.1"))
port = int(ibkr_cfg.get("port", 7496))
client_id = int(ibkr_cfg.get("client_id", 1))

gate_failures = []
if not execute:
    gate_failures.append("--execute was not provided")
if not read_only_required:
    gate_failures.append("read_only_required must be true")
if not real_connection_allowed:
    gate_failures.append("real_connection_allowed must be true")
if not contract_qualification_allowed:
    gate_failures.append("contract_qualification_allowed must be true")
if market_data_request_allowed:
    gate_failures.append("market_data_request_allowed must be false")
if historical_data_request_allowed:
    gate_failures.append("historical_data_request_allowed must be false")
if trading_actions_allowed:
    gate_failures.append("trading_actions_allowed must be false")

targets = [
    {
        "display_symbol": "1540.T",
        "symbol": "1540",
        "exchange": "TSE",
        "currency": "JPY",
        "sec_type": "STK",
        "primary_exchange": "TSE",
        "market": "JP",
        "instrument_type": "gold_etf",
    },
    {
        "display_symbol": "1542.T",
        "symbol": "1542",
        "exchange": "TSE",
        "currency": "JPY",
        "sec_type": "STK",
        "primary_exchange": "TSE",
        "market": "JP",
        "instrument_type": "silver_etf",
    },
    {
        "display_symbol": "518880.SH",
        "symbol": "518880",
        "exchange": "SEHK",
        "currency": "CNH",
        "sec_type": "STK",
        "primary_exchange": "SEHK",
        "market": "CN",
        "instrument_type": "gold_etf_placeholder",
    },
]

decision = "NO_GO" if gate_failures else "GO_CONTRACT_DETAILS_ONLY"
connection_attempted = False
connection_succeeded = False
connection_error = ""
rows = []

ib = None

try:
    if not gate_failures:
        connection_attempted = True
        from ib_insync import IB, Contract
        ib = IB()
        ib.connect(host, port, clientId=client_id, timeout=5, readonly=True)
        connection_succeeded = ib.isConnected()

        for target in targets:
            details_count = 0
            conid = ""
            local_symbol = ""
            trading_class = ""
            market_name = ""
            min_tick = ""
            notes = ""

            try:
                contract = Contract(
                    secType=target["sec_type"],
                    symbol=target["symbol"],
                    exchange=target["exchange"],
                    currency=target["currency"],
                    primaryExchange=target["primary_exchange"],
                )
                details = ib.reqContractDetails(contract)
                details_count = len(details)
                if details:
                    detail = details[0]
                    conid = str(getattr(detail.contract, "conId", "") or "")
                    local_symbol = str(getattr(detail.contract, "localSymbol", "") or "")
                    trading_class = str(getattr(detail.contract, "tradingClass", "") or "")
                    market_name = str(getattr(detail, "marketName", "") or "")
                    min_tick = str(getattr(detail, "minTick", "") or "")
                    notes = "contract_details_returned"
                else:
                    notes = "no_contract_details_returned"
            except Exception as exc:
                notes = type(exc).__name__ + ": " + str(exc)

            rows.append({
                **target,
                "contract_details_count": str(details_count),
                "conid": conid,
                "local_symbol": local_symbol,
                "trading_class": trading_class,
                "market_name": market_name,
                "min_tick": min_tick,
                "notes": notes,
            })
    else:
        notes = "; ".join(gate_failures)
        for target in targets:
            rows.append({
                **target,
                "contract_details_count": "0",
                "conid": "",
                "local_symbol": "",
                "trading_class": "",
                "market_name": "",
                "min_tick": "",
                "notes": notes,
            })
except Exception as exc:
    connection_error = type(exc).__name__ + ": " + str(exc)
    if not rows:
        for target in targets:
            rows.append({
                **target,
                "contract_details_count": "0",
                "conid": "",
                "local_symbol": "",
                "trading_class": "",
                "market_name": "",
                "min_tick": "",
                "notes": connection_error,
            })
finally:
    if ib is not None:
        try:
            ib.disconnect()
        except Exception:
            pass

output_rows = []
for row in rows:
    output_rows.append({
        "run_id": "${RUN_ID}",
        "run_timestamp": "${RUN_TS}",
        "timezone": "Asia/Tokyo",
        "branch": "${BRANCH}",
        "commit": "${COMMIT}",
        "workflow": "ibkr_contract_qualification_oneshot",
        "decision": decision,
        "execute_requested": str(execute).lower(),
        "display_symbol": row["display_symbol"],
        "symbol": row["symbol"],
        "exchange": row["exchange"],
        "currency": row["currency"],
        "sec_type": row["sec_type"],
        "primary_exchange": row["primary_exchange"],
        "market": row["market"],
        "instrument_type": row["instrument_type"],
        "read_only_required": str(read_only_required).lower(),
        "real_connection_allowed": str(real_connection_allowed).lower(),
        "contract_qualification_allowed": str(contract_qualification_allowed).lower(),
        "market_data_request_allowed": str(market_data_request_allowed).lower(),
        "historical_data_request_allowed": str(historical_data_request_allowed).lower(),
        "trading_actions_allowed": str(trading_actions_allowed).lower(),
        "ibkr_connection_triggered": str(connection_attempted).lower(),
        "connection_succeeded": str(connection_succeeded).lower(),
        "contract_qualification_triggered": str(bool(connection_succeeded and not gate_failures)).lower(),
        "contract_details_count": row["contract_details_count"],
        "conid": row["conid"],
        "local_symbol": row["local_symbol"],
        "trading_class": row["trading_class"],
        "market_name": row["market_name"],
        "min_tick": row["min_tick"],
        "market_data_request_triggered": "false",
        "historical_data_request_triggered": "false",
        "broker_execution_triggered": "false",
        "manual_review_required": "true",
        "action_allowed": "false",
        "notes": row["notes"] or connection_error,
    })

header = list(output_rows[0].keys())
with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()
    writer.writerows(output_rows)

target_lines = "\\n".join(
    f"| {r['display_symbol']} | {r['exchange']} | {r['currency']} | {r['contract_details_count']} | {r['conid']} | {r['notes']} |"
    for r in output_rows
)

report_path.write_text(f"""# IBKR Contract Qualification One-shot Report

## 1. Run metadata

- run_id: ${RUN_ID}
- run_timestamp: ${RUN_TS}
- timezone: Asia/Tokyo
- branch: ${BRANCH}
- commit: ${COMMIT}
- workflow: ibkr_contract_qualification_oneshot

## 2. Decision

| field | value |
|---|---|
| decision | {decision} |
| execute_requested | {str(execute).lower()} |
| ibkr_connection_triggered | {str(connection_attempted).lower()} |
| connection_succeeded | {str(connection_succeeded).lower()} |
| contract_qualification_triggered | {str(bool(connection_succeeded and not gate_failures)).lower()} |
| manual_review_required | true |
| action_allowed | false |

## 3. Target results

| display_symbol | exchange | currency | contract_details_count | conid | notes |
|---|---|---|---:|---|---|
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

- market_data_request_triggered=false
- historical_data_request_triggered=false
- broker_execution_triggered=false
- action_allowed=false
- manual_review_required=true

## 6. Final boundary

This workflow is limited to contract details lookup only when explicitly executed and gated.

No market data, historical data, account data, order action, cancellation, rebalance, or automatic trading occurred.
""")

print("[PASS] IBKR contract qualification one-shot report generated")
print(f"decision={decision}")
print(f"execute_requested={str(execute).lower()}")
print(f"connection_attempted={str(connection_attempted).lower()}")
print(f"connection_succeeded={str(connection_succeeded).lower()}")
print(f"contract_qualification_triggered={str(bool(connection_succeeded and not gate_failures)).lower()}")
print(f"csv={csv_path}")
print(f"report={report_path}")
PY

echo "[PASS] No market data request triggered"
echo "[PASS] No historical data request triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
