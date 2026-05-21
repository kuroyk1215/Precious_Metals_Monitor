# Cloud Scheduler Deployment Plan

## 1. Purpose

This document defines a future cloud deployment review plan for running Precious_Metals_Monitor on a 24h server.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

Phase 36 does not deploy any cloud infrastructure.

## 2. Why consider cloud deployment

Cloud deployment may be useful when local Mac scheduling is unreliable.

Potential advantages:

- 24h uptime
- stable network
- persistent logging
- easier remote monitoring
- better suited for scheduled reporting

## 3. Cloud deployment candidates

Potential options:

- small VPS
- cloud VM
- container-based service
- systemd timer
- cron on Linux

No option should be used before security and cost review.

## 4. Minimum cloud requirements

A future cloud deployment should require:

- private repository access method
- Python runtime
- virtual environment or container
- secure config storage
- log directory
- restricted firewall
- SSH key authentication
- no public secrets
- no auto trade permission

## 5. Secret handling

Cloud deployment must not expose:

- Telegram Bot token
- broker credentials
- account IDs
- private API keys

Allowed storage options:

- environment variables
- private config file outside Git
- cloud secret manager in a later phase

## 6. Scheduler choices

Potential Linux scheduler options:

- cron
- systemd timer

Recommended future review path:

1. start with manual command on server
2. validate report generation
3. validate logs
4. validate dry-run Telegram-ready output
5. enable scheduler only after safety checks

## 7. Logging requirements

Cloud scheduler should log:

- run timestamp
- time zone
- command
- config reference
- result
- output path
- error category
- no-trade assertion

Logs must not include secrets.

## 8. Failure handling

Cloud failure handling should:

- avoid infinite retry
- preserve last successful report
- write failure state
- optionally generate Telegram failure notification in later phase
- never trigger trading behavior

## 9. Cost and maintenance risks

Cloud deployment adds:

- monthly cost
- security maintenance
- OS updates
- SSH key management
- backup requirements
- log retention management
- network dependency

## 10. Safety boundary

Cloud deployment must not create any route to automatic trading.

Forbidden:

- broker order execution
- broker cancellation
- auto rebalance
- Telegram trade commands
- unattended trade execution
