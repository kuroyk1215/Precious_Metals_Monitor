from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv


@dataclass
class IBKRReadOnlyQualificationRunbookRow:
    step_id: str
    step_order: str
    step_group: str
    step_title: str
    operator_action: str
    expected_result: str
    verification_method: str
    required_before_real_qualification: str
    runbook_status: str
    qualification_allowed: str
    tws_connection_allowed: str
    contract_qualification_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    api_request_allowed: str
    action_allowed: str
    block_reason: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


def _now_pair(tz_cfg: dict[str, str]) -> tuple[str, str]:
    now_utc = datetime.now(timezone.utc)
    return (
        now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat(),
        now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat(),
    )


def _flags(*values: str) -> str:
    flags: set[str] = {
        "phase10l_ibkr_readonly_qualification_runbook",
        "runbook_only",
        "manual_confirmation_required",
        "no_tws_connection",
        "no_contract_qualification",
        "no_api_request",
        "no_ibkr_connection",
        "no_reqMktData",
        "no_reqHistoricalData",
        "no_order",
        "no_auto_trade",
    }
    for value in values:
        if value and value != "none":
            flags.update(flag.strip() for flag in value.split(";") if flag.strip())
    return ";".join(sorted(flags))


def _precheck_lookup(precheck_rows: list[Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in precheck_rows:
        row = item if isinstance(item, dict) else item.__dict__
        out[str(row.get("check_id", "unknown"))] = str(row.get("precheck_status", "unknown"))
    return out


def _runbook_status(prechecks: dict[str, str], required_checks: list[str]) -> tuple[str, str]:
    missing_or_blocked = [
        check_id
        for check_id in required_checks
        if prechecks.get(check_id, "precheck_blocked") != "precheck_pass"
    ]
    if missing_or_blocked:
        return "blocked_by_precheck", "blocked_checks=" + ",".join(missing_or_blocked)
    return "ready_for_manual_review_only", "phase10l_runbook_does_not_execute"


def _row(
    step_id: str,
    step_order: int,
    step_group: str,
    step_title: str,
    operator_action: str,
    expected_result: str,
    verification_method: str,
    required_checks: list[str],
    prechecks: dict[str, str],
    ts_jst: str,
    ts_et: str,
) -> IBKRReadOnlyQualificationRunbookRow:
    status, reason = _runbook_status(prechecks, required_checks)

    return IBKRReadOnlyQualificationRunbookRow(
        step_id=step_id,
        step_order=str(step_order),
        step_group=step_group,
        step_title=step_title,
        operator_action=operator_action,
        expected_result=expected_result,
        verification_method=verification_method,
        required_before_real_qualification="true",
        runbook_status=status,
        qualification_allowed="false",
        tws_connection_allowed="false",
        contract_qualification_allowed="false",
        market_data_request_allowed="false",
        historical_data_request_allowed="false",
        api_request_allowed="false",
        action_allowed="false",
        block_reason=reason,
        warning_flags=_flags(status, reason),
        notes="Runbook output only; no TWS connection and no IBKR API request is performed.",
        timestamp_jst=ts_jst,
        timestamp_et=ts_et,
    )


def build_ibkr_readonly_qualification_runbook_rows(
    precheck_rows: list[Any],
    tz_cfg: dict[str, str],
) -> list[IBKRReadOnlyQualificationRunbookRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    prechecks = _precheck_lookup(precheck_rows)

    definitions = [
        (
            "open_tws_gateway",
            1,
            "environment",
            "Open TWS or IB Gateway manually",
            "Start TWS or IB Gateway on the local machine; do not allow this CLI to connect.",
            "TWS/Gateway is visible and operator confirms it is the intended session.",
            "Manual screen check only",
            ["tws_runtime_state"],
        ),
        (
            "confirm_read_only",
            2,
            "safety",
            "Confirm read-only mode",
            "Confirm the project config requires read_only_required=true.",
            "Read-only requirement is explicitly true.",
            "Config review",
            ["read_only_required"],
        ),
        (
            "confirm_account_mode",
            3,
            "safety",
            "Confirm account mode",
            "Confirm account_mode is explicitly live or paper.",
            "No implicit or unknown account mode is used.",
            "Config review",
            ["account_mode"],
        ),
        (
            "confirm_connection_fields",
            4,
            "connection_config",
            "Confirm host, port, and client_id",
            "Confirm host, port, and client_id are configured before any future session.",
            "host configured; port is 7496 or 7497; client_id configured.",
            "Config review",
            ["host", "ibkr_port", "client_id"],
        ),
        (
            "confirm_request_gate",
            5,
            "safety",
            "Confirm request gate remains active",
            "Confirm live provider request gate remains in the chain.",
            "Request gate is required before any future IBKR operation.",
            "CLI/report review",
            ["request_gate"],
        ),
        (
            "confirm_explicit_flag",
            6,
            "execution_control",
            "Confirm explicit execution flag is false",
            "Keep explicit execution flag false in this phase.",
            "No real qualification can run from this runbook.",
            "CLI/report review",
            ["explicit_execution_flag"],
        ),
        (
            "confirm_qualification_blocked",
            7,
            "execution_control",
            "Confirm contract qualification remains blocked",
            "Confirm qualification_allowed=false and contract_qualification_allowed=false.",
            "No contract qualification is performed.",
            "CLI/report review",
            ["qualification_allowed"],
        ),
        (
            "confirm_market_data_blocked",
            8,
            "execution_control",
            "Confirm market data requests remain blocked",
            "Confirm no reqMktData and no reqHistoricalData are allowed.",
            "No market-data request is performed.",
            "CLI/report review",
            ["market_data_allowed"],
        ),
        (
            "confirm_trading_blocked",
            9,
            "execution_control",
            "Confirm order and cancel remain blocked",
            "Confirm no order, cancel, rebalance, or auto trade is allowed.",
            "No trading operation is performed.",
            "CLI/report review",
            ["order_cancel_allowed"],
        ),
        (
            "operator_signoff",
            10,
            "manual_review",
            "Operator sign-off before any future real qualification phase",
            "Review all reports from Phase 10G to Phase 10K before moving to a real qualification design.",
            "Operator explicitly approves a future phase design; this command still does not execute.",
            "Manual sign-off",
            [
                "tws_runtime_state",
                "read_only_required",
                "account_mode",
                "host",
                "ibkr_port",
                "client_id",
                "request_gate",
                "explicit_execution_flag",
                "qualification_allowed",
                "market_data_allowed",
                "order_cancel_allowed",
            ],
        ),
    ]

    return [
        _row(
            step_id,
            order,
            group,
            title,
            action,
            expected,
            method,
            checks,
            prechecks,
            ts_jst,
            ts_et,
        )
        for step_id, order, group, title, action, expected, method, checks in definitions
    ]


def write_ibkr_readonly_qualification_runbook_csv(
    path: Path,
    rows: list[IBKRReadOnlyQualificationRunbookRow],
) -> None:
    fields = list(IBKRReadOnlyQualificationRunbookRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_readonly_qualification_runbook_report(
    path: Path,
    rows: list[IBKRReadOnlyQualificationRunbookRow],
    input_source: str,
) -> None:
    statuses = sorted({row.runbook_status for row in rows})
    blocked_count = sum(1 for row in rows if row.runbook_status == "blocked_by_precheck")
    manual_ready_count = sum(1 for row in rows if row.runbook_status == "ready_for_manual_review_only")
    qualification_allowed_count = sum(1 for row in rows if row.qualification_allowed == "true")
    tws_allowed_count = sum(1 for row in rows if row.tws_connection_allowed == "true")

    lines = [
        "# Phase 10L IBKR Read-Only Qualification Runbook Report",
        "",
        "- phase: Phase 10L",
        "- scope: IBKR read-only qualification runbook only",
        "- input_source: " + input_source,
        "- row_count: " + str(len(rows)),
        "- manual_ready_count: " + str(manual_ready_count),
        "- blocked_count: " + str(blocked_count),
        "- qualification_allowed_count: " + str(qualification_allowed_count),
        "- tws_connection_allowed_count: " + str(tws_allowed_count),
        "- runbook_statuses: " + (",".join(statuses) if statuses else "none"),
        "- api_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Runbook Steps",
        "",
        "| step_order | step_id | step_group | runbook_status | qualification_allowed | action_allowed | block_reason |",
        "|---:|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.step_order} | {row.step_id} | {row.step_group} | {row.runbook_status} | {row.qualification_allowed} | {row.action_allowed} | {row.block_reason} |"
        )

    lines.extend(
        [
            "",
            "## Manual Operator Actions",
            "",
        ]
    )

    for row in rows:
        lines.append(
            f"- Step {row.step_order} {row.step_id}: {row.operator_action}"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- IBKR read-only qualification runbook only",
            "- no TWS connection",
            "- no IBKR connection",
            "- no real contract qualification",
            "- qualification_allowed=false for every row",
            "- contract_qualification_allowed=false for every row",
            "- market_data_request_allowed=false for every row",
            "- historical_data_request_allowed=false for every row",
            "- api_request_allowed=false for every row",
            "- action_allowed=false for every row",
            "- no reqMktData",
            "- no reqHistoricalData",
            "- no order",
            "- no cancel",
            "- no rebalance",
            "- no auto trade",
            "- no automatic execution",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
