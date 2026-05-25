# Operator GLD/SLV Spread Framework Report

## Safety Banner

- observation-only spread framework
- no auto trading
- no account reads
- no position reads
- no historical data requests
- no Telegram real send
- no order/cancel/rebalance

## Spread Framework

- gld_quote_status=UNAVAILABLE
- slv_quote_status=UNAVAILABLE
- spread_available=false
- gld_slv_ratio=
- relative_strength_status=SAFE_UNAVAILABLE
- spread_observation_status=SAFE_UNAVAILABLE
- diagnostic_reason=gld_or_slv_real_quote_unavailable_for_spread_framework
- operator_next_step=review_real_marketdata_connection_before_spread_observation
