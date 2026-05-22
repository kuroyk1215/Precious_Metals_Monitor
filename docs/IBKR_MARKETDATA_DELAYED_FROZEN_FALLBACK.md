# IBKR Market Data Delayed/Frozen Fallback (Phase 241-256)

## Execution B Facts Recap
- IBKR/TWS connection succeeded.
- 1540.T / 1542.T conId lookup succeeded.
- `reqMktData` was triggered.
- TSEJ live subscription missing.
- IBKR Error 354 observed with delayed market data availability hint.
- Snapshot could still return empty payload.

## Error 354 Meaning
Error 354 does **not** mean contract mapping failed. It means live market data subscription is unavailable for the instrument/venue.

## Market Data Type Differences
- `live` (1): real-time feed with subscription.
- `frozen` (2): latest frozen value near market close/open boundaries.
- `delayed` (3): delayed reference feed.
- `delayed_frozen` (4): delayed + frozen reference mode.

## snapshot_empty Interpretation
`snapshot_empty` means one-shot fields were all empty in this pull. It may happen even with delayed permission.

## Why Delayed Is Not Real-Time
Delayed feeds are reference-only and cannot be used as immediate execution signal quality.

## Why action_allowed Must Stay false
The fallback path is strictly research-only/read-only/manual-only, so `action_allowed=false` and `manual_review_required=true` are mandatory.

## Daily Integration Preflight Next Step
Integrate fallback result fields into daily preflight summary, and explicitly surface terminal status (`usable_price` vs `empty_price`) before manual analyst review.
