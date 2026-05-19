from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping
from zoneinfo import ZoneInfo


FALSE_TEXT = "false"
TRUE_TEXT = "true"

DEFAULT_WARNING_FLAGS = (
    "BLOCKED",
    "CLOSED",
    "effective_approval_gate_closed",
    "effective_approval_allowed_false",
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
    "phase12g_ibkr_readonly_qualification_effective_approval_gate",
)


@dataclass(frozen=True)
class EffectiveApprovalGateRow:
    section_id: str
    section_name: str
    source_layer: str
    operator_approval_status: str
    effective_approval_gate_status: str
    approval_effective: str
    effective_approval_allowed: str
    candidate_final_gate_status: str
    candidate_safety_status: str
    qualification_allowed: str
    tws_connection_allowed: str
    contract_qualification_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    api_request_allowed: str
    action_allowed: str
    decision_reason: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "section_id",
    "section_name",
    "source_layer",
    "operator_approval_status",
    "effective_approval_gate_status",
    "approval_effective",
    "effective_approval_allowed",
    "candidate_final_gate_status",
    "candidate_safety_status",
    "qualification_allowed",
    "tws_connection_allowed",
    "contract_qualification_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "api_request_allowed",
    "action_allowed",
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


def _read_approval_stub_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    required = {"section_id", "operator_approval_status"}
    if not rows or not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        return []
    return rows


def _default_stub_rows() -> list[Mapping[str, object]]:
    return [
        {
            "section_id": "12A",
            "section_name": "Candidate resolver effective approval gate",
            "source_layer": "Phase 12A",
            "operator_approval_status": "PENDING",
        },
        {
            "section_id": "12B",
            "section_name": "Candidate review pack effective approval gate",
            "source_layer": "Phase 12B",
            "operator_approval_status": "PENDING",
        },
        {
            "section_id": "12C",
            "section_name": "Candidate final gate effective approval gate",
            "source_layer": "Phase 12C",
            "operator_approval_status": "PENDING",
        },
        {
            "section_id": "FINAL",
            "section_name": "Final effective approval gate",
            "source_layer": "Phase 12A-12F",
            "operator_approval_status": "PENDING",
        },
    ]


def _source_rows(input_source: str | Path) -> list[Mapping[str, object]]:
    path = Path(input_source)
    if path.exists() and path.suffix.lower() == ".csv":
        rows = _read_approval_stub_csv(path)
        if rows:
            return rows
    return _default_stub_rows()


def _make_gate_row(source: Mapping[str, object], timestamp_jst: str, timestamp_et: str) -> EffectiveApprovalGateRow:
    section_id = str(source.get("section_id") or "UNKNOWN")
    section_name = str(source.get("section_name") or "Effective approval gate row")
    source_layer = str(source.get("source_layer") or "Phase 12A-12F")
    operator_status = str(source.get("operator_approval_status") or "PENDING").upper()

    if operator_status == "APPROVED":
        decision_reason = "operator_approved_but_effective_approval_gate_remains_closed"
    elif operator_status == "REJECTED":
        decision_reason = "operator_rejected_and_effective_approval_gate_closed"
    elif operator_status == "NEEDS_REVIEW":
        decision_reason = "operator_needs_review_and_effective_approval_gate_closed"
    else:
        decision_reason = "operator_approval_pending_and_effective_approval_gate_closed"

    return EffectiveApprovalGateRow(
        section_id=section_id,
        section_name=section_name,
        source_layer=source_layer,
        operator_approval_status=operator_status,
        effective_approval_gate_status="CLOSED",
        approval_effective=FALSE_TEXT,
        effective_approval_allowed=FALSE_TEXT,
        candidate_final_gate_status="CLOSED",
        candidate_safety_status="BLOCKED",
        qualification_allowed=FALSE_TEXT,
        tws_connection_allowed=FALSE_TEXT,
        contract_qualification_allowed=FALSE_TEXT,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        api_request_allowed=FALSE_TEXT,
        action_allowed=FALSE_TEXT,
        decision_reason=decision_reason,
        warning_flags=_flags([decision_reason]),
        notes=(
            "Effective approval gate only; Phase 12G keeps the gate CLOSED. "
            "Even an APPROVED upstream stub is not executable here. No TWS connection, "
            "no IBKR API request, no qualification, no market data request, no historical data request, and no trading."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_qualification_effective_approval_gate_rows(
    input_source: str | Path = "data/market_data_provider_config.yaml",
) -> list[EffectiveApprovalGateRow]:
    timestamp_jst, timestamp_et = _now_pair()
    return [_make_gate_row(row, timestamp_jst, timestamp_et) for row in _source_rows(input_source)]


def write_ibkr_readonly_qualification_effective_approval_gate_csv(
    path: str | Path,
    rows: Iterable[EffectiveApprovalGateRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_qualification_effective_approval_gate_report(
    path: str | Path,
    rows: Iterable[EffectiveApprovalGateRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    approved_count = sum(1 for row in row_list if row.operator_approval_status == "APPROVED")
    closed_count = sum(1 for row in row_list if row.effective_approval_gate_status == "CLOSED")
    effective_count = sum(1 for row in row_list if row.approval_effective == TRUE_TEXT)
    allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    statuses = sorted({row.operator_approval_status for row in row_list}) or ["none"]

    lines = [
        "# Phase 12G IBKR Read-Only Qualification Effective Approval Gate Report",
        "",
        "- phase: Phase 12G",
        "- scope: IBKR read-only qualification effective approval gate",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- operator_approval_statuses: {','.join(statuses)}",
        f"- approved_count: {approved_count}",
        f"- closed_count: {closed_count}",
        f"- approval_effective_count: {effective_count}",
        f"- action_allowed_count: {allowed_count}",
        "- effective_approval_gate_status: CLOSED",
        "- effective_approval_allowed: false",
        "- approval_effective: false",
        "- candidate_safety_status: BLOCKED",
        "- candidate_final_gate_status: CLOSED",
        "",
        "## Effective Approval Gate Rows",
        "",
        "| section_id | source_layer | operator_approval_status | effective_approval_gate_status | approval_effective | effective_approval_allowed | qualification_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.section_id,
                    row.source_layer,
                    row.operator_approval_status,
                    row.effective_approval_gate_status,
                    row.approval_effective,
                    row.effective_approval_allowed,
                    row.qualification_allowed,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Final Decision",
            "",
            "- Effective approval gate status: CLOSED",
            "- Effective approval allowed: false",
            "- Approval is not effective in Phase 12G.",
            "- APPROVED upstream status is not executable in Phase 12G.",
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
            "- IBKR read-only qualification effective approval gate only",
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
