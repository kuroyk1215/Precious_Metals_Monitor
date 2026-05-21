# Phase 209-240 IBKR Market Data and Daily Integration Preflight

## 1. Purpose

This mega batch prepares the IBKR market data snapshot and daily research integration preflight layers.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Verified contract map

The verified IBKR contract map is:

| display_symbol | conId | exchange | primaryExchange | currency | localSymbol | tradingClass |
|---|---:|---|---|---|---|---|
| 1540.T | 117595037 | SMART | TSEJ | JPY | 1540.T | 1540 |
| 1542.T | 121557296 | SMART | TSEJ | JPY | 1542.T | 1542 |
| 518880.SH | | | | | | IBKR_UNSUPPORTED |

## 3. Default behavior

Default behavior is NO_GO.

Without explicit local gates and `--execute`, scripts must not:

- connect to IBKR
- call reqMktData
- call reqHistoricalData
- call reqContractDetails
- read account data
- read positions
- place or cancel orders

## 4. Execution requirements

Market data one-shot requires all of the following:

- `--execute`
- read_only_required=true
- real_connection_allowed=true
- market_data_request_allowed=true
- contract_qualification_allowed=false
- historical_data_request_allowed=false
- trading_actions_allowed=false

## 5. Final boundary

This batch does not authorize historical data requests, account reads, position reads, order actions, or automatic trading.
