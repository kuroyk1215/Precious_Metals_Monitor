from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Union
from zoneinfo import ZoneInfo

from src.ibkr_readonly_connection_preflight_pack import (
    PREFLIGHT_READY,
    build_ibkr_readonly_connection_preflight_pack_rows,
)
from src.ibkr_readonly_external_readiness_pack import (
    READY_FOR_OPERATOR_REVIEW,
    build_ibkr_readonly_external_readiness_pack_rows,
)


TRUE_TEXT = "true"
FALSE_TEXT = "false"

READY_FOR_APPROVAL_REVIEW = "READY_FOR_APPROVAL_REVIEW"
NOT_AUTHORIZED = "NOT_AUTHORIZED"
BLOCKED = "BLOCKED"
KILL_SWITCH_LOCKED = "KILL_SWITCH_LOCKED"
APPROVAL_REQUIRED = "APPROVAL_REQUIRED"

DEFAULT_WARNING_FLAGS = (
    "AUTHORIZATION_PACK_DEFINED",
    "OPERATOR_APPROVAL_REQUIRED",
    "RUNTIME_KILL_SWITCH_LOCKED",
    "NO_TWS_CONNECTION",
    "NO_IBKR_CONNECTION",
    "IBKR_API_REQUEST_BLOCKED",
    "CONTRACT_QUALIFICATION_BLOCKED",
    "MARKET_DATA_REQUEST_BLOCKED",
    "HISTORICAL_DATA_REQUEST_BLOCKED",
    "ORDER_ACTION_BLOCKED",
    "CANCEL_ACTION_BLOCKED",
    "REBALANCE_BLOCKED",
    "AUTO_TRADE_BLOCKED",
    "phase16d16f_ibkr_readonly_authorization_pack",
)


@dataclass(frozen=True)
class AuthorizationPackRow:
    authorization_id: str
    authorization_name: str
    source_layer: str
    input_source: str
    selected_profile: str
    component: str
    upstream_status: str
    authorization_status: str
    operator_approval_required: str
    operator_approved: str
    runtime_kill_switch_enabled: str
    next_real_connection_phase_allowed: str
    current_connection_allowed: str
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
    evidence: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "authorization_id",
    "authorization_name",
    "source_layer",
    "input_source",
    "selected_profile",
    "component",
    "upstream_status",
    "authorization_status",
    "operator_approval_required",
    "operator_approved",
    "runtime_kill_switch_enabled",
    "next_real_connection_phase_allowed",
    "current_connection_allowed",
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
    "evidence",
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
    authorization_id,
    authorization_name,
    input_source,
    selected_profile,
    component,
    upstream_status,
    authorization_status,
    operator_approval_required,
    operator_approved,
    runtime_kill_switch_enabled,
    next_real_connection_phase_allowed,
    evidence,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return AuthorizationPackRow(
        authorization_id=authorization_id,
        authorization_name=authorization_name,
        source_layer="Phase 16D-16F",
        input_source=str(input_source),
        selected_profile=selected_profile,
        component=component,
        upstream_status=upstream_status,
        authorization_status=authorization_status,
        operator_approval_required=operator_approval_required,
        operator_approved=operator_approved,
        runtime_kill_switch_enabled=runtime_kill_switch_enabled,
        next_real_connection_phase_allowed=next_real_connection_phase_allowed,
        current_connection_allowed=FALSE_TEXT,
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
        evidence=evidence,
        warning_flags=_flags(extra_flags),
        notes=(
            "Phase 16D-16F authorization pack only. This creates an operator approval ledger, "
            "runtime kill-switch contract, and final authorization packet for a future "
            "connect/disconnect-only phase. It does not connect to TWS or IBKR, does not send API "
            "requests, does not qualify contracts, does not request market or historical data, and "
            "does not allow any trading action."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_authorization_pack_rows(
    input_source: Union[str, Path] = "config.yaml",
):
    timestamp_jst, timestamp_et = _now_pair()
    input_source_text = str(input_source)

    connection_preflight_rows = build_ibkr_readonly_connection_preflight_pack_rows(input_source)
    external_readiness_rows = build_ibkr_readonly_external_readiness_pack_rows(input_source)

    connection_final = connection_preflight_rows[-1]
    readiness_final = external_readiness_rows[-1]

    selected_profile = connection_final.selected_profile

    connection_preflight_ready = connection_final.preflight_status == PREFLIGHT_READY
    external_ready = readiness_final.readiness_status == READY_FOR_OPERATOR_REVIEW

    operator_approved = False
    runtime_kill_switch_enabled = True

    ready_for_review = connection_preflight_ready and external_ready
    final_authorized = ready_for_review and operator_approved and runtime_kill_switch_enabled

    rows = [
        _make_row(
            "CONNECTION_PREFLIGHT_SUMMARY",
            "Phase 16A-16C connection preflight summary",
            input_source_text,
            selected_profile,
            "Phase 16A-16C",
            connection_final.preflight_status,
            READY_FOR_APPROVAL_REVIEW if connection_preflight_ready else BLOCKED,
            TRUE_TEXT,
            FALSE_TEXT,
            TRUE_TEXT,
            FALSE_TEXT,
            connection_final.evidence,
            timestamp_jst,
            timestamp_et,
            [
                "CONNECTION_PREFLIGHT_READY"
                if connection_preflight_ready
                else "CONNECTION_PREFLIGHT_BLOCKED"
            ],
        ),
        _make_row(
            "EXTERNAL_READINESS_SUMMARY",
            "Phase 15B-15D external readiness summary",
            input_source_text,
            selected_profile,
            "Phase 15B-15D",
            readiness_final.readiness_status,
            READY_FOR_APPROVAL_REVIEW if external_ready else BLOCKED,
            TRUE_TEXT,
            FALSE_TEXT,
            TRUE_TEXT,
            FALSE_TEXT,
            readiness_final.evidence,
            timestamp_jst,
            timestamp_et,
            [
                "EXTERNAL_READY_FOR_OPERATOR_REVIEW"
                if external_ready
                else "EXTERNAL_READINESS_BLOCKED"
            ],
        ),
        _make_row(
            "OPERATOR_APPROVAL_LEDGER",
            "Operator approval ledger",
            input_source_text,
            selected_profile,
            "Phase 16D",
            APPROVAL_REQUIRED,
            APPROVAL_REQUIRED,
            TRUE_TEXT,
            FALSE_TEXT,
            TRUE_TEXT,
            FALSE_TEXT,
            (
                "operator_approved=false;operator must explicitly approve later connection "
                "scope before any real connection phase"
            ),
            timestamp_jst,
            timestamp_et,
            ["OPERATOR_APPROVAL_REQUIRED", "OPERATOR_APPROVED_FALSE"],
        ),
        _make_row(
            "RUNTIME_KILL_SWITCH",
            "Runtime kill-switch contract",
            input_source_text,
            selected_profile,
            "Phase 16E",
            KILL_SWITCH_LOCKED,
            KILL_SWITCH_LOCKED,
            TRUE_TEXT,
            FALSE_TEXT,
            TRUE_TEXT,
            FALSE_TEXT,
            (
                "runtime_kill_switch_enabled=true;current_connection_allowed=false;"
                "next_real_connection_phase_allowed=false"
            ),
            timestamp_jst,
            timestamp_et,
            ["RUNTIME_KILL_SWITCH_LOCKED"],
        ),
        _make_row(
            "FINAL_AUTHORIZATION_PACKET",
            "Final authorization packet",
            input_source_text,
            selected_profile,
            "Phase 16F",
            NOT_AUTHORIZED,
            NOT_AUTHORIZED,
            TRUE_TEXT,
            FALSE_TEXT,
            TRUE_TEXT,
            FALSE_TEXT,
            (
                "ready_for_review={};operator_approved=false;"
                "runtime_kill_switch_enabled=true;final_authorized=false"
            ).format(str(ready_for_review).lower()),
            timestamp_jst,
            timestamp_et,
            ["FINAL_AUTHORIZATION_PACKET_NOT_AUTHORIZED"],
        ),
        _make_row(
            "FINAL",
            "Final read-only authorization decision",
            input_source_text,
            selected_profile,
            "Phase 16D-16F",
            NOT_AUTHORIZED if not final_authorized else READY_FOR_APPROVAL_REVIEW,
            NOT_AUTHORIZED,
            TRUE_TEXT,
            FALSE_TEXT,
            TRUE_TEXT,
            FALSE_TEXT,
            (
                "selected_profile={};connection_preflight_ready={};external_ready={};"
                "operator_approved=false;runtime_kill_switch_enabled=true;"
                "next_real_connection_phase_allowed=false"
            ).format(
                selected_profile,
                str(connection_preflight_ready).lower(),
                str(external_ready).lower(),
            ),
            timestamp_jst,
            timestamp_et,
            ["PHASE16D16F_NOT_AUTHORIZED"],
        ),
    ]

    return rows


def write_ibkr_readonly_authorization_pack_csv(
    path: Union[str, Path],
    rows: Iterable[AuthorizationPackRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_authorization_pack_report(
    path: Union[str, Path],
    rows: Iterable[AuthorizationPackRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    final_row = row_list[-1] if row_list else None
    selected_profile = final_row.selected_profile if final_row else "unknown"
    final_status = final_row.authorization_status if final_row else NOT_AUTHORIZED

    operator_required_count = sum(1 for row in row_list if row.operator_approval_required == TRUE_TEXT)
    operator_approved_count = sum(1 for row in row_list if row.operator_approved == TRUE_TEXT)
    kill_switch_enabled_count = sum(1 for row in row_list if row.runtime_kill_switch_enabled == TRUE_TEXT)
    next_allowed_count = sum(1 for row in row_list if row.next_real_connection_phase_allowed == TRUE_TEXT)
    current_connection_allowed_count = sum(1 for row in row_list if row.current_connection_allowed == TRUE_TEXT)
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    modified_count = sum(1 for row in row_list if row.config_file_modified == TRUE_TEXT)

    lines = [
        "# Phase 16D-16F IBKR Read-Only Authorization Pack Report",
        "",
        "- phase: Phase 16D-16F",
        "- scope: IBKR read-only authorization pack",
        f"- input_source: {input_source}",
        f"- selected_profile: {selected_profile}",
        f"- row_count: {len(row_list)}",
        f"- final_authorization_status: {final_status}",
        f"- operator_review_required_count: {operator_required_count}",
        f"- operator_approved_count: {operator_approved_count}",
        f"- runtime_kill_switch_enabled_count: {kill_switch_enabled_count}",
        f"- current_connection_allowed_count: {current_connection_allowed_count}",
        f"- next_real_connection_phase_allowed_count: {next_allowed_count}",
        f"- config_file_modified_count: {modified_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- config_file_modified: false",
        "- current_connection_allowed: false",
        "- next_real_connection_phase_allowed: false",
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
        "## Authorization Rows",
        "",
        "| authorization_id | selected_profile | component | upstream_status | authorization_status | operator_approved | runtime_kill_switch_enabled | next_real_connection_phase_allowed | current_connection_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.authorization_id,
                    row.selected_profile,
                    row.component,
                    row.upstream_status,
                    row.authorization_status,
                    row.operator_approved,
                    row.runtime_kill_switch_enabled,
                    row.next_real_connection_phase_allowed,
                    row.current_connection_allowed,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Authorization Rule",
            "",
            "- Operator approval is intentionally false in this pack.",
            "- Runtime kill-switch is locked before any future connection phase.",
            "- Current connection is not allowed in this phase.",
            "- Next real connection phase is not allowed until a later explicit approval gate changes it.",
            "- Future connection scope must remain connect/disconnect only until separately expanded.",
            "",
            "## Safety Statement",
            "",
            "- no TWS connection",
            "- no IBKR connection",
            "- no IBKR API request",
            "- no real contract qualification",
            "- no reqMktData",
            "- no reqHistoricalData",
            "- no order action",
            "- no cancellation action",
            "- no rebalance",
            "- no auto trade",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
