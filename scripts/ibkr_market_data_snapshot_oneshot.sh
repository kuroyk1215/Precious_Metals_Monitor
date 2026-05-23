#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="config.yaml"
CONTRACT_MAP_CSV="ibkr_verified_contract_map.csv"
EXECUTE="false"
MARKET_DATA_TYPE="auto"

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
    --market-data-type=*)
      MARKET_DATA_TYPE="${arg#--market-data-type=}"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

case "$MARKET_DATA_TYPE" in
  live|frozen|delayed|delayed_frozen|auto) ;;
  *) echo "[FAIL] Invalid --market-data-type: $MARKET_DATA_TYPE"; exit 2;;
esac

export CONFIG_PATH CONTRACT_MAP_CSV EXECUTE MARKET_DATA_TYPE
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
import csv, math, os, yaml
from src.ibkr_market_data_contract_builder import build_market_data_contract
from src.ibkr_market_data_fallback import build_attempt_result, classify_error

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
requested_type = os.environ["MARKET_DATA_TYPE"]

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

gate_failures = []
if not execute: gate_failures.append("--execute was not provided")
if not read_only_required: gate_failures.append("read_only_required must be true")
if not real_connection_allowed: gate_failures.append("real_connection_allowed must be true")
if contract_qualification_allowed: gate_failures.append("contract_qualification_allowed must be false for market data snapshot")
if not market_data_request_allowed: gate_failures.append("market_data_request_allowed must be true")
if historical_data_request_allowed: gate_failures.append("historical_data_request_allowed must be false")
if trading_actions_allowed: gate_failures.append("trading_actions_allowed must be false")

decision = "NO_GO" if gate_failures else "GO_MARKET_DATA_SNAPSHOT_ONLY"
connection_attempted = False
connection_succeeded = False
rows=[]
ib=None

try:
  if not gate_failures:
    connection_attempted=True
    from ib_insync import IB, Contract
    ib=IB(); ib.connect(host, port, clientId=client_id, timeout=5, readonly=True); connection_succeeded=ib.isConnected()

    def market_data_attempt(contract, md_type_name):
      md_map={"live":1,"frozen":2,"delayed":3,"delayed_frozen":4}
      if md_type_name != "auto":
        ib.reqMarketDataType(md_map[md_type_name])
      ticker=ib.reqMktData(contract, "", True, False)
      ib.sleep(2)
      bid=as_float(getattr(ticker,"bid",None)); ask=as_float(getattr(ticker,"ask",None)); last=as_float(getattr(ticker,"last",None)); close=as_float(getattr(ticker,"close",None))
      try: market_price=as_float(ticker.marketPrice())
      except Exception: market_price=""
      has_price=any([bid,ask,last,close,market_price])
      effective={1:"live",2:"frozen",3:"delayed",4:"delayed_frozen"}.get(getattr(ticker,"marketDataType",None), md_type_name if md_type_name!="auto" else "unknown")
      err_code=""; err_message=""
      if hasattr(ticker, "snapshotPermissions") and getattr(ticker, "snapshotPermissions", None) in (0, None):
        pass
      ib.cancelMktData(contract)
      return bid,ask,last,close,market_price,has_price,effective,err_code,err_message

    def normalize_subscription_error(err_code, err_message):
      cls = classify_error(err_code, err_message)
      if cls == "live_not_subscribed":
        return "354", (err_message or "delayed market data available"), "delayed_available"
      return "", "", "live_snapshot_empty"

    for item in map_rows:
      status=item.get("status","")
      if status != "MAP_READY":
        result=build_attempt_result(requested_type,"unknown","unsupported","","Unsupported contract map status",False,0,"unsupported")
        rows.append((item,"","","","","",result))
        continue
      contract=build_market_data_contract(Contract, item)
      bid=ask=last=close=market_price=""
      error_code=""; error_message=""; fallback_stage="none"; attempts=0; fallback_reason=""
      if requested_type == "auto":
        ib.reqMarketDataType(1)
        bid,ask,last,close,market_price,has_price,effective,error_code,error_message = market_data_attempt(contract,"live")
        attempts=1
        if has_price:
          result=build_attempt_result("auto",effective,fallback_stage,error_code,error_message,True,attempts,fallback_reason)
        else:
          error_code,error_message,fallback_reason = normalize_subscription_error(error_code,error_message)
          fallback_stage="live_to_delayed"
          ib.reqMarketDataType(3)
          bid,ask,last,close,market_price,has_price,effective,error_code,error_message = market_data_attempt(contract,"delayed")
          attempts=2
          if not has_price:
            fallback_stage="delayed_to_delayed_frozen"; fallback_reason="delayed_snapshot_empty"
            ib.reqMarketDataType(4)
            bid,ask,last,close,market_price,has_price,effective,error_code,error_message = market_data_attempt(contract,"delayed_frozen")
            attempts=3
          result=build_attempt_result("auto",effective,fallback_stage,error_code,error_message,has_price,attempts,fallback_reason)
      else:
        bid,ask,last,close,market_price,has_price,effective,error_code,error_message = market_data_attempt(contract,requested_type)
        attempts=1
        result=build_attempt_result(requested_type,effective,fallback_stage,error_code,error_message,has_price,attempts,fallback_reason)
      rows.append((item,bid,ask,last,close,market_price,result))
  else:
    reason='; '.join(gate_failures)
    for item in map_rows:
      result=build_attempt_result(requested_type,"unknown","connection_error","",reason,False,0,reason)
      rows.append((item,"","","","","",result))
except Exception as exc:
  for item in map_rows:
    result=build_attempt_result(requested_type,"unknown","connection_error","",f"{type(exc).__name__}: {exc}",False,0,"connection_error")
    rows.append((item,"","","","","",result))
finally:
  if ib is not None:
    try: ib.disconnect()
    except Exception: pass

output=[]
for item,bid,ask,last,close,market_price,res in rows:
  output.append({"run_id":os.environ["RUN_ID"],"run_timestamp":os.environ["RUN_TS"],"timezone":"Asia/Tokyo","branch":os.environ["BRANCH"],"commit":os.environ["COMMIT"],"workflow":"ibkr_market_data_snapshot_oneshot","decision":decision,"execute_requested":str(execute).lower(),"display_symbol":item.get("display_symbol",""),"contract_map_status":item.get("status",""),"conid":item.get("conid",""),"local_symbol":item.get("local_symbol",""),"trading_class":item.get("trading_class",""),"exchange":item.get("exchange",""),"primary_exchange":item.get("primary_exchange",""),"currency":item.get("currency",""),"requested_market_data_type":res.requested_market_data_type,"effective_market_data_type":res.effective_market_data_type,"fallback_stage":res.fallback_stage,"error_code":res.error_code,"error_message":res.error_message,"live_permission_status":res.live_permission_status,"delayed_permission_status":res.delayed_permission_status,"delayed_frozen_permission_status":res.delayed_frozen_permission_status,"price_source_priority":res.price_source_priority,"data_delay_flag":res.data_delay_flag,"snapshot_attempt_count":str(res.snapshot_attempt_count),"fallback_reason":res.fallback_reason,"fallback_terminal_status":res.fallback_terminal_status,"read_only_required":str(read_only_required).lower(),"real_connection_allowed":str(real_connection_allowed).lower(),"contract_qualification_allowed":str(contract_qualification_allowed).lower(),"market_data_request_allowed":str(market_data_request_allowed).lower(),"historical_data_request_allowed":str(historical_data_request_allowed).lower(),"trading_actions_allowed":str(trading_actions_allowed).lower(),"ibkr_connection_triggered":str(connection_attempted).lower(),"connection_succeeded":str(connection_succeeded).lower(),"market_data_request_triggered":str(bool(connection_succeeded and not gate_failures and item.get('status')=='MAP_READY')).lower(),"historical_data_request_triggered":"false","broker_execution_triggered":"false","bid":bid,"ask":ask,"last":last,"close":close,"market_price":market_price,"data_status":res.data_status,"snapshot_status":res.snapshot_status,"manual_review_required":"true","action_allowed":"false","notes":res.error_message or res.fallback_reason})

Path(os.environ["CSV_PATH"]).write_text("")
with Path(os.environ["CSV_PATH"]).open("w", newline="") as f:
  w=csv.DictWriter(f, fieldnames=list(output[0].keys())); w.writeheader(); w.writerows(output)

lines="\n".join([f"| {r['display_symbol']} | {r['requested_market_data_type']} | {r['effective_market_data_type']} | {r['fallback_stage']} | {r['snapshot_status']} | {r['data_delay_flag']} | {r['fallback_terminal_status']} | {r['error_code']} | {r['error_message']} |" for r in output])
Path(os.environ["REPORT_PATH"]).write_text(f"""# IBKR Market Data Snapshot One-shot Report

## 1. Market Data Fallback Decision
- decision: {decision}
- requested_market_data_type: {requested_type}
- action_allowed: false
- manual_review_required: true

## 2. Error 354 Interpretation
- Error 354 does not imply contract failure.
- It means live market data subscription is missing for this venue/instrument.
- If delayed data is available, delayed/delayed_frozen fallback is allowed for research-only reference.
- action_allowed=false.

## 3. Fallback Attempt Summary
| display_symbol | requested | effective | fallback_stage | snapshot_status | delay_flag | terminal_status | error_code | error_message |
|---|---|---|---|---|---|---|---|---|
{lines}

## 4. Data Delay Classification
- real_time/frozen/delayed/delayed_frozen are recorded in `data_delay_flag`.
- delayed and delayed_frozen are non-real-time reference-only outputs.

## 5. Safety Confirmation
- historical_data_request_triggered=false
- broker_execution_triggered=false
- action_allowed=false
- manual_review_required=true
""")
print("[PASS] IBKR market data snapshot one-shot generated")
PY

echo "[PASS] No historical data request triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
