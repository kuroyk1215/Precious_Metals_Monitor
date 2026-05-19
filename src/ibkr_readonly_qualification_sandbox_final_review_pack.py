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
    "SANDBOX_FINAL_REVIEW_PACK",
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
    "phase13g_ibkr_readonly_qualification_sandbox_final_review_pack",
)


@dataclass(frozen=True)
class SandboxFinalReviewPackRow:
    review_id: str
    review_name: str
    source_layer: str
    sandbox_final_review_status: str
    sandbox_safety_gate_status: str
    sandbox_result_accepted_for_review: str
    simulated_result_only: str
    sandbox_qualification_status: str
    simulated_qualification_result: str
    simulated_symbol: str
    simulated_contract_id: str
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
    review_decision: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "review_id",
    "review_name",
    "source_layer",
    "sandbox_final_review_status",
    "sandbox_safety_gate_status",
    "sandbox_result_accepted_for_review",
    "simulated_result_only",
    "sandbox_qualification_status",
    "simulated_qualification_result",
    "simulated_symbol",
    "simulated_contract_id",
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
    "review_decision",
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


def _read_safety_gate_csv(path: Path) -> list[Mapping[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    required = {
        "gate_id",
        "sandbox_safety_gate_status",
        "sandbox_result_accepted_for_review",
        "simulated_result_only",
        "action_allowed",
    }
    if not rows or not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        return []

    return rows


def _default_safety_gate_rows() -> list[Mapping[str, object]]:
    return [
        {
            "gate_id": "13A",
            "gate_name": "Sandbox design review",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "sandbox_qualification_status": "NOT_SIMULATED",
            "simulated_qualification_result": "DESIGN_REVIEW_ONLY",
            "simulated_symbol": "",
            "simulated_contract_id": "",
            "action_allowed": "false",
        },
        {
            "gate_id": "13B",
            "gate_name": "Sandbox input contract review",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "sandbox_qualification_status": "NOT_SIMULATED",
            "simulated_qualification_result": "INPUT_CONTRACT_REVIEW_ONLY",
            "simulated_symbol": "",
            "simulated_contract_id": "",
            "action_allowed": "false",
        },
        {
            "gate_id": "13C",
            "gate_name": "Sandbox input validator review",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "sandbox_qualification_status": "NOT_SIMULATED",
            "simulated_qualification_result": "INPUT_VALIDATOR_REVIEW_ONLY",
            "simulated_symbol": "",
            "simulated_contract_id": "",
            "action_allowed": "false",
        },
        {
            "gate_id": "13D",
            "gate_name": "Sandbox qualification simulator review",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "sandbox_qualification_status": "SIMULATED",
            "simulated_qualification_result": "QUALIFIED_SIMULATED",
            "simulated_symbol": "1540,1542,518880",
            "simulated_contract_id": "SIM-1540,SIM-1542,SIM-518880",
            "action_allowed": "false",
        },
        {
            "gate_id": "13E",
            "gate_name": "Sandbox result pack review",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "sandbox_qualification_status": "SIMULATED",
            "simulated_qualification_result": "RESULT_PACK_BUILT_SIMULATED_ONLY",
            "simulated_symbol": "1540,1542,518880",
            "simulated_contract_id": "SIM-1540,SIM-1542,SIM-518880",
            "action_allowed": "false",
        },
        {
            "gate_id": "13F",
            "gate_name": "Sandbox safety gate review",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "sandbox_qualification_status": "NOT_SIMULATED",
            "simulated_qualification_result": "SAFETY_GATE_CLOSED",
            "simulated_symbol": "",
            "simulated_contract_id": "",
            "action_allowed": "false",
        },
        {
            "gate_id": "FINAL",
            "gate_name": "Final sandbox review pack",
            "sandbox_safety_gate_status": "CLOSED",
            "sandbox_result_accepted_for_review": "true",
            "simulated_result_only": "true",
            "sandbox_qualification_status": "NOT_SIMULATED",
            "simulated_qualification_result": "FINAL_REVIEW_PACK_READY",
            "simulated_symbol": "",
            "simulated_contract_id": "",
            "action_allowed": "false",
        },
    ]


def _source_rows(input_source: str | Path) -> list[Mapping[str, object]]:
    path = Path(input_source)
    if path.exists() and path.suffix.lower() == ".csv":
        rows = _read_safety_gate_csv(path)
        if rows:
            return rows
    return _default_safety_gate_rows()


def _make_row(source: Mapping[str, object], timestamp_jst: str, timestamp_et: str) -> SandboxFinalReviewPackRow:
    review_id = str(source.get("gate_id") or source.get("review_id") or "UNKNOWN")
    review_name = str(source.get("gate_name") or source.get("review_name") or review_id)

    upstream_action_allowed = str(source.get("action_allowed") or "false").lower()
    upstream_gate_status = str(source.get("sandbox_safety_gate_status") or "CLOSED").upper()
    upstream_simulated_only = str(source.get("simulated_result_only") or "true").lower()

    if upstream_action_allowed == "true" or upstream_gate_status != "CLOSED" or upstream_simulated_only != "true":
        review_decision = "upstream_unlock_attempt_detected_final_review_kept_locked"
    else:
        review_decision = "sandbox_final_review_ready_safety_gate_closed"

    if review_id == "FINAL":
        review_decision = "sandbox_final_review_pack_ready_but_execution_blocked"

    return SandboxFinalReviewPackRow(
        review_id=review_id,
        review_name=review_name,
        source_layer="Phase 13G",
        sandbox_final_review_status="READY_FOR_REVIEW",
        sandbox_safety_gate_status="CLOSED",
        sandbox_result_accepted_for_review=TRUE_TEXT,
        simulated_result_only=TRUE_TEXT,
        sandbox_qualification_status=str(source.get("sandbox_qualification_status") or "NOT_SIMULATED").upper(),
        simulated_qualification_result=str(source.get("simulated_qualification_result") or "FINAL_REVIEW_ONLY"),
        simulated_symbol=str(source.get("simulated_symbol") or source.get("symbol") or ""),
        simulated_contract_id=str(source.get("simulated_contract_id") or ""),
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
        review_decision=review_decision,
        warning_flags=_flags([review_decision]),
        notes=(
            "Sandbox final review pack only. Sandbox outputs are ready for human review but not execution. "
            "Safety gate remains CLOSED. Real TWS connection, IBKR API requests, real contract qualification, "
            "market data, historical data, orders, cancels, rebalancing, and auto-trading remain blocked."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_qualification_sandbox_final_review_pack_rows(
    input_source: str | Path = "data/market_data_provider_config.yaml",
) -> list[SandboxFinalReviewPackRow]:
    timestamp_jst, timestamp_et = _now_pair()
    return [_make_row(row, timestamp_jst, timestamp_et) for row in _source_rows(input_source)]


def write_ibkr_readonly_qualification_sandbox_final_review_pack_csv(
    path: str | Path,
    rows: Iterable[SandboxFinalReviewPackRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_qualification_sandbox_final_review_pack_report(
    path: str | Path,
    rows: Iterable[SandboxFinalReviewPackRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    ready_count = sum(1 for row in row_list if row.sandbox_final_review_status == "READY_FOR_REVIEW")
    closed_count = sum(1 for row in row_list if row.sandbox_safety_gate_status == "CLOSED")
    review_count = sum(1 for row in row_list if row.sandbox_result_accepted_for_review == TRUE_TEXT)
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    statuses = sorted({row.sandbox_final_review_status for row in row_list}) or ["none"]

    lines = [
        "# Phase 13G IBKR Read-Only Qualification Sandbox Final Review Pack Report",
        "",
        "- phase: Phase 13G",
        "- scope: IBKR read-only qualification sandbox final review pack",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- sandbox_final_review_statuses: {','.join(statuses)}",
        f"- ready_for_review_count: {ready_count}",
        f"- safety_gate_closed_count: {closed_count}",
        f"- review_accepted_count: {review_count}",
        f"- action_allowed_count: {action_allowed_count}",
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
        "## Sandbox Final Review Pack Rows",
        "",
        "| review_id | sandbox_final_review_status | sandbox_safety_gate_status | sandbox_result_accepted_for_review | simulated_result_only | real_qualification_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.review_id,
                    row.sandbox_final_review_status,
                    row.sandbox_safety_gate_status,
                    row.sandbox_result_accepted_for_review,
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
            "- Phase 13G sandbox final review pack report only",
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
