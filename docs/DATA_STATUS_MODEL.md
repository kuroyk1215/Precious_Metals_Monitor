# Data Status Model

## 1. Purpose

This document defines the data status model for Precious_Metals_Monitor.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Status labels

### real_time

Data is considered current and directly sourced from a real-time provider.

Manual review is still required.

### delayed

Data is delayed but still sourced from a market data provider.

Output must clearly state that the value is delayed.

### delayed_frozen

Data is delayed and may not be actively updating.

This status requires additional manual confirmation.

### historical_close

Data comes from a previous official or provider-reported close.

It must not be treated as current intraday data.

### manual_input

Data was entered or provided manually.

Manual input should be auditable and timestamped.

### inferred

Data was estimated from related instruments, FX, theoretical pricing, or proxy relationships.

Inferred data must not be used as execution-grade data.

### unavailable

No valid usable data is available.

The output should avoid price-dependent conclusions where possible.

## 3. Data quality fields

Future data records should include:

- data_status
- source_status
- fallback_method
- has_valid_price
- quality_note
- timestamp
- timezone

## 4. Confidence levels

Recommended confidence classification:

- high: real_time or validated manual_input
- medium: delayed or historical_close
- low: delayed_frozen or inferred
- none: unavailable

## 5. Output requirements

Reports should expose data status directly.

Recommended display fields:

- instrument
- price
- currency
- data_status
- source
- timestamp
- fallback_method
- quality_note

## 6. Trading boundary

Even high-confidence data does not permit auto trade.

The system remains:

- research-only
- read-only
- manual-only
- no auto trade

## 7. Manual review escalation

Escalate manual review if:

- data_status is inferred
- data_status is unavailable
- timestamp is stale
- market session is closed
- cross-market FX conversion is required
- ETF and underlying reference diverge materially
