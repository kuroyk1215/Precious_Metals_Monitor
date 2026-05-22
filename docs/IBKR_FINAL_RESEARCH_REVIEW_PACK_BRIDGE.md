# IBKR Final Research Review Pack Bridge

## Phase 273-288 Input

Phase 273-288 writes `ibkr_daily_integration_review_pack.csv`. Phase 289-304 consumes that review pack and produces an independent IBKR final research review pack:

```bash
bash scripts/ibkr_final_research_review_pack.sh --review-pack=ibkr_daily_integration_review_pack.csv
```

Outputs:

- `ibkr_final_research_review_pack.csv`
- `reports/ibkr_final_research_review_pack_report.md`

This is an IBKR market data chain bridge. It does not alter the existing non-IBKR `final_research_review_pack.py` flow.

## Final Review Fields

| source review pack state | final_review_status | final_decision_label | final_research_bucket |
|---|---|---|---|
| REVIEW_READY / REFERENCE_ONLY | FINAL_REVIEW_READY | REFERENCE_ONLY_REVIEW | reference_only |
| REVIEW_BLOCKED / NO_PRICE | FINAL_REVIEW_BLOCKED | BLOCKED | no_price |
| REVIEW_BLOCKED / UNSUPPORTED | FINAL_REVIEW_BLOCKED | BLOCKED | unsupported |
| REVIEW_BLOCKED / NO_GO | FINAL_REVIEW_BLOCKED | BLOCKED | no_go |
| action_allowed not false | SAFETY_REJECTED | NO_ACTION | source bucket retained or no_go |

`FINAL_REVIEW_READY` means the row is ready for manual final research review only. It does not mean trade-ready.

## Delayed And Delayed Frozen

Delayed and delayed_frozen inputs remain reference-only:

- `tier_2_delayed` becomes `final_research_bucket=delayed_reference`
- `tier_3_delayed_frozen` becomes `final_research_bucket=stale_reference`

The bridge never promotes delayed or delayed_frozen data to a real-time signal.

## No Trading Advice

This phase does not create trading instructions, order sizes, rebalance instructions, broker actions, or execution readiness. It is a final research review bridge over existing CSV inputs.

## Safety Boundary

Every output row forces:

- `action_allowed=false`
- `broker_execution_triggered=false`
- `historical_data_request_triggered=false`
- `account_read_triggered=false`
- `position_read_triggered=false`
- `manual_review_required=true`

This keeps the bridge research-only and manual-review-only.

## Missing Input

If the review pack input is missing, the script does not fail hard. It writes one NO_GO row:

- `final_review_status=FINAL_REVIEW_BLOCKED`
- `final_decision_label=BLOCKED`
- `final_research_bucket=no_go`
- `action_allowed=false`

## Next Phase

Phase 305-320 can build a one-command daily run, Execution C wrapper, or operator packet around the IBKR market data chain. That future phase must preserve explicit operator review and must not introduce automatic broker execution.
