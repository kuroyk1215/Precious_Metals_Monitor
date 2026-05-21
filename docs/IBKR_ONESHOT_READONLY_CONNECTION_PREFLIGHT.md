# Phase 145-152 IBKR One-shot Read-only Connection Preflight

## 1. Purpose

This document defines the preflight workflow for a future one-shot IBKR read-only connection test.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Goal

The one-shot preflight script should make the connection decision explicit.

Default behavior is NO_GO when:

- real_connection_allowed=false
- operator execute flag is absent
- required read-only safety flags are not satisfied

## 3. Allowed scope

Only in a later explicit local run with `--execute` and `real_connection_allowed=true`, the script may:

- open one IBKR/TWS connection
- immediately disconnect
- write a local connection status report

## 4. Forbidden scope

This phase must not call:

- reqMktData
- reqHistoricalData
- reqContractDetails
- placeOrder
- cancelOrder
- bracketOrder
- whatIfOrder
- exerciseOptions
- rebalance

## 5. Required safety gates

The script must require:

- read_only_required=true
- trading_actions_allowed=false
- contract_qualification_allowed=false
- market_data_request_allowed=false
- historical_data_request_allowed=false

## 6. Runtime outputs

Generated local artifacts:

- ibkr_oneshot_readonly_connection_preflight.csv
- reports/ibkr_oneshot_readonly_connection_preflight_report.md

## 7. Final boundary

This is a preflight layer.

It does not authorize market data requests, historical data requests, contract qualification, account reads, broker execution, or automatic trading.
