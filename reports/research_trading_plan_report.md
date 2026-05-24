# Research Trading Plan Report

## Top-level Status

- top_level_status=RESEARCH_PLAN_REFERENCE_READY
- source_artifact=latest_daily_operator_handoff_summary.csv:present

## Safety Summary

- action_allowed=false
- broker_execution_triggered=false
- historical_data_request_triggered=false
- account_read_triggered=false
- position_read_triggered=false
- telegram_send_triggered=false

## Data Quality Summary

- GLD: NO_PRICE / NO_PRICE_BLOCKED
- SLV: DELAYED_USABLE_REFERENCE / DELAYED_REFERENCE_ONLY

## Symbol Research Table

| symbol | reference_price | price_status | data_delay_flag | research_plan_status | manual_observation_bias | manual_watch_zone |
|---|---|---|---|---|---|---|
| GLD | N/A | no_price | delayed | NO_PRICE_PLAN_BLOCKED | NO_PRICE_BLOCKED | N/A |
| SLV | 68.31 | usable_price | delayed | REFERENCE_ONLY_PLAN_READY | REFERENCE_ONLY | observe around reference price +/-2% (68.31); manual review only |

## Reference-only Explanation

- reference_only_symbols=SLV
- Delayed usable prices are manual reference context only.

## No-price Blocked Explanation

- no_price_symbols=GLD
- No-price symbols require manual data review before any research plan.

## Risk Notes

- GLD: Manual data review required before any research plan.
- SLV: Reference-only research artifact from delayed data; manual review required; no broker or account calls.

## Next Operator Step

- manual_reference_review
