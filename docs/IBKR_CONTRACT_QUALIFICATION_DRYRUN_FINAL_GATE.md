# Phase 153-160 IBKR Contract Qualification Dry-run Final Gate

## 1. Purpose

This document defines the dry-run final gate before any IBKR contract qualification execution.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Goal

The dry-run gate prepares contract qualification readiness for core instruments:

- 1540.T
- 1542.T
- 518880.SH

Default decision is `NO_GO`.

## 3. Allowed scope

This dry-run phase may:

- generate a local qualification plan
- validate safety flags
- produce CSV and Markdown review artifacts

## 4. Forbidden scope

This phase must not call:

- reqContractDetails
- reqMktData
- reqHistoricalData
- placeOrder
- cancelOrder
- bracketOrder
- whatIfOrder
- exerciseOptions

## 5. Required safety gates

The dry-run gate requires:

- read_only_required=true
- real_connection_allowed=false
- contract_qualification_allowed=false
- market_data_request_allowed=false
- historical_data_request_allowed=false
- trading_actions_allowed=false

## 6. Runtime outputs

Generated local artifacts:

- ibkr_contract_qualification_final_gate.csv
- reports/ibkr_contract_qualification_final_gate_report.md

## 7. Final boundary

This phase does not connect to IBKR and does not qualify contracts.

A later explicit one-shot execution phase is required before real `reqContractDetails` can be tested.
