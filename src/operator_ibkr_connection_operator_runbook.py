from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


PHASE = "Phase 521-524"
RUNBOOK_STATUS = "IBKR_CONNECTION_OPERATOR_RUNBOOK_READY"
OPERATOR_RUNBOOK_READY = "YES"
OPERATOR_APPROVAL_REQUIRED = "YES"
CONNECTION_ALLOWED = "NO"
NEXT_PHASE_CONNECT_DRY_RUN_CANDIDATE = "YES"
YES_TEXT = "YES"
NO_TEXT = "NO"

CSV_FIELDS = (
    "phase",
    "step_id",
    "step_name",
    "category",
    "required_operator_check",
    "expected_state",
    "observed_state",
    "status",
    "severity",
    "manual_only",
    "external_effect",
    "blocked_capability",
    "operator_action_required",
    "failure_mode",
    "rollback_action",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

STATUS_FIELDS = (
    "runbook_status",
    "operator_runbook_ready",
    "operator_approval_required",
    "connection_allowed",
    "external_connections_attempted",
    "ibkr_connected",
    "market_data_requested",
    "account_read_attempted",
    "positions_read_attempted",
    "historical_data_requested",
    "contract_qualification_attempted",
    "orders_submitted",
    "telegram_real_send_attempted",
    "network_probe_attempted",
    "next_phase_connect_dry_run_candidate",
)

STATUS_VALUES = {
    "runbook_status": RUNBOOK_STATUS,
    "operator_runbook_ready": OPERATOR_RUNBOOK_READY,
    "operator_approval_required": OPERATOR_APPROVAL_REQUIRED,
    "connection_allowed": CONNECTION_ALLOWED,
    "external_connections_attempted": NO_TEXT,
    "ibkr_connected": NO_TEXT,
    "market_data_requested": NO_TEXT,
    "account_read_attempted": NO_TEXT,
    "positions_read_attempted": NO_TEXT,
    "historical_data_requested": NO_TEXT,
    "contract_qualification_attempted": NO_TEXT,
    "orders_submitted": NO_TEXT,
    "telegram_real_send_attempted": NO_TEXT,
    "network_probe_attempted": NO_TEXT,
    "next_phase_connect_dry_run_candidate": NEXT_PHASE_CONNECT_DRY_RUN_CANDIDATE,
}

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _row(
    *,
    step_id: str,
    step_name: str,
    category: str,
    required_operator_check: str,
    expected_state: str,
    observed_state: str,
    status: str,
    severity: str,
    blocked_capability: str,
    operator_action_required: str,
    failure_mode: str,
    rollback_action: str,
    evidence: str,
    recommendation: str,
    timestamp_utc: str,
) -> Dict[str, str]:
    return {
        "phase": PHASE,
        "step_id": step_id,
        "step_name": step_name,
        "category": category,
        "required_operator_check": required_operator_check,
        "expected_state": expected_state,
        "observed_state": observed_state,
        "status": status,
        "severity": severity,
        "manual_only": YES_TEXT,
        "external_effect": "NONE",
        "blocked_capability": blocked_capability,
        "operator_action_required": operator_action_required,
        "failure_mode": failure_mode,
        "rollback_action": rollback_action,
        "evidence": evidence,
        "recommendation": recommendation,
        "timestamp_utc": timestamp_utc,
    }


def build_ibkr_connection_operator_runbook_rows(
    *,
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    return [
        _row(
            step_id="IBKR-RUNBOOK-000",
            step_name="Final runbook decision",
            category="final_decision",
            required_operator_check="confirm_this_phase_is_runbook_only",
            expected_state="runbook_ready_connection_not_allowed",
            observed_state="runbook_ready_no_connection_authorization",
            status=RUNBOOK_STATUS,
            severity="CRITICAL",
            blocked_capability="IBKR_CONNECTION",
            operator_action_required=YES_TEXT,
            failure_mode="operator_misreads_runbook_as_connection_approval",
            rollback_action="stop_before_any_external_command_and_reconfirm_manual_authorization",
            evidence="artifact_only_operator_runbook_generated",
            recommendation="use_this_packet_only_as_preparation_for_a_future_separately_authorized_connect_only_dry_run",
            timestamp_utc=timestamp,
        ),
        _row(
            step_id="IBKR-RUNBOOK-001",
            step_name="Confirm local TWS or IB Gateway responsibility",
            category="operator_runbook",
            required_operator_check="operator_confirms_local_app_state_manually_without_probe",
            expected_state="manual_check_only_no_network_probe",
            observed_state="no_probe_performed",
            status="PASS",
            severity="HIGH",
            blocked_capability="NETWORK_PROBE",
            operator_action_required=YES_TEXT,
            failure_mode="local_app_not_ready_or_wrong_session",
            rollback_action="do_not_attempt_connection_close_or_leave_local_app_unchanged",
            evidence="runbook_step_only",
            recommendation="future_phase_must_require_manual_confirmation_before_any_connect_only_attempt",
            timestamp_utc=timestamp,
        ),
        _row(
            step_id="IBKR-RUNBOOK-002",
            step_name="Confirm read-only intent",
            category="operator_runbook",
            required_operator_check="operator_confirms_connect_only_no_market_or_account_requests",
            expected_state="connect_only_scope_documented_for_future_phase",
            observed_state="no_connect_command_present",
            status="PASS",
            severity="CRITICAL",
            blocked_capability="MARKET_DATA_ACCOUNT_POSITIONS_HISTORICAL_CONTRACTS_TRADING",
            operator_action_required=YES_TEXT,
            failure_mode="scope_expands_beyond_connect_only",
            rollback_action="abort_future_attempt_and_return_to_permission_gate_review",
            evidence="no_execute_path_in_this_phase",
            recommendation="future_dry_run_must_stop_after_connect_disconnect_metadata_only_if_authorized",
            timestamp_utc=timestamp,
        ),
        _row(
            step_id="IBKR-RUNBOOK-003",
            step_name="Confirm no secrets in artifacts",
            category="local_checklist",
            required_operator_check="operator_reviews_outputs_for_no_secret_token_or_account_id",
            expected_state="no_secret_or_account_value_written",
            observed_state="status_fields_only_no_secret_values",
            status="PASS",
            severity="CRITICAL",
            blocked_capability="SECRET_OR_ACCOUNT_ID_DISCLOSURE",
            operator_action_required=YES_TEXT,
            failure_mode="secret_or_account_identifier_written_to_artifact",
            rollback_action="delete_uncommitted_artifact_and_regenerate_after_redaction_fix",
            evidence="artifact_schema_contains_status_and_check_fields_only",
            recommendation="keep_secret_material_out_of_csv_markdown_stdout_and_commit_history",
            timestamp_utc=timestamp,
        ),
        _row(
            step_id="IBKR-RUNBOOK-004",
            step_name="Confirm config remains untouched",
            category="local_checklist",
            required_operator_check="operator_keeps_config_yaml_unmodified_by_this_phase",
            expected_state="config_yaml_not_modified_by_generator",
            observed_state="generator_does_not_read_or_write_runtime_config",
            status="PASS",
            severity="HIGH",
            blocked_capability="CONFIG_MUTATION",
            operator_action_required=YES_TEXT,
            failure_mode="configuration_changed_during_runbook_generation",
            rollback_action="restore_unintended_config_change_before_commit",
            evidence="module_uses_static_artifact_generation_only",
            recommendation="do_not_commit_config_yaml",
            timestamp_utc=timestamp,
        ),
        _row(
            step_id="IBKR-RUNBOOK-005",
            step_name="Connection precondition packet",
            category="connection_preconditions",
            required_operator_check="operator_collects_future_explicit_authorization_before_connect_only_dry_run",
            expected_state="approval_required_and_not_granted_here",
            observed_state="connection_allowed_NO",
            status="PASS",
            severity="CRITICAL",
            blocked_capability="IBKR_CONNECTION",
            operator_action_required=YES_TEXT,
            failure_mode="future_connection_attempt_without_explicit_user_authorization",
            rollback_action="stop_process_and_request_explicit_connect_only_authorization",
            evidence="operator_approval_required_YES_connection_allowed_NO",
            recommendation="next_phase_may_be_connect_dry_run_candidate_only_after_manual_approval",
            timestamp_utc=timestamp,
        ),
        _row(
            step_id="IBKR-RUNBOOK-006",
            step_name="No external capability execution",
            category="explicitly_prohibited_actions",
            required_operator_check="confirm_no_ibkr_market_account_positions_historical_contract_order_telegram_or_probe_action",
            expected_state="all_external_actions_blocked",
            observed_state="all_external_attempt_flags_NO",
            status="PASS",
            severity="CRITICAL",
            blocked_capability="ALL_EXTERNAL_ACTIONS",
            operator_action_required=YES_TEXT,
            failure_mode="any_external_side_effect_detected",
            rollback_action="stop_and_remove_uncommitted_runtime_artifacts_then_review_code_path",
            evidence="external_effect_NONE_for_all_rows",
            recommendation="treat_any_external_call_as_phase_failure",
            timestamp_utc=timestamp,
        ),
        _row(
            step_id="IBKR-RUNBOOK-007",
            step_name="Failure mode catalog",
            category="failure_modes",
            required_operator_check="operator_reviews_expected_failure_paths_before_future_attempt",
            expected_state="known_failures_have_manual_stop_actions",
            observed_state="failure_modes_documented_without_execution",
            status="PASS",
            severity="HIGH",
            blocked_capability="UNCONTROLLED_RETRY",
            operator_action_required=YES_TEXT,
            failure_mode="connection_refused_timeout_wrong_port_wrong_client_id_or_session_locked",
            rollback_action="do_not_retry_automatically_capture_manual_note_and_return_to_no_go_state",
            evidence="failure_mode_and_rollback_columns_populated",
            recommendation="future_phase_must_fail_closed_without_auto_retry_or_escalation",
            timestamp_utc=timestamp,
        ),
        _row(
            step_id="IBKR-RUNBOOK-008",
            step_name="Rollback checklist",
            category="rollback_actions",
            required_operator_check="operator_confirms_manual_rollback_path_before_future_attempt",
            expected_state="rollback_is_stop_only_no_cleanup_of_external_state",
            observed_state="rollback_actions_documented",
            status="PASS",
            severity="HIGH",
            blocked_capability="STATEFUL_EXTERNAL_RECOVERY",
            operator_action_required=YES_TEXT,
            failure_mode="operator_attempts_to_fix_by_running_more_external_commands",
            rollback_action="stop_do_not_retry_do_not_request_data_do_not_send_notifications",
            evidence="rollback_actions_are_artifact_only",
            recommendation="future_phase_should_write_local_failure_artifact_only_if_authorized",
            timestamp_utc=timestamp,
        ),
        _row(
            step_id="IBKR-RUNBOOK-009",
            step_name="State label guard",
            category="state_label_guard",
            required_operator_check="operator_confirms_prior_labels_are_not_reclassified",
            expected_state="freeze_preflight_permission_labels_preserved",
            observed_state="no_production_ready_no_real_market_verified_no_connection_approved",
            status="PASS",
            severity="HIGH",
            blocked_capability="STATUS_RECLASSIFICATION",
            operator_action_required=NO_TEXT,
            failure_mode="runbook_status_rewritten_as_operational_approval",
            rollback_action="revert_misleading_artifact_text_before_commit",
            evidence="POST_MVP_MULTI_MARKET_FREEZE_READY_REAL_MARKET_ENV_READINESS_PREFLIGHT_READY_IBKR_CONNECTION_PERMISSION_GATE_READY_preserved",
            recommendation="do_not_treat_ready_labels_as_external_action_permission",
            timestamp_utc=timestamp,
        ),
    ]


def write_ibkr_connection_operator_runbook_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_ibkr_connection_operator_runbook_report(rows: Sequence[Dict[str, str]]) -> str:
    status_lines = [f"- {field}={STATUS_VALUES[field]}" for field in STATUS_FIELDS]
    runbook_lines = [
        f"- {row['step_id']} {row['step_name']}: {row['required_operator_check']} / observed={row['observed_state']}"
        for row in rows
        if row["category"] == "operator_runbook"
    ]
    checklist_lines = [
        f"- {row['step_id']} {row['step_name']}: expected={row['expected_state']} / status={row['status']}"
        for row in rows
        if row["category"] == "local_checklist"
    ]
    precondition_lines = [
        f"- {row['step_id']} {row['step_name']}: {row['evidence']} / recommendation={row['recommendation']}"
        for row in rows
        if row["category"] in {"connection_preconditions", "state_label_guard"}
    ]
    failure_lines = [
        f"- {row['step_id']} {row['failure_mode']}: rollback={row['rollback_action']}"
        for row in rows
        if row["category"] in {"failure_modes", "operator_runbook", "local_checklist"}
    ]
    rollback_lines = [
        f"- {row['step_id']} {row['rollback_action']}"
        for row in rows
        if row["category"] in {"rollback_actions", "connection_preconditions", "explicitly_prohibited_actions"}
    ]

    lines = [
        "# Phase 521-524 IBKR Connection Operator Runbook",
        "",
        "## Final Decision",
        "",
        *status_lines,
        "",
        "This phase is a runbook and local checklist only. It does not approve or attempt any real connection.",
        "",
        "## Scope Boundary",
        "",
        "- manual operator runbook for a future separately authorized connect-only dry-run",
        "- local checklist, preconditions, failure modes, and rollback actions only",
        "- no executable connection command is generated",
        "- no secret, token, or account id values are read or written",
        "- POST_MVP_MULTI_MARKET_FREEZE_READY remains unchanged and is not reclassified as production-ready",
        "- REAL_MARKET_ENV_READINESS_PREFLIGHT_READY remains unchanged and is not reclassified as real-market-data-verified",
        "- IBKR_CONNECTION_PERMISSION_GATE_READY remains unchanged and is not reclassified as connection-approved",
        "",
        "## Explicitly Prohibited Actions",
        "",
        "- IBKR, TWS, or IB Gateway connection",
        "- network probe",
        "- market data request",
        "- account read",
        "- positions read",
        "- historical data request",
        "- contract qualification",
        "- order submission",
        "- order cancellation",
        "- rebalance action",
        "- Telegram real send",
        "",
        "## Operator Runbook",
        "",
        *runbook_lines,
        "",
        "## Local Checklist",
        "",
        *checklist_lines,
        "",
        "## Connection Preconditions",
        "",
        *precondition_lines,
        "",
        "## Failure Modes",
        "",
        *failure_lines,
        "",
        "## Rollback Actions",
        "",
        *rollback_lines,
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_ibkr_connection_operator_runbook.csv",
        "- report=reports/operator_ibkr_connection_operator_runbook_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Residual Risks",
        "",
        "- this runbook does not prove IBKR connectivity",
        "- this runbook does not prove TWS or IB Gateway availability",
        "- this runbook does not prove market data entitlement",
        "- this runbook does not prove account, position, historical data, contract qualification, order, cancel, rebalance, or Telegram behavior",
        "",
        "## Next Phase Preconditions",
        "",
        "- explicit user authorization for a future connect-only dry-run",
        "- a separate fail-closed command reviewed before any real connection",
        "- no market data, account, positions, historical data, contract qualification, order, cancel, rebalance, Telegram real send, or network probe unless separately approved",
        "- no automatic transition from this runbook to any connection-approved state",
    ]
    return "\n".join(lines) + "\n"


def write_ibkr_connection_operator_runbook_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_ibkr_connection_operator_runbook_report(rows), encoding="utf-8")


def generate_ibkr_connection_operator_runbook(
    *,
    output_csv: PathLike = "operator_ibkr_connection_operator_runbook.csv",
    output_report: PathLike = "reports/operator_ibkr_connection_operator_runbook_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_ibkr_connection_operator_runbook_rows(generated_at=generated_at)
    write_ibkr_connection_operator_runbook_csv(output_csv, rows)
    write_ibkr_connection_operator_runbook_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 521-524 IBKR connection operator runbook.")
    parser.add_argument("--output-csv", default="operator_ibkr_connection_operator_runbook.csv")
    parser.add_argument("--output-report", default="reports/operator_ibkr_connection_operator_runbook_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_ibkr_connection_operator_runbook(
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[IBKR_CONNECTION_OPERATOR_RUNBOOK] generated")
    for field in STATUS_FIELDS:
        print(f"{field}={STATUS_VALUES[field]}")
    print(f"steps={len(rows)}")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    print(
        "NOTICE: Phase 521-524 runbook/checklist artifacts only. No IBKR/TWS/Gateway connection, "
        "no network probe, no market data request, no account reads, no position reads, "
        "no historical data request, no contract qualification, no orders, no cancellation, "
        "no rebalance, no Telegram real send, and no connection approval."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
