# Operator Strategy Quality Report

## Safety Banner

- no auto trading
- no account reads
- no position reads
- no historical data requests
- no Telegram real send
- no order/cancel/rebalance

## Quality Categories

- data available=false
- data unavailable but safe=true
- insufficient history=false
- signal insufficient=true
- manual review only=true

## Strategy Quality

- quality_status=DATA_UNAVAILABLE_BUT_SAFE
- archive_status_consistency=CONSISTENT_OBSERVATION_STATE
- threshold_statuses=HOLD_NO_REAL_QUOTE
- mvp_status=MVP_SAFE_UNAVAILABLE
- diagnostic_reason=real_quote_unavailable_but_forbidden_actions_remain_false
- operator_next_step=review_connection_permission_continue_collection
