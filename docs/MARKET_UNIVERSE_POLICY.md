# Market Universe Policy

## Core Policy

This project does not perform global market scanning. It only processes symbols that the operator explicitly adds to a watchlist or universe file.

The operating rule is user watchlist only. No default workflow should infer a market-wide universe, scrape all listings, or expand the symbol set without an explicit operator-maintained input.

## IBKR Validation Universe

IBKR validation should use GLD and SLV first. These US ETFs are the preferred first test universe because the US ETF data path is better suited for validating the IBKR market data connection, delayed/frozen fallback behavior, and dashboard-ready output files.

First Execution C validation uses `ibkr_verified_contract_map_gld_slv.csv`. The older runtime `ibkr_verified_contract_map.csv` may contain JP/CN legacy rows and should not be used for first validation readiness.

1540.T and 1542.T remain optional JP ETF watchlist entries. They are supported as optional observations, but they are not the only core of the system and must not lock the project into a Japan-only precious metals ETF monitor.

518880.SH is excluded from IBKR contract universe files. It must not be placed into the IBKR validation contract universe.

## China Market Handling

A share and China ETF coverage, including 518880.SH, should use one of these future paths:

- manual market data adapter
- CSV import
- non-IBKR data source
- future broker API adapter

These paths must remain separate from the IBKR contract universe unless a later phase explicitly adds a reviewed, non-trading adapter.

## Unified Schema Direction

US ETFs, JP ETFs, and China ETFs should eventually enter through a unified universe schema. The schema should preserve source, exchange, currency, provider, and adapter routing so dashboard and research outputs can handle all markets consistently.

## Safety Boundary

All research outputs remain research-only and manual-only. The system must keep action_allowed=false, must not create broker execution, and must not authorize trades.
