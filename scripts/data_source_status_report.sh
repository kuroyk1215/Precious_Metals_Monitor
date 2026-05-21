#!/usr/bin/env bash
set -euo pipefail

RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"

CSV_PATH="data_source_status.csv"
REPORT_PATH="reports/data_source_status_report.md"

mkdir -p reports

cat > "${CSV_PATH}" <<CSV
source_name,market,instrument,source_type,data_status,license_required,subscription_required,fallback_priority,manual_review_required,action_allowed,notes
manual_csv,JP,1540.T,local_file,manual_csv,false,false,1,true,false,Manual CSV is allowed for local research review only.
manual_csv,JP,1542.T,local_file,manual_csv,false,false,1,true,false,Manual CSV is allowed for local research review only.
manual_csv,CN,518880.SH,local_file,manual_csv,false,false,1,true,false,Manual CSV is allowed for local research review only.
ibkr_readonly,JP,1540.T,broker_readonly,unavailable,true,true,2,true,false,IBKR read-only data is unavailable unless explicitly enabled and entitled.
ibkr_readonly,JP,1542.T,broker_readonly,unavailable,true,true,2,true,false,IBKR read-only data is unavailable unless explicitly enabled and entitled.
ibkr_readonly,CN,518880.SH,broker_readonly,unavailable,true,true,2,true,false,IBKR coverage must be manually verified before use.
synthetic_sample,ALL,ALL,local_sample,synthetic_sample,false,false,3,true,false,Synthetic samples are for tests only and must not be treated as market data.
mock_runtime,ALL,ALL,local_mock,mock,false,false,4,true,false,Mock runtime data is for pipeline validation only.
CSV

cat > "${REPORT_PATH}" <<MD
# Data Source Status Report

## 1. Run metadata

- run_id: ${RUN_ID}
- run_timestamp: ${RUN_TS}
- timezone: Asia/Tokyo
- branch: ${BRANCH}
- commit: ${COMMIT}
- workflow: data_source_status_report

## 2. Summary

| field | value |
|---|---|
| data_source_report_status | INPUT_REQUIRED |
| real_time_source_available | false |
| delayed_source_available | false |
| manual_csv_available | true |
| mock_source_available | true |
| synthetic_sample_available | true |
| manual_review_required | true |
| action_allowed | false |

## 3. Data source posture

| source_name | status | use |
|---|---|---|
| manual_csv | manual_csv | local research review only |
| ibkr_readonly | unavailable | requires explicit entitlement and gate approval |
| synthetic_sample | synthetic_sample | tests only |
| mock_runtime | mock | pipeline validation only |

## 4. Safety assertions

- ibkr_connection_triggered=false
- market_data_request_triggered=false
- historical_data_request_triggered=false
- contract_qualification_triggered=false
- telegram_api_called=false
- scheduler_deployed=false
- broker_execution_triggered=false
- action_allowed=false
- manual_review_required=true

## 5. Final boundary

This report is a local audit artifact only.

No IBKR connection, no market data request, no historical data request, no Telegram send, no scheduler deployment, and no broker execution occurred.
MD

echo "[PASS] Data source status report generated"
echo "csv=${CSV_PATH}"
echo "report=${REPORT_PATH}"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
