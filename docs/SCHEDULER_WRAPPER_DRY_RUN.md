# Scheduler Wrapper Dry-Run

## 1. Purpose

This document defines the local scheduler wrapper dry-run.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Dry-run behavior

The wrapper dry-run checks:

- project directory
- Python virtual environment path
- main.py existence
- cleanup script
- MVP acceptance script
- daily manual check script
- logs/scheduler directory

It does not install launchd, cron, or systemd timers.

## 3. Future real scheduler boundary

Any future scheduler must only trigger research workflow.

Forbidden:

- placeOrder
- cancelOrder
- rebalance
- auto trade
- Telegram trade command
- broker execution
