# Phase 161-168 IBKR Contract Qualification One-shot Preflight

## 1. Purpose

This document defines the one-shot preflight workflow for IBKR contract qualification.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Goal

The workflow prepares a gated local one-shot execution path for `reqContractDetails`.

Default behavior is `NO_GO`.

## 3. Default behavior

Without explicit execution and without local gate changes, the script must:

- not connect to IBKR
- not call reqContractDetails
- not call reqMktData
- not call reqHistoricalData
- not trigger broker execution

## 4. Execution requirements

A future one-shot execution requires all of the following:

- `--execute`
- read_only_required=true
- real_connection_allowed=true
- contract_qualification_allowed=true
- market_data_request_allowed=false
- historical_data_request_allowed=false
- trading_actions_allowed=false

## 5. Allowed execution scope

When all gates pass, the script may only:

- connect to TWS / IB Gateway in read-only mode
- call reqContractDetails for configured targets
- immediately disconnect
- write local CSV and Markdown reports

## 6. Forbidden scope

This phase must not call:

- reqMktData
- reqHistoricalData
- placeOrder
- cancelOrder
- bracketOrder
- whatIfOrder
- exerciseOptions
- account reads
- position reads
- broker execution

## 7. Final boundary

This workflow is contract qualification only.

It does not authorize market data requests, historical data requests, account reads, order actions, or automatic trading.
