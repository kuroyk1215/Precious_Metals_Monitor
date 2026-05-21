# Operation Handoff Pack

## 1. Purpose

This document defines the manual operation handoff pack for Precious_Metals_Monitor MVP v1.0.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Handoff goal

The handoff pack should allow the user to resume daily manual operation from a clean baseline.

## 3. Current operating baseline

Required baseline:

- main branch up to date
- tests passing
- acceptance checks passing
- local automation dry-run passing
- deployment decision check passing
- local archive check passing
- archive dry-run passing
- config.yaml remains local
- runtime archives ignored

## 4. Daily operation sequence

Recommended daily sequence:

1. Enter project directory
2. Activate virtual environment
3. Run daily manual check
4. Run one-command workflow manually
5. Review Markdown report
6. Review final research trading plan
7. Review data_status and risk triggers
8. Archive useful outputs manually if needed
9. Run cleanup script
10. Confirm git status

## 5. Required scripts

Required scripts:

- scripts/check_mvp_v1_acceptance.sh
- scripts/daily_manual_check.sh
- scripts/local_automation_dryrun.sh
- scripts/deployment_decision_check.sh
- scripts/local_run_archive_check.sh
- scripts/report_archive_dryrun.sh
- scripts/retention_validation_check.sh
- scripts/operation_handoff_check.sh

## 6. Manual trade boundary

The handoff pack does not authorize automated execution.

Any trade must be:

- manually reviewed
- manually confirmed
- manually entered in an external broker or trading terminal

## 7. Safety boundary

The operation handoff pack must not trigger:

- placeOrder
- cancelOrder
- rebalance
- auto trade
- Telegram trade command
- scheduler trade execution
