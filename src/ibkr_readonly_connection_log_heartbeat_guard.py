from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union
from zoneinfo import ZoneInfo

from src.ibkr_readonly_first_connect_disconnect import (
    PASS_TEXT,
    build_ibkr_readonly_first_connect_disconnect_rows,
)


TRUE_TEXT = "true"
FALSE_TEXT = "false"

DRY_RUN_READY = "DRY_RUN_READY"
PASS_STATUS = "PASS"
FAIL_STATUS = "FAIL"
SKIPPED_STATUS = "SKIPPED"
LOG_READY = "LOG_READY"
HEARTBEAT_READY = "HEARTBEAT_READY"
HEARTBEAT_METADATA_PARTIAL = "HEARTBEAT_METADATA_PARTIAL"
HEARTBEAT_BLOCKED = "HEARTBEAT_BLOCKED"

DEFAULT_WARNING_FLAGS = (
    "CONNECTION_LOG_HEARTBEAT_GUARD_DEFINED",
    "CONNECT_DISCONNECT_METADATA_ONLY",
    "NO_MARKET_DATA_REQUEST",
    "NO_HISTORICAL_DATA_REQUEST",
    "NO_CONTRACT_QUALIFICATION",
    "ORDER_ACTION_BLOCKED",
    "CANCELLATION_ACTION_BLOCKED",
    "REBALANCE_BLOCKED",
    "AUTO_TRADE_BLOCKED",
    "phase17c17d_ibkr_readonly_connection_log_heartbeat_guard",
)


@dataclass(frozen=True)
class ConnectionLogHeartbeatGuardRow:
    row_id: str
    row_name: str
    source_layer: str
    input_source: str
    selected_profile: str
    execute_requested: str
    component: str
    status: str
    first_connect_status: str
    connection_attempted: str
    connect_succeeded: str
    disconnect_succeeded: str
    server_version: str
    connection_time: str
    heartbeat_metadata_available: str
    log_retention_required: str
    current_call_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    contract_qualification_allowed: str
    order_action_allowed: str
    cancellation_action_allowed: str
    rebalance_action_allowed: str
    auto_trade_allowed: str
    action_allowed: str
    evidence: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "row_id",
    "row_name",
    "source_layer",
    "input_source",
    "selected_profile",
    "execute_requested",
    "component",
    "status",
    "first_connect_status",
    "connection_attempted",
    "connect_succeeded",
    "disconnect_succeeded",
    "server_version",
    "connection_time",
    "heartbeat_metadata_available",
    "log_retention_required",
    "current_call_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "contract_qualification_allowed",
    "order_action_allowed",
    "cancellation_action_allowed",
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
    row_id,
    row_name,
    input_source,
    selected_profile,
    execute_requested,
    component,
    status,
    first_connect_status,
    connection_attempted,
    connect_succeeded,
    disconnect_succeeded,
    server_version,
    connection_time,
    heartbeat_metadata_available,
    log_retention_required,
    current_call_allowed,
    evidence,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return ConnectionLogHeartbeatGuardRow(
        row_id=row_id,
        row_name=row_name,
        source_layer="Phase 17C-17D",
        input_source=str(input_source),
        selected_profile=selected_profile,
        execute_requested=TRUE_TEXT if execute_requested else FALSE_TEXT,
        component=component,
        status=status,
        first_connect_status=first_connect_status,
        connection_attempted=connection_attempted,
        connect_succeeded=connect_succeeded,
        disconnect_succeeded=disconnect_succeeded,
        server_version=server_version,
        connection_time=connection_time,
        heartbeat_metadata_available=heartbeat_metadata_available,
        log_retention_required=log_retention_required,
        current_call_allowed=current_call_allowed,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        contract_qualification_allowed=FALSE_TEXT,
        order_action_allowed=FALSE_TEXT,
        cancellation_action_allowed=FALSE_TEXT,
        rebalance_action_allowed=FALSE_TEXT,
        auto_trade_allowed=FALSE_TEXT,
        action_allowed=FALSE_TEXT,
        evidence=evidence,
        warning_flags=_flags(extra_flags),
        notes=(
            "Phase 17C-17D connection log and heartbeat guard only. Default mode is dry-run. "
            "When explicitly executed, it reuses the Phase 17A connect/disconnect metadata-only "
            "flow. This phase must not request market data, historical data, contract details, "
            "or any trading action."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def _connect_row(rows):
    matches = [row for row in rows if row.row_id == "CONNECT_DISCONNECT"]
    return matches[0] if matches else rows[-1]


def build_ibkr_readonly_connection_log_heartbeat_guard_rows(
    input_source: Union[str, Path] = "config.yaml",
    execute: bool = False,
    connector_factory: Optional[Callable[[], Any]] = None,
):
    timestamp_jst, timestamp_et = _now_pair()
    input_source_text = str(input_source)

    first_rows = build_ibkr_readonly_first_connect_disconnect_rows(
        input_source,
        execute=execute,
        connector_factory=connector_factory,
    )

    connect_row = _connect_row(first_rows)
    final_first_row = first_rows[-1]

    selected_profile = final_first_row.selected_profile
    first_status = final_first_row.status

    server_version_available = connect_row.server_version not in {
        "not_requested",
        "unavailable",
        "",
    }
    connection_time_available = connect_row.connection_time not in {
        "not_requested",
        "unavailable",
        "",
    }
    metadata_available = server_version_available or connection_time_available
    connection_roundtrip_ok = (
        connect_row.connect_succeeded == TRUE_TEXT
        and connect_row.disconnect_succeeded == TRUE_TEXT
    )

    heartbeat_status = SKIPPED_STATUS
    if execute:
        if connection_roundtrip_ok and metadata_available:
            heartbeat_status = HEARTBEAT_READY
        elif connection_roundtrip_ok:
            heartbeat_status = HEARTBEAT_METADATA_PARTIAL
        else:
            heartbeat_status = HEARTBEAT_BLOCKED

    final_status = DRY_RUN_READY
    if execute:
        final_status = PASS_STATUS if first_status == PASS_TEXT and connection_roundtrip_ok else FAIL_STATUS

    rows = [
        _make_row(
            "FIRST_CONNECT_SUMMARY",
            "Phase 17A first connect/disconnect summary",
            input_source_text,
            selected_profile,
            execute,
            "connection_log",
            first_status,
            first_status,
            connect_row.connection_attempted,
            connect_row.connect_succeeded,
            connect_row.disconnect_succeeded,
            connect_row.server_version,
            connect_row.connection_time,
            TRUE_TEXT if metadata_available else FALSE_TEXT,
            TRUE_TEXT,
            connect_row.current_call_allowed,
            connect_row.evidence,
            timestamp_jst,
            timestamp_et,
            ["FIRST_CONNECT_SUMMARY"],
        ),
        _make_row(
            "LOG_RETENTION",
            "Connection log retention guard",
            input_source_text,
            selected_profile,
            execute,
            "log_retention",
            LOG_READY,
            first_status,
            connect_row.connection_attempted,
            connect_row.connect_succeeded,
            connect_row.disconnect_succeeded,
            connect_row.server_version,
            connect_row.connection_time,
            TRUE_TEXT if metadata_available else FALSE_TEXT,
            TRUE_TEXT,
            FALSE_TEXT,
            "retain connection status, selected profile, server version, connection time, and failure evidence",
            timestamp_jst,
            timestamp_et,
            ["CONNECTION_LOG_RETENTION_REQUIRED"],
        ),
        _make_row(
            "HEARTBEAT_METADATA_GUARD",
            "Heartbeat-style metadata guard",
            input_source_text,
            selected_profile,
            execute,
            "heartbeat_guard",
            heartbeat_status,
            first_status,
            connect_row.connection_attempted,
            connect_row.connect_succeeded,
            connect_row.disconnect_succeeded,
            connect_row.server_version,
            connect_row.connection_time,
            TRUE_TEXT if metadata_available else FALSE_TEXT,
            TRUE_TEXT,
            connect_row.current_call_allowed,
            (
                "heartbeat_metadata_available={};server_version_available={};"
                "connection_time_available={};connection_roundtrip_ok={}"
            ).format(
                str(metadata_available).lower(),
                str(server_version_available).lower(),
                str(connection_time_available).lower(),
                str(connection_roundtrip_ok).lower(),
            ),
            timestamp_jst,
            timestamp_et,
            [
                "HEARTBEAT_METADATA_AVAILABLE"
                if metadata_available
                else "HEARTBEAT_METADATA_PARTIAL_OR_UNAVAILABLE"
            ],
        ),
        _make_row(
            "FINAL",
            "Final connection log and heartbeat guard decision",
            input_source_text,
            selected_profile,
            execute,
            "final",
            final_status,
            first_status,
            connect_row.connection_attempted,
            connect_row.connect_succeeded,
            connect_row.disconnect_succeeded,
            connect_row.server_version,
            connect_row.connection_time,
            TRUE_TEXT if metadata_available else FALSE_TEXT,
            TRUE_TEXT,
            connect_row.current_call_allowed if execute else FALSE_TEXT,
            (
                "execute={};first_status={};metadata_available={};"
                "connect_succeeded={};disconnect_succeeded={}"
            ).format(
                str(execute).lower(),
                first_status,
                str(metadata_available).lower(),
                connect_row.connect_succeeded,
                connect_row.disconnect_succeeded,
            ),
            timestamp_jst,
            timestamp_et,
            ["PHASE17C17D_DRY_RUN_READY" if not execute else "PHASE17C17D_EXECUTION_RESULT"],
        ),
    ]

    return rows


def write_ibkr_readonly_connection_log_heartbeat_guard_csv(
    path: Union[str, Path],
    rows: Iterable[ConnectionLogHeartbeatGuardRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_connection_log_heartbeat_guard_report(
    path: Union[str, Path],
    rows: Iterable[ConnectionLogHeartbeatGuardRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    final_row = row_list[-1] if row_list else None
    selected_profile = final_row.selected_profile if final_row else "unknown"
    final_status = final_row.status if final_row else FAIL_STATUS

    actual_connection_rows = [
        row for row in row_list if row.row_id == "FIRST_CONNECT_SUMMARY"
    ]
    connection_attempt_count = sum(
        1 for row in actual_connection_rows if row.connection_attempted == TRUE_TEXT
    )
    connect_success_count = sum(
        1 for row in actual_connection_rows if row.connect_succeeded == TRUE_TEXT
    )
    disconnect_success_count = sum(
        1 for row in actual_connection_rows if row.disconnect_succeeded == TRUE_TEXT
    )
    metadata_available_count = sum(
        1 for row in row_list if row.heartbeat_metadata_available == TRUE_TEXT
    )
    current_call_allowed_count = sum(
        1 for row in actual_connection_rows if row.current_call_allowed == TRUE_TEXT
    )
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)

    lines = [
        "# Phase 17C-17D IBKR Read-Only Connection Log Heartbeat Guard Report",
        "",
        "- phase: Phase 17C-17D",
        "- scope: connection log retention and heartbeat-style metadata guard",
        f"- input_source: {input_source}",
        f"- selected_profile: {selected_profile}",
        f"- row_count: {len(row_list)}",
        f"- final_status: {final_status}",
        f"- connection_attempt_count: {connection_attempt_count}",
        f"- connect_success_count: {connect_success_count}",
        f"- disconnect_success_count: {disconnect_success_count}",
        f"- heartbeat_metadata_available_count: {metadata_available_count}",
        f"- current_call_allowed_count: {current_call_allowed_count}",
        "- counter_scope: FIRST_CONNECT_SUMMARY row only for actual connection counters",
        f"- action_allowed_count: {action_allowed_count}",
        "- market_data_request_allowed: false",
        "- historical_data_request_allowed: false",
        "- contract_qualification_allowed: false",
        "- order_action_allowed: false",
        "- cancellation_action_allowed: false",
        "- rebalance_action_allowed: false",
        "- auto_trade_allowed: false",
        "- action_allowed: false",
        "",
        "## Rows",
        "",
        "| row_id | component | status | first_connect_status | execute_requested | connection_attempted | connect_succeeded | disconnect_succeeded | server_version | connection_time | heartbeat_metadata_available | current_call_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.row_id,
                    row.component,
                    row.status,
                    row.first_connect_status,
                    row.execute_requested,
                    row.connection_attempted,
                    row.connect_succeeded,
                    row.disconnect_succeeded,
                    row.server_version,
                    row.connection_time,
                    row.heartbeat_metadata_available,
                    row.current_call_allowed,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Guard Rule",
            "",
            "- Default mode is dry-run and does not connect.",
            "- Explicit execution reuses the Phase 17A connect/disconnect metadata-only flow.",
            "- Heartbeat-style guard passes when connect/disconnect roundtrip succeeds; metadata availability is retained as diagnostics.",
            "- This phase does not request market data, historical data, contract details, or trading actions.",
            "",
            "## Safety Statement",
            "",
            "- no market data request",
            "- no historical data request",
            "- no real contract qualification",
            "- no order action",
            "- no cancellation action",
            "- no rebalance",
            "- no auto trade",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
