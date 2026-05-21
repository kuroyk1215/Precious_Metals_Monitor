# Manual Trade Review Boundary

## 1. Purpose

This document defines the boundary between research output and manual trading action.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. System role

Precious_Metals_Monitor may generate:

- research summary
- data status notes
- final research trading plan
- risk trigger checklist
- invalidation conditions
- Telegram-ready text
- daily logs

It does not generate broker-executable instructions.

## 3. User role

The user must independently confirm:

- market price
- market session
- order size
- cash availability
- liquidity
- spread
- risk limit
- broker terminal state
- tax and account constraints if applicable

## 4. Forbidden interpretation

Research output must not be interpreted as:

- order ticket
- broker instruction
- automatic buy signal
- automatic sell signal
- rebalance instruction
- guaranteed entry
- guaranteed exit

## 5. Required manual checks

Before any manual trade, check:

- latest market data in broker terminal
- latest spread and volume
- account buying power or settled cash
- position size
- invalidation condition
- stop or exit logic
- maximum daily risk
- whether the plan is stale

## 6. Data-driven escalation

Manual review must be stricter if:

- data_status is delayed
- data_status is inferred
- data_status is unavailable
- timestamp is stale
- source_status is partial
- fallback_method is used

## 7. No-trade assertion

The system must not:

- create orders
- submit orders
- cancel orders
- modify orders
- rebalance positions
- trade from Telegram
- trade from scheduler
- trade from UI

## 8. Final boundary

The project is a research and monitoring support tool.

Execution, if any, happens outside the project and only by manual user action.
