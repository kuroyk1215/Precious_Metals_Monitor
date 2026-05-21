# Mac vs Cloud Decision Matrix

## 1. Purpose

This document compares local Mac operation and cloud operation.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Local Mac advantages

- no cloud cost
- simpler security model
- local file access
- easy manual inspection
- suitable for personal use

## 3. Local Mac risks

- sleep mode
- Wi-Fi outage
- battery issue
- system restart
- app permission issue
- not reliable for 24h unattended operation

## 4. Cloud advantages

- better uptime
- remote execution
- stable server process
- easier 24h monitoring
- can run while local Mac is off

## 5. Cloud risks

- monthly cost
- SSH key management
- server hardening
- secret management
- log retention
- OS updates
- accidental public exposure

## 6. Decision matrix

| Factor | Local Mac | Cloud |
|---|---|---|
| Cost | Low | Medium |
| Security complexity | Low | Higher |
| Uptime | Medium | High |
| Setup complexity | Low | Medium |
| Secret exposure risk | Lower | Higher |
| 24h reliability | Medium | High |
| Best first step | Yes | No |

## 7. Recommendation

Use local Mac dry-run before cloud.

Cloud should be considered only after:

- local dry-run is stable
- logs are clear
- Telegram dry-run is stable
- no-trade assertions are verified
- secret handling is finalized
