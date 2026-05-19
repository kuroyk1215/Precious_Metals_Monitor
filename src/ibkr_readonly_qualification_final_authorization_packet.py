from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping
from zoneinfo import ZoneInfo


FALSE_TEXT = "false"

DEFAULT_WARNING_FLAGS = (
    "BLOCKED",
    "CLOSED",
    "final_authorization_blocked",
    "final_authorization_allowed_false",
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
    "phase12h_ibkr_readonly_qualification_final_authorization_packet",
)


@dataclass(frozen=True)
class FinalAuthorizationPacketRow:
    section_id: str
    section_name: str
    source_layer: str
    final_authorization_status: str
    final_authorization_allowed: str
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
    "final_authorization_status",
    "final_authorization_allowed",
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


def _read_effective_gate_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    required = {"section_id", "effective_approval_gate_status", "approval_effective", "action_allowed"}
    if not rows or not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        return []
    return rows


def _default_source_rows() -> list[Mapping[str, object]]:
    return [
        {"section_id": "12A", "section_name": "Candidate resolver final authorization packet", "source_layer": "Phase 12A"},
        {"section_id": "12B", "section_name": "Candidate review pack final authorization packet", "source_layer": "Phase 12B"},
        {"section_id": "12C", "section_name": "Candidate final gate final authorization packet", "source_layer": "Phase 12C"},
        {"section_id": "12D", "section_name": "Candidate safety summary final authorization packet", "source_layer": "Phase 12D"},
        {"section_id": "12E", "section_name": "Operator decision ledger final authorization packet", "source_layer": "Phase 12E"},
        {"section_id": "12F", "section_name": "Operator approval stub final authorization packet", "source_layer": "Phase 12F"},
        {"section_id": "12G", "section_name": "Effective approval gate final authorization packet", "source_layer": "Phase 12G"},
        {"section_id": "FINAL", "section_name": "Final authorization packet", "source_layer": "Phase 12A-12G"},
    ]


def _source_rows(input_source: str | Path) -> list[Mapping[str, object]]:
    path = Path(input_source)
    if path.exists() and path.suffix.lower() == ".csv":
        rows = _read_effective_gate_csv(path)
        if rows:
            return rows
    return _default_source_rows()


def _make_packet_row(source: Mapping[str, object], timestamp_jst: str, timestamp_et: str) -> FinalAuthorizationPacketRow:
    section_id = str(source.get("section_id") or "UNKNOWN")
    section_name = str(source.get("section_name") or "Final authorization packet row")
    source_layer = str(source.get("source_layer") or "Phase 12A-12G")

    upstream_gate_status = str(source.get("effective_approval_gate_status") or "CLOSED").upper()
    upstream_action_allowed = str(source.get("action_allowed") or "false").lower()

    if upstream_gate_status != "CLOSED" or upstream_action_allowed == "true":
        decision_reason = "upstream_attempted_unlock_but_final_authorization_remains_blocked"
    else:
        decision_reason = "final_authorization_blocked_by_design"

    return FinalAuthorizationPacketRow(
        section_id=section_id,
        section_name=section_name,
        source_layer=source_layer,
        final_authorization_status="BLOCKED",
        final_authorization_allowed=FALSE_TEXT,
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
            "Final authorization packet only; final authorization remains BLOCKED. "
            "No TWS connection, no IBKR API request, no real contract qualification, "
            "no market data request, no historical data request, and no trading."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_qualification_final_authorization_packet_rows(
    input_source: str | Path = "data/market_data_provider_config.yaml",
) -> list[FinalAuthorizationPacketRow]:
    timestamp_jst, timestamp_et = _now_pair()
    return [_make_packet_row(row, timestamp_jst, timestamp_et) for row in _source_rows(input_source)]


def write_ibkr_readonly_qualification_final_authorization_packet_csv(
    path: str | Path,
    rows: Iterable[FinalAuthorizationPacketRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_qualification_final_authorization_packet_report(
    path: str | Path,
    rows: Iterable[FinalAuthorizationPacketRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    blocked_count = sum(1 for row in row_list if row.final_authorization_status == "BLOCKED")
    allowed_count = sum(1 for row in row_list if row.action_allowed == "true")
    statuses = sorted({row.final_authorization_status for row in row_list}) or ["none"]

    lines = [
        "# Phase 12H IBKR Read-Only Qualification Final Authorization Packet Report",
        "",
        "- phase: Phase 12H",
        "- scope: IBKR read-only qualification final authorization packet",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- final_authorization_statuses: {','.join(statuses)}",
        f"- blocked_count: {blocked_count}",
        f"- action_allowed_count: {allowed_count}",
        "- final_authorization_status: BLOCKED",
        "- final_authorization_allowed: false",
        "- effective_approval_gate_status: CLOSED",
        "- effective_approval_allowed: false",
        "- approval_effective: false",
        "- candidate_safety_status: BLOCKED",
        "- candidate_final_gate_status: CLOSED",
        "",
        "## Final Authorization Packet Rows",
        "",
        "| section_id | source_layer | final_authorization_status | final_authorization_allowed | effective_approval_gate_status | approval_effective | qualification_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.section_id,
                    row.source_layer,
                    row.final_authorization_status,
                    row.final_authorization_allowed,
                    row.effective_approval_gate_status,
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
            "## Final Decision",
            "",
            "- Final authorization status: BLOCKED",
            "- Final authorization allowed: false",
            "- Effective approval gate status: CLOSED",
            "- Approval is not effective.",
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
            "- IBKR read-only qualification final authorization packet only",
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
