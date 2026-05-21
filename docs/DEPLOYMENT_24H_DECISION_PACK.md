# 24h Deployment Decision Pack

## 1. Purpose

This document defines the Phase 50 decision pack for future 24h operation.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

Phase 50 does not deploy a server, install scheduler jobs, send Telegram messages, or connect broker execution.

## 2. Decision goal

The goal is to decide the next deployment path:

- continue manual daily operation
- local Mac dry-run automation
- local Mac scheduled automation
- cloud 24h deployment
- defer UI deployment

## 3. Current project state

The project has:

- MVP v1.0 release pack
- one-command acceptance pack
- generated artifact cleanup
- daily manual operation checklist
- scheduler dry-run plan
- Telegram dry-run plan
- local automation dry-run scripts
- no-trade assertion boundary

## 4. Deployment candidates

Candidate A: Manual operation

- lowest risk
- no automation dependency
- user manually runs workflow
- suitable for continued validation

Candidate B: Local Mac dry-run

- uses local machine
- no real scheduler installed
- verifies wrapper and logs
- suitable before real launchd

Candidate C: Local Mac launchd

- scheduled local run
- depends on Mac uptime
- affected by sleep, Wi-Fi, battery, restart
- suitable for personal non-critical automation

Candidate D: Cloud 24h deployment

- better uptime
- higher security burden
- monthly cost
- SSH and secret management required
- suitable after local dry-run is stable

## 5. Recommended decision

Recommended next path:

1. Continue manual operation
2. Add stronger local operation logs
3. Add scheduler dry-run wrapper output
4. Only then evaluate real launchd
5. Defer cloud until local reliability issues are clear

## 6. Not recommended immediately

Do not immediately enable:

- real Telegram send
- real launchd schedule
- cloud server
- IBKR live data expansion
- full UI app
- auto trade

## 7. Safety boundary

No deployment path may enable:

- placeOrder
- cancelOrder
- auto rebalance
- auto trade
- Telegram trade command
- scheduler trade execution
- UI trade execution
