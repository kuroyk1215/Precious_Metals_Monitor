# Read-Only Live Data Admission Review

## 1. Purpose

This document defines the Phase 39 admission review before enabling any broader read-only live data workflow.

Current boundary:

- research-only
- read-only
- manual-only
- no auto trade

Phase 39 does not enable real-time data, does not change IBKR behavior, and does not add any trading path.

## 2. Goal

The goal is to define the gate requirements before any future read-only live data source is allowed.

Allowed future scope:

- read-only data observation
- data status labeling
- contract qualification review
- market data availability review
- historical data availability review
- output quality checks

Forbidden scope:

- order placement
- order cancellation
- automatic rebalance
- automatic trading
- Telegram trade commands
- broker-side execution workflow

## 3. Admission principle

No live data integration should be enabled unless the project can prove:

- all trading actions are unavailable
- all order actions are blocked
- all cancel actions are blocked
- all rebalance actions are blocked
- read-only mode is explicitly required
- data quality labels are visible
- local secrets are not committed
- tests pass

## 4. Required pre-admission checks

Before enabling any future read-only live data path, confirm:

- no placeOrder path
- no cancelOrder path
- no bracketOrder path
- no exerciseOptions path
- no auto trade path
- no auto rebalance path
- no Telegram trading command path
- no scheduler-triggered trade path
- no config secrets committed
- no account credentials logged

## 5. Data status requirements

Any read-only data result must show:

- symbol
- market
- source
- source_status
- data_status
- timestamp
- timezone
- fallback_method
- has_valid_price
- quality_note

## 6. IBKR admission requirements

Future IBKR read-only expansion must require:

- read_only_required: true
- trading_actions_allowed: false
- order_action_allowed: false
- cancel_action_allowed: false
- rebalance_action_allowed: false
- historical_data_request_allowed explicitly gated
- market_data_request_allowed explicitly gated
- logs must not expose credentials

## 7. Scheduler interaction

Scheduler must not be allowed to trigger live trading.

Allowed:

- scheduled research run
- scheduled report generation
- scheduled data observation
- scheduled Telegram-ready text generation

Forbidden:

- scheduled order placement
- scheduled cancellation
- scheduled rebalance
- scheduled execution

## 8. Telegram interaction

Telegram must remain notification-only.

Forbidden Telegram behavior:

- /buy
- /sell
- /cancel
- /rebalance
- /execute
- any broker-side action

## 9. Exit criteria

Phase 39 is complete when the project has:

- read-only live data admission review
- IBKR read-only gate checklist
- no-trade assertion gate
- live data risk register
- public sample admission config

## 10. Non-goals

Phase 39 does not:

- change main.py
- change src/
- enable real IBKR live data
- enable real historical fetch
- enable scheduler deployment
- enable real Telegram sending
- add automatic trading
