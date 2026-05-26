from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


PHASE = "Phase 521-524"
LAUNCH_PACK_STATUS = "IBKR_READONLY_CONNECT_DRYRUN_LAUNCH_PACK_READY"
FINAL_DECISION = "NO_GO"
ARTIFACT_ONLY = "YES"
CONNECTION_ALLOWED = "NO"
EXECUTION_COMMAND_INCLUDED = "NO"
YES_TEXT = "YES"
NO_TEXT = "NO"

CSV_FIELDS = (
    "phase",
    "check_id",
    "check_name",
    "category",
    "required_state",
    "observed_state",
    "result",
    "severity",
    "fail_closed",
    "blocks",
    "operator_approval_required",
    "external_effect",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

STATUS_FIELDS = (
    "final_decision",
    "launch_pack_status",
    "artifact_only",
    "operator_approval_required",
    "connection_allowed",
    "execution_command_included",
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
    "final_decision": FINAL_DECISION,
    "launch_pack_status": LAUNCH_PACK_STATUS,
    "artifact_only": ARTIFACT_ONLY,
    "operator_approval_required": YES_TEXT,
    "connection_allowed": CONNECTION_ALLOWED,
    "execution_command_included": EXECUTION_COMMAND_INCLUDED,
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

BOUNDARY_CHECKS = (
    ("IBKR-DRYRUN-LAUNCH-001", "Artifact-only launch packet", "artifact_boundary", "EXTERNAL_EXECUTION", "HIGH"),
    ("IBKR-DRYRUN-LAUNCH-002", "No connection command execution", "connection_boundary", "IBKR_CONNECTION", "CRITICAL"),
    ("IBKR-DRYRUN-LAUNCH-003", "No network probe", "network_boundary", "NETWORK_PROBE", "CRITICAL"),
    ("IBKR-DRYRUN-LAUNCH-004", "No market data request", "market_data_boundary", "MARKET_DATA_REQUEST", "CRITICAL"),
    ("IBKR-DRYRUN-LAUNCH-005", "No account or positions read", "account_boundary", "ACCOUNT_OR_POSITIONS_READ", "CRITICAL"),
    ("IBKR-DRYRUN-LAUNCH-006", "No historical data request", "historical_boundary", "HISTORICAL_DATA_REQUEST", "CRITICAL"),
    ("IBKR-DRYRUN-LAUNCH-007", "No contract qualification", "contract_boundary", "CONTRACT_QUALIFICATION", "CRITICAL"),
    ("IBKR-DRYRUN-LAUNCH-008", "No trading action", "trading_boundary", "ORDER_CANCEL_REBALANCE", "CRITICAL"),
    ("IBKR-DRYRUN-LAUNCH-009", "No Telegram real send", "telegram_boundary", "TELEGRAM_REAL_SEND", "CRITICAL"),
    ("IBKR-DRYRUN-LAUNCH-010", "No secret or account id disclosure", "secret_boundary", "SECRET_OR_ACCOUNT_ID_DISCLOSURE", "CRITICAL"),
    ("IBKR-DRYRUN-LAUNCH-011", "Prior readiness labels preserved", "state_label_guard", "PRODUCTION_READY_RECLASSIFICATION", "HIGH"),
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _row(
    *,
    check_id: str,
    check_name: str,
    category: str,
    required_state: str,
    observed_state: str,
    result: str,
    severity: str,
    blocks: str,
    operator_approval_required: str,
    evidence: str,
    recommendation: str,
    timestamp_utc: str,
) -> Dict[str, str]:
    return {
        "phase": PHASE,
        "check_id": check_id,
        "check_name": check_name,
        "category": category,
        "required_state": required_state,
        "observed_state": observed_state,
        "result": result,
        "severity": severity,
        "fail_closed": YES_TEXT,
        "blocks": blocks,
        "operator_approval_required": operator_approval_required,
        "external_effect": "NONE",
        "evidence": evidence,
        "recommendation": recommendation,
        "timestamp_utc": timestamp_utc,
    }


def build_ibkr_readonly_connect_dryrun_launch_pack_rows(
    *,
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    rows: List[Dict[str, str]] = [
        _row(
            check_id="IBKR-DRYRUN-LAUNCH-000",
            check_name="Final launch decision",
            category="final_decision",
            required_state="explicit_future_operator_authorization_before_any_real_connection",
            observed_state="authorization_not_present_no_go",
            result=FINAL_DECISION,
            severity="CRITICAL",
            blocks="IBKR_CONNECTION",
            operator_approval_required=YES_TEXT,
            evidence="dryrun_launch_packet_generated_without_execution_command",
            recommendation="do_not_run_any_real_connection_from_this_packet",
            timestamp_utc=timestamp,
        )
    ]

    for check_id, check_name, category, blocks, severity in BOUNDARY_CHECKS:
        rows.append(
            _row(
                check_id=check_id,
                check_name=check_name,
                category=category,
                required_state="blocked_for_phase_521_524",
                observed_state="blocked_no_runtime_call_attempted",
                result="PASS",
                severity=severity,
                blocks=blocks,
                operator_approval_required=YES_TEXT if severity == "CRITICAL" else NO_TEXT,
                evidence="artifact_only_checker_no_external_side_effect",
                recommendation="keep_blocked_until_separate_explicit_operator_authorization",
                timestamp_utc=timestamp,
            )
        )

    rows.append(
        _row(
            check_id="IBKR-DRYRUN-LAUNCH-012",
            check_name="Connection skeleton intentionally omitted",
            category="execution_skeleton_boundary",
            required_state="no_execute_path_in_this_phase",
            observed_state="execution_command_included_NO",
            result="PASS",
            severity="HIGH",
            blocks="REAL_CONNECTION_EXECUTION",
            operator_approval_required=YES_TEXT,
            evidence="cli_generates_artifacts_only",
            recommendation="add_any_future_execute_path_only_after_new_user_authorization",
            timestamp_utc=timestamp,
        )
    )
    return rows


def write_ibkr_readonly_connect_dryrun_launch_pack_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_ibkr_readonly_connect_dryrun_launch_pack_report(rows: Sequence[Dict[str, str]]) -> str:
    status_lines = [f"- {field}={STATUS_VALUES[field]}" for field in STATUS_FIELDS]
    boundary_lines = [
        f"- {row['check_id']} {row['check_name']}: {row['result']} / fail_closed={row['fail_closed']} / blocks={row['blocks']}"
        for row in rows
        if row["category"] not in {"final_decision"}
    ]
    findings = [row for row in rows if row["result"] not in {"PASS", FINAL_DECISION}]
    finding_lines = [f"- {row['check_id']} {row['severity']}: {row['recommendation']}" for row in findings] or ["- none"]

    lines = [
        "# Phase 521-524 IBKR Read-Only Connect Dry-Run Launch Pack",
        "",
        "## Final Decision",
        "",
        *status_lines,
        "",
        "NO_GO is the safe default for this phase. It means no real connection is authorized or attempted.",
        "",
        "## Scope Boundary",
        "",
        "- artifact-only checker and operator launch packet",
        "- no executable IBKR connection command is produced by this phase",
        "- no secret, token, or account id values are read into the artifacts or written",
        "- POST_MVP_MULTI_MARKET_FREEZE_READY remains unchanged and is not reclassified as production-ready",
        "- REAL_MARKET_ENV_READINESS_PREFLIGHT_READY remains unchanged and is not reclassified as real-market-data-verified",
        "- IBKR_CONNECTION_PERMISSION_GATE_READY remains unchanged and is not interpreted as connection approval",
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
        "- order submission, cancellation, or rebalance",
        "- Telegram real send",
        "",
        "## Boundary Checks",
        "",
        *boundary_lines,
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_ibkr_readonly_connect_dryrun_launch_pack.csv",
        "- report=reports/operator_ibkr_readonly_connect_dryrun_launch_pack_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Findings",
        "",
        *finding_lines,
        "",
        "## Residual Risks",
        "",
        "- this packet does not prove IBKR connectivity",
        "- this packet does not prove TWS or IB Gateway availability",
        "- this packet does not prove market data entitlement",
        "- this packet does not prove account, position, historical data, contract qualification, order, or Telegram behavior",
        "",
        "## Next Phase Preconditions",
        "",
        "- explicit user authorization for any future real IBKR connection attempt",
        "- a separate fail-closed implementation for that future connection attempt",
        "- no market data request, account read, positions read, historical data request, contract qualification, order, cancel, rebalance, Telegram real send, or network probe unless separately approved",
        "- no automatic transition from this NO_GO packet to a connection-approved state",
    ]
    return "\n".join(lines) + "\n"


def write_ibkr_readonly_connect_dryrun_launch_pack_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_ibkr_readonly_connect_dryrun_launch_pack_report(rows), encoding="utf-8")


def generate_ibkr_readonly_connect_dryrun_launch_pack(
    *,
    output_csv: PathLike = "operator_ibkr_readonly_connect_dryrun_launch_pack.csv",
    output_report: PathLike = "reports/operator_ibkr_readonly_connect_dryrun_launch_pack_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_ibkr_readonly_connect_dryrun_launch_pack_rows(generated_at=generated_at)
    write_ibkr_readonly_connect_dryrun_launch_pack_csv(output_csv, rows)
    write_ibkr_readonly_connect_dryrun_launch_pack_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 521-524 IBKR read-only connect dry-run launch pack.")
    parser.add_argument("--output-csv", default="operator_ibkr_readonly_connect_dryrun_launch_pack.csv")
    parser.add_argument("--output-report", default="reports/operator_ibkr_readonly_connect_dryrun_launch_pack_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_ibkr_readonly_connect_dryrun_launch_pack(
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[IBKR_READONLY_CONNECT_DRYRUN_LAUNCH_PACK] generated")
    for field in STATUS_FIELDS:
        print(f"{field}={STATUS_VALUES[field]}")
    print(f"checks={len(rows)}")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    print(
        "NOTICE: Phase 521-524 artifact-only dry-run launch packet. No IBKR/TWS/Gateway connection, "
        "no network probe, no market data request, no account reads, no position reads, "
        "no historical data request, no contract qualification, no orders, no cancellation, "
        "no rebalance, no Telegram real send, and no execute command is included."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
