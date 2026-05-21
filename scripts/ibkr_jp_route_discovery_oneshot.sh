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

export CONFIG_PATH EXECUTE
export RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
export RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
export BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
export COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"
export CSV_PATH="ibkr_jp_route_discovery_oneshot.csv"
export REPORT_PATH="reports/ibkr_jp_route_discovery_oneshot_report.md"

mkdir -p reports

echo "[INFO] IBKR JP route discovery one-shot started: ${RUN_TS}"

python3 - <<'PY'
from pathlib import Path
import csv
import os
import yaml

config_path = Path(os.environ["CONFIG_PATH"])
execute = os.environ["EXECUTE"] == "true"
csv_path = Path(os.environ["CSV_PATH"])
report_path = Path(os.environ["REPORT_PATH"])

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

decision = "NO_GO" if gate_failures else "GO_ROUTE_DISCOVERY_ONLY"
connection_attempted = False
connection_succeeded = False
connection_error = ""

candidates = []
for display_symbol, symbol, instrument_type in [
    ("1540.T", "1540", "gold_etf"),
    ("1542.T", "1542", "silver_etf"),
]:
    for priority, route in enumerate([
        ("SMART", "TSEJ", "JPY", "STK", "smart_tsej"),
        ("TSEJ", "TSEJ", "JPY", "STK", "direct_tsej"),
        ("TSE", "TSEJ", "JPY", "STK", "tse_primary_tsej"),
        ("SMART", "", "JPY", "STK", "smart_no_primary"),
    ], start=1):
        exchange, primary_exchange, currency, sec_type, route_family = route
        candidates.append({
            "display_symbol": display_symbol,
            "symbol": symbol,
            "market": "JP",
            "instrument_type": instrument_type,
            "candidate_priority": str(priority),
            "route_family": route_family,
            "sec_type": sec_type,
            "exchange": exchange,
            "primary_exchange": primary_exchange,
            "currency": currency,
            "route_status": "CANDIDATE",
        })

candidates.append({
    "display_symbol": "518880.SH",
    "symbol": "518880",
    "market": "CN",
    "instrument_type": "gold_etf",
    "candidate_priority": "",
    "route_family": "external_or_manual_only",
    "sec_type": "",
    "exchange": "",
    "primary_exchange": "",
    "currency": "",
    "route_status": "IBKR_UNSUPPORTED",
})

rows = []
ib = None

try:
    if not gate_failures:
        connection_attempted = True
        from ib_insync import IB, Contract

        ib = IB()
        ib.connect(host, port, clientId=client_id, timeout=5, readonly=True)
        connection_succeeded = ib.isConnected()

        for candidate in candidates:
            details_count = 0
            conid = ""
            local_symbol = ""
            trading_class = ""
            market_name = ""
            min_tick = ""
            notes = ""

            if candidate["route_status"] == "IBKR_UNSUPPORTED":
                notes = "IBKR_UNSUPPORTED_external_or_manual_only"
            else:
                try:
                    kwargs = {
                        "secType": candidate["sec_type"],
                        "symbol": candidate["symbol"],
                        "exchange": candidate["exchange"],
                        "currency": candidate["currency"],
                    }
                    if candidate["primary_exchange"]:
                        kwargs["primaryExchange"] = candidate["primary_exchange"]

                    contract = Contract(**kwargs)
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

            rows.append((candidate, details_count, conid, local_symbol, trading_class, market_name, min_tick, notes))
    else:
        notes = "; ".join(gate_failures)
        for candidate in candidates:
            if candidate["route_status"] == "IBKR_UNSUPPORTED":
                row_notes = "IBKR_UNSUPPORTED_external_or_manual_only"
            else:
                row_notes = notes
            rows.append((candidate, 0, "", "", "", "", "", row_notes))
except Exception as exc:
    connection_error = type(exc).__name__ + ": " + str(exc)
    if not rows:
        for candidate in candidates:
            rows.append((candidate, 0, "", "", "", "", "", connection_error))
finally:
    if ib is not None:
        try:
            ib.disconnect()
        except Exception:
            pass

output_rows = []
for candidate, details_count, conid, local_symbol, trading_class, market_name, min_tick, notes in rows:
    output_rows.append({
        "run_id": os.environ["RUN_ID"],
        "run_timestamp": os.environ["RUN_TS"],
        "timezone": "Asia/Tokyo",
        "branch": os.environ["BRANCH"],
        "commit": os.environ["COMMIT"],
        "workflow": "ibkr_jp_route_discovery_oneshot",
        "decision": decision,
        "execute_requested": str(execute).lower(),
        "display_symbol": candidate["display_symbol"],
        "symbol": candidate["symbol"],
        "market": candidate["market"],
        "instrument_type": candidate["instrument_type"],
        "route_status": candidate["route_status"],
        "candidate_priority": candidate["candidate_priority"],
        "route_family": candidate["route_family"],
        "sec_type": candidate["sec_type"],
        "exchange": candidate["exchange"],
        "primary_exchange": candidate["primary_exchange"],
        "currency": candidate["currency"],
        "read_only_required": str(read_only_required).lower(),
        "real_connection_allowed": str(real_connection_allowed).lower(),
        "contract_qualification_allowed": str(contract_qualification_allowed).lower(),
        "market_data_request_allowed": str(market_data_request_allowed).lower(),
        "historical_data_request_allowed": str(historical_data_request_allowed).lower(),
        "trading_actions_allowed": str(trading_actions_allowed).lower(),
        "ibkr_connection_triggered": str(connection_attempted).lower(),
        "connection_succeeded": str(connection_succeeded).lower(),
        "contract_qualification_triggered": str(bool(connection_succeeded and not gate_failures)).lower(),
        "contract_details_count": str(details_count),
        "conid": conid,
        "local_symbol": local_symbol,
        "trading_class": trading_class,
        "market_name": market_name,
        "min_tick": str(min_tick),
        "market_data_request_triggered": "false",
        "historical_data_request_triggered": "false",
        "broker_execution_triggered": "false",
        "manual_review_required": "true",
        "action_allowed": "false",
        "notes": notes or connection_error,
    })

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(output_rows[0].keys()))
    writer.writeheader()
    writer.writerows(output_rows)

candidate_count = sum(1 for r in output_rows if r["route_status"] == "CANDIDATE")
success_count = sum(1 for r in output_rows if int(r["contract_details_count"]) > 0)
unsupported_count = sum(1 for r in output_rows if r["route_status"] == "IBKR_UNSUPPORTED")

lines = "\n".join(
    f"| {r['display_symbol']} | {r['route_family']} | {r['exchange']} | {r['primary_exchange']} | {r['contract_details_count']} | {r['conid']} | {r['local_symbol']} | {r['notes']} |"
    for r in output_rows
)

report_path.write_text(f"""# IBKR JP Route Discovery One-shot Report

## 1. Run metadata

- run_id: {os.environ["RUN_ID"]}
- run_timestamp: {os.environ["RUN_TS"]}
- timezone: Asia/Tokyo
- branch: {os.environ["BRANCH"]}
- commit: {os.environ["COMMIT"]}
- workflow: ibkr_jp_route_discovery_oneshot

## 2. Decision

| field | value |
|---|---|
| decision | {decision} |
| execute_requested | {str(execute).lower()} |
| ibkr_connection_triggered | {str(connection_attempted).lower()} |
| connection_succeeded | {str(connection_succeeded).lower()} |
| contract_qualification_triggered | {str(bool(connection_succeeded and not gate_failures)).lower()} |
| candidate_count | {candidate_count} |
| success_count | {success_count} |
| unsupported_count | {unsupported_count} |
| action_allowed | false |

## 3. Route results

| display_symbol | route_family | exchange | primary_exchange | details_count | conid | local_symbol | notes |
|---|---|---|---|---:|---|---|---|
{lines}

## 4. Safety assertions

- market_data_request_triggered=false
- historical_data_request_triggered=false
- broker_execution_triggered=false
- action_allowed=false
- manual_review_required=true

## 5. Final boundary

This workflow is limited to contract route discovery only.

No market data, historical data, account reads, order actions, cancellation, rebalance, or automatic trading occurred.
""")

print("[PASS] IBKR JP route discovery one-shot report generated")
print(f"decision={decision}")
print(f"execute_requested={str(execute).lower()}")
print(f"connection_attempted={str(connection_attempted).lower()}")
print(f"connection_succeeded={str(connection_succeeded).lower()}")
print(f"success_count={success_count}")
print(f"csv={csv_path}")
print(f"report={report_path}")
PY

echo "[PASS] No market data request triggered"
echo "[PASS] No historical data request triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
