# MVP v1.0 Operation Index

## 1. Purpose

This index provides a navigation map for operating Precious_Metals_Monitor MVP v1.0.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Start here

Recommended reading order:

1. docs/MVP_SUMMARY.md
2. docs/USER_WORKFLOW.md
3. docs/RUNBOOK.md
4. docs/IO_REFERENCE.md
5. docs/CURRENT_LIMITATIONS.md

## 3. Daily operation

For local manual use:

1. Enter project directory
2. Activate virtual environment
3. Check git status
4. Run tests if needed
5. Run main workflow command
6. Review generated outputs
7. Make any trading decision manually outside the system

Core command:

    python main.py --report-template-daily-log-telegram-ready-output <primary_metals_config.yaml>

## 4. Input reference

Main input reference:

- examples/primary_metals_config.sample.yaml

Private runtime config should not be committed.

## 5. Output reference

Primary output references:

- Markdown report
- daily log
- Telegram-ready text
- final research trading plan

Related docs:

- docs/REPORT_EXAMPLES.md
- docs/TRADING_PLAN_OUTPUT_SCHEMA.md
- docs/RISK_TRIGGER_CHECKLIST.md

## 6. Telegram reference

Telegram is not live by default.

Related docs:

- docs/TELEGRAM_PRE_INTEGRATION_REVIEW.md
- docs/TELEGRAM_SECURITY_MODEL.md
- docs/TELEGRAM_FAILURE_HANDLING.md
- examples/telegram_config.sample.yaml

## 7. Scheduler reference

Scheduler is not live by default.

Related docs:

- docs/SCHEDULER_DEPLOYMENT_REVIEW.md
- docs/SCHEDULER_MACOS_LAUNCHD_PLAN.md
- docs/SCHEDULER_CLOUD_DEPLOYMENT_PLAN.md
- examples/scheduler_config.sample.yaml

## 8. Data source reference

Live data is not broadly enabled by default.

Related docs:

- docs/DATA_SOURCE_ENHANCEMENT_REVIEW.md
- docs/DATA_STATUS_MODEL.md
- docs/IBKR_DATA_AVAILABILITY_REVIEW.md
- docs/DATA_FALLBACK_RULES.md
- docs/READ_ONLY_LIVE_DATA_ADMISSION_REVIEW.md
- docs/IBKR_READ_ONLY_GATE_CHECKLIST.md
- examples/data_source_policy.sample.yaml
- examples/ibkr_read_only_admission.sample.yaml

## 9. UI reference

UI is not implemented in MVP v1.0.

Related docs:

- docs/PERSONAL_UI_EVALUATION.md
- docs/UI_ARCHITECTURE_OPTIONS.md
- docs/UI_SECURITY_MODEL.md
- docs/UI_MVP_SCREEN_SPEC.md
- examples/ui_config.sample.yaml

## 10. Safety reference

Safety docs:

- docs/NO_TRADE_ASSERTION_GATE.md
- docs/LIVE_DATA_RISK_REGISTER.md
- docs/CURRENT_LIMITATIONS.md

Required boundary:

    research-only / read-only / manual-only / no auto trade
