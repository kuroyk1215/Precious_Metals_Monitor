# Phase 77-80 Daily Research Run Metadata Schema

## 1. Purpose

This document defines the metadata and schema requirements for daily research run outputs.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Summary CSV schema

`daily_research_run_summary.csv` must include:

- schema_version
- run_id
- run_timestamp
- timezone
- branch
- commit
- workflow
- python_compile_passed
- pytest_passed
- final_research_plan_orchestrator_run
- report_template_daily_log_telegram_ready_output_run
- telegram_api_called
- scheduler_deployed
- broker_execution_triggered
- final_action_allowed
- manual_review_required
- safety_boundary

## 3. Required metadata

Each daily run must record:

- run_id
- run_timestamp
- timezone=Asia/Tokyo
- branch
- commit
- schema_version

## 4. Artifact manifest

The Markdown report must include an artifact manifest describing generated local outputs.

Runtime artifacts are not committed by default.

## 5. Safety boundary

The schema must preserve these assertions:

- telegram_api_called=false
- scheduler_deployed=false
- broker_execution_triggered=false
- final_action_allowed=false
- manual_review_required=true

## 6. Final boundary

Daily research run metadata supports auditability only.

It does not authorize external execution, background operation, broker connection, or automatic trading.
