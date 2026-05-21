#!/usr/bin/env bash
set -euo pipefail

RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"

SUMMARY_CSV="dashboard_static_view_summary.csv"
REPORT_MD="reports/dashboard_static_view_report.md"
HTML_PATH="reports/dashboard/index.html"

mkdir -p reports/dashboard

echo "[INFO] Dashboard local static view generation started: ${RUN_TS}"

# Generate upstream local runtime artifacts first.
./scripts/daily_research_run.sh --skip-tests
./scripts/data_source_status_report.sh
./scripts/telegram_ready_digest.sh
./scripts/scheduler_dryrun_plan.sh

DASHBOARD_STATUS="STATIC_VIEW_READY"
DAILY_SUMMARY_STATUS="INPUT_REQUIRED"
DATA_SOURCE_STATUS="manual_csv_available=true; real_time_source_available=false"
TELEGRAM_READY_STATUS="TELEGRAM_BLOCKED"
SCHEDULER_STATUS="DRY_RUN_ONLY"
BLOCKED_REASON="Dashboard is local static view only; no external execution controls are enabled."
MANUAL_REVIEW_REQUIRED="true"
ACTION_ALLOWED="false"

cat > "${SUMMARY_CSV}" <<CSV
run_id,run_timestamp,timezone,branch,commit,workflow,dashboard_status,daily_summary_status,data_source_status,telegram_ready_status,scheduler_status,blocked_reason,manual_review_required,action_allowed,broker_execution_triggered,telegram_api_called,scheduler_deployed,auto_trade_allowed,safety_boundary
${RUN_ID},${RUN_TS},Asia/Tokyo,${BRANCH},${COMMIT},dashboard_static_view,${DASHBOARD_STATUS},${DAILY_SUMMARY_STATUS},${DATA_SOURCE_STATUS},${TELEGRAM_READY_STATUS},${SCHEDULER_STATUS},${BLOCKED_REASON},${MANUAL_REVIEW_REQUIRED},${ACTION_ALLOWED},false,false,false,false,research-only/read-only/manual-only/no-auto-trade
CSV

cat > "${HTML_PATH}" <<HTML
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>Precious Metals Monitor - Local Static Dashboard</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; line-height: 1.5; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 16px 0; }
    table { border-collapse: collapse; width: 100%; }
    td, th { border: 1px solid #ddd; padding: 8px; }
    code { background: #f5f5f5; padding: 2px 4px; }
  </style>
</head>
<body>
  <h1>Precious Metals Monitor - Local Static Dashboard</h1>

  <div class="card">
    <h2>Run metadata</h2>
    <table>
      <tr><th>field</th><th>value</th></tr>
      <tr><td>run_id</td><td>${RUN_ID}</td></tr>
      <tr><td>run_timestamp</td><td>${RUN_TS}</td></tr>
      <tr><td>timezone</td><td>Asia/Tokyo</td></tr>
      <tr><td>branch</td><td>${BRANCH}</td></tr>
      <tr><td>commit</td><td>${COMMIT}</td></tr>
    </table>
  </div>

  <div class="card">
    <h2>Status summary</h2>
    <table>
      <tr><th>field</th><th>value</th></tr>
      <tr><td>dashboard_status</td><td>${DASHBOARD_STATUS}</td></tr>
      <tr><td>daily_summary_status</td><td>${DAILY_SUMMARY_STATUS}</td></tr>
      <tr><td>data_source_status</td><td>${DATA_SOURCE_STATUS}</td></tr>
      <tr><td>telegram_ready_status</td><td>${TELEGRAM_READY_STATUS}</td></tr>
      <tr><td>scheduler_status</td><td>${SCHEDULER_STATUS}</td></tr>
      <tr><td>blocked_reason</td><td>${BLOCKED_REASON}</td></tr>
    </table>
  </div>

  <div class="card">
    <h2>Safety assertions</h2>
    <ul>
      <li>broker_execution_triggered=false</li>
      <li>telegram_api_called=false</li>
      <li>scheduler_deployed=false</li>
      <li>auto_trade_allowed=false</li>
      <li>action_allowed=false</li>
      <li>manual_review_required=true</li>
    </ul>
  </div>

  <div class="card">
    <h2>Local artifacts</h2>
    <ul>
      <li><code>daily_research_run_summary.csv</code></li>
      <li><code>data_source_status.csv</code></li>
      <li><code>telegram_ready_summary.csv</code></li>
      <li><code>scheduler_dryrun_plan.csv</code></li>
      <li><code>reports/dashboard/index.html</code></li>
    </ul>
  </div>

  <p>This is a local static review page only. It does not send Telegram messages, deploy schedulers, connect to brokers, request market data, or execute trades.</p>
</body>
</html>
HTML

cat > "${REPORT_MD}" <<MD
# Dashboard Local Static View Report

## 1. Run metadata

- run_id: ${RUN_ID}
- run_timestamp: ${RUN_TS}
- timezone: Asia/Tokyo
- branch: ${BRANCH}
- commit: ${COMMIT}
- workflow: dashboard_static_view

## 2. Summary

| field | value |
|---|---|
| dashboard_status | ${DASHBOARD_STATUS} |
| daily_summary_status | ${DAILY_SUMMARY_STATUS} |
| data_source_status | ${DATA_SOURCE_STATUS} |
| telegram_ready_status | ${TELEGRAM_READY_STATUS} |
| scheduler_status | ${SCHEDULER_STATUS} |
| blocked_reason | ${BLOCKED_REASON} |
| manual_review_required | ${MANUAL_REVIEW_REQUIRED} |
| action_allowed | ${ACTION_ALLOWED} |

## 3. Runtime artifacts

| artifact | path | committed_by_default |
|---|---|---:|
| dashboard summary CSV | dashboard_static_view_summary.csv | false |
| dashboard report | reports/dashboard_static_view_report.md | false |
| dashboard HTML | reports/dashboard/index.html | false |

## 4. Safety assertions

- broker_execution_triggered=false
- telegram_api_called=false
- scheduler_deployed=false
- auto_trade_allowed=false
- action_allowed=false
- manual_review_required=true

## 5. Final boundary

This workflow generated a local static dashboard view only.

No broker connection, no market data request, no Telegram send, no scheduler deployment, and no automatic trading occurred.
MD

echo "[PASS] Dashboard local static view generated"
echo "summary_csv=${SUMMARY_CSV}"
echo "report=${REPORT_MD}"
echo "html=${HTML_PATH}"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
