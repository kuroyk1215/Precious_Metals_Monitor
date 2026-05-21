# Final Research Trading Plan Sample

## 1. Safety Boundary

This sample is:

- research-only
- read-only
- manual-only
- no auto trade

It is not an order ticket, broker instruction, or automatic trading signal.

## 2. Instrument

- Instrument: SAMPLE_GOLD_ETF
- Market: SAMPLE_MARKET
- Currency: SAMPLE_CURRENCY
- Data status: delayed
- Source status: sample only
- Fallback method: documentation example

## 3. Executive Summary

The instrument remains within a reference range. Short-term action should require manual confirmation because the data status is not real_time.

## 4. Short-Term View

- Horizon: intraday to 3 sessions
- Bias: range observation
- Reference support: SAMPLE_SUPPORT
- Reference resistance: SAMPLE_RESISTANCE
- Tactical note: observe reaction near support and resistance
- Invalidation: break below SAMPLE_SUPPORT with weak recovery

## 5. Medium-Term View

- Horizon: several sessions to several weeks
- Expected range: SAMPLE_RANGE_LOW to SAMPLE_RANGE_HIGH
- Confirmation: sustained close above SAMPLE_CONFIRMATION_LEVEL
- Risk condition: failure to hold range midpoint
- Invalidation: sustained break below medium-term support

## 6. Long-Term View

- Horizon: structural reference
- Context: precious metals allocation reference
- Major risk: macro repricing or FX distortion
- Invalidation: structural trend break or major data revision

## 7. Rolling Trade Reference

- Observation zone: SAMPLE_OBSERVATION_ZONE
- Potential entry reference: SAMPLE_ENTRY_REFERENCE
- Potential exit reference: SAMPLE_EXIT_REFERENCE
- Stop or invalidation reference: SAMPLE_INVALIDATION_REFERENCE
- Execution note: manual review and manual execution only

## 8. Risk Triggers

- Price trigger: break outside expected range
- Time trigger: stale report or near market close
- Event trigger: macro data or central bank event
- Data quality trigger: inferred or unavailable data
- Liquidity trigger: abnormal spread or weak volume
- FX trigger: currency conversion distortion

## 9. Manual Review Checklist

Before any real decision:

- Confirm latest price
- Confirm market session
- Confirm data_status
- Confirm spread and liquidity
- Confirm FX reference if applicable
- Confirm position size externally
- Confirm no automatic order was generated
- Execute manually only if independently confirmed

## 10. No-Trade Assertion

No order is created.

No broker action is triggered.

No Telegram command can execute a trade.

The plan is for manual research review only.
