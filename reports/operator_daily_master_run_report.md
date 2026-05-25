# Operator Daily Master Run Report

## Safety Banner

- no auto trading
- no account reads
- no position reads
- no historical data requests
- no Telegram real send
- no order/cancel/rebalance

## Master Status

- master_status=MASTER_SAFE_UNAVAILABLE
- safety_clean=true
- quote_unavailable=true
- real_quote_available=false
- diagnostic_reason=real_quote_unavailable_but_safety_clean_audit_chain_completed
- operator_next_step=review_connection_permission_continue_daily_collection

## Wrapper Exit Codes

- operator_real_marketdata_daily_run.sh: exit_code=0
- operator_real_quote_normalization.sh: exit_code=0
- operator_real_quote_signal_bridge.sh: exit_code=0
- operator_daily_real_market_report.sh: exit_code=0
- operator_real_market_mvp_status.sh: exit_code=0
- operator_real_market_archive_compare.sh: exit_code=0
- operator_signal_threshold_explainer.sh: exit_code=0
- operator_strategy_quality_report.sh: exit_code=0
- operator_daily_checklist.sh: exit_code=0
- operator_real_market_mvp_regression_check.sh: exit_code=0
