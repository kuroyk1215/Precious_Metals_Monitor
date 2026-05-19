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
    "PHASE12_COMPLETE",
    "BLOCKED",
    "CLOSED",
    "phase12_closure_report_only",
    "final_authorization_blocked",
    "final_authorization_allowed_false",
    "effective_approval_gate_closed",
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
    "phase12i_ibkr_readonly_qualification_phase12_closure_report",
)


@dataclass(frozen=True)
class Phase12ClosureReportRow:
    phase_id: str
    phase_name: str
    source_layer: str
    phase12_closure_status: str
    final_authorization_status: str
    final_authorization_allowed: str
    effective_approval_gate_status: str
    approval_effective: str
    candidate_final_gate_status: str
    candidate_safety_status: str
    qualification_allowed: str
    tws_connection_allowed: str
    contract_qualification_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    api_request_allowed: str
    action_allowed: str
    closure_decision: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "phase_id",
    "phase_name",
    "source_layer",
    "phase12_closure_status",
    "final_authorization_status",
    "final_authorization_allowed",
    "effective_approval_gate_status",
    "approval_effective",
    "candidate_final_gate_status",
    "candidate_safety_status",
    "qualification_allowed",
    "tws_connection_allowed",
    "contract_qualification_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "api_request_allowed",
    "action_allowed",
    "closure_decision",
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


def _default_phase_rows() -> list[Mapping[str, object]]:
    return [
        {"phase_id": "12A", "phase_name": "Candidate resolver", "source_layer": "Phase 12A"},
        {"phase_id": "12B", "phase_name": "Candidate review pack", "source_layer": "Phase 12B"},
        {"phase_id": "12C", "phase_name": "Candidate final gate", "source_layer": "Phase 12C"},
        {"phase_id": "12D", "phase_name": "Candidate safety summary", "source_layer": "Phase 12D"},
        {"phase_id": "12E", "phase_name": "Operator decision ledger", "source_layer": "Phase 12E"},
        {"phase_id": "12F", "phase_name": "Operator approval stub", "source_layer": "Phase 12F"},
        {"phase_id": "12G", "phase_name": "Effective approval gate", "source_layer": "Phase 12G"},
        {"phase_id": "12H", "phase_name": "Final authorization packet", "source_layer": "Phase 12H"},
        {"phase_id": "FINAL", "phase_name": "Phase 12 final closure", "source_layer": "Phase 12A-12H"},
    ]


def _read_final_authorization_packet_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    required = {"section_id", "final_authorization_status", "final_authorization_allowed", "action_allowed"}
    if not rows or not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        return []
    return rows


def _source_rows(input_source: str | Path) -> list[Mapping[str, object]]:
    path = Path(input_source)
    if path.exists() and path.suffix.lower() == ".csv":
        rows = _read_final_authorization_packet_csv(path)
        if rows:
            return [
                {
                    "phase_id": row.get("section_id") or "UNKNOWN",
                    "phase_name": row.get("section_name") or "Phase 12 closure row",
                    "source_layer": row.get("source_layer") or "Phase 12A-12H",
                    "final_authorization_status": row.get("final_authorization_status") or "BLOCKED",
                    "final_authorization_allowed": row.get("final_authorization_allowed") or "false",
                    "action_allowed": row.get("action_allowed") or "false",
                }
                for row in rows
            ]
    return _default_phase_rows()


def _make_closure_row(source: Mapping[str, object], timestamp_jst: str, timestamp_et: str) -> Phase12ClosureReportRow:
    phase_id = str(source.get("phase_id") or "UNKNOWN")
    phase_name = str(source.get("phase_name") or "Phase 12 closure row")
    source_layer = str(source.get("source_layer") or "Phase 12A-12H")

    upstream_final_status = str(source.get("final_authorization_status") or "BLOCKED").upper()
    upstream_final_allowed = str(source.get("final_authorization_allowed") or "false").lower()
    upstream_action_allowed = str(source.get("action_allowed") or "false").lower()

    if upstream_final_status != "BLOCKED" or upstream_final_allowed == "true" or upstream_action_allowed == "true":
        closure_decision = "upstream_attempted_unlock_but_phase12_closure_remains_blocked"
    else:
        closure_decision = "phase12_closed_with_final_authorization_blocked"

    return Phase12ClosureReportRow(
        phase_id=phase_id,
        phase_name=phase_name,
        source_layer=source_layer,
        phase12_closure_status="COMPLETE",
        final_authorization_status="BLOCKED",
        final_authorization_allowed=FALSE_TEXT,
        effective_approval_gate_status="CLOSED",
        approval_effective=FALSE_TEXT,
        candidate_final_gate_status="CLOSED",
        candidate_safety_status="BLOCKED",
        qualification_allowed=FALSE_TEXT,
        tws_connection_allowed=FALSE_TEXT,
        contract_qualification_allowed=FALSE_TEXT,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        api_request_allowed=FALSE_TEXT,
        action_allowed=FALSE_TEXT,
        closure_decision=closure_decision,
        warning_flags=_flags([closure_decision]),
        notes=(
            "Phase 12 closure report only; this report closes the research-only IBKR read-only "
            "qualification safety chain without granting authorization. No TWS connection, no IBKR API request, "
            "no real contract qualification, no market data request, no historical data request, and no trading."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_qualification_phase12_closure_report_rows(
    input_source: str | Path = "data/market_data_provider_config.yaml",
) -> list[Phase12ClosureReportRow]:
    timestamp_jst, timestamp_et = _now_pair()
    return [_make_closure_row(row, timestamp_jst, timestamp_et) for row in _source_rows(input_source)]


def write_ibkr_readonly_qualification_phase12_closure_report_csv(
    path: str | Path,
    rows: Iterable[Phase12ClosureReportRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_qualification_phase12_closure_report_report(
    path: str | Path,
    rows: Iterable[Phase12ClosureReportRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    complete_count = sum(1 for row in row_list if row.phase12_closure_status == "COMPLETE")
    blocked_count = sum(1 for row in row_list if row.final_authorization_status == "BLOCKED")
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    statuses = sorted({row.phase12_closure_status for row in row_list}) or ["none"]

    lines = [
        "# Phase 12I IBKR Read-Only Qualification Phase 12 Closure Report",
        "",
        "- phase: Phase 12I",
        "- scope: Phase 12 final closure report",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- phase12_closure_statuses: {','.join(statuses)}",
        f"- complete_count: {complete_count}",
        f"- final_authorization_blocked_count: {blocked_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- phase12_closure_status: COMPLETE",
        "- final_authorization_status: BLOCKED",
        "- final_authorization_allowed: false",
        "- effective_approval_gate_status: CLOSED",
        "- approval_effective: false",
        "- candidate_safety_status: BLOCKED",
        "- candidate_final_gate_status: CLOSED",
        "",
        "## Phase 12 Closure Rows",
        "",
        "| phase_id | source_layer | phase12_closure_status | final_authorization_status | final_authorization_allowed | effective_approval_gate_status | qualification_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.phase_id,
                    row.source_layer,
                    row.phase12_closure_status,
                    row.final_authorization_status,
                    row.final_authorization_allowed,
                    row.effective_approval_gate_status,
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
            "- Phase 12 closure status: COMPLETE",
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
            "- Phase 12 closure report only",
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
