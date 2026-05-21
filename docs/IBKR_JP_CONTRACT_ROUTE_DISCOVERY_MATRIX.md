# Phase 169-176 IBKR JP Contract Route Discovery Matrix Dry-run

## 1. Purpose

This document defines the IBKR JP contract route discovery matrix dry-run.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Scope correction

The IBKR qualification target set is corrected as follows:

| display_symbol | IBKR route status | handling |
|---|---|---|
| 1540.T | route discovery required | included |
| 1542.T | route discovery required | included |
| 518880.SH | IBKR_UNSUPPORTED | excluded from IBKR route qualification |

## 3. Goal

Generate a local candidate route matrix for JP ETF contract qualification.

Default decision is `NO_GO`.

## 4. Candidate route families

The matrix should include candidates such as:

- exchange=SMART / primaryExchange=TSEJ / currency=JPY / secType=STK
- exchange=TSEJ / primaryExchange=TSEJ / currency=JPY / secType=STK
- exchange=TSE / primaryExchange=TSEJ / currency=JPY / secType=STK
- localSymbol-based candidates for future manual verification

## 5. Forbidden scope

This phase must not call:

- IBKR connection
- reqContractDetails
- reqMktData
- reqHistoricalData
- placeOrder
- cancelOrder
- bracketOrder
- whatIfOrder
- exerciseOptions
- account reads
- position reads

## 6. Runtime outputs

Generated local artifacts:

- ibkr_jp_contract_route_discovery_matrix.csv
- reports/ibkr_jp_contract_route_discovery_matrix_report.md

## 7. Final boundary

This is a planning artifact only.

Real route discovery execution requires a separate one-shot execution gate.
