# Operator Real Marketdata Smoke Report

## Safety Banner

- read-only / manual-only / audit-first
- no automatic trading
- no account read
- no position read
- no historical data request
- no Telegram real send

## Required Audit Fields

- top_level_status=REAL_MARKETDATA_SMOKE_AUDIT_READY
- started_at=2026-05-25T02:05:36+00:00
- ended_at=2026-05-25T02:05:37+00:00
- read_only_required=true
- real_connection_allowed_during_run=true
- market_data_request_allowed_during_run=true
- contract_qualification_allowed=false
- historical_data_request_allowed=false
- trading_actions_allowed=false
- account_read_allowed=false
- position_read_allowed=false
- telegram_send_allowed=false
- config_restored=true
- config_file_modified=false
- ibkr_api_request_allowed=true
- req_mkt_data_allowed=true
- req_historical_data_allowed=false
- order_action_allowed=false
- cancel_action_allowed=false
- rebalance_action_allowed=false
- final_safety_status=PASS_READ_ONLY_MARKETDATA_SMOKE_AUDITED

## Runtime Observations

- wrapper_exit_code=0
- smoke_exit_code=0
- snapshot_rows_detected=3
- connection_succeeded=false
- market_data_request_triggered=false
- historical_data_request_triggered=false
- broker_execution_triggered=false
- account_read_triggered=false
- position_read_triggered=false
- telegram_send_triggered=false

## Failure / Warning Section

- none

## Next Manual Operator Step

- Review `operator_real_marketdata_smoke_summary.csv` and this report before any next phase decision.
