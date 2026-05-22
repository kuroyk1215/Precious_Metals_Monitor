# IBKR Daily Integration Preflight Delayed/Frozen Intake

## Phase 241-256 Snapshot Intake

`scripts/ibkr_market_data_snapshot_oneshot.sh` writes `ibkr_market_data_snapshot.csv` after an explicitly gated market data snapshot run. Phase 257-272 lets `scripts/ibkr_daily_integration_preflight.sh` consume that CSV with:

```bash
bash scripts/ibkr_daily_integration_preflight.sh --market-data-snapshot=ibkr_market_data_snapshot.csv
```

The daily integration preflight reads only the snapshot file. It does not connect to IBKR, does not request market data, does not request historical data, and does not read account, cash, or position state.

## Data Quality Tiers

Daily integration maps snapshot delay state to research-only tiers:

| snapshot input | data_quality_tier | research_usage |
|---|---|---|
| live | tier_1_real_time_or_live | reference_only |
| frozen | tier_1_real_time_or_live | reference_only |
| delayed | tier_2_delayed | reference_only |
| delayed_frozen | tier_3_delayed_frozen | stale_reference_only |
| snapshot_empty | tier_9_unavailable | unavailable |
| delayed_snapshot_empty | tier_9_unavailable | unavailable |
| delayed_frozen_snapshot_empty | tier_9_unavailable | unavailable |
| unsupported | tier_9_unavailable | unsupported |
| connection_error | tier_9_unavailable | unavailable |
| no_go | tier_9_unavailable | unavailable |

Delayed and delayed_frozen prices are references for manual research review only. They are not real-time market signals and cannot be promoted into action.

## Price Selection

The usable reference price is selected in this order:

1. `market_price`
2. `last`
3. `close`
4. midpoint of `bid` and `ask` when both are valid
5. unavailable

Rows without any usable reference price become `EMPTY_PRICE`.

## Safety Boundary

Daily integration always writes:

- `action_allowed=false`
- `broker_execution_triggered=false`
- `historical_data_request_triggered=false`
- `account_read_triggered=false`
- `position_read_triggered=false`
- `manual_review_required=true`

Any snapshot row that has `action_allowed`, `historical_data_request_triggered`, or `broker_execution_triggered` set to anything other than `false` is classified as `SAFETY_REJECTED`.

## Missing And Empty Snapshot Handling

If the snapshot file is missing, the daily preflight does not fail hard. It writes one `NO_GO` row, prints:

```text
market_data_snapshot_status=missing
daily_integration_status=NO_GO
action_allowed=false
```

An existing but empty snapshot file is treated as unavailable input and remains `NO_GO`.

## Next Phase Handoff

Phase 273+ can consume `ibkr_daily_integration_preflight.csv` in a research review pack. That handoff must preserve the same manual-only boundary: no broker execution, no historical data request, no account reads, no position reads, and no automatic trading action.
