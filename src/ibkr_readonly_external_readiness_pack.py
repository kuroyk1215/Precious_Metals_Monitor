from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Union
from zoneinfo import ZoneInfo

from src.ibkr_readonly_preflight_profile_aware_final_gate import (
    GO_TEXT,
    build_ibkr_readonly_preflight_profile_aware_final_gate_rows,
)
from src.ibkr_readonly_tws_environment_checklist import (
    CHECKLIST_BLOCKED_TEXT,
    build_ibkr_readonly_tws_environment_checklist_rows,
)


TRUE_TEXT = "true"
FALSE_TEXT = "false"

READY_FOR_OPERATOR_REVIEW = "READY_FOR_OPERATOR_REVIEW"
BLOCKED = "BLOCKED"
MANUAL_REQUIRED = "MANUAL_REQUIRED"
NO_GO = "NO_GO"

DEFAULT_WARNING_FLAGS = (
    "EXTERNAL_READINESS_PACK_DEFINED",
    "OPERATOR_REVIEW_REQUIRED",
    "NO_TWS_CONNECTION",
    "NO_IBKR_CONNECTION",
    "IBKR_API_REQUEST_BLOCKED",
    "CONTRACT_QUALIFICATION_BLOCKED",
    "MARKET_DATA_REQUEST_BLOCKED",
    "HISTORICAL_DATA_REQUEST_BLOCKED",
    "ORDER_BLOCKED",
    "CANCEL_BLOCKED",
    "REBALANCE_BLOCKED",
    "AUTO_TRADE_BLOCKED",
    "phase15b15d_ibkr_readonly_external_readiness_pack",
)


@dataclass(frozen=True)
class ExternalReadinessPackRow:
    readiness_id: str
    readiness_name: str
    source_layer: str
    input_source: str
    selected_profile: str
    upstream_component: str
    upstream_status: str
    readiness_status: str
    operator_review_required: str
    operator_approved: str
    next_connection_phase_allowed: str
    evidence: str
    config_file_modified: str
    real_connection_allowed: str
    tws_connection_allowed: str
    ibkr_api_request_allowed: str
    contract_qualification_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    order_action_allowed: str
    cancel_action_allowed: str
    rebalance_action_allowed: str
    auto_trade_allowed: str
    action_allowed: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "readiness_id",
    "readiness_name",
    "source_layer",
    "input_source",
    "selected_profile",
    "upstream_component",
    "upstream_status",
    "readiness_status",
    "operator_review_required",
    "operator_approved",
    "next_connection_phase_allowed",
    "evidence",
    "config_file_modified",
    "real_connection_allowed",
    "tws_connection_allowed",
    "ibkr_api_request_allowed",
    "contract_qualification_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "auto_trade_allowed",
    "action_allowed",
    "warning_flags",
    "notes",
    "timestamp_jst",
    "timestamp_et",
]


def _now_pair():
    now_utc = datetime.now(ZoneInfo("UTC"))
    return (
        now_utc.astimezone(ZoneInfo("Asia/Tokyo")).isoformat(),
        now_utc.astimezone(ZoneInfo("America/New_York")).isoformat(),
    )


def _flags(extra=()):
    values = list(DEFAULT_WARNING_FLAGS)
    for item in extra:
        if item and item not in values:
            values.append(item)
    return ";".join(values)


def _make_row(
    readiness_id,
    readiness_name,
    input_source,
    selected_profile,
    upstream_component,
    upstream_status,
    readiness_status,
    operator_review_required,
    next_connection_phase_allowed,
    evidence,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return ExternalReadinessPackRow(
        readiness_id=readiness_id,
        readiness_name=readiness_name,
        source_layer="Phase 15B-15D",
        input_source=str(input_source),
        selected_profile=selected_profile,
        upstream_component=upstream_component,
        upstream_status=upstream_status,
        readiness_status=readiness_status,
        operator_review_required=operator_review_required,
        operator_approved=FALSE_TEXT,
        next_connection_phase_allowed=next_connection_phase_allowed,
        evidence=evidence,
        config_file_modified=FALSE_TEXT,
        real_connection_allowed=FALSE_TEXT,
        tws_connection_allowed=FALSE_TEXT,
        ibkr_api_request_allowed=FALSE_TEXT,
        contract_qualification_allowed=FALSE_TEXT,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        order_action_allowed=FALSE_TEXT,
        cancel_action_allowed=FALSE_TEXT,
        rebalance_action_allowed=FALSE_TEXT,
        auto_trade_allowed=FALSE_TEXT,
        action_allowed=FALSE_TEXT,
        warning_flags=_flags(extra_flags),
        notes=(
            "Phase 15B-15D external readiness pack only. This summarizes preflight final gate, "
            "TWS environment checklist, and operator review requirements before any later read-only "
            "connection phase. It does not connect to TWS or IBKR, does not modify config files, "
            "does not request market data or historical data, and does not allow trading actions."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_external_readiness_pack_rows(
    input_source: Union[str, Path] = "config.yaml",
):
    timestamp_jst, timestamp_et = _now_pair()
    input_source_text = str(input_source)

    final_gate_rows = build_ibkr_readonly_preflight_profile_aware_final_gate_rows(
        input_source,
        "auto",
    )
    checklist_rows = build_ibkr_readonly_tws_environment_checklist_rows(input_source)

    final_gate = final_gate_rows[-1]
    checklist_final = checklist_rows[-1]

    selected_profile = final_gate.selected_profile
    final_gate_go = final_gate.final_gate_decision == GO_TEXT
    checklist_blocked = any(
        row.checklist_status == CHECKLIST_BLOCKED_TEXT for row in checklist_rows
    )
    manual_required_count = sum(
        1 for row in checklist_rows if row.manual_check_required == TRUE_TEXT
    )

    readiness_blocked = not final_gate_go or checklist_blocked
    readiness_status = BLOCKED if readiness_blocked else READY_FOR_OPERATOR_REVIEW

    rows = [
        _make_row(
            "PREFLIGHT_FINAL_GATE",
            "Phase 14I profile-aware final gate summary",
            input_source_text,
            selected_profile,
            "Phase 14I",
            final_gate.final_gate_decision,
            READY_FOR_OPERATOR_REVIEW if final_gate_go else BLOCKED,
            TRUE_TEXT,
            FALSE_TEXT,
            final_gate.evidence,
            timestamp_jst,
            timestamp_et,
            ["PREFLIGHT_FINAL_GATE_GO" if final_gate_go else "PREFLIGHT_FINAL_GATE_NO_GO"],
        ),
        _make_row(
            "TWS_ENVIRONMENT_CHECKLIST",
            "Phase 15A TWS environment checklist summary",
            input_source_text,
            selected_profile,
            "Phase 15A",
            checklist_final.checklist_status,
            BLOCKED if checklist_blocked else READY_FOR_OPERATOR_REVIEW,
            TRUE_TEXT,
            FALSE_TEXT,
            "manual_required={};final_checklist_status={}".format(
                manual_required_count,
                checklist_final.checklist_status,
            ),
            timestamp_jst,
            timestamp_et,
            ["TWS_ENVIRONMENT_READY_FOR_REVIEW" if not checklist_blocked else "TWS_ENVIRONMENT_BLOCKED"],
        ),
        _make_row(
            "OPERATOR_REVIEW_LEDGER",
            "Operator review ledger placeholder",
            input_source_text,
            selected_profile,
            "Phase 15C",
            MANUAL_REQUIRED,
            MANUAL_REQUIRED,
            TRUE_TEXT,
            FALSE_TEXT,
            (
                "operator must manually confirm TWS profile, read-only API setting, "
                "trusted IP, socket port, and no trading action before any later connection phase"
            ),
            timestamp_jst,
            timestamp_et,
            ["OPERATOR_REVIEW_REQUIRED"],
        ),
        _make_row(
            "READONLY_CONNECTION_REVIEW_PACK",
            "Read-only connection go/no-go review pack placeholder",
            input_source_text,
            selected_profile,
            "Phase 15D",
            NO_GO,
            readiness_status,
            TRUE_TEXT,
            FALSE_TEXT,
            (
                "preflight_go={};checklist_blocked={};operator_approved=false"
            ).format(str(final_gate_go).lower(), str(checklist_blocked).lower()),
            timestamp_jst,
            timestamp_et,
            ["CONNECTION_REVIEW_PACK_NO_GO_UNTIL_OPERATOR_APPROVAL"],
        ),
        _make_row(
            "FINAL",
            "Final external readiness pack decision",
            input_source_text,
            selected_profile,
            "Phase 15B-15D",
            readiness_status,
            readiness_status,
            TRUE_TEXT,
            FALSE_TEXT,
            (
                "selected_profile={};preflight_go={};checklist_blocked={};"
                "manual_required={};operator_approved=false"
            ).format(
                selected_profile,
                str(final_gate_go).lower(),
                str(checklist_blocked).lower(),
                manual_required_count,
            ),
            timestamp_jst,
            timestamp_et,
            ["PHASE15B15D_READY_FOR_OPERATOR_REVIEW" if not readiness_blocked else "PHASE15B15D_BLOCKED"],
        ),
    ]

    return rows


def write_ibkr_readonly_external_readiness_pack_csv(
    path: Union[str, Path],
    rows: Iterable[ExternalReadinessPackRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_external_readiness_pack_report(
    path: Union[str, Path],
    rows: Iterable[ExternalReadinessPackRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    final_row = row_list[-1] if row_list else None
    selected_profile = final_row.selected_profile if final_row else "unknown"
    final_status = final_row.readiness_status if final_row else BLOCKED

    operator_required_count = sum(1 for row in row_list if row.operator_review_required == TRUE_TEXT)
    operator_approved_count = sum(1 for row in row_list if row.operator_approved == TRUE_TEXT)
    next_allowed_count = sum(1 for row in row_list if row.next_connection_phase_allowed == TRUE_TEXT)
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    modified_count = sum(1 for row in row_list if row.config_file_modified == TRUE_TEXT)

    lines = [
        "# Phase 15B-15D IBKR Read-Only External Readiness Pack Report",
        "",
        "- phase: Phase 15B-15D",
        "- scope: IBKR read-only external readiness pack",
        f"- input_source: {input_source}",
        f"- selected_profile: {selected_profile}",
        f"- row_count: {len(row_list)}",
        f"- final_readiness_status: {final_status}",
        f"- operator_review_required_count: {operator_required_count}",
        f"- operator_approved_count: {operator_approved_count}",
        f"- next_connection_phase_allowed_count: {next_allowed_count}",
        f"- config_file_modified_count: {modified_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- config_file_modified: false",
        "- real_connection_allowed: false",
        "- tws_connection_allowed: false",
        "- ibkr_api_request_allowed: false",
        "- contract_qualification_allowed: false",
        "- market_data_request_allowed: false",
        "- historical_data_request_allowed: false",
        "- order_action_allowed: false",
        "- cancel_action_allowed: false",
        "- rebalance_action_allowed: false",
        "- auto_trade_allowed: false",
        "- action_allowed: false",
        "",
        "## Readiness Rows",
        "",
        "| readiness_id | selected_profile | upstream_component | upstream_status | readiness_status | operator_review_required | operator_approved | next_connection_phase_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.readiness_id,
                    row.selected_profile,
                    row.upstream_component,
                    row.upstream_status,
                    row.readiness_status,
                    row.operator_review_required,
                    row.operator_approved,
                    row.next_connection_phase_allowed,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Manual Review Requirements",
            "",
            "- Confirm Phase 14I profile-aware final gate is GO.",
            "- Confirm Phase 15A TWS environment checklist has no BLOCKED rows.",
            "- Operator must manually confirm TWS/IB Gateway profile, socket port, read-only API setting, and trusted IP.",
            "- Operator approval is intentionally false in this pack.",
            "- The next connection phase remains disallowed until a later explicit approval gate is added.",
            "",
            "## Safety Statement",
            "",
            "- no configuration file is modified",
            "- no TWS connection",
            "- no IBKR connection",
            "- no IBKR API request",
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
