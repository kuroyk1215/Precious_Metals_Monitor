# Operator Dashboard Artifact Reader

## Scope

- local read-only dashboard artifact summary
- no UI frontend and no web service
- no IBKR, account, position, historical data, Telegram real send, or trading action path

## Dashboard Summary

- generated_at=2026-05-25T09:35:45+00:00
- dashboard_status=DASHBOARD_ARTIFACT_READER_READY
- final_packet_status=FINAL_PACKET_SAFE_UNAVAILABLE
- batch_i_env_gate_status=SAFE_UNAVAILABLE_REVIEW_REQUIRED
- batch_i_audit_gate_status=PASS
- batch_j_gate_status=PASS
- batch_j_threshold_profile_status=BATCH_J_THRESHOLD_PROFILE_REVIEW_ONLY
- batch_j_audit_gate_status=PASS
- safe_unavailable_status=SAFE_UNAVAILABLE_REVIEW_REQUIRED
- multi_market_schema_gate_status=MULTI_MARKET_SYMBOL_SCHEMA_READY
- multi_market_adapter_gate_status=MULTI_MARKET_ADAPTER_SKELETON_READY
- jp_symbol_count=6
- cn_symbol_count=6
- us_symbol_count=6
- all_markets_observation_only=true
- all_symbols_trading_disabled=true
- real_market_data_request_allowed=false
- contract_qualification_allowed=false
- production_ready_claim_detected=false
- real_market_data_verified=false
- strategy_execution_ready=false
- operator_display_mode=SAFE_UNAVAILABLE_REVIEW_ONLY
- dashboard_data_source=operator_final_daily_packet.csv,reports/operator_final_daily_packet.md,operator_batch_i_final_integration_audit_gate.csv,operator_batch_j_final_integration_audit_gate.csv,operator_batch_j_strategy_threshold_gate.csv,operator_mvp_final_audit_gate.csv,operator_real_market_mvp_completion_gate.csv
- trading_actions_allowed=false
- order_action_allowed=false
- cancel_action_allowed=false
- rebalance_action_allowed=false
- account_read_allowed=false
- position_read_allowed=false
- historical_data_request_allowed=false
- telegram_real_send_allowed=false
- manual_only=true
- research_only=true
- observation_only=true
- diagnostic_reason=local_dashboard_artifact_reader_ready_for_review_only_summary
