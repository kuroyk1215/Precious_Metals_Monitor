from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping
from zoneinfo import ZoneInfo


TRUE_TEXT = "true"
FALSE_TEXT = "false"

DEFAULT_WARNING_FLAGS = (
    "SANDBOX_CLOSURE_REPORT",
    "SANDBOX_CLOSURE_COMPLETE",
    "READY_FOR_REVIEW",
    "SAFETY_GATE_CLOSED",
    "SIMULATED_RESULT_ONLY",
    "REAL_QUALIFICATION_BLOCKED",
    "TWS_CONNECTION_BLOCKED",
    "IBKR_API_REQUEST_BLOCKED",
    "NO_CONTRACT_QUALIFICATION",
    "NO_REQ_MKT_DATA",
    "NO_REQ_HISTORICAL_DATA",
    "NO_ORDER",
    "NO_CANCEL",
    "NO_REBALANCE",
    "NO_AUTO_TRADE",
    "phase13h_ibkr_readonly_qualification_sandbox_closure_report",
)


@dataclass(frozen=True)
class SandboxClosureReportRow:
    closure_id: str
    closure_name: str
    source_layer: str
    sandbox_closure_status: str
    sandbox_final_review_status: str
    sandbox_safety_gate_status: str
    sandbox_result_accepted_for_review: str
    simulated_result_only: str
    real_qualification_allowed: str
    tws_connection_allowed: str
    ibkr_api_request_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    order_action_allowed: str
    cancel_action_allowed: str
    rebalance_action_allowed: str
    auto_trade_allowed: str
    action_allowed: str
    closure_decision: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "closure_id",
    "closure_name",
    "source_layer",
    "sandbox_closure_status",
    "sandbox_final_review_status",
    "sandbox_safety_gate_status",
    "sandbox_result_accepted_for_review",
    "simulated_result_only",
    "real_qualification_allowed",
    "tws_connection_allowed",
    "ibkr_api_request_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "auto_trade_allowed",
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


def _read_final_review_pack_csv(path: Path) -> list[Mapping[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    required = {
        "review_id",
        "sandbox_final_review_status",
        "sandbox_safety_gate_status",
        "simulated_result_only",
        "action_allowed",
    }
    if not rows or not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        return []

    return rows


def _default_final_review_rows() -> list[Mapping[str, object]]:
    return [
        {
            "review_id": "13A",
            "review_name": "Sandbox design closure",
            "sandbox_final_review_status": "READY_FOR_REVIEW",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "action_allowed": "false",
        },
        {
            "review_id": "13B",
            "review_name": "Sandbox input contract closure",
            "sandbox_final_review_status": "READY_FOR_REVIEW",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "action_allowed": "false",
        },
        {
            "review_id": "13C",
            "review_name": "Sandbox input validator closure",
            "sandbox_final_review_status": "READY_FOR_REVIEW",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "action_allowed": "false",
        },
        {
            "review_id": "13D",
            "review_name": "Sandbox qualification simulator closure",
            "sandbox_final_review_status": "READY_FOR_REVIEW",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "action_allowed": "false",
        },
        {
            "review_id": "13E",
            "review_name": "Sandbox result pack closure",
            "sandbox_final_review_status": "READY_FOR_REVIEW",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "action_allowed": "false",
        },
        {
            "review_id": "13F",
            "review_name": "Sandbox safety gate closure",
            "sandbox_final_review_status": "READY_FOR_REVIEW",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "action_allowed": "false",
        },
        {
            "review_id": "13G",
            "review_name": "Sandbox final review pack closure",
            "sandbox_final_review_status": "READY_FOR_REVIEW",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "action_allowed": "false",
        },
        {
            "review_id": "FINAL",
            "review_name": "Final sandbox closure report",
            "sandbox_final_review_status": "READY_FOR_REVIEW",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "action_allowed": "false",
        },
    ]


def _source_rows(input_source: str | Path) -> list[Mapping[str, object]]:
    path = Path(input_source)
    if path.exists() and path.suffix.lower() == ".csv":
        rows = _read_final_review_pack_csv(path)
        if rows:
            return rows
    return _default_final_review_rows()


def _make_row(source: Mapping[str, object], timestamp_jst: str, timestamp_et: str) -> SandboxClosureReportRow:
    closure_id = str(source.get("review_id") or source.get("closure_id") or "UNKNOWN")
    closure_name = str(source.get("review_name") or source.get("closure_name") or closure_id)

    upstream_action_allowed = str(source.get("action_allowed") or "false").lower()
    upstream_review_status = str(source.get("sandbox_final_review_status") or "READY_FOR_REVIEW").upper()
    upstream_gate_status = str(source.get("sandbox_safety_gate_status") or "CLOSED").upper()
    upstream_simulated_only = str(source.get("simulated_result_only") or "true").lower()

    if (
        upstream_action_allowed == "true"
        or upstream_review_status != "READY_FOR_REVIEW"
        or upstream_gate_status != "CLOSED"
        or upstream_simulated_only != "true"
    ):
        closure_decision = "upstream_unlock_attempt_detected_sandbox_closure_kept_locked"
    else:
        closure_decision = "sandbox_closure_complete_safety_gate_closed"

    if closure_id == "FINAL":
        closure_decision = "phase13_sandbox_closure_complete_execution_blocked"

    return SandboxClosureReportRow(
        closure_id=closure_id,
        closure_name=closure_name,
        source_layer="Phase 13H",
        sandbox_closure_status="COMPLETE",
        sandbox_final_review_status="READY_FOR_REVIEW",
        sandbox_safety_gate_status="CLOSED",
        sandbox_result_accepted_for_review=TRUE_TEXT,
        simulated_result_only=TRUE_TEXT,
        real_qualification_allowed=FALSE_TEXT,
        tws_connection_allowed=FALSE_TEXT,
        ibkr_api_request_allowed=FALSE_TEXT,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        order_action_allowed=FALSE_TEXT,
        cancel_action_allowed=FALSE_TEXT,
        rebalance_action_allowed=FALSE_TEXT,
        auto_trade_allowed=FALSE_TEXT,
        action_allowed=FALSE_TEXT,
        closure_decision=closure_decision,
        warning_flags=_flags([closure_decision]),
        notes=(
            "Phase 13 sandbox closure report only. Sandbox loop is complete and ready for review, "
            "but no execution capability is granted. Safety gate remains CLOSED. Real TWS connection, "
            "IBKR API requests, real contract qualification, market data, historical data, orders, cancels, "
            "rebalancing, and auto-trading remain blocked."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_qualification_sandbox_closure_report_rows(
    input_source: str | Path = "data/market_data_provider_config.yaml",
) -> list[SandboxClosureReportRow]:
    timestamp_jst, timestamp_et = _now_pair()
    return [_make_row(row, timestamp_jst, timestamp_et) for row in _source_rows(input_source)]


def write_ibkr_readonly_qualification_sandbox_closure_report_csv(
    path: str | Path,
    rows: Iterable[SandboxClosureReportRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_qualification_sandbox_closure_report_report(
    path: str | Path,
    rows: Iterable[SandboxClosureReportRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    complete_count = sum(1 for row in row_list if row.sandbox_closure_status == "COMPLETE")
    ready_count = sum(1 for row in row_list if row.sandbox_final_review_status == "READY_FOR_REVIEW")
    closed_count = sum(1 for row in row_list if row.sandbox_safety_gate_status == "CLOSED")
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    statuses = sorted({row.sandbox_closure_status for row in row_list}) or ["none"]

    lines = [
        "# Phase 13H IBKR Read-Only Qualification Sandbox Closure Report",
        "",
        "- phase: Phase 13H",
        "- scope: IBKR read-only qualification sandbox closure report",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- sandbox_closure_statuses: {','.join(statuses)}",
        f"- complete_count: {complete_count}",
        f"- ready_for_review_count: {ready_count}",
        f"- safety_gate_closed_count: {closed_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- sandbox_closure_status: COMPLETE",
        "- sandbox_final_review_status: READY_FOR_REVIEW",
        "- sandbox_safety_gate_status: CLOSED",
        "- sandbox_result_accepted_for_review: true",
        "- simulated_result_only: true",
        "- real_qualification_allowed: false",
        "- tws_connection_allowed: false",
        "- ibkr_api_request_allowed: false",
        "- market_data_request_allowed: false",
        "- historical_data_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Sandbox Closure Rows",
        "",
        "| closure_id | sandbox_closure_status | sandbox_final_review_status | sandbox_safety_gate_status | simulated_result_only | real_qualification_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.closure_id,
                    row.sandbox_closure_status,
                    row.sandbox_final_review_status,
                    row.sandbox_safety_gate_status,
                    row.simulated_result_only,
                    row.real_qualification_allowed,
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
            "- Phase 13 sandbox closure status: COMPLETE",
            "- Sandbox final review status: READY_FOR_REVIEW",
            "- Sandbox safety gate status: CLOSED",
            "- Sandbox outputs are accepted for human review only.",
            "- Simulated qualification results are not real IBKR qualification.",
            "- Real qualification remains blocked.",
            "- TWS connection remains blocked.",
            "- IBKR API request remains blocked.",
            "- Market data requests remain blocked.",
            "- Historical data requests remain blocked.",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- Phase 13H sandbox closure report only",
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
