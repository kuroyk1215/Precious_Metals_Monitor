# No-Trade Assertion Gate

## 1. Purpose

This document defines the no-trade assertion gate for all future integrations.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Required assertion

Every future integration path should be able to assert:

- no order is created
- no order is submitted
- no order is cancelled
- no position is rebalanced
- no broker execution path is called
- no Telegram command can execute a trade
- no scheduler job can execute a trade

## 3. Forbidden behaviors

The following behaviors are forbidden:

- automatic buy
- automatic sell
- automatic cancellation
- automatic rebalance
- unattended execution
- Telegram-triggered execution
- scheduler-triggered execution
- broker-side order routing

## 4. Required output language

Reports should use research wording.

Allowed:

- reference only
- manual review required
- observation zone
- risk trigger
- invalidation condition
- data status warning

Forbidden:

- execute now
- buy now
- sell now
- place order
- cancel order
- guaranteed entry
- guaranteed exit

## 5. Integration coverage

The no-trade assertion should apply to:

- IBKR
- Telegram
- scheduler
- report generation
- final research trading plan
- future UI
- future API layer

## 6. Failure behavior

If no-trade assertion cannot be verified:

- block the integration
- mark admission failed
- do not run live workflow
- require manual review
- do not fallback to trading behavior

## 7. Review checklist

Before merging future live-data-related changes, verify:

- no trading function added
- no order function added
- no cancel function added
- no rebalance function added
- no auto trade config enabled
- no sample config enables trading
- no test fixture contains real secrets
