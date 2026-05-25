# Operator Real Marketdata Decision Gate Report

## Safety Banner

- read-only / manual-only / audit-first
- no automatic trading
- no account read
- no position read
- no historical data request
- no Telegram real send

## Decision Fields

- decision_generated_at=2026-05-25T02:58:09+00:00
- source_archive_file=operator_real_marketdata_smoke_archive.csv
- source_exists=true
- source_diagnostic_category=PASS_READY
- operator_decision=HOLD_SAFE_FAILURE
- decision_reason=connection_succeeded_false,market_data_request_triggered_false
- operator_next_step=hold_and_inspect_real_marketdata_connection
- source_summary_file=operator_real_marketdata_smoke_summary.csv
- summary_exists=true
- smoke_exit_code=0
- snapshot_rows_detected=3
- connection_succeeded=false
- market_data_request_triggered=false
- top_level_status=REAL_MARKETDATA_SMOKE_AUDIT_READY
- final_safety_status=PASS_READ_ONLY_MARKETDATA_SMOKE_AUDITED
- config_restored=true
- config_file_modified=false
- real_connection_allowed_during_run=true
- market_data_request_allowed_during_run=true
- contract_qualification_allowed=false
- historical_data_request_allowed=false
- trading_actions_allowed=false
- account_read_allowed=false
- position_read_allowed=false
- telegram_send_allowed=false
- req_mkt_data_allowed=true
- req_historical_data_allowed=false
- order_action_allowed=false
- cancel_action_allowed=false
- rebalance_action_allowed=false
