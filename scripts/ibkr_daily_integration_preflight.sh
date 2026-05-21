#!/usr/bin/env bash
set -euo pipefail

SNAPSHOT_CSV="ibkr_market_data_snapshot.csv"
CSV_PATH="ibkr_daily_integration_preflight.csv"
REPORT_PATH="reports/ibkr_daily_integration_preflight_report.md"

export SNAPSHOT_CSV CSV_PATH REPORT_PATH
export RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
export RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
export BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
export COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"

mkdir -p reports

echo "[INFO] IBKR daily integration preflight started: ${RUN_TS}"

python3 - <<'PY'
from pathlib import Path
import csv
import os

snapshot_path = Path(os.environ["SNAPSHOT_CSV"])
snapshot_rows = []
if snapshot_path.exists():
    with snapshot_path.open(newline="") as f:
        snapshot_rows = list(csv.DictReader(f))

if not snapshot_rows:
    snapshot_rows = [
        {"display_symbol": "1540.T", "contract_map_status": "MAP_READY", "conid": "117595037", "snapshot_status": "NO_GO", "data_status": "not_requested", "market_price": "", "bid": "", "ask": "", "last": "", "close": ""},
        {"display_symbol": "1542.T", "contract_map_status": "MAP_READY", "conid": "121557296", "snapshot_status": "NO_GO", "data_status": "not_requested", "market_price": "", "bid": "", "ask": "", "last": "", "close": ""},
        {"display_symbol": "518880.SH", "contract_map_status": "IBKR_UNSUPPORTED", "conid": "", "snapshot_status": "SKIPPED_UNSUPPORTED", "data_status": "external_or_unsupported", "market_price": "", "bid": "", "ask": "", "last": "", "close": ""},
    ]

rows = []
for s in snapshot_rows:
    snapshot_status = s.get("snapshot_status", "")
    if snapshot_status == "SNAPSHOT_RETURNED":
        integration_status = "READY_FOR_DAILY_RESEARCH_INPUT"
        blocked_reason = "IBKR snapshot is available, but downstream report remains manual review only."
    elif s.get("contract_map_status") == "IBKR_UNSUPPORTED":
        integration_status = "EXTERNAL_OR_MANUAL_ONLY"
        blocked_reason = "Instrument is not eligible for IBKR market data."
    else:
        integration_status = "BLOCKED_MARKET_DATA_NOT_READY"
        blocked_reason = "Market data snapshot is not available."

    rows.append({
        "run_id": os.environ["RUN_ID"],
        "run_timestamp": os.environ["RUN_TS"],
        "timezone": "Asia/Tokyo",
        "branch": os.environ["BRANCH"],
        "commit": os.environ["COMMIT"],
        "workflow": "ibkr_daily_integration_preflight",
        "decision": "NO_GO",
        "display_symbol": s.get("display_symbol", ""),
        "contract_map_status": s.get("contract_map_status", ""),
        "conid": s.get("conid", ""),
        "snapshot_status": snapshot_status,
        "data_status": s.get("data_status", ""),
        "bid": s.get("bid", ""),
        "ask": s.get("ask", ""),
        "last": s.get("last", ""),
        "close": s.get("close", ""),
        "market_price": s.get("market_price", ""),
        "integration_status": integration_status,
        "daily_research_input_allowed": "false",
        "telegram_send_allowed": "false",
        "dashboard_publish_allowed": "false",
        "broker_execution_allowed": "false",
        "manual_review_required": "true",
        "action_allowed": "false",
        "blocked_reason": blocked_reason,
    })

csv_path = Path(os.environ["CSV_PATH"])
report_path = Path(os.environ["REPORT_PATH"])

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

ready_count = sum(1 for r in rows if r["integration_status"] == "READY_FOR_DAILY_RESEARCH_INPUT")
blocked_count = sum(1 for r in rows if r["integration_status"] == "BLOCKED_MARKET_DATA_NOT_READY")
external_count = sum(1 for r in rows if r["integration_status"] == "EXTERNAL_OR_MANUAL_ONLY")

lines = "\n".join(
    f"| {r['display_symbol']} | {r['snapshot_status']} | {r['data_status']} | {r['market_price']} | {r['integration_status']} | {r['blocked_reason']} |"
    for r in rows
)

report_path.write_text(f"""# IBKR Daily Integration Preflight Report

## 1. Summary

| field | value |
|---|---:|
| decision | NO_GO |
| ready_count | {ready_count} |
| blocked_count | {blocked_count} |
| external_count | {external_count} |
| action_allowed | false |

## 2. Integration rows

| display_symbol | snapshot_status | data_status | market_price | integration_status | blocked_reason |
|---|---|---|---:|---|---|
{lines}

## 3. Safety

- daily_research_input_allowed=false
- telegram_send_allowed=false
- dashboard_publish_allowed=false
- broker_execution_allowed=false
- action_allowed=false
- manual_review_required=true
""")

print("[PASS] IBKR daily integration preflight generated")
print(f"ready_count={ready_count}")
print(f"blocked_count={blocked_count}")
print(f"external_count={external_count}")
print(f"csv={csv_path}")
print(f"report={report_path}")
PY
