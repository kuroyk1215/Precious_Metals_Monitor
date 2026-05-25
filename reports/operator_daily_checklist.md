# Operator Daily Checklist

## Safety Banner

- no auto trading
- no account reads
- no position reads
- no historical data requests
- no Telegram real send
- no order/cancel/rebalance

## Checklist

1. git status safety check: run git status --short and review local-only files
2. confirm config.yaml remains local-only: verify config.yaml is not staged or committed
3. confirm ibkr_market_data_api_errors.csv remains local-only: verify ibkr_market_data_api_errors.csv is not staged or committed
4. run real marketdata daily wrapper: run scripts/operator_real_marketdata_daily_run.sh
5. run quote normalization: run scripts/operator_real_quote_normalization.sh
6. run signal bridge: run scripts/operator_real_quote_signal_bridge.sh
7. run daily real-market report: run scripts/operator_daily_real_market_report.sh
8. run MVP status aggregator: run scripts/operator_real_market_mvp_status.sh
9. review decision / quote / signal status: manually review decision, quote, signal, and MVP status outputs
10. do not trade automatically: keep all trading, account, position, historical, and Telegram send actions disabled
