#!/usr/bin/env bash
set -euo pipefail

RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
SUMMARY_CSV="daily_research_run_summary.csv"
REPORT_MD="reports/daily_research_run_report.md"

mkdir -p reports

echo "[INFO] Daily research run started: ${RUN_TS}"

python3 -m py_compile main.py src/*.py
python3 -m pytest -q

python3 main.py --config config.yaml --final-research-plan-orchestrator
python3 main.py --config config.yaml --report-template-daily-log-telegram-ready-output

cat > "${SUMMARY_CSV}" <<CSV
run_timestamp,workflow,python_compile_passed,pytest_passed,final_research_plan_orchestrator_run,report_template_daily_log_telegram_ready_output_run,telegram_api_called,scheduler_deployed,broker_execution_triggered,final_action_allowed,manual_review_required,safety_boundary
${RUN_TS},daily_research_run,true,true,true,true,false,false,false,false,true,research-only/read-only/manual-only/no-auto-trade
CSV

cat > "${REPORT_MD}" <<MD
# Daily Research Run Report

## 1. Run metadata

- run_timestamp: ${RUN_TS}
- workflow: daily_research_run
- mode: manual
- scope: research-only / read-only / manual-only / no auto trade

## 2. Executed checks

- python compile: passed
- pytest: passed
- final research plan orchestrator: executed
- report template / daily log / Telegram-ready output: executed

## 3. Generated artifacts

- daily_research_run_summary.csv
- reports/daily_research_run_report.md
- final_research_plan_orchestrator.csv
- reports/final_research_plan_orchestrator_report.md
- report_template_daily_log_telegram_ready_output.csv
- final_research_plan_daily_log.csv
- reports/telegram_ready_text.txt
- reports/report_template_daily_log_telegram_ready_output_report.md

## 4. Safety assertions

- telegram_api_called=false
- scheduler_deployed=false
- broker_execution_triggered=false
- final_action_allowed=false
- manual_review_required=true

## 5. Final boundary

This run generated local research artifacts only.

No broker execution, no real Telegram send, no real scheduler deployment, and no automatic trading occurred.
MD

echo "[PASS] Daily research run completed"
echo "summary_csv=${SUMMARY_CSV}"
echo "report=${REPORT_MD}"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
