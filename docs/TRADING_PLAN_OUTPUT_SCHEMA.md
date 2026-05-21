# Trading Plan Output Schema

## 1. Purpose

This document defines the recommended human-readable schema for final research trading plan output.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Top-level fields

Recommended final research trading plan fields:

- run_timestamp
- timezone
- instrument
- market
- currency
- data_status
- source_status
- strategy_context
- short_term_view
- medium_term_view
- long_term_view
- rolling_trade_reference
- entry_reference
- exit_reference
- invalidation_conditions
- risk_triggers
- manual_review_checklist
- safety_boundary

## 3. Data status section

Required fields:

- data_status
- source_status
- fallback_method
- timestamp
- timezone
- quality_note

If data_status is not real_time, the plan should explicitly say manual review is required.

## 4. Short-term view section

Recommended fields:

- horizon
- directional_bias
- reference_range
- key_support
- key_resistance
- tactical_notes
- invalidation_condition

## 5. Medium-term view section

Recommended fields:

- horizon
- expected_range
- trend_condition
- confirmation_signal
- risk_condition
- invalidation_condition

## 6. Long-term view section

Recommended fields:

- horizon
- structural_view
- macro_context
- allocation_relevance
- major_risk
- invalidation_condition

## 7. Rolling trade reference section

Recommended fields:

- observation_zone
- potential_entry_reference
- potential_exit_reference
- stop_or_invalidation_reference
- position_sizing_note
- manual_execution_note

## 8. Risk trigger section

Recommended fields:

- price_trigger
- time_trigger
- event_trigger
- volatility_trigger
- liquidity_trigger
- data_quality_trigger
- FX_trigger
- macro_trigger

## 9. Manual review checklist

Required checklist:

- confirm latest price
- confirm data_status
- confirm market session
- confirm liquidity
- confirm spread
- confirm FX if applicable
- confirm no auto order generated
- confirm execution is manual

## 10. Safety boundary

Every output should include:

    This plan is research-only, read-only, manual-only, and does not execute trades.
