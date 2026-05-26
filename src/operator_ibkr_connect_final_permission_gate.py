from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


PHASE = "Phase 533-536"
FINAL_PERMISSION_GATE_STATUS = "IBKR_CONNECT_FINAL_PERMISSION_GATE_READY"
CONNECT_EXECUTION_PERMISSION_DECISION = "DENIED"
YES_TEXT = "YES"
NO_TEXT = "NO"

CSV_FIELDS = (
    "phase",
    "gate_id",
    "gate_name",
    "category",
    "required_state",
    "observed_state",
    "result",
    "severity",
    "fail_closed",
    "approval_required",
    "operator_authorization_required",
    "connect_execution_allowed",
    "external_effect",
    "blocked_capability",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

STATUS_FIELDS = (
    "connect_execution_permission_decision",
    "final_permission_gate_status",
    "operator_authorization_required",
    "connect_execution_allowed",
    "connection_allowed",
    "external_connections_attempted",
    "ibkr_connected",
    "network_probe_attempted",
    "market_data_requested",
    "account_read_attempted",
    "positions_read_attempted",
    "historical_data_requested",
    "contract_qualification_attempted",
    "orders_submitted",
    "telegram_real_send_attempted",
    "next_phase_connect_only_execute_candidate",
)

STATUS_VALUES = {
    "connect_execution_permission_decision": CONNECT_EXECUTION_PERMISSION_DECISION,
    "final_permission_gate_status": FINAL_PERMISSION_GATE_STATUS,
    "operator_authorization_required": YES_TEXT,
    "connect_execution_allowed": NO_TEXT,
    "connection_allowed": NO_TEXT,
    "external_connections_attempted": NO_TEXT,
    "ibkr_connected": NO_TEXT,
    "network_probe_attempted": NO_TEXT,
    "market_data_requested": NO_TEXT,
    "account_read_attempted": NO_TEXT,
    "positions_read_attempted": NO_TEXT,
    "historical_data_requested": NO_TEXT,
    "contract_qualification_attempted": NO_TEXT,
    "orders_submitted": NO_TEXT,
    "telegram_real_send_attempted": NO_TEXT,
    "next_phase_connect_only_execute_candidate": YES_TEXT,
}

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _row(
    *,
    gate_id: str,
    gate_name: str,
    category: str,
    required_state: str,
    observed_state: str,
    result: str,
    severity: str,
    approval_required: str,
    blocked_capability: str,
    evidence: str,
    recommendation: str,
    timestamp_utc: str,
) -> Dict[str, str]:
    return {
        "phase": PHASE,
        "gate_id": gate_id,
        "gate_name": gate_name,
        "category": category,
        "required_state": required_state,
        "observed_state": observed_state,
        "result": result,
        "severity": severity,
        "fail_closed": YES_TEXT,
        "approval_required": approval_required,
        "operator_authorization_required": YES_TEXT,
        "connect_execution_allowed": NO_TEXT,
        "external_effect": "NONE",
        "blocked_capability": blocked_capability,
        "evidence": evidence,
        "recommendation": recommendation,
        "timestamp_utc": timestamp_utc,
    }


def build_ibkr_connect_final_permission_gate_rows(
    *,
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    return [
        _row(
            gate_id="IBKR-CONNECT-FINAL-GATE-000",
            gate_name="Final permission decision",
            category="final_decision",
            required_state="deny_connect_execution_until_separate_operator_authorization",
            observed_state="connect_execution_permission_decision_DENIED",
            result=CONNECT_EXECUTION_PERMISSION_DECISION,
            severity="CRITICAL",
            approval_required=YES_TEXT,
            blocked_capability="IBKR_CONNECTION_EXECUTION",
            evidence="final_permission_gate_artifact_generated_without_connection_path",
            recommendation="do_not_execute_connect_only_dry_run_until_later_explicit_authorization",
            timestamp_utc=timestamp,
        ),
        _row(
            gate_id="IBKR-CONNECT-FINAL-GATE-001",
            gate_name="Operator authorization gate",
            category="authorization_gate",
            required_state="human_operator_authorization_required_before_any_real_connect",
            observed_state="operator_authorization_required_YES_connect_execution_allowed_NO",
            result="PASS",
            severity="CRITICAL",
            approval_required=YES_TEXT,
            blocked_capability="UNAUTHORIZED_CONNECT_EXECUTION",
            evidence="operator_authorization_required_flag_is_yes_and_allowed_flags_are_no",
            recommendation="collect explicit next-phase authorization before adding or running an execute path",
            timestamp_utc=timestamp,
        ),
        _row(
            gate_id="IBKR-CONNECT-FINAL-GATE-002",
            gate_name="Connect-only scope boundary",
            category="scope_boundary",
            required_state="future_authorized_action_may_only_connect_disconnect",
            observed_state="market_account_positions_historical_contract_order_telegram_capabilities_blocked",
            result="PASS",
            severity="CRITICAL",
            approval_required=YES_TEXT,
            blocked_capability="MARKET_ACCOUNT_POSITIONS_HISTORICAL_CONTRACTS_TRADING_TELEGRAM",
            evidence="all_external_effect_status_values_are_NO",
            recommendation="reject any future dry-run that chains data requests or trading actions",
            timestamp_utc=timestamp,
        ),
        _row(
            gate_id="IBKR-CONNECT-FINAL-GATE-003",
            gate_name="No connection or network probe",
            category="external_effect_guard",
            required_state="no_ibkr_connection_no_socket_probe_no_http_probe",
            observed_state="external_connections_attempted_NO_network_probe_attempted_NO_ibkr_connected_NO",
            result="PASS",
            severity="CRITICAL",
            approval_required=YES_TEXT,
            blocked_capability="NETWORK_OR_IBKR_SIDE_EFFECT",
            evidence="artifact_only_generation_no_connector_imports_or_probe_code",
            recommendation="keep local readiness checks manual until a separately approved execute phase",
            timestamp_utc=timestamp,
        ),
        _row(
            gate_id="IBKR-CONNECT-FINAL-GATE-004",
            gate_name="Read and request guard",
            category="data_access_guard",
            required_state="no_market_data_account_positions_historical_or_contract_requests",
            observed_state="market_data_account_positions_historical_contract_flags_NO",
            result="PASS",
            severity="CRITICAL",
            approval_required=YES_TEXT,
            blocked_capability="IBKR_DATA_ACCESS",
            evidence="no_data_request_or_contract_qualification_path_present",
            recommendation="future connect-only run must stop before any IBKR data access call",
            timestamp_utc=timestamp,
        ),
        _row(
            gate_id="IBKR-CONNECT-FINAL-GATE-005",
            gate_name="Order and Telegram guard",
            category="action_guard",
            required_state="no_order_submit_cancel_rebalance_or_telegram_real_send",
            observed_state="orders_submitted_NO_telegram_real_send_attempted_NO",
            result="PASS",
            severity="CRITICAL",
            approval_required=YES_TEXT,
            blocked_capability="TRADING_OR_REAL_NOTIFICATION",
            evidence="artifact_contains_no_trading_or_real_send_execution_path",
            recommendation="do not attach trading cancellation rebalance or real send behavior to connect-only dry-run",
            timestamp_utc=timestamp,
        ),
        _row(
            gate_id="IBKR-CONNECT-FINAL-GATE-006",
            gate_name="Secret and account redaction boundary",
            category="redaction_guard",
            required_state="no_secret_token_password_or_account_identifier_output",
            observed_state="no_sensitive_runtime_values_required_or_written",
            result="PASS",
            severity="CRITICAL",
            approval_required=YES_TEXT,
            blocked_capability="SECRET_OR_ACCOUNT_DISCLOSURE",
            evidence="static_gate_values_only_config_yaml_not_modified",
            recommendation="do_not_commit_config_or_sensitive_runtime_outputs",
            timestamp_utc=timestamp,
        ),
        _row(
            gate_id="IBKR-CONNECT-FINAL-GATE-007",
            gate_name="Status reclassification guard",
            category="state_label_guard",
            required_state="do_not_claim_production_ready_or_real_market_data_verified",
            observed_state="final_gate_ready_means_artifact_ready_only",
            result="PASS",
            severity="HIGH",
            approval_required=NO_TEXT,
            blocked_capability="MISLEADING_STATUS_RECLASSIFICATION",
            evidence="connect_execution_permission_decision_DENIED",
            recommendation="do_not_treat_skeleton_review_or_this_gate_as_actual_connection_approval",
            timestamp_utc=timestamp,
        ),
    ]


def write_ibkr_connect_final_permission_gate_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_ibkr_connect_final_permission_gate_report(rows: Sequence[Dict[str, str]]) -> str:
    status_lines = [f"- {field}={STATUS_VALUES[field]}" for field in STATUS_FIELDS]
    gate_lines = [
        f"- {row['gate_id']} {row['gate_name']}: {row['result']} / blocks={row['blocked_capability']}"
        for row in rows
    ]
    prohibited_actions = [
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
    ]
    lines = [
        "# Phase 533-536 IBKR Connect Final Permission Gate",
        "",
        "## Final Decision",
        "",
        *status_lines,
        "",
        "The connect-only execution decision is denied for this artifact-only phase.",
        "",
        "## Scope Boundary",
        "",
        "- final human authorization gate for a possible later first real read-only connect-only dry-run",
        "- this phase does not add or approve an execution path",
        "- skeleton review remains a review artifact, not actual connection approval",
        "- ready status means this permission gate artifact is ready only",
        "",
        "## Explicitly Prohibited Actions",
        "",
        *prohibited_actions,
        "",
        "## Final Permission Gates",
        "",
        *gate_lines,
        "",
        "## Operator Authorization Requirements",
        "",
        "- explicit operator authorization is required before any real connect-only execution",
        "- authorization must be separate from prior readiness, runbook, approval packet, or skeleton review artifacts",
        "- no status in this packet authorizes connection execution",
        "",
        "## Connect-Only Preconditions",
        "",
        "- future candidate must be limited to connect and disconnect only",
        "- future candidate must fail closed after one failed attempt",
        "- future candidate must not request data, qualify contracts, trade, cancel, rebalance, or send Telegram messages",
        "- future candidate must not read or print secret material or account identifiers",
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_ibkr_connect_final_permission_gate.csv",
        "- report=reports/operator_ibkr_connect_final_permission_gate_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Residual Risks",
        "",
        "- this gate does not prove IBKR connectivity",
        "- this gate does not prove TWS or IB Gateway availability",
        "- this gate does not prove market data entitlement",
        "- this gate does not prove account, position, historical data, contract qualification, order, cancel, rebalance, or Telegram behavior",
        "",
        "## Next Phase Preconditions",
        "",
        "- explicit user authorization for a connect-only execute candidate",
        "- reviewed implementation that emits no market, account, position, historical, contract, order, cancel, rebalance, or Telegram request",
        "- no automatic transition from this final permission gate to production-ready or real-market-data-verified status",
    ]
    return "\n".join(lines) + "\n"


def write_ibkr_connect_final_permission_gate_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_ibkr_connect_final_permission_gate_report(rows), encoding="utf-8")


def generate_ibkr_connect_final_permission_gate(
    *,
    output_csv: PathLike = "operator_ibkr_connect_final_permission_gate.csv",
    output_report: PathLike = "reports/operator_ibkr_connect_final_permission_gate_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_ibkr_connect_final_permission_gate_rows(generated_at=generated_at)
    write_ibkr_connect_final_permission_gate_csv(output_csv, rows)
    write_ibkr_connect_final_permission_gate_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 533-536 IBKR connect final permission gate.")
    parser.add_argument("--output-csv", default="operator_ibkr_connect_final_permission_gate.csv")
    parser.add_argument("--output-report", default="reports/operator_ibkr_connect_final_permission_gate_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_ibkr_connect_final_permission_gate(
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[IBKR_CONNECT_FINAL_PERMISSION_GATE] generated")
    for field in STATUS_FIELDS:
        print(f"{field}={STATUS_VALUES[field]}")
    print(f"gates={len(rows)}")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    print(
        "NOTICE: Phase 533-536 final permission gate artifacts only. No IBKR/TWS/Gateway connection, "
        "no network probe, no market data request, no account reads, no position reads, no historical data "
        "request, no contract qualification, no orders, no cancellation, no rebalance, no Telegram real send, "
        "and no production-ready or real-market-data-verified reclassification."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
