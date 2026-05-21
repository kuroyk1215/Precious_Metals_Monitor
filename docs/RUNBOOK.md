# Runbook

## 1. Purpose

This runbook explains how to run the Precious_Metals_Monitor MVP workflow locally.

The current MVP is:

- research-only
- read-only
- manual-only
- no auto trade

It does not place orders, cancel orders, rebalance positions, or execute trades.

## 2. Current baseline

Known MVP baseline:

- main commit after Phase 33: 525e13e
- Phase 33 PR: #112
- Test baseline: 428 passed
- Main workflow command:

    python main.py --report-template-daily-log-telegram-ready-output <primary_metals_config.yaml>

## 3. Enter project directory

    cd ~/Precious_Metals_Monitor

## 4. Activate virtual environment

    source .venv/bin/activate

If pytest cannot be found, use:

    python -m pytest -q

instead of:

    pytest -q

## 5. Check repository state

    git status --short

Expected local-only items may include:

    M config.yaml
    ?? .venv/

Do not commit:

- config.yaml
- .venv/

## 6. Run tests

    python -m pytest -q

Expected result:

    428 passed

Tests may generate temporary CSV and Markdown output files. These files should be cleaned before committing unless the task explicitly requires them.

## 7. Prepare input config

Use a private runtime config, for example:

    primary_metals_config.yaml

A public reference example is available at:

    examples/primary_metals_config.sample.yaml

The sample file is for documentation and structure reference only. Do not store secrets in it.

## 8. Run main MVP workflow

    python main.py --report-template-daily-log-telegram-ready-output <primary_metals_config.yaml>

## 9. Review outputs

Review generated outputs manually:

- Markdown report
- daily log
- Telegram-ready text
- final research trading plan

All outputs require manual review.

## 10. Manual execution boundary

The system does not execute trades.

Any real trade must be:

- reviewed manually
- confirmed manually
- entered manually in an external broker or trading terminal

## 11. Clean test or runtime artifacts

Common generated files may include:

- conversion_factor_calibration_log.csv
- historical_quality_gate_log.csv
- ibkr_historical_fetch_log.csv
- ibkr_smoke_log.csv
- precious_metals_signal_log.csv
- theoretical_price_snapshot.csv
- upstream_factor_snapshot.csv
- reports/latest_report.md
- reports/theoretical_price_report.md
- reports/upstream_factor_report.md

Before committing, check:

    git status --short

Only files related to the current phase should be staged.
