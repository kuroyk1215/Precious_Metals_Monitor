# One-Command Operation Acceptance Pack

## 1. Purpose

This document defines the MVP v1.0 one-command operation acceptance pack.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Core command

The documented core workflow command is:

    python main.py --report-template-daily-log-telegram-ready-output <primary_metals_config.yaml>

This command should remain the main manual operation entry point for MVP v1.0.

## 3. Pre-run checklist

Before running the command:

1. Enter project directory:

       cd ~/Precious_Metals_Monitor

2. Activate virtual environment:

       source .venv/bin/activate

3. Confirm branch and local state:

       git branch --show-current
       git status --short

4. Confirm local config is not staged:

       git status --short

5. Confirm test baseline if needed:

       python -m pytest -q

6. Clean generated artifacts if needed:

       ./scripts/cleanup_generated_artifacts.sh

## 4. Input requirement

The command requires a private runtime config:

    <primary_metals_config.yaml>

Public reference sample:

    examples/primary_metals_config.sample.yaml

Do not commit private runtime config if it contains local settings or secrets.

## 5. Expected output categories

The workflow should generate or update research outputs such as:

- Markdown report
- daily log
- Telegram-ready text
- final research trading plan

Exact paths may vary by config and workflow stage.

## 6. Acceptance criteria

The workflow is acceptable if:

- command completes without unexpected error
- output files are generated as expected
- data_status is visible where applicable
- final research trading plan is reviewable
- no order action is created
- no cancel action is created
- no rebalance action is created
- no auto trade path is triggered

## 7. Post-run cleanup

After local runs or tests:

    ./scripts/cleanup_generated_artifacts.sh

Expected local state may remain:

    M config.yaml

## 8. Safety boundary

All outputs remain:

- research-only
- read-only
- manual-only
- no auto trade

The system does not execute trades.
