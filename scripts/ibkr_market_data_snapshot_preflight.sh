#!/usr/bin/env bash
set -euo pipefail

CONTRACT_MAP_CSV="ibkr_contract_map_lockin.csv"
CSV_PATH="ibkr_market_data_snapshot_preflight.csv"
REPORT_PATH="reports/ibkr_market_data_snapshot_preflight_report.md"

export CONTRACT_MAP_CSV CSV_PATH REPORT_PATH
export RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
export RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
export BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
export COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"

mkdir -p reports

echo "[INFO] IBKR market data snapshot preflight started: ${RUN_TS}"

python3 - <<'PY'
from pathlib import Path
import csv
import os

contract_map = Path(os.environ["CONTRACT_MAP_CSV"])
csv_path = Path(os.environ["CSV_PATH"])
report_path = Path(os.environ["REPORT_PATH"])

map_rows = []
if contract_map.exists():
    with contract_map.open(newline="") as f:
        map_rows = list(csv.DictReader(f))

if not map_rows:
    map_rows = [
        {"display_symbol": "1540.T", "status": "ROUTE_REQUIRED", "conid": "", "data_source_route": "IBKR_ROUTE_DISCOVERY_REQUIRED"},
        {"display_symbol": "1542.T", "status": "ROUTE_REQUIRED", "conid": "", "data_source_route": "IBKR_ROUTE_DISCOVERY_REQUIRED"},
        {"display_symbol": "518880.SH", "status": "IBKR_UNSUPPORTED", "conid": "", "data_source_route": "EXTERNAL_OR_MANUAL_ONLY"},
    ]

rows = []
for row in map_rows:
    status = row.get("status", "")
    conid = row.get("conid", "")
    if status == "MAP_READY" and conid:
        preflight_status = "READY_FOR_MARKET_DATA_FINAL_GATE"
        blocked_reason = "Market data still blocked until separate execution gate."
    elif status == "IBKR_UNSUPPORTED":
        preflight_status = "EXTERNAL_OR_MANUAL_ONLY"
        blocked_reason = "Instrument is not supported by IBKR route."
    else:
        preflight_status = "BLOCKED_ROUTE_REQUIRED"
        blocked_reason = "Contract map is not ready."

    rows.append({
        "run_id": os.environ["RUN_ID"],
        "run_timestamp": os.environ["RUN_TS"],
        "timezone": "Asia/Tokyo",
        "branch": os.environ["BRANCH"],
        "commit": os.environ["COMMIT"],
        "workflow": "ibkr_market_data_snapshot_preflight",
        "decision": "NO_GO",
        "display_symbol": row.get("display_symbol", ""),
        "contract_map_status": status,
        "conid": conid,
        "data_source_route": row.get("data_source_route", ""),
        "preflight_status": preflight_status,
        "market_data_request_allowed": "false",
        "historical_data_request_allowed": "false",
        "broker_execution_allowed": "false",
        "market_data_request_triggered": "false",
        "historical_data_request_triggered": "false",
        "broker_execution_triggered": "false",
        "manual_review_required": "true",
        "action_allowed": "false",
        "blocked_reason": blocked_reason,
    })

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

ready_count = sum(1 for r in rows if r["preflight_status"] == "READY_FOR_MARKET_DATA_FINAL_GATE")
blocked_count = sum(1 for r in rows if r["preflight_status"] == "BLOCKED_ROUTE_REQUIRED")
external_count = sum(1 for r in rows if r["preflight_status"] == "EXTERNAL_OR_MANUAL_ONLY")

lines = "\n".join(
    f"| {r['display_symbol']} | {r['contract_map_status']} | {r['conid']} | {r['preflight_status']} | {r['blocked_reason']} |"
    for r in rows
)

report_path.write_text(f"""# IBKR Market Data Snapshot Preflight Report

## 1. Summary

| field | value |
|---|---:|
| decision | NO_GO |
| ready_count | {ready_count} |
| blocked_count | {blocked_count} |
| external_count | {external_count} |
| action_allowed | false |

## 2. Preflight rows

| display_symbol | contract_map_status | conid | preflight_status | blocked_reason |
|---|---|---|---|---|
{lines}

## 3. Safety

- market_data_request_allowed=false
- historical_data_request_allowed=false
- broker_execution_allowed=false
- market_data_request_triggered=false
- historical_data_request_triggered=false
- broker_execution_triggered=false
- action_allowed=false
""")

print("[PASS] IBKR market data snapshot preflight generated")
print(f"ready_count={ready_count}")
print(f"blocked_count={blocked_count}")
print(f"external_count={external_count}")
print(f"csv={csv_path}")
print(f"report={report_path}")
PY
