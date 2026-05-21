#!/usr/bin/env bash
set -euo pipefail

RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"

SUMMARY_CSV="telegram_ready_summary.csv"
REPORT_MD="reports/telegram_ready_report.md"
DIGEST_TXT="reports/telegram_ready_daily_digest.txt"

mkdir -p reports

echo "[INFO] Telegram-ready readable digest started: ${RUN_TS}"

# Generate upstream local runtime artifacts first.
./scripts/daily_research_run.sh --skip-tests
./scripts/data_source_status_report.sh

DAILY_STATUS="INPUT_REQUIRED"
FINAL_PLAN_STATUS="INPUT_REQUIRED"
TELEGRAM_READY_STATUS="TELEGRAM_BLOCKED"
DATA_SOURCE_STATUS="manual_csv_available=true; real_time_source_available=false; delayed_source_available=false"
BLOCKED_REASON="Required finalized research input is not available; digest is generated for manual review only."
MANUAL_REVIEW_REQUIRED="true"
ACTION_ALLOWED="false"

cat > "${SUMMARY_CSV}" <<CSV
run_id,run_timestamp,timezone,branch,commit,workflow,daily_summary_status,final_plan_status,telegram_ready_status,data_source_status,blocked_reason,manual_review_required,action_allowed,telegram_api_called,scheduler_deployed,broker_execution_triggered,safety_boundary
${RUN_ID},${RUN_TS},Asia/Tokyo,${BRANCH},${COMMIT},telegram_ready_digest,${DAILY_STATUS},${FINAL_PLAN_STATUS},${TELEGRAM_READY_STATUS},${DATA_SOURCE_STATUS},${BLOCKED_REASON},${MANUAL_REVIEW_REQUIRED},${ACTION_ALLOWED},false,false,false,research-only/read-only/manual-only/no-auto-trade
CSV

cat > "${DIGEST_TXT}" <<TXT
【贵金属监控日报 / Telegram-ready】

run_id: ${RUN_ID}
time: ${RUN_TS}
timezone: Asia/Tokyo
branch: ${BRANCH}
commit: ${COMMIT}

【状态摘要】
daily_summary_status: ${DAILY_STATUS}
final_plan_status: ${FINAL_PLAN_STATUS}
telegram_ready_status: ${TELEGRAM_READY_STATUS}
data_source_status: ${DATA_SOURCE_STATUS}

【阻断原因】
${BLOCKED_REASON}

【人工复核】
manual_review_required: ${MANUAL_REVIEW_REQUIRED}
action_allowed: ${ACTION_ALLOWED}

【安全边界】
telegram_api_called: false
scheduler_deployed: false
broker_execution_triggered: false
auto_trade_allowed: false

本消息仅为本地生成的研究摘要文本。未发送 Telegram，未连接券商，未请求行情，未触发任何交易。
TXT

cat > "${REPORT_MD}" <<MD
# Telegram-ready Readable Digest Report

## 1. Run metadata

- run_id: ${RUN_ID}
- run_timestamp: ${RUN_TS}
- timezone: Asia/Tokyo
- branch: ${BRANCH}
- commit: ${COMMIT}
- workflow: telegram_ready_digest

## 2. Digest summary

| field | value |
|---|---|
| daily_summary_status | ${DAILY_STATUS} |
| final_plan_status | ${FINAL_PLAN_STATUS} |
| telegram_ready_status | ${TELEGRAM_READY_STATUS} |
| data_source_status | ${DATA_SOURCE_STATUS} |
| blocked_reason | ${BLOCKED_REASON} |
| manual_review_required | ${MANUAL_REVIEW_REQUIRED} |
| action_allowed | ${ACTION_ALLOWED} |

## 3. Runtime artifacts

| artifact | path | committed_by_default |
|---|---|---:|
| telegram summary CSV | telegram_ready_summary.csv | false |
| telegram report | reports/telegram_ready_report.md | false |
| telegram digest text | reports/telegram_ready_daily_digest.txt | false |

## 4. Safety assertions

- telegram_api_called=false
- scheduler_deployed=false
- broker_execution_triggered=false
- action_allowed=false
- manual_review_required=true

## 5. Final boundary

This workflow generated local Telegram-ready text only.

No real message was sent, no scheduler was deployed, no broker connection occurred, and no automatic trading occurred.
MD

echo "[PASS] Telegram-ready readable digest generated"
echo "summary_csv=${SUMMARY_CSV}"
echo "report=${REPORT_MD}"
echo "digest=${DIGEST_TXT}"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
