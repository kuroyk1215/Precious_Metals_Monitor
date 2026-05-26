from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


PHASE = "Phase 529-532"
EXECUTION_SKELETON_STATUS = "IBKR_CONNECT_EXECUTION_SKELETON_REVIEW_READY"
FINAL_DECISION = "NO_GO"
YES_TEXT = "YES"
NO_TEXT = "NO"

CSV_FIELDS = (
    "phase",
    "review_id",
    "review_name",
    "category",
    "required_state",
    "observed_state",
    "status",
    "severity",
    "manual_only",
    "external_effect",
    "blocked_capability",
    "operator_action_required",
    "skeleton_rule",
    "failure_response",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

STATUS_FIELDS = (
    "execution_skeleton_status",
    "final_decision",
    "operator_approval_required",
    "connection_allowed",
    "execute_cli_present",
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
    "next_phase_execute_candidate",
)

STATUS_VALUES = {
    "execution_skeleton_status": EXECUTION_SKELETON_STATUS,
    "final_decision": FINAL_DECISION,
    "operator_approval_required": YES_TEXT,
    "connection_allowed": NO_TEXT,
    "execute_cli_present": NO_TEXT,
    "connect_command_emitted": NO_TEXT,
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
    "next_phase_execute_candidate": YES_TEXT,
}

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _row(
    *,
    review_id: str,
    review_name: str,
    category: str,
    required_state: str,
    observed_state: str,
    status: str,
    severity: str,
    blocked_capability: str,
    operator_action_required: str,
    skeleton_rule: str,
    failure_response: str,
    evidence: str,
    recommendation: str,
    timestamp_utc: str,
) -> Dict[str, str]:
    return {
        "phase": PHASE,
        "review_id": review_id,
        "review_name": review_name,
        "category": category,
        "required_state": required_state,
        "observed_state": observed_state,
        "status": status,
        "severity": severity,
        "manual_only": YES_TEXT,
        "external_effect": "NONE",
        "blocked_capability": blocked_capability,
        "operator_action_required": operator_action_required,
        "skeleton_rule": skeleton_rule,
        "failure_response": failure_response,
        "evidence": evidence,
        "recommendation": recommendation,
        "timestamp_utc": timestamp_utc,
    }


def build_ibkr_connect_execution_skeleton_review_rows(
    *,
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    return [
        _row(
            review_id="IBKR-CONNECT-SKELETON-000",
            review_name="Final skeleton review decision",
            category="final_decision",
            required_state="future_explicit_authorization_before_any_execute_cli",
            observed_state="execute_cli_present_NO_connection_allowed_NO",
            status=FINAL_DECISION,
            severity="CRITICAL",
            blocked_capability="IBKR_CONNECTION",
            operator_action_required=YES_TEXT,
            skeleton_rule="review_only_no_execute_path",
            failure_response="stop_before_any_connection_attempt",
            evidence="execution_skeleton_review_generated_without_connect_command",
            recommendation="do_not_treat_this_review_as_authorization_to_connect",
            timestamp_utc=timestamp,
        ),
        _row(
            review_id="IBKR-CONNECT-SKELETON-001",
            review_name="Execute CLI intentionally absent",
            category="execute_cli_guard",
            required_state="no_execute_flag_no_connect_command_no_copy_paste_command",
            observed_state="execute_cli_present_NO",
            status="PASS",
            severity="CRITICAL",
            blocked_capability="REAL_CONNECTION_EXECUTION",
            operator_action_required=YES_TEXT,
            skeleton_rule="future_execute_cli_requires_new_user_authorization",
            failure_response="remove_command_preview_and_revert_to_artifact_only_packet",
            evidence="cli_generates_csv_and_markdown_only",
            recommendation="add_execute_path_only_in_a_later_explicitly_authorized_phase",
            timestamp_utc=timestamp,
        ),
        _row(
            review_id="IBKR-CONNECT-SKELETON-002",
            review_name="Connect-only scope lock",
            category="scope_guard",
            required_state="future_scope_may_only_connect_disconnect_if_authorized",
            observed_state="all_non_connection_capabilities_blocked",
            status="PASS",
            severity="CRITICAL",
            blocked_capability="MARKET_ACCOUNT_POSITIONS_HISTORICAL_CONTRACTS_TRADING_TELEGRAM",
            operator_action_required=YES_TEXT,
            skeleton_rule="no_market_data_no_account_no_positions_no_historical_no_contracts_no_orders_no_send",
            failure_response="reject_any_scope_expansion_and_stop",
            evidence="all_external_attempt_flags_NO",
            recommendation="future_execute_candidate_must_not_chain_to_any_data_or_action_request",
            timestamp_utc=timestamp,
        ),
        _row(
            review_id="IBKR-CONNECT-SKELETON-003",
            review_name="No local readiness probe",
            category="probe_guard",
            required_state="no_socket_process_port_or_network_probe",
            observed_state="network_probe_attempted_NO",
            status="PASS",
            severity="HIGH",
            blocked_capability="NETWORK_PROBE",
            operator_action_required=YES_TEXT,
            skeleton_rule="operator_readiness_check_remains_manual",
            failure_response="remove_probe_code_and_regenerate_artifacts",
            evidence="static_artifact_generation_only",
            recommendation="keep_local_tws_gateway_status_outside_automation_until_authorized",
            timestamp_utc=timestamp,
        ),
        _row(
            review_id="IBKR-CONNECT-SKELETON-004",
            review_name="Secret and config boundary",
            category="redaction_guard",
            required_state="no_secret_token_password_account_or_config_mutation",
            observed_state="no_secret_values_required_config_not_modified",
            status="PASS",
            severity="CRITICAL",
            blocked_capability="SECRET_OR_ACCOUNT_ID_DISCLOSURE",
            operator_action_required=YES_TEXT,
            skeleton_rule="do_not_read_or_write_secret_values",
            failure_response="stop_redact_restore_unintended_artifacts_before_commit",
            evidence="status_packet_without_secret_material",
            recommendation="do_not_commit_config_yaml_or_sensitive_runtime_outputs",
            timestamp_utc=timestamp,
        ),
        _row(
            review_id="IBKR-CONNECT-SKELETON-005",
            review_name="Fail-closed behavior contract",
            category="failure_contract",
            required_state="future_execute_attempt_stops_after_one_failure_without_retry",
            observed_state="failure_contract_documented_only",
            status="PASS",
            severity="HIGH",
            blocked_capability="UNCONTROLLED_RETRY_OR_ESCALATION",
            operator_action_required=YES_TEXT,
            skeleton_rule="one_attempt_disconnect_stop_if_future_authorized",
            failure_response="write_local_artifact_only_and_do_not_retry",
            evidence="no_runtime_connector_present",
            recommendation="future_execute_candidate_must_not_auto_retry_or_fallback_to_data_requests",
            timestamp_utc=timestamp,
        ),
        _row(
            review_id="IBKR-CONNECT-SKELETON-006",
            review_name="Status label guard",
            category="state_label_guard",
            required_state="do_not_reclassify_ready_labels_as_approval",
            observed_state="prior_ready_labels_preserved_without_connection_approval",
            status="PASS",
            severity="HIGH",
            blocked_capability="STATUS_RECLASSIFICATION",
            operator_action_required=NO_TEXT,
            skeleton_rule="ready_means_artifact_ready_only",
            failure_response="revert_misleading_text_before_commit",
            evidence="POST_MVP_MULTI_MARKET_FREEZE_READY_REAL_MARKET_ENV_READINESS_PREFLIGHT_READY_IBKR_CONNECTION_PERMISSION_GATE_READY_preserved",
            recommendation="do_not_claim_production_ready_real_market_data_verified_or_connection_approved",
            timestamp_utc=timestamp,
        ),
    ]


def write_ibkr_connect_execution_skeleton_review_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_ibkr_connect_execution_skeleton_review_report(rows: Sequence[Dict[str, str]]) -> str:
    status_lines = [f"- {field}={STATUS_VALUES[field]}" for field in STATUS_FIELDS]
    review_lines = [
        f"- {row['review_id']} {row['review_name']}: {row['status']} / blocks={row['blocked_capability']}"
        for row in rows
    ]
    failure_lines = [
        f"- {row['review_id']} {row['failure_response']}"
        for row in rows
        if row["operator_action_required"] == YES_TEXT
    ]
    lines = [
        "# Phase 529-532 IBKR Connect Execution Skeleton Review",
        "",
        "## Final Decision",
        "",
        *status_lines,
        "",
        "NO_GO is the safe default. This phase reviews an execution skeleton boundary but does not add execution.",
        "",
        "## Scope Boundary",
        "",
        "- artifact-only skeleton review for a possible future connect-only execute CLI",
        "- no execute flag, connect command, socket probe, or local environment probe is generated",
        "- no secret, token, password, authorization header, or account id value is read or written",
        "- prior readiness labels remain artifact-ready only and are not connection approval",
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
        "- order submission or cancellation",
        "- rebalance action",
        "- Telegram real send",
        "",
        "## Skeleton Review",
        "",
        *review_lines,
        "",
        "## Failure Responses",
        "",
        *failure_lines,
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_ibkr_connect_execution_skeleton_review.csv",
        "- report=reports/operator_ibkr_connect_execution_skeleton_review_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Residual Risks",
        "",
        "- this review does not prove IBKR connectivity",
        "- this review does not prove TWS or IB Gateway availability",
        "- this review does not prove market data entitlement",
        "- this review does not prove account, position, historical data, contract qualification, order, cancel, rebalance, or Telegram behavior",
        "",
        "## Next Phase Preconditions",
        "",
        "- explicit user authorization before any execute CLI or real connection path is added",
        "- reviewed fail-closed implementation that emits no market/account/position/historical/contract/order/Telegram requests",
        "- no automatic transition from this skeleton review to any connection-approved state",
    ]
    return "\n".join(lines) + "\n"


def write_ibkr_connect_execution_skeleton_review_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_ibkr_connect_execution_skeleton_review_report(rows), encoding="utf-8")


def generate_ibkr_connect_execution_skeleton_review(
    *,
    output_csv: PathLike = "operator_ibkr_connect_execution_skeleton_review.csv",
    output_report: PathLike = "reports/operator_ibkr_connect_execution_skeleton_review_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_ibkr_connect_execution_skeleton_review_rows(generated_at=generated_at)
    write_ibkr_connect_execution_skeleton_review_csv(output_csv, rows)
    write_ibkr_connect_execution_skeleton_review_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 529-532 IBKR connect execution skeleton review.")
    parser.add_argument("--output-csv", default="operator_ibkr_connect_execution_skeleton_review.csv")
    parser.add_argument("--output-report", default="reports/operator_ibkr_connect_execution_skeleton_review_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_ibkr_connect_execution_skeleton_review(
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[IBKR_CONNECT_EXECUTION_SKELETON_REVIEW] generated")
    for field in STATUS_FIELDS:
        print(f"{field}={STATUS_VALUES[field]}")
    print(f"reviews={len(rows)}")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    print(
        "NOTICE: Phase 529-532 execution skeleton review artifacts only. No execute CLI, no IBKR/TWS/Gateway "
        "connection, no network probe, no market data request, no account reads, no position reads, "
        "no historical data request, no contract qualification, no orders, no cancellation, "
        "no rebalance, and no Telegram real send."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
