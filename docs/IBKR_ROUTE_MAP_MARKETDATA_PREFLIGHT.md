# Phase 177-208 IBKR Route Map and Market Data Preflight

## 1. Purpose

This mega batch prepares the route discovery, contract map lock-in, and market data snapshot preflight layers.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Scope

Included:

- JP route discovery one-shot script for 1540.T and 1542.T
- contract map lock-in builder
- market data snapshot preflight gate

Excluded:

- 518880.SH from IBKR route qualification
- market data execution
- historical data execution
- account reads
- position reads
- broker execution
- automatic trading

## 3. Default behavior

Default behavior is NO_GO.

Without explicit local gates and `--execute`, scripts must not:

- connect to IBKR
- call reqContractDetails
- call reqMktData
- call reqHistoricalData
- place or cancel orders

## 4. Execution sequence

1. Run JP route discovery one-shot after local gates are enabled.
2. Build contract map from successful route results.
3. Run market data snapshot preflight.
4. Only after contract map is valid should a later market data one-shot phase be created.

## 5. Final boundary

This batch does not authorize live market data, historical data, account access, order actions, or automatic trading.
