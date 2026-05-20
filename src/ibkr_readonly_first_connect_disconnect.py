from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union
from zoneinfo import ZoneInfo

from src.ibkr_readonly_connection_preflight_pack import (
    PREFLIGHT_READY,
    build_ibkr_readonly_connection_preflight_pack_rows,
)
from src.ibkr_readonly_preflight_config_validator import _actual_text, _get_dotted, _load_config
from src.ibkr_readonly_preflight_profile_aware_final_gate import (
    GO_TEXT,
    build_ibkr_readonly_preflight_profile_aware_final_gate_rows,
)


TRUE_TEXT = "true"
FALSE_TEXT = "false"

DRY_RUN_READY = "DRY_RUN_READY"
EXECUTE_REQUESTED = "EXECUTE_REQUESTED"
PASS_TEXT = "PASS"
FAIL_TEXT = "FAIL"
SKIPPED_TEXT = "SKIPPED"
BLOCKED_TEXT = "BLOCKED"

DEFAULT_WARNING_FLAGS = (
    "FIRST_CONNECT_DISCONNECT_DEFINED",
    "CONNECT_DISCONNECT_ONLY",
    "NO_MARKET_DATA_REQUEST",
    "NO_HISTORICAL_DATA_REQUEST",
    "NO_CONTRACT_QUALIFICATION",
    "ORDER_ACTION_BLOCKED",
    "CANCEL_ACTION_BLOCKED",
    "REBALANCE_BLOCKED",
    "AUTO_TRADE_BLOCKED",
    "phase17a_ibkr_first_real_readonly_connect_disconnect",
)


@dataclass(frozen=True)
class FirstConnectDisconnectRow:
    row_id: str
    row_name: str
    source_layer: str
    input_source: str
    selected_profile: str
    execute_requested: str
    component: str
    status: str
    host: str
    port: str
    client_id: str
    server_version: str
    connection_time: str
    connection_attempted: str
    connect_succeeded: str
    disconnect_attempted: str
    disconnect_succeeded: str
    current_call_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    contract_qualification_allowed: str
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
    "row_id",
    "row_name",
    "source_layer",
    "input_source",
    "selected_profile",
    "execute_requested",
    "component",
    "status",
    "host",
    "port",
    "client_id",
    "server_version",
    "connection_time",
    "connection_attempted",
    "connect_succeeded",
    "disconnect_attempted",
    "disconnect_succeeded",
    "current_call_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "contract_qualification_allowed",
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


def _detect_profile(config) -> str:
    account_mode = _actual_text(_get_dotted(config, "ibkr.account_mode")).lower()
    port = _actual_text(_get_dotted(config, "ibkr.port"))
    if account_mode == "live" or port == "7496":
        return "live-readonly"
    return "paper"


def _as_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _read_callable(obj: Any, name: str) -> Optional[str]:
    value = getattr(obj, name, None)
    if value is None:
        return None
    if callable(value):
        try:
            return str(value())
        except Exception:
            return None
    return str(value)


def _connection_metadata(connector: Any) -> tuple[str, str]:
    server_version = _read_callable(connector, "serverVersion")

    client = getattr(connector, "client", None)
    if server_version is None and client is not None:
        server_version = _read_callable(client, "serverVersion")

    connection_time = _read_callable(connector, "twsConnectionTime")
    if connection_time is None:
        connection_time = _read_callable(connector, "connectionTime")
    if connection_time is None and client is not None:
        connection_time = _read_callable(client, "twsConnectionTime")

    return server_version or "unavailable", connection_time or "unavailable"


def _diagnose_connection_exception(exc: Exception, host: str, port: str) -> str:
    message = str(exc)
    class_name = exc.__class__.__name__

    if isinstance(exc, ConnectionRefusedError) or "ConnectionRefusedError" in message:
        return (
            "connect_failed:tws_api_socket_not_listening;"
            "host={};port={};error_type={};error={}"
        ).format(host, port, class_name, message)

    if "Connect call failed" in message:
        return (
            "connect_failed:tws_api_socket_unreachable;"
            "host={};port={};error_type={};error={}"
        ).format(host, port, class_name, message)

    return "connect_failed:error_type={};error={}".format(class_name, message)


def _default_connector_factory():
    try:
        from ib_insync import IB  # type: ignore
    except Exception as exc:
        raise RuntimeError("ib_insync_import_failed: {}".format(exc)) from exc

    return IB()


def _make_row(
    row_id,
    row_name,
    input_source,
    selected_profile,
    execute_requested,
    component,
    status,
    host,
    port,
    client_id,
    server_version,
    connection_time,
    connection_attempted,
    connect_succeeded,
    disconnect_attempted,
    disconnect_succeeded,
    current_call_allowed,
    evidence,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return FirstConnectDisconnectRow(
        row_id=row_id,
        row_name=row_name,
        source_layer="Phase 17A",
        input_source=str(input_source),
        selected_profile=selected_profile,
        execute_requested=TRUE_TEXT if execute_requested else FALSE_TEXT,
        component=component,
        status=status,
        host=str(host),
        port=str(port),
        client_id=str(client_id),
        server_version=str(server_version),
        connection_time=str(connection_time),
        connection_attempted=connection_attempted,
        connect_succeeded=connect_succeeded,
        disconnect_attempted=disconnect_attempted,
        disconnect_succeeded=disconnect_succeeded,
        current_call_allowed=current_call_allowed,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        contract_qualification_allowed=FALSE_TEXT,
        order_action_allowed=FALSE_TEXT,
        cancel_action_allowed=FALSE_TEXT,
        rebalance_action_allowed=FALSE_TEXT,
        auto_trade_allowed=FALSE_TEXT,
        action_allowed=FALSE_TEXT,
        evidence=evidence,
        warning_flags=_flags(extra_flags),
        notes=(
            "Phase 17A first read-only connect/disconnect only. Default mode is dry-run. "
            "Execution requires an explicit runtime flag. This phase must not request market data, "
            "historical data, contract qualification, or any trading action."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_first_connect_disconnect_rows(
    input_source: Union[str, Path] = "config.yaml",
    execute: bool = False,
    connector_factory: Optional[Callable[[], Any]] = None,
):
    timestamp_jst, timestamp_et = _now_pair()
    input_source_text = str(input_source)

    config, load_error = _load_config(input_source)
    selected_profile = _detect_profile(config)

    host = _actual_text(_get_dotted(config, "ibkr.host"))
    port = _actual_text(_get_dotted(config, "ibkr.port"))
    client_id = _actual_text(_get_dotted(config, "ibkr.client_id"))

    final_gate_rows = build_ibkr_readonly_preflight_profile_aware_final_gate_rows(
        input_source,
        "auto",
    )
    connection_preflight_rows = build_ibkr_readonly_connection_preflight_pack_rows(input_source)

    final_gate = final_gate_rows[-1]
    connection_preflight = connection_preflight_rows[-1]

    final_gate_go = final_gate.final_gate_decision == GO_TEXT
    preflight_ready = connection_preflight.preflight_status == PREFLIGHT_READY
    parameter_ready = (
        not load_error
        and host in {"127.0.0.1", "localhost"}
        and port not in {"missing", "null", ""}
        and client_id not in {"missing", "null", ""}
    )

    execution_allowed = execute and final_gate_go and preflight_ready and parameter_ready

    rows = [
        _make_row(
            "PROFILE_AWARE_FINAL_GATE",
            "Phase 14I final gate prerequisite",
            input_source_text,
            selected_profile,
            execute,
            "precondition",
            PASS_TEXT if final_gate_go else FAIL_TEXT,
            host,
            port,
            client_id,
            "not_requested",
            "not_requested",
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            final_gate.evidence,
            timestamp_jst,
            timestamp_et,
            ["PROFILE_AWARE_FINAL_GATE_GO" if final_gate_go else "PROFILE_AWARE_FINAL_GATE_NOT_GO"],
        ),
        _make_row(
            "CONNECTION_PREFLIGHT_PACK",
            "Phase 16A-16C preflight prerequisite",
            input_source_text,
            selected_profile,
            execute,
            "precondition",
            PASS_TEXT if preflight_ready else FAIL_TEXT,
            host,
            port,
            client_id,
            "not_requested",
            "not_requested",
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            connection_preflight.evidence,
            timestamp_jst,
            timestamp_et,
            ["CONNECTION_PREFLIGHT_READY" if preflight_ready else "CONNECTION_PREFLIGHT_NOT_READY"],
        ),
        _make_row(
            "EXECUTION_MODE",
            "Runtime execution mode",
            input_source_text,
            selected_profile,
            execute,
            "runtime_guard",
            EXECUTE_REQUESTED if execute else DRY_RUN_READY,
            host,
            port,
            client_id,
            "not_requested",
            "not_requested",
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            TRUE_TEXT if execute else FALSE_TEXT,
            "execute_requested={}".format(str(execute).lower()),
            timestamp_jst,
            timestamp_et,
            ["EXECUTE_REQUESTED" if execute else "DRY_RUN_ONLY"],
        ),
    ]

    server_version = "not_requested"
    connection_time = "not_requested"
    connection_attempted = FALSE_TEXT
    connect_succeeded = FALSE_TEXT
    disconnect_attempted = FALSE_TEXT
    disconnect_succeeded = FALSE_TEXT
    connect_status = SKIPPED_TEXT
    connect_evidence = "dry_run_only"

    if execute and not execution_allowed:
        connect_status = BLOCKED_TEXT
        connect_evidence = (
            "execution_blocked;final_gate_go={};preflight_ready={};parameter_ready={}"
        ).format(
            str(final_gate_go).lower(),
            str(preflight_ready).lower(),
            str(parameter_ready).lower(),
        )

    if execution_allowed:
        connector = None
        connection_attempted = TRUE_TEXT
        disconnect_attempted = TRUE_TEXT
        try:
            factory = connector_factory or _default_connector_factory
            connector = factory()
            connector.connect(
                host,
                _as_int(port, 7496),
                clientId=_as_int(client_id, 1),
                readonly=True,
            )
            connect_succeeded = TRUE_TEXT
            server_version, connection_time = _connection_metadata(connector)
            connect_status = PASS_TEXT
            connect_evidence = "connect_disconnect_metadata_only"
        except Exception as exc:
            connect_status = FAIL_TEXT
            connect_evidence = _diagnose_connection_exception(exc, host, port)
        finally:
            if connector is not None:
                try:
                    connector.disconnect()
                    disconnect_succeeded = TRUE_TEXT
                except Exception as exc:
                    if connect_status == PASS_TEXT:
                        connect_status = FAIL_TEXT
                    connect_evidence = "{};disconnect_failed: {}".format(connect_evidence, exc)

    rows.append(
        _make_row(
            "CONNECT_DISCONNECT",
            "First real read-only connect/disconnect attempt",
            input_source_text,
            selected_profile,
            execute,
            "connect_disconnect",
            connect_status,
            host,
            port,
            client_id,
            server_version,
            connection_time,
            connection_attempted,
            connect_succeeded,
            disconnect_attempted,
            disconnect_succeeded,
            TRUE_TEXT if execution_allowed else FALSE_TEXT,
            connect_evidence,
            timestamp_jst,
            timestamp_et,
            ["CONNECT_DISCONNECT_ONLY"],
        )
    )

    final_status = DRY_RUN_READY
    if execute:
        final_status = PASS_TEXT if connect_status == PASS_TEXT else FAIL_TEXT

    rows.append(
        _make_row(
            "FINAL",
            "Final first read-only connect/disconnect decision",
            input_source_text,
            selected_profile,
            execute,
            "final",
            final_status,
            host,
            port,
            client_id,
            server_version,
            connection_time,
            connection_attempted,
            connect_succeeded,
            disconnect_attempted,
            disconnect_succeeded,
            TRUE_TEXT if execution_allowed else FALSE_TEXT,
            (
                "execute={};execution_allowed={};connect_succeeded={};"
                "disconnect_succeeded={};server_version={};connection_time={}"
            ).format(
                str(execute).lower(),
                str(execution_allowed).lower(),
                connect_succeeded,
                disconnect_succeeded,
                server_version,
                connection_time,
            ),
            timestamp_jst,
            timestamp_et,
            ["PHASE17A_DRY_RUN_READY" if not execute else "PHASE17A_EXECUTION_RESULT"],
        )
    )

    return rows


def write_ibkr_readonly_first_connect_disconnect_csv(
    path: Union[str, Path],
    rows: Iterable[FirstConnectDisconnectRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_first_connect_disconnect_report(
    path: Union[str, Path],
    rows: Iterable[FirstConnectDisconnectRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    final_row = row_list[-1] if row_list else None
    selected_profile = final_row.selected_profile if final_row else "unknown"
    final_status = final_row.status if final_row else FAIL_TEXT

    execute_count = 1 if final_row and final_row.execute_requested == TRUE_TEXT else 0
    actual_connection_rows = [
        row for row in row_list if row.row_id == "CONNECT_DISCONNECT"
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
    current_call_allowed_count = sum(
        1 for row in actual_connection_rows if row.current_call_allowed == TRUE_TEXT
    )
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)

    lines = [
        "# Phase 17A IBKR First Read-Only Connect/Disconnect Report",
        "",
        "- phase: Phase 17A",
        "- scope: first real read-only connect/disconnect",
        f"- input_source: {input_source}",
        f"- selected_profile: {selected_profile}",
        f"- row_count: {len(row_list)}",
        f"- final_status: {final_status}",
        f"- execute_requested_count: {execute_count}",
        f"- connection_attempt_count: {connection_attempt_count}",
        f"- connect_success_count: {connect_success_count}",
        f"- disconnect_success_count: {disconnect_success_count}",
        f"- current_call_allowed_count: {current_call_allowed_count}",
        "- counter_scope: CONNECT_DISCONNECT row only for actual connection counters",
        f"- action_allowed_count: {action_allowed_count}",
        "- market_data_request_allowed: false",
        "- historical_data_request_allowed: false",
        "- contract_qualification_allowed: false",
        "- order_action_allowed: false",
        "- cancel_action_allowed: false",
        "- rebalance_action_allowed: false",
        "- auto_trade_allowed: false",
        "- action_allowed: false",
        "",
        "## Rows",
        "",
        "| row_id | component | status | execute_requested | connection_attempted | connect_succeeded | disconnect_succeeded | server_version | connection_time | current_call_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.row_id,
                    row.component,
                    row.status,
                    row.execute_requested,
                    row.connection_attempted,
                    row.connect_succeeded,
                    row.disconnect_succeeded,
                    row.server_version,
                    row.connection_time,
                    row.current_call_allowed,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Execution Rule",
            "",
            "- Default mode is dry-run and does not connect.",
            "- Real connect/disconnect requires explicit runtime execution flag.",
            "- This phase allows only connect/disconnect and connection metadata.",
            "- This phase must not request market data, historical data, contract qualification, or trading actions.",
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
