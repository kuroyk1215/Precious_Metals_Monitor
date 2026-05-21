# Scheduler Deployment Review

## 1. Purpose

This document defines the pre-deployment review requirements before using a real scheduler with Precious_Metals_Monitor.

Current boundary:

- research-only
- read-only
- manual-only
- no auto trade

Phase 36 does not deploy a real scheduler. It only documents deployment options, risks, logging, time zones, and failure handling requirements.

## 2. Scheduler goal

The scheduler should trigger the existing research workflow at predefined times.

Allowed scheduler actions:

- run research workflow
- generate Markdown report
- generate daily log
- generate Telegram-ready text
- generate final research trading plan
- write scheduler run status

Forbidden scheduler actions:

- place orders
- cancel orders
- rebalance positions
- trigger broker-side trading actions
- execute Telegram trading commands
- bypass manual review

## 3. Candidate deployment modes

Potential deployment modes:

- local manual run
- local macOS launchd
- local cron
- cloud server cron
- cloud systemd timer
- later UI-triggered manual run

Phase 36 only reviews these options. It does not enable any real deployment.

## 4. Recommended initial path

Recommended order:

1. Keep manual run as baseline
2. Add dry-run scheduler config
3. Test local scheduled report generation
4. Add failure logging
5. Add Telegram-ready output only
6. Later evaluate real Telegram send
7. Later evaluate 24h cloud deployment

## 5. Time zone policy

The project should explicitly define schedule time zones.

Default market references:

- JP market: JST
- CN market: CST
- US market: ET
- User operating context: JST

Scheduler documentation should avoid ambiguous terms such as today, tomorrow, morning, or close without explicit time zone.

## 6. Suggested schedule windows

Potential future schedule windows:

- JP pre-market review: 08:30 JST
- JP lunch review: 12:00 JST
- JP close review: 16:00 JST
- US pre-market / open context: 21:30 JST depending on DST
- US mid-session review: 01:00 JST depending on DST
- US post-session review: 05:15 JST depending on DST

US schedule must explicitly handle ET to JST conversion and daylight saving time.

## 7. Required safety gates

Before real scheduling is enabled, the project should confirm:

- command is research-only
- IBKR mode remains read-only
- no order action path exists
- no cancel action path exists
- no rebalance action path exists
- Telegram send is disabled or explicitly gated
- local private config is not committed
- logs do not contain secrets

## 8. Logging requirements

A future scheduler run should log:

- timestamp
- time zone
- command executed
- config file reference
- run result
- report output path
- Telegram-ready output path
- error category if failed
- no-trade assertion status

Logs must not include:

- Bot token
- broker credentials
- account numbers
- private API keys

## 9. Failure handling

If a scheduled run fails:

- record failure
- preserve previous valid reports
- avoid infinite retry
- avoid automatic trading fallback
- do not send broker instructions
- do not delete previous outputs automatically

## 10. Phase 36 non-goals

Phase 36 does not:

- install launchd job
- install cron job
- deploy cloud server
- enable real Telegram sending
- change main.py
- change src/
- add trading logic
- add broker execution
