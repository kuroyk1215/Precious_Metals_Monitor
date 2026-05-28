from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


PHASE = "Phase 545-548"
GATE_STATUS = "CONTRACT_QUALIFICATION_PERMISSION_GATE_READY"
PERMISSION_DECISION = "DENIED"
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
    "contract_qualification_allowed",
    "external_effect",
    "blocked_capability",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

STATUS_FIELDS = (
    "contract_qualification_permission_decision",
    "qualification_permission_gate_status",
    "operator_authorization_required",
    "contract_qualification_allowed",
    "external_connections_attempted",
    "ibkr_connected",
    "market_data_requested",
    "account_read_attempted",
    "positions_read_attempted",
    "historical_data_requested",
    "contract_qualification_attempted",
    "orders_submitted",
    "telegram_real_send_attempted",
    "next_phase_single_symbol_qualification_candidate",
)

STATUS_VALUES = {
    "contract_qualification_permission_decision": PERMISSION_DECISION,
    "qualification_permission_gate_status": GATE_STATUS,
    "operator_authorization_required": YES_TEXT,
    "contract_qualification_allowed": NO_TEXT,
    "external_connections_attempted": NO_TEXT,
    "ibkr_connected": NO_TEXT,
    "market_data_requested": NO_TEXT,
    "account_read_attempted": NO_TEXT,
    "positions_read_attempted": NO_TEXT,
    "historical_data_requested": NO_TEXT,
    "contract_qualification_attempted": NO_TEXT,
    "orders_submitted": NO_TEXT,
    "telegram_real_send_attempted": NO_TEXT,
    "next_phase_single_symbol_qualification_candidate": YES_TEXT,
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
        "contract_qualification_allowed": NO_TEXT,
        "external_effect": "NONE",
        "blocked_capability": blocked_capability,
        "evidence": evidence,
        "recommendation": recommendation,
        "timestamp_utc": timestamp_utc,
    }


def build_contract_qualification_permission_gate_rows(
    *,
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    return [
        _row(
            gate_id="CONTRACT-QUALIFICATION-GATE-000",
            gate_name="Final permission decision",
            category="final_decision",
            required_state="deny_contract_qualification_until_separate_operator_authorization",
            observed_state="contract_qualification_permission_decision_DENIED",
            result=PERMISSION_DECISION,
            severity="CRITICAL",
            approval_required=YES_TEXT,
            blocked_capability="CONTRACT_QUALIFICATION_EXECUTION",
            evidence="permission_gate_artifact_generated_without_qualification_path",
            recommendation="do_not_qualify_any_contract_until_later_explicit_authorization",
            timestamp_utc=timestamp,
        ),
        _row(
            gate_id="CONTRACT-QUALIFICATION-GATE-001",
            gate_name="Operator authorization gate",
            category="authorization_gate",
            required_state="human_operator_authorization_required_before_any_single_symbol_qualification",
            observed_state="operator_authorization_required_YES_contract_qualification_allowed_NO",
            result="PASS",
            severity="CRITICAL",
            approval_required=YES_TEXT,
            blocked_capability="UNAUTHORIZED_CONTRACT_QUALIFICATION",
            evidence="authorization_required_and_allowed_flags_fail_closed",
            recommendation="collect explicit next-phase authorization before adding or running qualification code",
            timestamp_utc=timestamp,
        ),
        _row(
            gate_id="CONTRACT-QUALIFICATION-GATE-002",
            gate_name="Single-symbol scope boundary",
            category="scope_boundary",
            required_state="future_candidate_must_be_single_symbol_contract_qualification_only",
            observed_state="candidate_scope_recorded_without_execution",
            result="PASS",
            severity="HIGH",
            approval_required=YES_TEXT,
            blocked_capability="MULTI_SYMBOL_OR_CHAINED_REQUESTS",
            evidence="next_phase_single_symbol_qualification_candidate_YES_only",
            recommendation="future phase must define one symbol and stop before market data account positions or trading actions",
            timestamp_utc=timestamp,
        ),
        _row(
            gate_id="CONTRACT-QUALIFICATION-GATE-003",
            gate_name="No connection or external request",
            category="external_effect_guard",
            required_state="no_ibkr_connection_no_network_probe_no_external_request",
            observed_state="external_connections_attempted_NO_ibkr_connected_NO",
            result="PASS",
            severity="CRITICAL",
            approval_required=YES_TEXT,
            blocked_capability="NETWORK_OR_IBKR_SIDE_EFFECT",
            evidence="artifact_only_generation_no_connector_imports_or_probe_code",
            recommendation="keep all qualification readiness checks local until separately approved",
            timestamp_utc=timestamp,
        ),
        _row(
            gate_id="CONTRACT-QUALIFICATION-GATE-004",
            gate_name="Data access guard",
            category="data_access_guard",
            required_state="no_market_data_account_positions_or_historical_requests",
            observed_state="market_data_account_positions_historical_flags_NO",
            result="PASS",
            severity="CRITICAL",
            approval_required=YES_TEXT,
            blocked_capability="IBKR_DATA_ACCESS",
            evidence="no_data_request_path_present_in_this_artifact",
            recommendation="future qualification candidate must not request market data historical data account or positions",
            timestamp_utc=timestamp,
        ),
        _row(
            gate_id="CONTRACT-QUALIFICATION-GATE-005",
            gate_name="Qualification execution guard",
            category="qualification_guard",
            required_state="no_real_contract_qualification_attempt",
            observed_state="contract_qualification_attempted_NO",
            result="PASS",
            severity="CRITICAL",
            approval_required=YES_TEXT,
            blocked_capability="REAL_CONTRACT_QUALIFICATION",
            evidence="contract_qualification_allowed_NO_and_attempted_NO",
            recommendation="do_not_treat_ibkr_connectivity_archive_as_contract_qualification_evidence",
            timestamp_utc=timestamp,
        ),
        _row(
            gate_id="CONTRACT-QUALIFICATION-GATE-006",
            gate_name="Order and notification guard",
            category="action_guard",
            required_state="no_order_submit_cancel_rebalance_or_telegram_real_send",
            observed_state="orders_submitted_NO_telegram_real_send_attempted_NO",
            result="PASS",
            severity="CRITICAL",
            approval_required=YES_TEXT,
            blocked_capability="TRADING_OR_REAL_NOTIFICATION",
            evidence="artifact_contains_no_trading_or_real_send_execution_path",
            recommendation="do_not_attach_trading_cancellation_rebalance_or_real_send_behavior_to_qualification",
            timestamp_utc=timestamp,
        ),
        _row(
            gate_id="CONTRACT-QUALIFICATION-GATE-007",
            gate_name="Secret and status label guard",
            category="redaction_and_label_guard",
            required_state="no_sensitive_output_and_no_production_ready_reclassification",
            observed_state="static_gate_values_only_no_runtime_sensitive_values",
            result="PASS",
            severity="HIGH",
            approval_required=NO_TEXT,
            blocked_capability="SECRET_DISCLOSURE_OR_MISLEADING_STATUS",
            evidence="config_yaml_not_required_or_modified_by_generator",
            recommendation="do_not_commit_config_or_reclassify_connectivity_as_qualification_verified",
            timestamp_utc=timestamp,
        ),
    ]


def write_contract_qualification_permission_gate_csv(
    path: PathLike, rows: Sequence[Dict[str, str]]
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_contract_qualification_permission_gate_report(rows: Sequence[Dict[str, str]]) -> str:
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
        "- real contract qualification",
        "- order submission or cancellation",
        "- rebalance action",
        "- Telegram real send",
    ]
    lines = [
        "# Phase 545-548 Contract Qualification Permission Gate",
        "",
        "## Final Decision",
        "",
        *status_lines,
        "",
        "The contract qualification permission decision is denied for this artifact-only phase.",
        "",
        "## Scope Boundary",
        "",
        "- artifact-only permission gate for a possible later single-symbol qualification candidate",
        "- this phase does not add or approve a real qualification path",
        "- prior IBKR connectivity evidence remains connectivity-only and does not verify contract qualification",
        "- ready status means this permission gate artifact is ready only",
        "",
        "## Explicitly Prohibited Actions",
        "",
        *prohibited_actions,
        "",
        "## Qualification Permission Gates",
        "",
        *gate_lines,
        "",
        "## Operator Authorization Requirements",
        "",
        "- explicit operator authorization is required before any real single-symbol contract qualification",
        "- authorization must be separate from prior connection result archive evidence",
        "- no status in this packet authorizes contract qualification execution",
        "",
        "## Single-Symbol Preconditions",
        "",
        "- future candidate must name exactly one symbol and one intended contract profile",
        "- future candidate must fail closed if authorization, symbol, exchange, currency, or instrument type is ambiguous",
        "- future candidate must not request market data, historical data, account, positions, orders, cancellations, rebalances, or Telegram sends",
        "- future candidate must not print secret material or account identifiers",
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_contract_qualification_permission_gate.csv",
        "- report=reports/operator_contract_qualification_permission_gate_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Residual Risks",
        "",
        "- this gate does not prove contract qualification access",
        "- this gate does not prove market data entitlement, account visibility, positions visibility, historical data access, trading readiness, or production readiness",
        "- future phases still require explicit gates before any external action",
        "",
        "## Next Phase Preconditions",
        "",
        "- explicit user authorization for a single-symbol qualification candidate",
        "- reviewed implementation that emits no market data, historical data, account, positions, order, cancel, rebalance, or Telegram request",
        "- no automatic transition from this permission gate to production-ready status",
    ]
    return "\n".join(lines) + "\n"


def write_contract_qualification_permission_gate_report(
    path: PathLike, rows: Sequence[Dict[str, str]]
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_contract_qualification_permission_gate_report(rows), encoding="utf-8")


def generate_contract_qualification_permission_gate(
    *,
    output_csv: PathLike = "operator_contract_qualification_permission_gate.csv",
    output_report: PathLike = "reports/operator_contract_qualification_permission_gate_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_contract_qualification_permission_gate_rows(generated_at=generated_at)
    write_contract_qualification_permission_gate_csv(output_csv, rows)
    write_contract_qualification_permission_gate_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 545-548 contract qualification permission gate.")
    parser.add_argument("--output-csv", default="operator_contract_qualification_permission_gate.csv")
    parser.add_argument(
        "--output-report",
        default="reports/operator_contract_qualification_permission_gate_report.md",
    )
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_contract_qualification_permission_gate(
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[CONTRACT_QUALIFICATION_PERMISSION_GATE] generated")
    for field in STATUS_FIELDS:
        print(f"{field}={STATUS_VALUES[field]}")
    print(f"gates={len(rows)}")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
