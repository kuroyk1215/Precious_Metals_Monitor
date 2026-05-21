# MVP v1.0 Command Reference

## 1. Purpose

This document defines the command reference for Precious_Metals_Monitor MVP v1.0.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Main workflow command

Primary command:

    python main.py --report-template-daily-log-telegram-ready-output <primary_metals_config.yaml>

Purpose:

- run the MVP research workflow
- generate Markdown report
- generate daily log
- generate Telegram-ready text
- generate final research trading plan

## 3. Test command

Recommended test command:

    python -m pytest -q

Expected baseline:

    428 passed

## 4. Cleanup command

Generated runtime artifacts can be cleaned with:

    ./scripts/cleanup_generated_artifacts.sh

Purpose:

- restore tracked generated report if modified
- remove known generated CSV files
- remove known generated Markdown report files
- keep config.yaml untouched
- keep source code untouched

## 5. Acceptance script

Lightweight local acceptance check:

    ./scripts/check_mvp_v1_acceptance.sh

Purpose:

- confirm required MVP v1.0 docs exist
- confirm key sample configs exist
- confirm cleanup script exists and is executable
- confirm core command is documented
- confirm safety docs exist

## 6. Local state commands

Check branch:

    git branch --show-current

Check working tree:

    git status --short

Expected local-only item may include:

    M config.yaml

## 7. Forbidden commands

Do not use:

    git add .

Do not intentionally stage:

- config.yaml
- .venv/
- generated CSV logs
- generated report artifacts
- secrets
- broker credentials
- Telegram Bot token

## 8. Safety boundary

Commands in this reference do not authorize:

- placeOrder
- cancelOrder
- auto trade
- auto rebalance
- Telegram trading command
- scheduler-triggered trading
