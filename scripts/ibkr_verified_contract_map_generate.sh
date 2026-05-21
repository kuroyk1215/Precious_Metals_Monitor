#!/usr/bin/env bash
set -euo pipefail

export RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
export RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
export BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
export COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"
export CSV_PATH="ibkr_verified_contract_map.csv"
export REPORT_PATH="reports/ibkr_verified_contract_map_report.md"

mkdir -p reports

echo "[INFO] IBKR verified contract map generator started: ${RUN_TS}"

python3 - <<'PY'
from pathlib import Path
import csv
import os

rows = [
    {
        "run_id": os.environ["RUN_ID"],
        "run_timestamp": os.environ["RUN_TS"],
        "timezone": "Asia/Tokyo",
        "branch": os.environ["BRANCH"],
        "commit": os.environ["COMMIT"],
        "workflow": "ibkr_verified_contract_map_generate",
        "display_symbol": "1540.T",
        "status": "MAP_READY",
        "symbol": "1540",
        "sec_type": "STK",
        "exchange": "SMART",
        "primary_exchange": "TSEJ",
        "currency": "JPY",
        "conid": "117595037",
        "local_symbol": "1540.T",
        "trading_class": "1540",
        "data_source_route": "IBKR_CONTRACT_DETAILS",
        "market_data_allowed": "false",
        "historical_data_allowed": "false",
        "broker_execution_allowed": "false",
        "manual_review_required": "true",
        "action_allowed": "false",
        "notes": "Verified from Execution A route discovery.",
    },
    {
        "run_id": os.environ["RUN_ID"],
        "run_timestamp": os.environ["RUN_TS"],
        "timezone": "Asia/Tokyo",
        "branch": os.environ["BRANCH"],
        "commit": os.environ["COMMIT"],
        "workflow": "ibkr_verified_contract_map_generate",
        "display_symbol": "1542.T",
        "status": "MAP_READY",
        "symbol": "1542",
        "sec_type": "STK",
        "exchange": "SMART",
        "primary_exchange": "TSEJ",
        "currency": "JPY",
        "conid": "121557296",
        "local_symbol": "1542.T",
        "trading_class": "1542",
        "data_source_route": "IBKR_CONTRACT_DETAILS",
        "market_data_allowed": "false",
        "historical_data_allowed": "false",
        "broker_execution_allowed": "false",
        "manual_review_required": "true",
        "action_allowed": "false",
        "notes": "Verified from Execution A route discovery.",
    },
    {
        "run_id": os.environ["RUN_ID"],
        "run_timestamp": os.environ["RUN_TS"],
        "timezone": "Asia/Tokyo",
        "branch": os.environ["BRANCH"],
        "commit": os.environ["COMMIT"],
        "workflow": "ibkr_verified_contract_map_generate",
        "display_symbol": "518880.SH",
        "status": "IBKR_UNSUPPORTED",
        "symbol": "518880",
        "sec_type": "",
        "exchange": "",
        "primary_exchange": "",
        "currency": "",
        "conid": "",
        "local_symbol": "",
        "trading_class": "",
        "data_source_route": "EXTERNAL_OR_MANUAL_ONLY",
        "market_data_allowed": "false",
        "historical_data_allowed": "false",
        "broker_execution_allowed": "false",
        "manual_review_required": "true",
        "action_allowed": "false",
        "notes": "Excluded from IBKR market data path.",
    },
]

csv_path = Path(os.environ["CSV_PATH"])
report_path = Path(os.environ["REPORT_PATH"])

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

ready_count = sum(1 for r in rows if r["status"] == "MAP_READY")
unsupported_count = sum(1 for r in rows if r["status"] == "IBKR_UNSUPPORTED")

lines = "\n".join(
    f"| {r['display_symbol']} | {r['status']} | {r['conid']} | {r['exchange']} | {r['primary_exchange']} | {r['local_symbol']} | {r['trading_class']} | {r['data_source_route']} |"
    for r in rows
)

report_path.write_text(f"""# IBKR Verified Contract Map Report

## 1. Summary

| field | value |
|---|---:|
| ready_count | {ready_count} |
| unsupported_count | {unsupported_count} |
| action_allowed | false |

## 2. Verified map

| display_symbol | status | conid | exchange | primary_exchange | local_symbol | trading_class | data_source_route |
|---|---|---:|---|---|---|---|---|
{lines}

## 3. Safety

- market_data_allowed=false
- historical_data_allowed=false
- broker_execution_allowed=false
- action_allowed=false
- manual_review_required=true
""")

print("[PASS] IBKR verified contract map generated")
print(f"ready_count={ready_count}")
print(f"unsupported_count={unsupported_count}")
print(f"csv={csv_path}")
print(f"report={report_path}")
PY
