# Data Source Enhancement Review

## 1. Purpose

This document defines the Phase 37 review scope for future data source enhancement.

Current boundary:

- research-only
- read-only
- manual-only
- no auto trade

Phase 37 does not add real-time data code, does not change IBKR behavior, and does not enable trading actions.

## 2. Goal

The purpose of data source enhancement is to improve observability and data quality labeling.

Allowed goals:

- clarify data source priority
- document real_time / delayed / inferred / unavailable status
- define fallback rules
- define data quality labels
- define market-specific limitations
- improve manual review confidence

Forbidden goals:

- automatic trading
- automatic order placement
- automatic cancellation
- automatic rebalance
- bypassing manual review
- uncontrolled market data requests

## 3. Market scope

Primary market groups:

- JP market
- CN market
- US market
- global precious metals references
- FX references
- ETF references

Each market may have different data availability and delay conditions.

## 4. Data source priority

Future data source selection should follow explicit priority:

1. validated local manual input
2. configured read-only market data source
3. delayed market data
4. historical close fallback
5. inferred reference value
6. unavailable

The selected data source must be visible in output.

## 5. Required data status labels

All generated outputs should preserve a data status field where applicable.

Required labels:

- real_time
- delayed
- delayed_frozen
- historical_close
- manual_input
- inferred
- unavailable

## 6. Required metadata

Future output should include:

- symbol
- market
- source
- source_status
- data_status
- timestamp
- timezone
- price
- currency
- fallback_method
- has_valid_price
- quality_note

## 7. Manual review rule

If data_status is not real_time, output must not imply execution certainty.

Delayed, inferred, or unavailable data requires stricter manual review.

## 8. IBKR boundary

IBKR remains read-only.

Forbidden IBKR actions:

- placeOrder
- cancelOrder
- whatIfOrder as execution path
- bracketOrder
- exerciseOptions
- auto rebalance
- auto trade

Any future IBKR market data request must be explicitly gated and documented.

## 9. Phase 37 non-goals

Phase 37 does not:

- change code
- add a new data adapter
- enable live IBKR data
- enable historical IBKR fetch
- change scheduler behavior
- change Telegram behavior
- generate broker instructions

## 10. Exit criteria

Phase 37 is complete when the project has:

- data source enhancement review
- data status model
- IBKR data availability review
- fallback rule documentation
- public data source policy sample config
