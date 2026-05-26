# Phase 521-524 IBKR Connection Operator Runbook

## Final Decision

- runbook_status=IBKR_CONNECTION_OPERATOR_RUNBOOK_READY
- operator_runbook_ready=YES
- operator_approval_required=YES
- connection_allowed=NO
- external_connections_attempted=NO
- ibkr_connected=NO
- market_data_requested=NO
- account_read_attempted=NO
- positions_read_attempted=NO
- historical_data_requested=NO
- contract_qualification_attempted=NO
- orders_submitted=NO
- telegram_real_send_attempted=NO
- network_probe_attempted=NO
- next_phase_connect_dry_run_candidate=YES

This phase is a runbook and local checklist only. It does not approve or attempt any real connection.

## Scope Boundary

- manual operator runbook for a future separately authorized connect-only dry-run
- local checklist, preconditions, failure modes, and rollback actions only
- no executable connection command is generated
- no secret, token, or account id values are read or written
- POST_MVP_MULTI_MARKET_FREEZE_READY remains unchanged and is not reclassified as production-ready
- REAL_MARKET_ENV_READINESS_PREFLIGHT_READY remains unchanged and is not reclassified as real-market-data-verified
- IBKR_CONNECTION_PERMISSION_GATE_READY remains unchanged and is not reclassified as connection-approved

## Explicitly Prohibited Actions

- IBKR, TWS, or IB Gateway connection
- network probe
- market data request
- account read
- positions read
- historical data request
- contract qualification
- order submission
- order cancellation
- rebalance action
- Telegram real send

## Operator Runbook

- IBKR-RUNBOOK-001 Confirm local TWS or IB Gateway responsibility: operator_confirms_local_app_state_manually_without_probe / observed=no_probe_performed
- IBKR-RUNBOOK-002 Confirm read-only intent: operator_confirms_connect_only_no_market_or_account_requests / observed=no_connect_command_present

## Local Checklist

- IBKR-RUNBOOK-003 Confirm no secrets in artifacts: expected=no_secret_or_account_value_written / status=PASS
- IBKR-RUNBOOK-004 Confirm config remains untouched: expected=config_yaml_not_modified_by_generator / status=PASS

## Connection Preconditions

- IBKR-RUNBOOK-005 Connection precondition packet: operator_approval_required_YES_connection_allowed_NO / recommendation=next_phase_may_be_connect_dry_run_candidate_only_after_manual_approval
- IBKR-RUNBOOK-009 State label guard: POST_MVP_MULTI_MARKET_FREEZE_READY_REAL_MARKET_ENV_READINESS_PREFLIGHT_READY_IBKR_CONNECTION_PERMISSION_GATE_READY_preserved / recommendation=do_not_treat_ready_labels_as_external_action_permission

## Failure Modes

- IBKR-RUNBOOK-001 local_app_not_ready_or_wrong_session: rollback=do_not_attempt_connection_close_or_leave_local_app_unchanged
- IBKR-RUNBOOK-002 scope_expands_beyond_connect_only: rollback=abort_future_attempt_and_return_to_permission_gate_review
- IBKR-RUNBOOK-003 secret_or_account_identifier_written_to_artifact: rollback=delete_uncommitted_artifact_and_regenerate_after_redaction_fix
- IBKR-RUNBOOK-004 configuration_changed_during_runbook_generation: rollback=restore_unintended_config_change_before_commit
- IBKR-RUNBOOK-007 connection_refused_timeout_wrong_port_wrong_client_id_or_session_locked: rollback=do_not_retry_automatically_capture_manual_note_and_return_to_no_go_state

## Rollback Actions

- IBKR-RUNBOOK-005 stop_process_and_request_explicit_connect_only_authorization
- IBKR-RUNBOOK-006 stop_and_remove_uncommitted_runtime_artifacts_then_review_code_path
- IBKR-RUNBOOK-008 stop_do_not_retry_do_not_request_data_do_not_send_notifications

## Artifact Summary

- csv=operator_ibkr_connection_operator_runbook.csv
- report=reports/operator_ibkr_connection_operator_runbook_report.md
- row_count=10

## Residual Risks

- this runbook does not prove IBKR connectivity
- this runbook does not prove TWS or IB Gateway availability
- this runbook does not prove market data entitlement
- this runbook does not prove account, position, historical data, contract qualification, order, cancel, rebalance, or Telegram behavior

## Next Phase Preconditions

- explicit user authorization for a future connect-only dry-run
- a separate fail-closed command reviewed before any real connection
- no market data, account, positions, historical data, contract qualification, order, cancel, rebalance, Telegram real send, or network probe unless separately approved
- no automatic transition from this runbook to any connection-approved state
