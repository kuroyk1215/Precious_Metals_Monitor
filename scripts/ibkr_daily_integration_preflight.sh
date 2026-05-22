#!/usr/bin/env bash
set -euo pipefail

SNAPSHOT_CSV="ibkr_market_data_snapshot.csv"
CSV_PATH="ibkr_daily_integration_preflight.csv"
REPORT_PATH="reports/ibkr_daily_integration_preflight_report.md"

for arg in "$@"; do
  case "$arg" in
    --market-data-snapshot=*)
      SNAPSHOT_CSV="${arg#--market-data-snapshot=}"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

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

from src.ibkr_daily_marketdata_integration import (
    OUTPUT_FIELDS,
    build_integration_rows,
    missing_input_row,
    read_snapshot_rows,
)

snapshot_path = Path(os.environ["SNAPSHOT_CSV"])
snapshot_input_status, snapshot_rows = read_snapshot_rows(snapshot_path)

if snapshot_rows:
    integration_rows = build_integration_rows(snapshot_rows)
else:
    integration_rows = [missing_input_row(str(snapshot_path))]

metadata = {
    "run_id": os.environ["RUN_ID"],
    "run_timestamp": os.environ["RUN_TS"],
    "timezone": "Asia/Tokyo",
    "branch": os.environ["BRANCH"],
    "commit": os.environ["COMMIT"],
    "workflow": "ibkr_daily_integration_preflight",
    "decision": "NO_GO",
    "daily_integration_status": "NO_GO",
    "market_data_snapshot_input": str(snapshot_path),
    "market_data_snapshot_status": snapshot_input_status,
    "daily_research_input_allowed": "false",
    "telegram_send_allowed": "false",
    "dashboard_publish_allowed": "false",
    "broker_execution_allowed": "false",
    "broker_execution_triggered": "false",
    "historical_data_request_triggered": "false",
    "account_read_triggered": "false",
    "position_read_triggered": "false",
}

rows = [{**metadata, **row} for row in integration_rows]

csv_path = Path(os.environ["CSV_PATH"])
report_path = Path(os.environ["REPORT_PATH"])

fieldnames = list(metadata.keys()) + list(OUTPUT_FIELDS)
with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

status_counts = {}
delay_counts = {}
for row in rows:
    status_counts[row["integration_status"]] = status_counts.get(row["integration_status"], 0) + 1
    delay_counts[row["data_delay_flag"]] = delay_counts.get(row["data_delay_flag"], 0) + 1

status_lines = "\n".join(
    f"| {status} | {count} |" for status, count in sorted(status_counts.items())
)
delay_lines = "\n".join(
    f"| {delay} | {count} |" for delay, count in sorted(delay_counts.items())
)
row_lines = "\n".join(
    "| {display_symbol} | {input_snapshot_status} | {effective_market_data_type} | "
    "{data_delay_flag} | {usable_reference_price} | {usable_reference_price_field} | "
    "{data_quality_tier} | {research_usage} | {integration_status} | {reject_reason} |".format(**row)
    for row in rows
)

report_path.write_text(f"""# IBKR Daily Integration Preflight Report

## Daily Integration Decision

| field | value |
|---|---|
| daily_integration_status | NO_GO |
| decision | NO_GO |
| action_allowed | false |
| manual_review_required | true |

## Market Data Snapshot Input

| field | value |
|---|---|
| market_data_snapshot_input | {snapshot_path} |
| market_data_snapshot_status | {snapshot_input_status} |
| rows_read | {len(snapshot_rows)} |

## Symbol Integration Rows

| display_symbol | input_snapshot_status | effective_market_data_type | data_delay_flag | usable_reference_price | usable_reference_price_field | data_quality_tier | research_usage | integration_status | reject_reason |
|---|---|---|---|---:|---|---|---|---|---|
{row_lines}

## Data Delay Classification

| data_delay_flag | count |
|---|---:|
{delay_lines}

| integration_status | count |
|---|---:|
{status_lines}

Delayed and delayed_frozen rows are research-only reference inputs. They are not real-time signals and cannot authorize broker action.

## Safety Confirmation

- action_allowed=false
- broker_execution_triggered=false
- historical_data_request_triggered=false
- account_read_triggered=false
- position_read_triggered=false
- manual_review_required=true

## Next Phase Handoff

Phase 273+ may consume this preflight CSV in a research review pack. It must preserve manual review, no account reads, no position reads, no historical requests, and no broker execution.
""")

print("[PASS] IBKR daily integration preflight generated")
print(f"market_data_snapshot_status={snapshot_input_status}")
print("daily_integration_status=NO_GO")
print("action_allowed=false")
print(f"csv={csv_path}")
print(f"report={report_path}")
PY
