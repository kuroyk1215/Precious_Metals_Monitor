# Strategy Explanation Layer Review

## 1. Purpose

This document defines the Phase 38 strategy explanation layer review.

Current boundary:

- research-only
- read-only
- manual-only
- no auto trade

Phase 38 does not add automatic trading, broker execution, or order generation.

## 2. Goal

The goal is to make the final research trading plan easier to review manually.

The strategy explanation layer should clarify:

- short-term view
- medium-term view
- long-term view
- rolling trade reference
- invalidation conditions
- risk triggers
- data limitations
- manual review checklist

## 3. Required output structure

A final research trading plan should include:

1. Executive summary
2. Data status summary
3. Short-term view
4. Medium-term view
5. Long-term view
6. Rolling trade reference
7. Entry reference zone
8. Exit reference zone
9. Invalidation conditions
10. Risk trigger checklist
11. Manual review checklist
12. Safety boundary

## 4. Time horizon definitions

### Short-term

Expected use:

- intraday
- 1 to 3 sessions
- tactical observation
- rolling trade reference

### Medium-term

Expected use:

- several sessions to several weeks
- range expectation
- trend confirmation
- risk control planning

### Long-term

Expected use:

- structural view
- macro or core allocation reference
- no automatic execution

## 5. Rolling trade explanation

Rolling trade output should not be phrased as an instruction.

Allowed wording:

- reference zone
- observation zone
- manual review required
- risk trigger
- invalidation point

Forbidden wording:

- buy now
- sell now
- execute
- auto trade
- guaranteed entry
- guaranteed exit

## 6. Invalidation conditions

Every plan should define conditions that weaken or invalidate the view.

Examples:

- price breaks below key support
- price fails to reclaim reference zone
- data_status becomes unavailable
- ETF diverges from underlying reference
- FX movement invalidates converted value
- market event changes risk assumptions

## 7. Risk trigger categories

Risk triggers should include:

- price trigger
- time trigger
- event trigger
- data quality trigger
- liquidity trigger
- volatility trigger
- FX trigger
- macro trigger

## 8. Manual review requirement

Every final plan must preserve manual review.

Required boundary:

    research-only / read-only / manual-only / no auto trade

## 9. Phase 38 non-goals

Phase 38 does not:

- modify main.py
- modify src/
- add order execution
- add cancel execution
- add broker routing
- add Telegram trade command
- enable automatic rebalancing
