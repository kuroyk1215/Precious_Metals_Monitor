# Scheduler Dry-Run Operation Plan

## 1. Purpose

This document defines a dry-run scheduler operation plan.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

Phase 45 in this combined pack does not deploy a real scheduler.

## 2. Dry-run goal

Scheduler dry-run should simulate scheduled operation without installing launchd, cron, systemd, or cloud automation.

Allowed:

- document planned run windows
- define wrapper behavior
- validate command readiness
- validate log path expectations
- validate no-trade assertion
- preserve manual execution

Not allowed:

- real scheduled deployment
- broker execution
- Telegram real send
- unattended trading
- auto rebalance

## 3. Future scheduler command concept

Future scheduler should call the existing research command only:

    python main.py --report-template-daily-log-telegram-ready-output <primary_metals_config.yaml>

The scheduler must not call any broker trading path.

## 4. Dry-run checks

A scheduler dry-run should verify:

- project directory exists
- virtual environment exists
- main.py exists
- config path exists
- cleanup script exists
- acceptance script passes
- output directories are available
- no-trade assertion is documented

## 5. Planned windows

Reference windows:

- JP morning: 08:30 JST
- JP lunch: 12:00 JST
- JP close: 16:00 JST
- US open context: ET to JST conversion required
- US mid-session: ET to JST conversion required
- US post-session: ET to JST conversion required

US schedule must account for daylight saving time.

## 6. Failure handling

If a scheduler dry-run fails:

- write failure status
- do not retry indefinitely
- do not trigger Telegram trade command
- do not trigger broker action
- preserve previous valid reports

## 7. Safety boundary

Scheduler dry-run must never trigger:

- placeOrder
- cancelOrder
- auto trade
- auto rebalance
- broker execution
- Telegram trading command
