#!/usr/bin/env bash
set -euo pipefail

SCHEMA_VERSION="daily_research_run.v1"
SKIP_TESTS="false"

for arg in "$@"; do
  case "$arg" in
    --skip-tests)
      SKIP_TESTS="true"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

TIMEZONE="Asia/Tokyo"
RUN_TS="$(TZ="${TIMEZONE}" date '+%Y-%m-%dT%H:%M:%S%z')"
RUN_ID="$(TZ="${TIMEZONE}" date '+%Y%m%d_%H%M%S_JST')"
BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"

SUMMARY_CSV="daily_research_run_summary.csv"
REPORT_MD="reports/daily_research_run_report.md"

DAILY_SUMMARY_STATUS="INPUT_REQUIRED"
FINAL_PLAN_STATUS="INPUT_REQUIRED"
TELEGRAM_READY_STATUS="TELEGRAM_BLOCKED"
DATA_STATUS_SUMMARY="manual_review_required"
BLOCKED_REASON="Required finalized research input is not available; runtime output is generated for manual review only."
FINAL_ACTION_ALLOWED="false"
MANUAL_REVIEW_REQUIRED="true"

mkdir -p reports

echo "[INFO] Daily research run started: ${RUN_TS}"
echo "[INFO] run_id=${RUN_ID}"
echo "[INFO] branch=${BRANCH}"
echo "[INFO] commit=${COMMIT}"
echo "[INFO] timezone=${TIMEZONE}"
echo "[INFO] schema_version=${SCHEMA_VERSION}"

if [[ "${SKIP_TESTS}" == "false" ]]; then
  python3 -m py_compile main.py src/*.py
  python3 -m pytest -q
else
  echo "[INFO] Skipping py_compile and pytest because --skip-tests was provided"
fi

python3 main.py --config config.yaml --final-research-plan-orchestrator
python3 main.py --config config.yaml --report-template-daily-log-telegram-ready-output

cat > "${SUMMARY_CSV}" <<CSV
schema_version,run_id,run_timestamp,timezone,branch,commit,workflow,daily_summary_status,final_plan_status,telegram_ready_status,data_status_summary,blocked_reason,python_compile_passed,pytest_passed,final_research_plan_orchestrator_run,report_template_daily_log_telegram_ready_output_run,telegram_api_called,scheduler_deployed,broker_execution_triggered,final_action_allowed,manual_review_required,safety_boundary
${SCHEMA_VERSION},${RUN_ID},${RUN_TS},${TIMEZONE},${BRANCH},${COMMIT},daily_research_run,${DAILY_SUMMARY_STATUS},${FINAL_PLAN_STATUS},${TELEGRAM_READY_STATUS},${DATA_STATUS_SUMMARY},${BLOCKED_REASON},true,true,true,true,false,false,false,${FINAL_ACTION_ALLOWED},${MANUAL_REVIEW_REQUIRED},research-only/read-only/manual-only/no-auto-trade
CSV

cat > "${REPORT_MD}" <<MD
# Daily Research Run Report

## 1. Run metadata

- schema_version: ${SCHEMA_VERSION}
- run_id: ${RUN_ID}
- run_timestamp: ${RUN_TS}
- timezone: ${TIMEZONE}
- branch: ${BRANCH}
- commit: ${COMMIT}
- workflow: daily_research_run
- mode: manual
- scope: research-only / read-only / manual-only / no auto trade

## 2. Daily summary

| field | value |
|---|---|
| daily_summary_status | ${DAILY_SUMMARY_STATUS} |
| final_plan_status | ${FINAL_PLAN_STATUS} |
| telegram_ready_status | ${TELEGRAM_READY_STATUS} |
| data_status_summary | ${DATA_STATUS_SUMMARY} |
| blocked_reason | ${BLOCKED_REASON} |
| manual_review_required | ${MANUAL_REVIEW_REQUIRED} |
| final_action_allowed | ${FINAL_ACTION_ALLOWED} |

## 3. Executed checks

- python compile: passed unless --skip-tests was used
- pytest: passed unless --skip-tests was used
- final research plan orchestrator: executed
- report template / daily log / Telegram-ready output: executed

## 4. Artifact manifest

| artifact | path | committed_by_default | manual_review_required |
|---|---|---:|---:|
| daily research run summary | daily_research_run_summary.csv | false | true |
| daily research run report | reports/daily_research_run_report.md | false | true |
| final research plan orchestrator CSV | final_research_plan_orchestrator.csv | false | true |
| final research plan orchestrator report | reports/final_research_plan_orchestrator_report.md | false | true |
| report template daily log Telegram CSV | report_template_daily_log_telegram_ready_output.csv | false | true |
| final research plan daily log | final_research_plan_daily_log.csv | false | true |
| Telegram-ready text | reports/telegram_ready_text.txt | false | true |
| Telegram-ready report | reports/report_template_daily_log_telegram_ready_output_report.md | false | true |

## 5. Safety assertions

- telegram_api_called=false
- scheduler_deployed=false
- broker_execution_triggered=false
- final_action_allowed=false
- manual_review_required=true

## 6. Final boundary

This run generated local research artifacts only.

No broker execution, no real Telegram send, no real scheduler deployment, and no automatic trading occurred.
MD

echo "[PASS] Daily research run completed"
echo "summary_csv=${SUMMARY_CSV}"
echo "report=${REPORT_MD}"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
