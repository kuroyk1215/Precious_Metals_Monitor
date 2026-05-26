from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


PHASE = "Phase 525-528"
APPROVAL_PACKET_STATUS = "IBKR_CONNECT_DRYRUN_APPROVAL_PACKET_READY"
APPROVAL_DECISION = "NO_GO"
OPERATOR_APPROVAL_REQUIRED = "YES"
CONNECT_DRY_RUN_CANDIDATE = "YES"
CONNECTION_ALLOWED = "NO"
CONNECT_COMMAND_EMITTED = "NO"
YES_TEXT = "YES"
NO_TEXT = "NO"

CSV_FIELDS = (
    "phase",
    "approval_id",
    "approval_name",
    "category",
    "required_approval",
    "expected_state",
    "observed_state",
    "decision",
    "severity",
    "manual_only",
    "external_effect",
    "blocked_capability",
    "operator_action_required",
    "go_condition",
    "no_go_condition",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

STATUS_FIELDS = (
    "approval_packet_status",
    "approval_decision",
    "operator_approval_required",
    "connect_dry_run_candidate",
    "connection_allowed",
    "connect_command_emitted",
    "external_connections_attempted",
    "network_probe_attempted",
    "ibkr_connected",
    "market_data_requested",
    "account_read_attempted",
    "positions_read_attempted",
    "historical_data_requested",
    "contract_qualification_attempted",
    "orders_submitted",
    "orders_cancelled",
    "rebalance_attempted",
    "telegram_real_send_attempted",
)

STATUS_VALUES = {
    "approval_packet_status": APPROVAL_PACKET_STATUS,
    "approval_decision": APPROVAL_DECISION,
    "operator_approval_required": OPERATOR_APPROVAL_REQUIRED,
    "connect_dry_run_candidate": CONNECT_DRY_RUN_CANDIDATE,
    "connection_allowed": CONNECTION_ALLOWED,
    "connect_command_emitted": CONNECT_COMMAND_EMITTED,
    "external_connections_attempted": NO_TEXT,
    "network_probe_attempted": NO_TEXT,
    "ibkr_connected": NO_TEXT,
    "market_data_requested": NO_TEXT,
    "account_read_attempted": NO_TEXT,
    "positions_read_attempted": NO_TEXT,
    "historical_data_requested": NO_TEXT,
    "contract_qualification_attempted": NO_TEXT,
    "orders_submitted": NO_TEXT,
    "orders_cancelled": NO_TEXT,
    "rebalance_attempted": NO_TEXT,
    "telegram_real_send_attempted": NO_TEXT,
}

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _row(
    *,
    approval_id: str,
    approval_name: str,
    category: str,
    required_approval: str,
    expected_state: str,
    observed_state: str,
    decision: str,
    severity: str,
    blocked_capability: str,
    operator_action_required: str,
    go_condition: str,
    no_go_condition: str,
    evidence: str,
    recommendation: str,
    timestamp_utc: str,
) -> Dict[str, str]:
    return {
        "phase": PHASE,
        "approval_id": approval_id,
        "approval_name": approval_name,
        "category": category,
        "required_approval": required_approval,
        "expected_state": expected_state,
        "observed_state": observed_state,
        "decision": decision,
        "severity": severity,
        "manual_only": YES_TEXT,
        "external_effect": "NONE",
        "blocked_capability": blocked_capability,
        "operator_action_required": operator_action_required,
        "go_condition": go_condition,
        "no_go_condition": no_go_condition,
        "evidence": evidence,
        "recommendation": recommendation,
        "timestamp_utc": timestamp_utc,
    }


def build_ibkr_connect_dryrun_approval_packet_rows(
    *,
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    return [
        _row(
            approval_id="IBKR-CONNECT-APPROVAL-000",
            approval_name="Final approval packet decision",
            category="final_decision",
            required_approval="future_explicit_user_authorization_required",
            expected_state="approval_packet_ready_but_connection_not_allowed",
            observed_state="authorization_not_present_decision_no_go",
            decision=APPROVAL_DECISION,
            severity="CRITICAL",
            blocked_capability="IBKR_CONNECTION",
            operator_action_required=YES_TEXT,
            go_condition="none_in_this_phase",
            no_go_condition="missing_explicit_user_authorization_for_real_connect_only_attempt",
            evidence="approval_packet_generated_without_connect_command",
            recommendation="do_not_run_any_real_connection_from_this_packet",
            timestamp_utc=timestamp,
        ),
        _row(
            approval_id="IBKR-CONNECT-APPROVAL-001",
            approval_name="Prior gate lineage check",
            category="lineage_check",
            required_approval="phase517_520_and_phase521_524_artifacts_reviewed",
            expected_state="permission_gate_and_operator_runbook_exist_as_prerequisites",
            observed_state="lineage_documented_not_reclassified_as_approval",
            decision="PASS",
            severity="HIGH",
            blocked_capability="CONNECTION_APPROVAL_RECLASSIFICATION",
            operator_action_required=YES_TEXT,
            go_condition="future_operator_reviews_prior_artifacts_and_grants_explicit_connect_only_authorization",
            no_go_condition="prior_ready_labels_are_misread_as_connection_approval",
            evidence="IBKR_CONNECTION_PERMISSION_GATE_READY_and_IBKR_CONNECTION_OPERATOR_RUNBOOK_READY_are_prerequisites_only",
            recommendation="keep_prior_ready_labels_as_documentation_not_permission",
            timestamp_utc=timestamp,
        ),
        _row(
            approval_id="IBKR-CONNECT-APPROVAL-002",
            approval_name="Connect-only scope confirmation",
            category="scope_check",
            required_approval="future_approval_must_say_connect_only_disconnect_only",
            expected_state="no_market_account_positions_historical_contract_or_trading_scope",
            observed_state="connect_command_emitted_NO",
            decision="PASS",
            severity="CRITICAL",
            blocked_capability="SCOPE_EXPANSION",
            operator_action_required=YES_TEXT,
            go_condition="future_approval_mentions_only_ibkr_tws_gateway_connect_disconnect",
            no_go_condition="approval_mentions_market_data_account_positions_historical_contracts_orders_telegram_or_probe",
            evidence="status_fields_block_all_non_connection_capabilities",
            recommendation="reject_any_future_approval_text_that_expands_scope",
            timestamp_utc=timestamp,
        ),
        _row(
            approval_id="IBKR-CONNECT-APPROVAL-003",
            approval_name="Command preview withheld",
            category="command_preview",
            required_approval="no_executable_command_before_future_authorized_phase",
            expected_state="human_packet_only_no_copy_paste_command",
            observed_state="connect_command_emitted_NO",
            decision="PASS",
            severity="CRITICAL",
            blocked_capability="REAL_CONNECTION_EXECUTION",
            operator_action_required=YES_TEXT,
            go_condition="future_phase_adds_fail_closed_command_after_explicit_authorization",
            no_go_condition="any_real_connect_command_is_generated_or_printed_here",
            evidence="artifact_only_csv_and_markdown",
            recommendation="do_not_include_host_port_client_id_or_connect_invocation_in_artifacts",
            timestamp_utc=timestamp,
        ),
        _row(
            approval_id="IBKR-CONNECT-APPROVAL-004",
            approval_name="Secret and account redaction",
            category="redaction_check",
            required_approval="no_secret_token_password_account_or_authorization_value",
            expected_state="redacted_status_only",
            observed_state="no_secret_or_account_value_required",
            decision="PASS",
            severity="CRITICAL",
            blocked_capability="SECRET_OR_ACCOUNT_ID_DISCLOSURE",
            operator_action_required=YES_TEXT,
            go_condition="future_artifacts_keep_all_secret_values_out_of_stdout_csv_markdown",
            no_go_condition="any_secret_token_password_account_authorization_or_bearer_value_is_present",
            evidence="static_status_packet_without_config_read",
            recommendation="stop_and_redact_before_commit_if_any_sensitive_value_appears",
            timestamp_utc=timestamp,
        ),
        _row(
            approval_id="IBKR-CONNECT-APPROVAL-005",
            approval_name="External action kill switch",
            category="external_action_guard",
            required_approval="all_external_actions_remain_denied",
            expected_state="all_external_attempt_flags_no",
            observed_state="all_external_attempt_flags_NO",
            decision="PASS",
            severity="CRITICAL",
            blocked_capability="ALL_EXTERNAL_ACTIONS",
            operator_action_required=YES_TEXT,
            go_condition="none_in_this_phase",
            no_go_condition="any_external_connection_probe_request_read_order_cancel_rebalance_or_send_is_attempted",
            evidence="external_effect_NONE_for_all_rows",
            recommendation="treat_any_external_side_effect_as_phase_failure",
            timestamp_utc=timestamp,
        ),
        _row(
            approval_id="IBKR-CONNECT-APPROVAL-006",
            approval_name="Local readiness is not probed",
            category="local_readiness_boundary",
            required_approval="operator_may_review_local_state_manually_only",
            expected_state="no_socket_no_process_no_network_probe",
            observed_state="network_probe_attempted_NO",
            decision="PASS",
            severity="HIGH",
            blocked_capability="NETWORK_PROBE",
            operator_action_required=YES_TEXT,
            go_condition="future_operator_manually_confirms_tws_or_gateway_state_outside_artifact_generation",
            no_go_condition="tool_attempts_to_detect_tws_gateway_port_process_or_network_state",
            evidence="packet_generation_does_not_inspect_local_network_or_process_state",
            recommendation="keep_local_readiness_as_manual_checkbox_until_authorized",
            timestamp_utc=timestamp,
        ),
        _row(
            approval_id="IBKR-CONNECT-APPROVAL-007",
            approval_name="Failure closure rule",
            category="failure_closure",
            required_approval="future_attempt_must_fail_closed_without_retry",
            expected_state="auto_retry_and_escalation_disallowed",
            observed_state="failure_closure_documented_only",
            decision="PASS",
            severity="HIGH",
            blocked_capability="UNCONTROLLED_RETRY",
            operator_action_required=YES_TEXT,
            go_condition="future_phase_documents_one_attempt_disconnect_and_stop",
            no_go_condition="future_plan_allows_retry_market_data_fallback_or_scope_escalation",
            evidence="approval_packet_records_no_go_conditions",
            recommendation="future_connect_only_phase_must_stop_after_failure_and_write_local_artifact_only",
            timestamp_utc=timestamp,
        ),
        _row(
            approval_id="IBKR-CONNECT-APPROVAL-008",
            approval_name="Status label guard",
            category="state_label_guard",
            required_approval="do_not_reclassify_existing_ready_states",
            expected_state="freeze_preflight_permission_runbook_labels_preserved",
            observed_state="no_production_ready_no_real_market_verified_no_connection_approved",
            decision="PASS",
            severity="HIGH",
            blocked_capability="STATUS_RECLASSIFICATION",
            operator_action_required=NO_TEXT,
            go_condition="none_in_this_phase",
            no_go_condition="ready_label_is_rewritten_as_production_verified_or_approved",
            evidence="POST_MVP_MULTI_MARKET_FREEZE_READY_REAL_MARKET_ENV_READINESS_PREFLIGHT_READY_IBKR_CONNECTION_PERMISSION_GATE_READY_preserved",
            recommendation="do_not_treat_this_packet_as_production_or_real_market_validation",
            timestamp_utc=timestamp,
        ),
    ]


def write_ibkr_connect_dryrun_approval_packet_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_ibkr_connect_dryrun_approval_packet_report(rows: Sequence[Dict[str, str]]) -> str:
    status_lines = [f"- {field}={STATUS_VALUES[field]}" for field in STATUS_FIELDS]
    approval_lines = [
        f"- {row['approval_id']} {row['approval_name']}: decision={row['decision']} / required={row['required_approval']}"
        for row in rows
        if row["category"] in {"final_decision", "lineage_check", "scope_check"}
    ]
    no_go_lines = [
        f"- {row['approval_id']} {row['no_go_condition']}"
        for row in rows
        if row["severity"] == "CRITICAL"
    ]
    guard_lines = [
        f"- {row['approval_id']} {row['approval_name']}: blocks={row['blocked_capability']} / evidence={row['evidence']}"
        for row in rows
        if row["category"] in {"command_preview", "redaction_check", "external_action_guard", "local_readiness_boundary", "state_label_guard"}
    ]

    lines = [
        "# Phase 525-528 IBKR Connect Dry-Run Approval Packet",
        "",
        "## Final Decision",
        "",
        *status_lines,
        "",
        "NO_GO is the safe default for this phase. This packet is an approval artifact, not authorization to connect.",
        "",
        "## Scope Boundary",
        "",
        "- manual approval packet for a possible future connect-only dry-run",
        "- no executable connection command is generated or printed",
        "- no local readiness probe is performed",
        "- no secret, token, password, authorization header, or account id value is read or written",
        "- POST_MVP_MULTI_MARKET_FREEZE_READY remains unchanged and is not reclassified as production-ready",
        "- REAL_MARKET_ENV_READINESS_PREFLIGHT_READY remains unchanged and is not reclassified as real-market-data-verified",
        "- IBKR_CONNECTION_PERMISSION_GATE_READY remains unchanged and is not reclassified as connection-approved",
        "- IBKR_CONNECTION_OPERATOR_RUNBOOK_READY remains unchanged and is not reclassified as operator-approved",
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
        "## Approval Packet",
        "",
        *approval_lines,
        "",
        "## No-Go Conditions",
        "",
        *no_go_lines,
        "",
        "## Guard Checks",
        "",
        *guard_lines,
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_ibkr_connect_dryrun_approval_packet.csv",
        "- report=reports/operator_ibkr_connect_dryrun_approval_packet_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Residual Risks",
        "",
        "- this packet does not prove IBKR connectivity",
        "- this packet does not prove TWS or IB Gateway availability",
        "- this packet does not prove market data entitlement",
        "- this packet does not prove account, position, historical data, contract qualification, order, cancel, rebalance, or Telegram behavior",
        "",
        "## Next Phase Preconditions",
        "",
        "- explicit user authorization naming a connect-only dry-run",
        "- a separate fail-closed implementation reviewed before any real connection",
        "- no market data, account, positions, historical data, contract qualification, order, cancel, rebalance, Telegram real send, or network probe unless separately approved",
        "- no automatic transition from this approval packet to any connection-approved state",
    ]
    return "\n".join(lines) + "\n"


def write_ibkr_connect_dryrun_approval_packet_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_ibkr_connect_dryrun_approval_packet_report(rows), encoding="utf-8")


def generate_ibkr_connect_dryrun_approval_packet(
    *,
    output_csv: PathLike = "operator_ibkr_connect_dryrun_approval_packet.csv",
    output_report: PathLike = "reports/operator_ibkr_connect_dryrun_approval_packet_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_ibkr_connect_dryrun_approval_packet_rows(generated_at=generated_at)
    write_ibkr_connect_dryrun_approval_packet_csv(output_csv, rows)
    write_ibkr_connect_dryrun_approval_packet_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 525-528 IBKR connect dry-run approval packet.")
    parser.add_argument("--output-csv", default="operator_ibkr_connect_dryrun_approval_packet.csv")
    parser.add_argument("--output-report", default="reports/operator_ibkr_connect_dryrun_approval_packet_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_ibkr_connect_dryrun_approval_packet(
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[IBKR_CONNECT_DRYRUN_APPROVAL_PACKET] generated")
    for field in STATUS_FIELDS:
        print(f"{field}={STATUS_VALUES[field]}")
    print(f"approvals={len(rows)}")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    print(
        "NOTICE: Phase 525-528 approval packet artifacts only. No IBKR/TWS/Gateway connection, "
        "no network probe, no market data request, no account reads, no position reads, "
        "no historical data request, no contract qualification, no orders, no cancellation, "
        "no rebalance, no Telegram real send, and no connect command is emitted."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
