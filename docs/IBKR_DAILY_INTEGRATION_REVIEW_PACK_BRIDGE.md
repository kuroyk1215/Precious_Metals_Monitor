# IBKR Daily Integration Review Pack Bridge

## Phase 257-272 Input

Phase 257-272 produces `ibkr_daily_integration_preflight.csv` from an existing market data snapshot. Phase 273-288 adds a research-only bridge that consumes that CSV:

```bash
bash scripts/ibkr_daily_integration_review_pack.sh --daily-integration=ibkr_daily_integration_preflight.csv
```

The bridge writes:

- `ibkr_daily_integration_review_pack.csv`
- `reports/ibkr_daily_integration_review_pack_report.md`

It only reads CSV input and writes research review output. It does not connect to IBKR, request market data, request historical data, read account state, read positions, or create orders.

## Review Status And Decision Labels

| source integration_status | review_status | decision_label |
|---|---|---|
| READY_REFERENCE_ONLY | REVIEW_READY | REFERENCE_ONLY |
| READY_DELAYED_REFERENCE_ONLY | REVIEW_READY | REFERENCE_ONLY |
| READY_DELAYED_FROZEN_REFERENCE_ONLY | REVIEW_READY | REFERENCE_ONLY |
| EMPTY_PRICE | REVIEW_BLOCKED | NO_PRICE |
| UNSUPPORTED | REVIEW_BLOCKED | UNSUPPORTED |
| MISSING_INPUT | REVIEW_BLOCKED | NO_GO |
| NO_GO | REVIEW_BLOCKED | NO_GO |
| action_allowed not false | SAFETY_REJECTED | NO_ACTION |

`REVIEW_READY` means a row can be inspected manually as a reference. It does not mean trade-ready.

## Delayed And Delayed Frozen Handling

Delayed and delayed_frozen rows remain reference-only:

- `tier_2_delayed` uses `next_step=manual_review_delayed_reference`
- `tier_3_delayed_frozen` uses `next_step=manual_review_stale_reference`

Neither tier is promoted to a real-time signal. Both require manual review.

## No Trading Advice

This phase intentionally stops before final trading plan generation. It does not calculate buy/sell instructions, rebalance instructions, order sizes, broker actions, or execution readiness.

The bridge exists to normalize IBKR daily integration state into a review-pack shape for a later phase.

## Safety Boundary

Every output row forces:

- `action_allowed=false`
- `manual_review_required=true`

The report also confirms:

- `broker_execution_triggered=false`
- `historical_data_request_triggered=false`
- `account_read_triggered=false`
- `position_read_triggered=false`

If any input row has `action_allowed` set to anything other than `false`, the bridge emits `SAFETY_REJECTED / NO_ACTION`.

## Missing Input

If the daily integration CSV is missing, the script does not fail hard. It creates a single NO_GO review-pack row with:

- `integration_status=MISSING_INPUT`
- `review_status=REVIEW_BLOCKED`
- `decision_label=NO_GO`
- `action_allowed=false`

## Next Phase

Phase 289-304 can connect `ibkr_daily_integration_review_pack.csv` to the existing final research review pack. That phase must preserve this bridge as a research-only input and must not introduce automatic trading, account reads, position reads, or historical data requests.
