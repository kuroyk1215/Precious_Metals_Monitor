from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


PHASE = "Phase 517-520"
CONNECTION_PERMISSION_DECISION = "DENIED"
PERMISSION_GATE_STATUS = "IBKR_CONNECTION_PERMISSION_GATE_READY"
OPERATOR_APPROVAL_REQUIRED = "YES"
CONNECTION_ALLOWED = "NO"
NEXT_PHASE_CONNECTION_CANDIDATE = "YES"
NO_TEXT = "NO"
YES_TEXT = "YES"

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
    "blocks",
    "approval_required",
    "operator_action_required",
    "external_effect",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

STATUS_FIELDS = (
    "connection_permission_decision",
    "permission_gate_status",
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
    "next_phase_connection_candidate",
)

STATUS_VALUES = {
    "connection_permission_decision": CONNECTION_PERMISSION_DECISION,
    "permission_gate_status": PERMISSION_GATE_STATUS,
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
    "next_phase_connection_candidate": NEXT_PHASE_CONNECTION_CANDIDATE,
}

PROHIBITED_ACTIONS = (
    ("IBKR-PERM-001", "No IBKR or TWS Gateway connection", "IBKR_CONNECTION"),
    ("IBKR-PERM-002", "No market data request", "MARKET_DATA_REQUEST"),
    ("IBKR-PERM-003", "No account read", "ACCOUNT_READ"),
    ("IBKR-PERM-004", "No positions read", "POSITIONS_READ"),
    ("IBKR-PERM-005", "No historical data request", "HISTORICAL_DATA_REQUEST"),
    ("IBKR-PERM-006", "No contract qualification", "CONTRACT_QUALIFICATION"),
    ("IBKR-PERM-007", "No order submission", "ORDER_SUBMISSION"),
    ("IBKR-PERM-008", "No order cancellation", "ORDER_CANCELLATION"),
    ("IBKR-PERM-009", "No rebalance action", "REBALANCE_ACTION"),
    ("IBKR-PERM-010", "No Telegram real send", "TELEGRAM_REAL_SEND"),
    ("IBKR-PERM-011", "No network probe", "NETWORK_PROBE"),
)

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
    blocks: str,
    approval_required: str,
    operator_action_required: str,
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
        "blocks": blocks,
        "approval_required": approval_required,
        "operator_action_required": operator_action_required,
        "external_effect": "NONE",
        "evidence": evidence,
        "recommendation": recommendation,
        "timestamp_utc": timestamp_utc,
    }


def build_ibkr_connection_permission_gate_rows(
    *,
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    rows: List[Dict[str, str]] = []

    rows.append(
        _row(
            gate_id="IBKR-PERM-000",
            gate_name="Final connection permission decision",
            category="final_decision",
            required_state="manual_operator_approval_before_any_real_connection",
            observed_state="approval_not_present_connection_denied",
            result=CONNECTION_PERMISSION_DECISION,
            severity="CRITICAL",
            blocks="IBKR_CONNECTION",
            approval_required=YES_TEXT,
            operator_action_required=YES_TEXT,
            evidence="artifact_only_permission_packet_generated",
            recommendation="treat_DENIED_as_safe_default_not_failure",
            timestamp_utc=timestamp,
        )
    )

    for gate_id, gate_name, blocks in PROHIBITED_ACTIONS:
        rows.append(
            _row(
                gate_id=gate_id,
                gate_name=gate_name,
                category="prohibited_action",
                required_state="blocked_for_phase_517_520",
                observed_state="blocked_no_runtime_call_attempted",
                result="PASS",
                severity="CRITICAL",
                blocks=blocks,
                approval_required=YES_TEXT,
                operator_action_required=YES_TEXT,
                evidence="static_permission_gate_generation_only",
                recommendation="keep_blocked_until_separate_explicit_operator_approved_phase",
                timestamp_utc=timestamp,
            )
        )

    rows.extend(
        [
            _row(
                gate_id="IBKR-PERM-012",
                gate_name="Operator approval packet requirement",
                category="operator_approval",
                required_state="approval_packet_reviewed_and_signed_in_later_phase",
                observed_state="approval_required_not_granted_in_this_phase",
                result="PASS",
                severity="CRITICAL",
                blocks="IBKR_CONNECTION",
                approval_required=YES_TEXT,
                operator_action_required=YES_TEXT,
                evidence="connection_permission_decision_DENIED",
                recommendation="collect_explicit_operator_approval_before_any_later_connection_candidate",
                timestamp_utc=timestamp,
            ),
            _row(
                gate_id="IBKR-PERM-013",
                gate_name="Connection preconditions are candidate-only",
                category="connection_precondition",
                required_state="candidate_only_no_real_connection_allowed",
                observed_state="next_phase_connection_candidate_only",
                result="PASS",
                severity="HIGH",
                blocks="REAL_CONNECTION_AUTHORIZATION",
                approval_required=YES_TEXT,
                operator_action_required=YES_TEXT,
                evidence="connection_allowed_NO_next_phase_connection_candidate_YES",
                recommendation="next_phase_may_review_connection_candidate_but_must_not_infer_GO",
                timestamp_utc=timestamp,
            ),
            _row(
                gate_id="IBKR-PERM-014",
                gate_name="Freeze and readiness labels remain unchanged",
                category="state_label_guard",
                required_state="do_not_reclassify_freeze_or_preflight_status",
                observed_state="freeze_and_preflight_labels_preserved",
                result="PASS",
                severity="HIGH",
                blocks="PRODUCTION_READY_RECLASSIFICATION",
                approval_required=NO_TEXT,
                operator_action_required=NO_TEXT,
                evidence="POST_MVP_MULTI_MARKET_FREEZE_READY_and_REAL_MARKET_ENV_READINESS_PREFLIGHT_READY_not_rewritten",
                recommendation="do_not_label_this_phase_as_production_ready_or_real_market_data_verified",
                timestamp_utc=timestamp,
            ),
        ]
    )
    return rows


def write_ibkr_connection_permission_gate_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_ibkr_connection_permission_gate_report(rows: Sequence[Dict[str, str]]) -> str:
    status_lines = [f"- {field}={STATUS_VALUES[field]}" for field in STATUS_FIELDS]
    gate_lines = [
        f"- {row['gate_id']} {row['gate_name']}: {row['result']} / fail_closed={row['fail_closed']} / blocks={row['blocks']}"
        for row in rows
        if row["category"] == "prohibited_action"
    ]
    approval_lines = [
        f"- {row['gate_id']} {row['gate_name']}: approval_required={row['approval_required']} / operator_action_required={row['operator_action_required']}"
        for row in rows
        if row["category"] in {"final_decision", "operator_approval"}
    ]
    precondition_lines = [
        f"- {row['gate_id']} {row['gate_name']}: {row['observed_state']} / recommendation={row['recommendation']}"
        for row in rows
        if row["category"] in {"connection_precondition", "state_label_guard"}
    ]
    findings = [row for row in rows if row["result"] not in {"PASS", CONNECTION_PERMISSION_DECISION}]
    finding_lines = [f"- {row['gate_id']} {row['severity']}: {row['recommendation']}" for row in findings] or ["- none"]

    lines = [
        "# Phase 517-520 IBKR Connection Permission Gate",
        "",
        "## Final Decision",
        "",
        *status_lines,
        "",
        "DENIED is the safe default for this phase and does not indicate a failed run.",
        "",
        "## Scope Boundary",
        "",
        "- operator approval packet generation only",
        "- fail-closed gate for any future real read-only connection candidate",
        "- no secret, token, or account id values are read into the artifacts or written",
        "- POST_MVP_MULTI_MARKET_FREEZE_READY remains unchanged and is not reclassified as production-ready",
        "- REAL_MARKET_ENV_READINESS_PREFLIGHT_READY remains unchanged and is not reclassified as real-market-data-verified",
        "",
        "## Explicitly Prohibited Actions",
        "",
        "- IBKR connection",
        "- TWS or IB Gateway connection",
        "- market data request",
        "- account read",
        "- positions read",
        "- historical data request",
        "- contract qualification",
        "- order submission",
        "- order cancellation",
        "- rebalance action",
        "- Telegram real send",
        "- network probe",
        "",
        "## Permission Gates",
        "",
        *gate_lines,
        "",
        "## Operator Approval Requirements",
        "",
        *approval_lines,
        "",
        "## Connection Preconditions",
        "",
        *precondition_lines,
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_ibkr_connection_permission_gate.csv",
        "- report=reports/operator_ibkr_connection_permission_gate_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Findings",
        "",
        *finding_lines,
        "",
        "## Residual Risks",
        "",
        "- this packet does not prove IBKR connectivity",
        "- this packet does not prove market data entitlement",
        "- this packet does not prove account, position, historical data, contract qualification, order, or Telegram send behavior",
        "- a later phase still needs explicit operator approval and must remain read-only unless separately authorized",
        "",
        "## Next Phase Preconditions",
        "",
        "- explicit operator approval for a single future read-only connection candidate",
        "- a separate fail-closed command for the actual connection attempt",
        "- no market data request, account read, positions read, historical data request, contract qualification, order, cancel, rebalance, Telegram real send, or network probe unless separately approved",
        "- no automatic transition from this DENIED packet to connection_allowed=YES",
    ]
    return "\n".join(lines) + "\n"


def write_ibkr_connection_permission_gate_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_ibkr_connection_permission_gate_report(rows), encoding="utf-8")


def generate_ibkr_connection_permission_gate(
    *,
    output_csv: PathLike = "operator_ibkr_connection_permission_gate.csv",
    output_report: PathLike = "reports/operator_ibkr_connection_permission_gate_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_ibkr_connection_permission_gate_rows(generated_at=generated_at)
    write_ibkr_connection_permission_gate_csv(output_csv, rows)
    write_ibkr_connection_permission_gate_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 517-520 IBKR connection permission gate.")
    parser.add_argument("--output-csv", default="operator_ibkr_connection_permission_gate.csv")
    parser.add_argument("--output-report", default="reports/operator_ibkr_connection_permission_gate_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_ibkr_connection_permission_gate(
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[IBKR_CONNECTION_PERMISSION_GATE] generated")
    for field in STATUS_FIELDS:
        print(f"{field}={STATUS_VALUES[field]}")
    print(f"gates={len(rows)}")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    print(
        "NOTICE: Phase 517-520 permission packet only. No IBKR/TWS/Gateway connection, "
        "no network probe, no market data request, no account reads, no position reads, "
        "no historical data request, no contract qualification, no orders, no cancellation, "
        "no rebalance, and no Telegram real send."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
