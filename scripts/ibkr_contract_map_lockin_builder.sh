#!/usr/bin/env bash
set -euo pipefail

SOURCE_CSV="ibkr_jp_route_discovery_oneshot.csv"
CSV_PATH="ibkr_contract_map_lockin.csv"
REPORT_PATH="reports/ibkr_contract_map_lockin_report.md"

export SOURCE_CSV CSV_PATH REPORT_PATH
export RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
export RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
export BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
export COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"

mkdir -p reports

echo "[INFO] IBKR contract map lock-in builder started: ${RUN_TS}"

python3 - <<'PY'
from pathlib import Path
import csv
import os

source = Path(os.environ["SOURCE_CSV"])
csv_path = Path(os.environ["CSV_PATH"])
report_path = Path(os.environ["REPORT_PATH"])

source_rows = []
if source.exists():
    with source.open(newline="") as f:
        source_rows = list(csv.DictReader(f))

def best_route(display_symbol: str):
    candidates = [
        r for r in source_rows
        if r.get("display_symbol") == display_symbol
        and r.get("route_status") == "CANDIDATE"
        and (r.get("contract_details_count") or "0").isdigit()
        and int(r.get("contract_details_count") or "0") > 0
        and r.get("conid")
    ]
    candidates.sort(key=lambda r: int(r.get("candidate_priority") or "999"))
    return candidates[0] if candidates else None

rows = []
for display_symbol in ["1540.T", "1542.T"]:
    route = best_route(display_symbol)
    if route:
        status = "MAP_READY"
        notes = "Locked from successful route discovery result."
        data_source_route = "IBKR_CONTRACT_DETAILS"
    else:
        status = "ROUTE_REQUIRED"
        notes = "No successful route discovery result available yet."
        data_source_route = "IBKR_ROUTE_DISCOVERY_REQUIRED"
        route = {
            "symbol": display_symbol.split(".")[0],
            "exchange": "",
            "primary_exchange": "",
            "currency": "",
            "sec_type": "",
            "conid": "",
            "local_symbol": "",
            "trading_class": "",
            "market_name": "",
            "min_tick": "",
            "route_family": "",
        }

    rows.append({
        "run_id": os.environ["RUN_ID"],
        "run_timestamp": os.environ["RUN_TS"],
        "timezone": "Asia/Tokyo",
        "branch": os.environ["BRANCH"],
        "commit": os.environ["COMMIT"],
        "workflow": "ibkr_contract_map_lockin_builder",
        "display_symbol": display_symbol,
        "status": status,
        "symbol": route.get("symbol", ""),
        "sec_type": route.get("sec_type", ""),
        "exchange": route.get("exchange", ""),
        "primary_exchange": route.get("primary_exchange", ""),
        "currency": route.get("currency", ""),
        "conid": route.get("conid", ""),
        "local_symbol": route.get("local_symbol", ""),
        "trading_class": route.get("trading_class", ""),
        "market_name": route.get("market_name", ""),
        "min_tick": route.get("min_tick", ""),
        "route_family": route.get("route_family", ""),
        "data_source_route": data_source_route,
        "market_data_allowed": "false",
        "historical_data_allowed": "false",
        "broker_execution_allowed": "false",
        "manual_review_required": "true",
        "action_allowed": "false",
        "notes": notes,
    })

rows.append({
    "run_id": os.environ["RUN_ID"],
    "run_timestamp": os.environ["RUN_TS"],
    "timezone": "Asia/Tokyo",
    "branch": os.environ["BRANCH"],
    "commit": os.environ["COMMIT"],
    "workflow": "ibkr_contract_map_lockin_builder",
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
    "market_name": "",
    "min_tick": "",
    "route_family": "external_or_manual_only",
    "data_source_route": "EXTERNAL_OR_MANUAL_ONLY",
    "market_data_allowed": "false",
    "historical_data_allowed": "false",
    "broker_execution_allowed": "false",
    "manual_review_required": "true",
    "action_allowed": "false",
    "notes": "Excluded from IBKR contract map.",
})

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

ready_count = sum(1 for r in rows if r["status"] == "MAP_READY")
route_required_count = sum(1 for r in rows if r["status"] == "ROUTE_REQUIRED")
unsupported_count = sum(1 for r in rows if r["status"] == "IBKR_UNSUPPORTED")

lines = "\n".join(
    f"| {r['display_symbol']} | {r['status']} | {r['conid']} | {r['exchange']} | {r['primary_exchange']} | {r['local_symbol']} | {r['data_source_route']} |"
    for r in rows
)

report_path.write_text(f"""# IBKR Contract Map Lock-in Report

## 1. Summary

| field | value |
|---|---:|
| ready_count | {ready_count} |
| route_required_count | {route_required_count} |
| unsupported_count | {unsupported_count} |
| action_allowed | false |

## 2. Contract map

| display_symbol | status | conid | exchange | primary_exchange | local_symbol | data_source_route |
|---|---|---|---|---|---|---|
{lines}

## 3. Safety

- market_data_allowed=false
- historical_data_allowed=false
- broker_execution_allowed=false
- action_allowed=false
- manual_review_required=true
""")

print("[PASS] IBKR contract map lock-in generated")
print(f"ready_count={ready_count}")
print(f"route_required_count={route_required_count}")
print(f"unsupported_count={unsupported_count}")
print(f"csv={csv_path}")
print(f"report={report_path}")
PY
