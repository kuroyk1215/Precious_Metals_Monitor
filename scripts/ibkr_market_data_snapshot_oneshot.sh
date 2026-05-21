#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="config.yaml"
CONTRACT_MAP_CSV="ibkr_verified_contract_map.csv"
EXECUTE="false"

for arg in "$@"; do
  case "$arg" in
    --execute)
      EXECUTE="true"
      ;;
    --config=*)
      CONFIG_PATH="${arg#--config=}"
      ;;
    --contract-map=*)
      CONTRACT_MAP_CSV="${arg#--contract-map=}"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

export CONFIG_PATH CONTRACT_MAP_CSV EXECUTE
export RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
export RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
export BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
export COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"
export CSV_PATH="ibkr_market_data_snapshot.csv"
export REPORT_PATH="reports/ibkr_market_data_snapshot_report.md"

mkdir -p reports

echo "[INFO] IBKR market data snapshot one-shot started: ${RUN_TS}"

python3 - <<'PY'
from pathlib import Path
import csv
import math
import os
import yaml

def as_float(value):
    try:
        if value is None:
            return ""
        v = float(value)
        if math.isnan(v):
            return ""
        return str(v)
    except Exception:
        return ""

config_path = Path(os.environ["CONFIG_PATH"])
contract_map_path = Path(os.environ["CONTRACT_MAP_CSV"])
execute = os.environ["EXECUTE"] == "true"

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
if contract_qualification_allowed:
    gate_failures.append("contract_qualification_allowed must be false for market data snapshot")
if not market_data_request_allowed:
    gate_failures.append("market_data_request_allowed must be true")
if historical_data_request_allowed:
    gate_failures.append("historical_data_request_allowed must be false")
if trading_actions_allowed:
    gate_failures.append("trading_actions_allowed must be false")

map_rows = []
if contract_map_path.exists():
    with contract_map_path.open(newline="") as f:
        map_rows = list(csv.DictReader(f))

if not map_rows:
    map_rows = [
        {"display_symbol": "1540.T", "status": "MAP_READY", "conid": "117595037", "symbol": "1540", "sec_type": "STK", "exchange": "SMART", "primary_exchange": "TSEJ", "currency": "JPY", "local_symbol": "1540.T", "trading_class": "1540"},
        {"display_symbol": "1542.T", "status": "MAP_READY", "conid": "121557296", "symbol": "1542", "sec_type": "STK", "exchange": "SMART", "primary_exchange": "TSEJ", "currency": "JPY", "local_symbol": "1542.T", "trading_class": "1542"},
        {"display_symbol": "518880.SH", "status": "IBKR_UNSUPPORTED", "conid": "", "symbol": "518880", "sec_type": "", "exchange": "", "primary_exchange": "", "currency": "", "local_symbol": "", "trading_class": ""},
    ]

decision = "NO_GO" if gate_failures else "GO_MARKET_DATA_SNAPSHOT_ONLY"
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

        for item in map_rows:
            status = item.get("status", "")
            conid = item.get("conid", "")
            bid = ask = last = close = market_price = ""
            data_status = "not_requested"
            snapshot_status = "SKIPPED"
            notes = ""

            if status != "MAP_READY":
                data_status = "external_or_unsupported"
                snapshot_status = "SKIPPED_UNSUPPORTED"
                notes = "Instrument is not eligible for IBKR market data snapshot."
            else:
                try:
                    contract = Contract(
                        conId=int(conid),
                        secType=item.get("sec_type", "STK"),
                        exchange=item.get("exchange", "SMART"),
                        currency=item.get("currency", "JPY"),
                    )
                    ticker = ib.reqMktData(contract, "", True, False)
                    ib.sleep(3)

                    bid = as_float(getattr(ticker, "bid", None))
                    ask = as_float(getattr(ticker, "ask", None))
                    last = as_float(getattr(ticker, "last", None))
                    close = as_float(getattr(ticker, "close", None))
                    try:
                        market_price = as_float(ticker.marketPrice())
                    except Exception:
                        market_price = ""

                    if any([bid, ask, last, close, market_price]):
                        snapshot_status = "SNAPSHOT_RETURNED"
                        data_status = "snapshot_available"
                        notes = "Market data snapshot returned at least one price field."
                    else:
                        snapshot_status = "SNAPSHOT_EMPTY"
                        data_status = "snapshot_empty"
                        notes = "Snapshot request returned no usable price field."
                except Exception as exc:
                    snapshot_status = "SNAPSHOT_ERROR"
                    data_status = "snapshot_error"
                    notes = type(exc).__name__ + ": " + str(exc)

            rows.append((item, bid, ask, last, close, market_price, data_status, snapshot_status, notes))
    else:
        reason = "; ".join(gate_failures)
        for item in map_rows:
            rows.append((item, "", "", "", "", "", "not_requested", "NO_GO", reason))
except Exception as exc:
    connection_error = type(exc).__name__ + ": " + str(exc)
    if not rows:
        for item in map_rows:
            rows.append((item, "", "", "", "", "", "connection_error", "CONNECTION_ERROR", connection_error))
finally:
    if ib is not None:
        try:
            ib.disconnect()
        except Exception:
            pass

output_rows = []
for item, bid, ask, last, close, market_price, data_status, snapshot_status, notes in rows:
    output_rows.append({
        "run_id": os.environ["RUN_ID"],
        "run_timestamp": os.environ["RUN_TS"],
        "timezone": "Asia/Tokyo",
        "branch": os.environ["BRANCH"],
        "commit": os.environ["COMMIT"],
        "workflow": "ibkr_market_data_snapshot_oneshot",
        "decision": decision,
        "execute_requested": str(execute).lower(),
        "display_symbol": item.get("display_symbol", ""),
        "contract_map_status": item.get("status", ""),
        "conid": item.get("conid", ""),
        "local_symbol": item.get("local_symbol", ""),
        "trading_class": item.get("trading_class", ""),
        "exchange": item.get("exchange", ""),
        "primary_exchange": item.get("primary_exchange", ""),
        "currency": item.get("currency", ""),
        "read_only_required": str(read_only_required).lower(),
        "real_connection_allowed": str(real_connection_allowed).lower(),
        "contract_qualification_allowed": str(contract_qualification_allowed).lower(),
        "market_data_request_allowed": str(market_data_request_allowed).lower(),
        "historical_data_request_allowed": str(historical_data_request_allowed).lower(),
        "trading_actions_allowed": str(trading_actions_allowed).lower(),
        "ibkr_connection_triggered": str(connection_attempted).lower(),
        "connection_succeeded": str(connection_succeeded).lower(),
        "market_data_request_triggered": str(bool(connection_succeeded and not gate_failures)).lower(),
        "historical_data_request_triggered": "false",
        "broker_execution_triggered": "false",
        "bid": bid,
        "ask": ask,
        "last": last,
        "close": close,
        "market_price": market_price,
        "data_status": data_status,
        "snapshot_status": snapshot_status,
        "manual_review_required": "true",
        "action_allowed": "false",
        "notes": notes or connection_error,
    })

csv_path = Path(os.environ["CSV_PATH"])
report_path = Path(os.environ["REPORT_PATH"])

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(output_rows[0].keys()))
    writer.writeheader()
    writer.writerows(output_rows)

snapshot_available_count = sum(1 for r in output_rows if r["snapshot_status"] == "SNAPSHOT_RETURNED")
snapshot_empty_count = sum(1 for r in output_rows if r["snapshot_status"] == "SNAPSHOT_EMPTY")
snapshot_error_count = sum(1 for r in output_rows if r["snapshot_status"] == "SNAPSHOT_ERROR")
unsupported_count = sum(1 for r in output_rows if r["snapshot_status"] == "SKIPPED_UNSUPPORTED")

lines = "\n".join(
    f"| {r['display_symbol']} | {r['snapshot_status']} | {r['data_status']} | {r['bid']} | {r['ask']} | {r['last']} | {r['close']} | {r['market_price']} | {r['notes']} |"
    for r in output_rows
)

report_path.write_text(f"""# IBKR Market Data Snapshot One-shot Report

## 1. Decision

| field | value |
|---|---|
| decision | {decision} |
| execute_requested | {str(execute).lower()} |
| ibkr_connection_triggered | {str(connection_attempted).lower()} |
| connection_succeeded | {str(connection_succeeded).lower()} |
| market_data_request_triggered | {str(bool(connection_succeeded and not gate_failures)).lower()} |
| snapshot_available_count | {snapshot_available_count} |
| snapshot_empty_count | {snapshot_empty_count} |
| snapshot_error_count | {snapshot_error_count} |
| unsupported_count | {unsupported_count} |
| action_allowed | false |

## 2. Snapshot rows

| display_symbol | snapshot_status | data_status | bid | ask | last | close | market_price | notes |
|---|---|---|---:|---:|---:|---:|---:|---|
{lines}

## 3. Safety

- historical_data_request_triggered=false
- broker_execution_triggered=false
- action_allowed=false
- manual_review_required=true
""")

print("[PASS] IBKR market data snapshot one-shot generated")
print(f"decision={decision}")
print(f"execute_requested={str(execute).lower()}")
print(f"connection_attempted={str(connection_attempted).lower()}")
print(f"connection_succeeded={str(connection_succeeded).lower()}")
print(f"snapshot_available_count={snapshot_available_count}")
print(f"snapshot_empty_count={snapshot_empty_count}")
print(f"snapshot_error_count={snapshot_error_count}")
print(f"csv={csv_path}")
print(f"report={report_path}")
PY

echo "[PASS] No historical data request triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
