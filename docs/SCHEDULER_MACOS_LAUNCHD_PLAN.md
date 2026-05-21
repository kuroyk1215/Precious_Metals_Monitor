# macOS Scheduler Plan

## 1. Purpose

This document defines a future macOS scheduling plan for Precious_Metals_Monitor.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Candidate tools

macOS scheduling options:

- launchd
- cron
- manual Terminal run

Recommended future default:

- launchd for persistent local Mac scheduling
- manual Terminal run for baseline validation

## 3. Why launchd

launchd is the native macOS scheduler.

Potential advantages:

- starts jobs at defined times
- can write stdout and stderr logs
- integrates with user session
- does not require third-party scheduler
- suitable for local personal automation

## 4. Why not jump directly to launchd

Before launchd deployment, the project should confirm:

- one-command workflow is stable
- config path is explicit
- Python venv path is explicit
- output directory is explicit
- logs are captured
- failure status is visible
- no secrets are printed

## 5. Required command structure

A future launchd job should call a wrapper script rather than embedding a long command directly.

Example future wrapper concept:

    scripts/run_daily_research.sh

The wrapper should:

- cd into project directory
- activate .venv
- run the main workflow
- capture stdout
- capture stderr
- write logs
- exit non-zero on failure

## 6. Local path requirements

Future scheduler config must use absolute paths.

Examples:

    /Users/a456/Precious_Metals_Monitor
    /Users/a456/Precious_Metals_Monitor/.venv/bin/python
    /Users/a456/Precious_Metals_Monitor/config.yaml

Do not rely on interactive shell aliases.

## 7. Suggested macOS run windows

Potential future launchd jobs:

- JP morning review: 08:30 JST
- JP lunch review: 12:00 JST
- JP close review: 16:00 JST
- US pre-session review: mapped from ET to JST
- US post-session review: mapped from ET to JST

US market schedules must account for daylight saving time.

## 8. Logging plan

Recommended local log directory:

    logs/scheduler/

Recommended log categories:

- stdout
- stderr
- run summary
- failure summary

Logs should not include:

- Telegram Bot token
- broker credentials
- account ID
- private API keys

## 9. Sleep and power limitations

Local Mac scheduling depends on machine availability.

Risks:

- Mac sleeping
- network unavailable
- app permissions
- system restart
- battery mode
- Wi-Fi outage

For reliable 24h monitoring, cloud deployment may be more appropriate.

## 10. Safety boundary

macOS scheduler must only trigger research workflow.

It must not trigger:

- placeOrder
- cancelOrder
- rebalance
- auto trade
- Telegram trading command
