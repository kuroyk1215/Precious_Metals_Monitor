from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo


FALSE_TEXT = "false"
TRUE_TEXT = "true"
APPROVAL_INPUT_TEMPLATE = "PENDING|APPROVED|REJECTED|NEEDS_REVIEW"

DEFAULT_WARNING_FLAGS = (
    "BLOCKED",
    "CLOSED",
    "operator_approval_stub_only",
    "operator_approval_required",
    "approval_effective_false",
    "candidate_safety_blocked_by_default",
    "candidate_final_gate_closed",
    "no_tws_connection",
    "no_ibkr_connection",
    "no_contract_qualification",
    "no_reqMktData",
    "no_reqHistoricalData",
    "no_api_request",
    "no_order",
    "no_cancel",
    "no_rebalance",
    "no_auto_trade",
    "phase12f_ibkr_readonly_qualification_operator_approval_stub",
)


@dataclass(frozen=True)
class OperatorApprovalStubRow:
    section_id: str
    section_name: str
    source_layer: str
    candidate_final_gate_status: str
    candidate_safety_status: str
    operator_decision_status: str
    operator_approval_status: str
    operator_approval_required: str
    approval_effective: str
    qualification_allowed: str
    tws_connection_allowed: str
    contract_qualification_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    api_request_allowed: str
    action_allowed: str
    approval_input_template: str
    decision_reason: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "section_id",
    "section_name",
    "source_layer",
    "candidate_final_gate_status",
    "candidate_safety_status",
    "operator_decision_status",
    "operator_approval_status",
    "operator_approval_required",
    "approval_effective",
    "qualification_allowed",
    "tws_connection_allowed",
    "contract_qualification_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "api_request_allowed",
    "action_allowed",
    "approval_input_template",
    "decision_reason",
    "warning_flags",
    "notes",
    "timestamp_jst",
    "timestamp_et",
]


def _now_pair() -> tuple[str, str]:
    now_utc = datetime.now(ZoneInfo("UTC"))
    return (
        now_utc.astimezone(ZoneInfo("Asia/Tokyo")).isoformat(),
        now_utc.astimezone(ZoneInfo("America/New_York")).isoformat(),
    )


def _flags(extra: Iterable[str] = ()) -> str:
    values = list(DEFAULT_WARNING_FLAGS)
    for item in extra:
        if item and item not in values:
            values.append(item)
    return ";".join(values)


def _make_row(
    section_id: str,
    section_name: str,
    source_layer: str,
    timestamp_jst: str,
    timestamp_et: str,
    decision_reason: str,
) -> OperatorApprovalStubRow:
    return OperatorApprovalStubRow(
        section_id=section_id,
        section_name=section_name,
        source_layer=source_layer,
        candidate_final_gate_status="CLOSED",
        candidate_safety_status="BLOCKED",
        operator_decision_status="PENDING",
        operator_approval_status="PENDING",
        operator_approval_required=TRUE_TEXT,
        approval_effective=FALSE_TEXT,
        qualification_allowed=FALSE_TEXT,
        tws_connection_allowed=FALSE_TEXT,
        contract_qualification_allowed=FALSE_TEXT,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        api_request_allowed=FALSE_TEXT,
        action_allowed=FALSE_TEXT,
        approval_input_template=APPROVAL_INPUT_TEMPLATE,
        decision_reason=decision_reason,
        warning_flags=_flags([decision_reason]),
        notes=(
            "Operator approval stub only; approval input is non-effective in Phase 12F. "
            "No TWS connection, no IBKR API request, no qualification, no market data request, "
            "no historical data request, and no trading."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_qualification_operator_approval_stub_rows(
    input_source: str | Path = "data/market_data_provider_config.yaml",
) -> list[OperatorApprovalStubRow]:
    timestamp_jst, timestamp_et = _now_pair()
    _ = str(input_source)

    return [
        _make_row(
            "12A",
            "Candidate resolver approval stub",
            "Phase 12A",
            timestamp_jst,
            timestamp_et,
            "operator_approval_pending_candidate_resolver_locked",
        ),
        _make_row(
            "12B",
            "Candidate review pack approval stub",
            "Phase 12B",
            timestamp_jst,
            timestamp_et,
            "operator_approval_pending_candidate_review_pack_locked",
        ),
        _make_row(
            "12C",
            "Candidate final gate approval stub",
            "Phase 12C",
            timestamp_jst,
            timestamp_et,
            "operator_approval_pending_candidate_final_gate_locked",
        ),
        _make_row(
            "FINAL",
            "Final operator approval stub",
            "Phase 12A-12E",
            timestamp_jst,
            timestamp_et,
            "operator_approval_pending_until_explicit_future_effective_gate",
        ),
    ]


def write_ibkr_readonly_qualification_operator_approval_stub_csv(
    path: str | Path,
    rows: Iterable[OperatorApprovalStubRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_qualification_operator_approval_stub_report(
    path: str | Path,
    rows: Iterable[OperatorApprovalStubRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    pending_count = sum(1 for row in row_list if row.operator_approval_status == "PENDING")
    effective_count = sum(1 for row in row_list if row.approval_effective == TRUE_TEXT)
    allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    statuses = sorted({row.operator_approval_status for row in row_list}) or ["none"]

    lines = [
        "# Phase 12F IBKR Read-Only Qualification Operator Approval Stub Report",
        "",
        "- phase: Phase 12F",
        "- scope: IBKR read-only qualification operator approval stub",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- operator_approval_statuses: {','.join(statuses)}",
        f"- pending_count: {pending_count}",
        f"- approval_effective_count: {effective_count}",
        f"- action_allowed_count: {allowed_count}",
        "- candidate_safety_status: BLOCKED",
        "- candidate_final_gate_status: CLOSED",
        "- approval_effective: false",
        "",
        "## Operator Approval Stub Rows",
        "",
        "| section_id | source_layer | candidate_final_gate_status | candidate_safety_status | operator_decision_status | operator_approval_status | approval_effective | qualification_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.section_id,
                    row.source_layer,
                    row.candidate_final_gate_status,
                    row.candidate_safety_status,
                    row.operator_decision_status,
                    row.operator_approval_status,
                    row.approval_effective,
                    row.qualification_allowed,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Approval Input Template",
            "",
            f"- allowed_stub_values: {APPROVAL_INPUT_TEMPLATE}",
            "- approval_effective: false",
            "- APPROVED is not executable in Phase 12F.",
            "- Any future effective approval requires a separate explicit gate phase.",
            "",
            "## Final Decision",
            "",
            "- Operator approval status: PENDING",
            "- Operator approval remains required.",
            "- Approval is not effective in Phase 12F.",
            "- Candidate safety status remains BLOCKED.",
            "- Candidate final gate remains CLOSED.",
            "- Real IBKR qualification remains blocked.",
            "- TWS connection remains blocked.",
            "- Market data requests remain blocked.",
            "- Historical data requests remain blocked.",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- IBKR read-only qualification operator approval stub only",
            "- no configuration file is modified",
            "- no TWS connection",
            "- no IBKR connection",
            "- no real contract qualification",
            "- no reqMktData",
            "- no reqHistoricalData",
            "- no order",
            "- no cancel",
            "- no rebalance",
            "- no auto trade",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
