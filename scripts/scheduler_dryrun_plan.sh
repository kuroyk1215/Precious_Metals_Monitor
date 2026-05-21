#!/usr/bin/env bash
set -euo pipefail

RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"

CSV_PATH="scheduler_dryrun_plan.csv"
REPORT_PATH="reports/scheduler_dryrun_report.md"
SAMPLE_PLIST="examples/launchd_daily_research_run.sample.plist"

mkdir -p reports logs/local logs/failures

echo "[INFO] Scheduler dry-run plan started: ${RUN_TS}"

cat > "${CSV_PATH}" <<CSV
run_id,run_timestamp,timezone,market,time_jst,workflow,launchd_installed,launchctl_called,telegram_api_called,broker_execution_triggered,auto_trade_allowed,manual_review_required,action_allowed
${RUN_ID},${RUN_TS},Asia/Tokyo,JP,08:30,pre_market_research_run,false,false,false,false,false,true,false
${RUN_ID},${RUN_TS},Asia/Tokyo,JP,12:00,midday_research_run,false,false,false,false,false,true,false
${RUN_ID},${RUN_TS},Asia/Tokyo,JP,16:00,post_close_research_run,false,false,false,false,false,true,false
${RUN_ID},${RUN_TS},Asia/Tokyo,US,21:30,pre_us_research_run,false,false,false,false,false,true,false
${RUN_ID},${RUN_TS},Asia/Tokyo,US,01:00,us_session_review,false,false,false,false,false,true,false
${RUN_ID},${RUN_TS},Asia/Tokyo,US,05:15,post_us_research_run,false,false,false,false,false,true,false
CSV

cat > "${REPORT_PATH}" <<MD
# Scheduler Dry-run Report

## 1. Run metadata

- run_id: ${RUN_ID}
- run_timestamp: ${RUN_TS}
- timezone: Asia/Tokyo
- branch: ${BRANCH}
- commit: ${COMMIT}
- workflow: scheduler_dryrun_plan

## 2. Proposed schedule

| market | time_jst | workflow |
|---|---:|---|
| JP | 08:30 | pre_market_research_run |
| JP | 12:00 | midday_research_run |
| JP | 16:00 | post_close_research_run |
| US | 21:30 | pre_us_research_run |
| US | 01:00 | us_session_review |
| US | 05:15 | post_us_research_run |

## 3. Launchd sample

- sample_plist: ${SAMPLE_PLIST}
- installed: false
- launchctl_called: false
- background_job_started: false

## 4. Safety assertions

- launchd_installed=false
- launchctl_called=false
- telegram_api_called=false
- broker_execution_triggered=false
- auto_trade_allowed=false
- manual_review_required=true
- action_allowed=false

## 5. Final boundary

This is a scheduler dry-run plan only.

No launchd job was installed, no launchctl command was called, no Telegram message was sent, no broker connection occurred, and no automatic trading occurred.
MD

echo "[PASS] Scheduler dry-run plan generated"
echo "csv=${CSV_PATH}"
echo "report=${REPORT_PATH}"
echo "sample_plist=${SAMPLE_PLIST}"
echo "[PASS] No launchd job installed"
echo "[PASS] No launchctl command called"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
