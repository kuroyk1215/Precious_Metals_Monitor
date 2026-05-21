# IBKR Data Availability Review

## 1. Purpose

This document defines the future review requirements for IBKR data availability.

Current boundary:

- research-only
- read-only
- manual-only
- no auto trade

Phase 37 does not enable new IBKR requests.

## 2. IBKR role

IBKR may be used in future phases as a read-only data source.

Permitted future use:

- market data observation
- historical data observation
- contract qualification
- data availability checking
- data status labeling

Forbidden use:

- order placement
- order cancellation
- auto rebalance
- auto trade
- broker-side execution workflow

## 3. Market data limitations

IBKR data availability may depend on:

- market subscription
- exchange permission
- delayed data availability
- trading session
- product type
- account settings
- TWS / Gateway status
- network connection

The system must not assume all symbols have real-time data.

## 4. JP / CN / US differences

Expected differences:

- US market data may be available depending on subscription
- JP market data may be delayed without paid subscription
- CN instruments may require alternative data sources
- ETF data and underlying metal reference data may differ by source
- FX data may require separate source validation

## 5. Required IBKR fields

Future IBKR-derived records should expose:

- symbol
- contract identifier if available
- exchange
- primary exchange
- currency
- market data type
- data_status
- source_status
- timestamp
- fallback_method
- has_valid_price

## 6. Fallback behavior

If live data is not available, future behavior may fall back to:

- delayed data
- delayed frozen data
- historical close
- manual input
- unavailable

Fallback must be visible in output.

## 7. Safety gates

Before enabling any broader IBKR read-only data use, confirm:

- read_only_required is true
- trading actions are disabled
- order action code paths remain absent
- cancel action code paths remain absent
- historical fetch is explicitly gated
- market data request is explicitly gated
- logs do not expose account credentials

## 8. Non-goals

This review does not authorize:

- live trading
- auto execution
- order routing
- margin use
- position management
- portfolio rebalance
