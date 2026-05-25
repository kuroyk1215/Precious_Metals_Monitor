# Operator Daily Real Market Report

## Safety Banner

- no auto trading
- no account reads
- no position reads
- no historical data requests
- no Telegram real send
- no order/cancel/rebalance

## Real Market States

- real quote available is reported as REAL_QUOTE_AVAILABLE
- safe unavailable is reported as SAFE_UNAVAILABLE
- permission / connection failure is reported as PERMISSION_OR_CONNECTION_FAILURE
- observation allowed remains observation-only
- manual review only remains true for every row

## Symbol Rows

- GLD: real_quote_state=PERMISSION_OR_CONNECTION_FAILURE; observation_allowed=false; manual_review_only=true; operator_next_step=review_real_marketdata_connection
- SLV: real_quote_state=PERMISSION_OR_CONNECTION_FAILURE; observation_allowed=false; manual_review_only=true; operator_next_step=review_real_marketdata_connection
