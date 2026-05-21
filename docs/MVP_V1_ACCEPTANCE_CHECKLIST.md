# MVP v1.0 Acceptance Checklist

## 1. Purpose

This checklist defines whether Precious_Metals_Monitor can be considered MVP v1.0 documentation-complete.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Repository baseline

Required checks:

- main branch is up to date
- Phase 33–40 PRs are merged
- tests pass
- local config.yaml is not committed
- .venv/ is not committed
- generated reports and CSV files are not accidentally committed

Expected local status may include:

    M config.yaml
    ?? .venv/

## 3. Test acceptance

Required test command:

    python -m pytest -q

Expected baseline:

    428 passed

## 4. Main workflow acceptance

Core command must remain documented:

    python main.py --report-template-daily-log-telegram-ready-output <primary_metals_config.yaml>

Expected output categories:

- Markdown report
- daily log
- Telegram-ready text
- final research trading plan

## 5. Documentation acceptance

The following documentation groups must exist:

- MVP summary and workflow docs
- input / output reference
- limitations
- runbook
- troubleshooting
- report examples
- Telegram pre-integration review
- scheduler deployment review
- data source enhancement review
- strategy explanation layer review
- read-only live data admission review
- personal UI evaluation

## 6. Sample config acceptance

The following sample configs should exist:

- examples/primary_metals_config.sample.yaml
- examples/telegram_config.sample.yaml
- examples/scheduler_config.sample.yaml
- examples/data_source_policy.sample.yaml
- examples/ibkr_read_only_admission.sample.yaml
- examples/ui_config.sample.yaml

All sample configs must remain public and non-sensitive.

They must not contain:

- real account IDs
- real Telegram Bot tokens
- real chat IDs
- broker credentials
- private endpoints
- API keys

## 7. Safety acceptance

The project must preserve:

- no placeOrder
- no cancelOrder
- no auto trade
- no auto rebalance
- no Telegram trading command
- no scheduler trading path
- no UI trading path

## 8. Manual review acceptance

All outputs must be interpreted as manual review material.

They are not:

- order tickets
- broker instructions
- automatic trading signals
- guaranteed entry or exit instructions

## 9. MVP v1.0 acceptance result

MVP v1.0 can be considered accepted only if:

- tests pass
- documentation is complete
- sample configs contain no secrets
- no code path enables trading
- no generated runtime artifacts are committed
- all safety boundaries remain explicit
