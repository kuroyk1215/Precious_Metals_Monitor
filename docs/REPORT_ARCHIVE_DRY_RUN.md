# Report Archive Dry-Run

## 1. Purpose

This document defines the local report archive dry-run workflow.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Goal

The archive dry-run validates archive readiness without moving real reports or committing runtime archives.

Allowed:

- validate archive directory policy
- validate archive manifest sample
- validate naming convention
- validate no-trade assertion
- validate no secret policy

Not allowed:

- broker execution
- Telegram real send
- real scheduler deployment
- automatic trading
- committing private runtime archives

## 3. Recommended archive categories

Recommended archive categories:

- archive/reports/
- archive/daily_logs/
- archive/telegram_ready/
- archive/final_plans/
- logs/local/
- logs/failures/
- logs/archive/

These are runtime output locations and should not be committed by default.

## 4. Naming convention

Recommended naming format:

    YYYYMMDD_HHMMSS_<market>_<workflow>_<output_type>.<ext>

Examples:

    20260521_083000_JP_daily_report.md
    20260521_120000_JP_final_plan.md
    20260521_213000_US_telegram_ready.txt

## 5. Dry-run behavior

The dry-run script should check:

- required docs exist
- required scripts exist
- sample archive manifest exists
- archive runtime paths are ignored
- no sample config enables trading
- no broker execution is triggered

## 6. Safety boundary

Archive dry-run must never trigger:

- placeOrder
- cancelOrder
- rebalance
- auto trade
- Telegram trade command
- scheduler trade execution
