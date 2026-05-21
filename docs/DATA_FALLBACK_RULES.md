# Data Fallback Rules

## 1. Purpose

This document defines fallback principles for market data quality handling.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Fallback principle

Fallback exists to keep reports usable when ideal data is unavailable.

Fallback must not create false certainty.

Every fallback must be labeled.

## 3. Fallback order

Recommended future fallback order:

1. real_time
2. delayed
3. delayed_frozen
4. historical_close
5. manual_input
6. inferred
7. unavailable

The chosen fallback method must be included in output.

## 4. No silent fallback

The system must not silently replace missing real-time data with inferred or stale data.

Reports should explicitly show:

- original requested source
- actual used source
- fallback_method
- data_status
- quality_note

## 5. Stale data handling

Data may be stale if:

- timestamp is missing
- timestamp is outside expected session
- timestamp is older than configured threshold
- market is closed
- source returned frozen data

Stale data should reduce confidence.

## 6. Inferred data handling

Inferred data may be based on:

- related ETF
- underlying precious metal
- FX conversion
- theoretical pricing
- previous close
- manual adjustment

Inferred data should never be presented as execution-grade.

## 7. Unavailable data handling

If data is unavailable:

- avoid precise price-dependent conclusions
- preserve report generation if possible
- mark affected instruments
- require manual review
- avoid trade-like instruction wording

## 8. Report wording

When fallback is used, reports should use cautious wording.

Allowed:

- data unavailable
- delayed data used
- inferred estimate
- manual review required
- reference only

Forbidden:

- execute now
- confirmed entry
- automatic buy
- automatic sell
- guaranteed price

## 9. Safety boundary

Fallback logic must not trigger:

- order placement
- order cancellation
- rebalance
- auto trade
- Telegram trade command
