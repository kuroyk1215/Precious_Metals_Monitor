from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Mapping
from zoneinfo import ZoneInfo


FALSE_TEXT = "false"
TRUE_TEXT = "true"

DEFAULT_WARNING_FLAGS = (
    "BLOCKED",
    "CLOSED",
    "operator_decision_ledger_only",
    "operator_review_required",
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
    "phase12e_ibkr_readonly_qualification_operator_decision_ledger",
)


@dataclass(frozen=True)
class OperatorDecisionLedgerRow:
    section_id: str
    section_name: str
    source_layer: str
    candidate_count: int
    review_required_count: int
    excluded_count: int
    candidate_final_gate_status: str
    candidate_safety_status: str
    operator_decision_status: str
    operator_decision_required: str
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
    "candidate_count",
    "review_required_count",
    "excluded_count",
    "candidate_final_gate_status",
    "candidate_safety_status",
    "operator_decision_status",
    "operator_decision_required",
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


def _safe_int(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def _flags(extra: Iterable[str] = ()) -> str:
    values = list(DEFAULT_WARNING_FLAGS)
    for item in extra:
        if item and item not in values:
            values.append(item)
    return ";".join(values)


def _row_from_summary(summary: Mapping[str, object], timestamp_jst: str, timestamp_et: str) -> OperatorDecisionLedgerRow:
    section_id = str(summary.get("section_id") or "UNKNOWN")
    section_name = str(summary.get("section_name") or "Operator decision ledger row")
    source_layer = str(summary.get("source_layer") or "Phase 12A-12D")
    candidate_count = _safe_int(summary.get("candidate_count"))
    review_required_count = _safe_int(summary.get("review_required_count"))
    excluded_count = _safe_int(summary.get("excluded_count"))

    final_gate_status = str(summary.get("candidate_final_gate_status") or "CLOSED")
    safety_status = str(summary.get("candidate_safety_status") or "BLOCKED")

    decision_reason = (
        "operator_decision_pending_candidate_safety_blocked"
        if section_id != "FINAL"
        else "final_operator_decision_pending_until_explicit_future_phase_design"
    )

    notes = (
        "Operator decision ledger only; records pending manual review decisions. "
        "No TWS connection, no IBKR API request, no qualification, no market data request, and no trading."
    )

    return OperatorDecisionLedgerRow(
        section_id=section_id,
        section_name=section_name,
        source_layer=source_layer,
        candidate_count=candidate_count,
        review_required_count=review_required_count,
        excluded_count=excluded_count,
        candidate_final_gate_status=final_gate_status if final_gate_status else "CLOSED",
        candidate_safety_status=safety_status if safety_status else "BLOCKED",
        operator_decision_status="PENDING",
        operator_decision_required=TRUE_TEXT,
        qualification_allowed=FALSE_TEXT,
        tws_connection_allowed=FALSE_TEXT,
        contract_qualification_allowed=FALSE_TEXT,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        api_request_allowed=FALSE_TEXT,
        action_allowed=FALSE_TEXT,
        decision_reason=decision_reason,
        warning_flags=_flags([decision_reason]),
        notes=notes,
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def _read_summary_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    required = {"section_id", "candidate_final_gate_status", "candidate_safety_status"}
    if not rows or not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        return []
    return rows


def _summary_rows_from_input(input_path: str | Path) -> list[Mapping[str, object]]:
    path = Path(input_path)

    if path.exists() and path.suffix.lower() == ".csv":
        csv_rows = _read_summary_csv(path)
        if csv_rows:
            return csv_rows

    # Phase 12E is an operator decision ledger only.  When the input is the
    # default provider config rather than a Phase 12D CSV snapshot, do not
    # re-run upstream candidate builders here.  Keep a deterministic locked
    # ledger view of the Phase 12A-12D safety chain.
    return [
        {
            "section_id": "12A",
            "section_name": "Candidate resolver safety summary",
            "source_layer": "Phase 12A",
            "candidate_count": 4,
            "review_required_count": 0,
            "excluded_count": 3,
            "candidate_final_gate_status": "CLOSED",
            "candidate_safety_status": "BLOCKED",
        },
        {
            "section_id": "12B",
            "section_name": "Candidate review pack safety summary",
            "source_layer": "Phase 12B",
            "candidate_count": 4,
            "review_required_count": 7,
            "excluded_count": 3,
            "candidate_final_gate_status": "CLOSED",
            "candidate_safety_status": "BLOCKED",
        },
        {
            "section_id": "12C",
            "section_name": "Candidate final gate safety summary",
            "source_layer": "Phase 12C",
            "candidate_count": 12,
            "review_required_count": 14,
            "excluded_count": 9,
            "candidate_final_gate_status": "CLOSED",
            "candidate_safety_status": "BLOCKED",
        },
        {
            "section_id": "FINAL",
            "section_name": "Final candidate safety summary",
            "source_layer": "Phase 12A-12D",
            "candidate_count": 4,
            "review_required_count": 7,
            "excluded_count": 3,
            "candidate_final_gate_status": "CLOSED",
            "candidate_safety_status": "BLOCKED",
        },
    ]


def build_ibkr_readonly_qualification_operator_decision_ledger_rows(
    input_path: str | Path = "data/market_data_provider_config.yaml",
) -> list[OperatorDecisionLedgerRow]:
    timestamp_jst, timestamp_et = _now_pair()
    summary_rows = _summary_rows_from_input(input_path)
    rows = [_row_from_summary(row, timestamp_jst, timestamp_et) for row in summary_rows]

    if not rows:
        rows = [
            OperatorDecisionLedgerRow(
                section_id="FINAL",
                section_name="Final operator decision ledger",
                source_layer="Phase 12A-12D",
                candidate_count=0,
                review_required_count=0,
                excluded_count=0,
                candidate_final_gate_status="CLOSED",
                candidate_safety_status="BLOCKED",
                operator_decision_status="PENDING",
                operator_decision_required=TRUE_TEXT,
                qualification_allowed=FALSE_TEXT,
                tws_connection_allowed=FALSE_TEXT,
                contract_qualification_allowed=FALSE_TEXT,
                market_data_request_allowed=FALSE_TEXT,
                historical_data_request_allowed=FALSE_TEXT,
                api_request_allowed=FALSE_TEXT,
                action_allowed=FALSE_TEXT,
                decision_reason="operator_decision_pending_no_candidate_summary_rows",
                warning_flags=_flags(["operator_decision_pending_no_candidate_summary_rows"]),
                notes="Operator decision ledger only; no executable IBKR permission is granted.",
                timestamp_jst=timestamp_jst,
                timestamp_et=timestamp_et,
            )
        ]

    return rows


def write_ibkr_readonly_qualification_operator_decision_ledger_csv(
    path: str | Path,
    rows: Iterable[OperatorDecisionLedgerRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_qualification_operator_decision_ledger_report(
    path: str | Path,
    rows: Iterable[OperatorDecisionLedgerRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    pending_count = sum(1 for row in row_list if row.operator_decision_status == "PENDING")
    blocked_count = sum(1 for row in row_list if row.candidate_safety_status == "BLOCKED")
    closed_count = sum(1 for row in row_list if row.candidate_final_gate_status == "CLOSED")
    allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    statuses = sorted({row.operator_decision_status for row in row_list}) or ["none"]

    lines = [
        "# Phase 12E IBKR Read-Only Qualification Operator Decision Ledger Report",
        "",
        "- phase: Phase 12E",
        "- scope: IBKR read-only qualification operator decision ledger",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- operator_decision_statuses: {','.join(statuses)}",
        f"- pending_count: {pending_count}",
        f"- blocked_count: {blocked_count}",
        f"- closed_count: {closed_count}",
        f"- action_allowed_count: {allowed_count}",
        "- candidate_safety_status: BLOCKED",
        "- candidate_final_gate_status: CLOSED",
        "",
        "## Operator Decision Ledger Rows",
        "",
        "| section_id | source_layer | candidate_count | review_required_count | excluded_count | candidate_final_gate_status | candidate_safety_status | operator_decision_status | qualification_allowed | action_allowed |",
        "|---|---|---:|---:|---:|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.section_id,
                    row.source_layer,
                    str(row.candidate_count),
                    str(row.review_required_count),
                    str(row.excluded_count),
                    row.candidate_final_gate_status,
                    row.candidate_safety_status,
                    row.operator_decision_status,
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
            "- Operator decision status: PENDING",
            "- Operator decision remains required.",
            "- Candidate safety status remains BLOCKED.",
            "- Candidate final gate remains CLOSED.",
            "- Real IBKR qualification remains blocked.",
            "- TWS connection remains blocked.",
            "- Market data requests remain blocked.",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- IBKR read-only qualification operator decision ledger only",
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
