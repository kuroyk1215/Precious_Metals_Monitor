# Manual Archive Acceptance Pack

## 1. Purpose

This document defines acceptance criteria for manual archive operation.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Acceptance criteria

Manual archive workflow is acceptable if:

- local run logging policy exists
- report archive policy exists
- failure log format exists
- archive acceptance check script passes
- MVP acceptance check passes
- daily manual check passes
- local automation dry-run remains valid
- tests pass
- cleanup script works
- config.yaml is not staged

## 3. Archive readiness checklist

Before future archive implementation:

- define archive root
- define naming convention
- define retention period
- define sensitive data exclusions
- define manual review marker
- define no-trade assertion marker

## 4. Rejection criteria

Reject archive workflow if:

- runtime logs are committed accidentally
- private reports are committed accidentally
- config.yaml is staged
- sample config enables auto trade
- sample config enables order action
- failure logs expose secrets
- archive process triggers Telegram real send
- archive process triggers broker behavior

## 5. Safety boundary

Manual archive workflow must never trigger:

- placeOrder
- cancelOrder
- rebalance
- auto trade
- Telegram trade command
- scheduler trade execution
