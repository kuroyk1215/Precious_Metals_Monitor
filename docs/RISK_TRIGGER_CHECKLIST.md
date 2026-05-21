# Risk Trigger Checklist

## 1. Purpose

This document defines the risk trigger checklist for future final research trading plan review.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Price triggers

Review price risk if:

- price breaks below support
- price fails to reclaim reference zone
- price gaps beyond expected range
- price reaches resistance faster than expected
- ETF price diverges from underlying reference

## 3. Time triggers

Review time risk if:

- expected move does not occur within planned window
- market session is near close
- scheduled report is stale
- overnight risk becomes relevant
- holiday calendar affects liquidity

## 4. Event triggers

Review event risk if:

- central bank decision is pending
- CPI / PPI / payrolls / GDP data is pending
- geopolitical event changes market pricing
- exchange announcement affects trading
- ETF issuer event affects tracking

## 5. Data quality triggers

Escalate review if:

- data_status is inferred
- data_status is unavailable
- data is delayed_frozen
- timestamp is stale
- fallback_method is used
- FX conversion source is unclear

## 6. Liquidity triggers

Review liquidity risk if:

- bid-ask spread widens
- volume is below normal
- order book is thin
- market is near open or close
- ETF liquidity diverges from underlying market

## 7. Volatility triggers

Review volatility risk if:

- intraday range expands materially
- volatility spikes after macro data
- stop reference becomes too wide
- price moves beyond expected range
- market correlation breaks down

## 8. FX triggers

Review FX risk if:

- JPY / CNY / USD movement changes converted value
- FX quote is stale
- cross-market ETF valuation changes
- currency move dominates metal move

## 9. Manual action boundary

If any risk trigger is active:

- do not treat plan as direct instruction
- re-check latest market data
- re-check position size
- re-check execution plan manually
- keep all execution outside the system

## 10. Forbidden escalation

Risk triggers must not trigger:

- automatic buy
- automatic sell
- automatic cancel
- automatic rebalance
- Telegram trade command
- broker-side execution
