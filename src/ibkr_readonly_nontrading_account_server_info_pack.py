from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union
from zoneinfo import ZoneInfo

from src.ibkr_readonly_connection_log_heartbeat_guard import (
    PASS_STATUS,
    build_ibkr_readonly_connection_log_heartbeat_guard_rows,
)
from src.ibkr_readonly_first_connect_disconnect import (
    _as_int,
    _connection_metadata,
    _default_connector_factory,
    _diagnose_connection_exception,
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
ALLOWLIST_DEFINED = "ALLOWLIST_DEFINED"
INFO_READ_READY = "INFO_READ_READY"
INFO_READ_BLOCKED = "INFO_READ_BLOCKED"

DEFAULT_WARNING_FLAGS = (
    "NONTRADING_ACCOUNT_SERVER_INFO_PACK_DEFINED",
    "SERVER_ACCOUNT_METADATA_ONLY",
    "NO_MARKET_DATA_REQUEST",
    "NO_HISTORICAL_DATA_REQUEST",
    "NO_CONTRACT_QUALIFICATION",
    "NO_CONTRACT_DETAILS_REQUEST",
    "ORDER_ACTION_BLOCKED",
    "CANCELLATION_ACTION_BLOCKED",
    "REBALANCE_BLOCKED",
    "AUTO_TRADE_BLOCKED",
    "phase18a18c_ibkr_readonly_nontrading_account_server_info_pack",
)


@dataclass(frozen=True)
class NonTradingAccountServerInfoRow:
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
    managed_accounts: str
    account_summary_items: str
    connection_attempted: str
    connect_succeeded: str
    disconnect_attempted: str
    disconnect_succeeded: str
    nontrading_info_request_attempted: str
    nontrading_info_read_succeeded: str
    current_call_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    contract_qualification_allowed: str
    contract_details_request_allowed: str
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
    "host",
    "port",
    "client_id",
    "server_version",
    "connection_time",
    "managed_accounts",
    "account_summary_items",
    "connection_attempted",
    "connect_succeeded",
    "disconnect_attempted",
    "disconnect_succeeded",
    "nontrading_info_request_attempted",
    "nontrading_info_read_succeeded",
    "current_call_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "contract_qualification_allowed",
    "contract_details_request_allowed",
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


def _detect_profile(config) -> str:
    account_mode = _actual_text(_get_dotted(config, "ibkr.account_mode")).lower()
    port = _actual_text(_get_dotted(config, "ibkr.port"))
    if account_mode == "live" or port == "7496":
        return "live-readonly"
    return "paper"


def _safe_join(values: Any) -> str:
    if values is None:
        return "unavailable"
    if isinstance(values, str):
        return values if values else "unavailable"
    if isinstance(values, (list, tuple, set)):
        if not values:
            return "unavailable"
        return ";".join(str(v) for v in values)
    return str(values)


def _read_managed_accounts(connector: Any) -> str:
    method = getattr(connector, "managedAccounts", None)
    if callable(method):
        return _safe_join(method())

    client = getattr(connector, "client", None)
    if client is not None:
        method = getattr(client, "managedAccounts", None)
        if callable(method):
            return _safe_join(method())

    return "unavailable"


def _read_account_summary(connector: Any) -> str:
    method = getattr(connector, "accountSummary", None)
    if not callable(method):
        return "unavailable"

    try:
        summary = method()
    except TypeError:
        try:
            summary = method(account="", tags="NetLiquidation,TotalCashValue,AvailableFunds")
        except Exception:
            return "unavailable"
    except Exception:
        return "unavailable"

    if summary is None:
        return "unavailable"

    try:
        items = list(summary)
    except TypeError:
        return str(summary) if str(summary) else "unavailable"

    if not items:
        return "unavailable"

    compact = []
    for item in items[:20]:
        account = getattr(item, "account", "")
        tag = getattr(item, "tag", "")
        value = getattr(item, "value", "")
        currency = getattr(item, "currency", "")
        compact.append("{}:{}:{}:{}".format(account, tag, value, currency))

    return ";".join(compact) if compact else "unavailable"


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
    managed_accounts,
    account_summary_items,
    connection_attempted,
    connect_succeeded,
    disconnect_attempted,
    disconnect_succeeded,
    nontrading_info_request_attempted,
    nontrading_info_read_succeeded,
    current_call_allowed,
    evidence,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return NonTradingAccountServerInfoRow(
        row_id=row_id,
        row_name=row_name,
        source_layer="Phase 18A-18C",
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
        managed_accounts=str(managed_accounts),
        account_summary_items=str(account_summary_items),
        connection_attempted=connection_attempted,
        connect_succeeded=connect_succeeded,
        disconnect_attempted=disconnect_attempted,
        disconnect_succeeded=disconnect_succeeded,
        nontrading_info_request_attempted=nontrading_info_request_attempted,
        nontrading_info_read_succeeded=nontrading_info_read_succeeded,
        current_call_allowed=current_call_allowed,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        contract_qualification_allowed=FALSE_TEXT,
        contract_details_request_allowed=FALSE_TEXT,
        order_action_allowed=FALSE_TEXT,
        cancellation_action_allowed=FALSE_TEXT,
        rebalance_action_allowed=FALSE_TEXT,
        auto_trade_allowed=FALSE_TEXT,
        action_allowed=FALSE_TEXT,
        evidence=evidence,
        warning_flags=_flags(extra_flags),
        notes=(
            "Phase 18A-18C non-trading account/server info pack. Default mode is dry-run. "
            "When explicitly executed, it allows connection metadata plus managed account and "
            "account summary metadata only. It must not request market data, historical data, "
            "contract qualification, contract details, or any trading action."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_nontrading_account_server_info_pack_rows(
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
    final_gate = final_gate_rows[-1]
    final_gate_go = final_gate.final_gate_decision == GO_TEXT

    heartbeat_rows = build_ibkr_readonly_connection_log_heartbeat_guard_rows(
        input_source,
        execute=False,
    )
    heartbeat_final = heartbeat_rows[-1]
    heartbeat_ready = heartbeat_final.status == DRY_RUN_READY or heartbeat_final.status == PASS_STATUS

    execution_allowed = (
        execute
        and not load_error
        and final_gate_go
        and heartbeat_ready
        and host in {"127.0.0.1", "localhost"}
        and port not in {"missing", "null", ""}
        and client_id not in {"missing", "null", ""}
    )

    rows = [
        _make_row(
            "METADATA_ALLOWLIST_SERVER_VERSION",
            "Server version metadata allowlist",
            input_source_text,
            selected_profile,
            execute,
            "Phase 18A",
            ALLOWLIST_DEFINED,
            host,
            port,
            client_id,
            "not_requested",
            "not_requested",
            "not_requested",
            "not_requested",
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            "serverVersion allowed only as non-trading connection metadata",
            timestamp_jst,
            timestamp_et,
            ["SERVER_VERSION_ALLOWLIST_DEFINED"],
        ),
        _make_row(
            "METADATA_ALLOWLIST_MANAGED_ACCOUNTS",
            "Managed accounts metadata allowlist",
            input_source_text,
            selected_profile,
            execute,
            "Phase 18A",
            ALLOWLIST_DEFINED,
            host,
            port,
            client_id,
            "not_requested",
            "not_requested",
            "not_requested",
            "not_requested",
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            "managed accounts allowed only as non-trading account metadata",
            timestamp_jst,
            timestamp_et,
            ["MANAGED_ACCOUNTS_ALLOWLIST_DEFINED"],
        ),
        _make_row(
            "METADATA_ALLOWLIST_ACCOUNT_SUMMARY",
            "Account summary metadata allowlist",
            input_source_text,
            selected_profile,
            execute,
            "Phase 18A",
            ALLOWLIST_DEFINED,
            host,
            port,
            client_id,
            "not_requested",
            "not_requested",
            "not_requested",
            "not_requested",
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            "account summary allowed only as non-trading account metadata",
            timestamp_jst,
            timestamp_et,
            ["ACCOUNT_SUMMARY_ALLOWLIST_DEFINED"],
        ),
        _make_row(
            "DRY_RUN_GATE",
            "Managed accounts and account summary dry-run gate",
            input_source_text,
            selected_profile,
            execute,
            "Phase 18B",
            EXECUTE_REQUESTED if execute else DRY_RUN_READY,
            host,
            port,
            client_id,
            "not_requested",
            "not_requested",
            "not_requested",
            "not_requested",
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            TRUE_TEXT if execute else FALSE_TEXT,
            FALSE_TEXT,
            TRUE_TEXT if execute else FALSE_TEXT,
            (
                "execute_requested={};execution_allowed={};final_gate_go={};"
                "heartbeat_ready={}"
            ).format(
                str(execute).lower(),
                str(execution_allowed).lower(),
                str(final_gate_go).lower(),
                str(heartbeat_ready).lower(),
            ),
            timestamp_jst,
            timestamp_et,
            ["EXECUTE_REQUESTED" if execute else "DRY_RUN_ONLY"],
        ),
    ]

    server_version = "not_requested"
    connection_time = "not_requested"
    managed_accounts = "not_requested"
    account_summary_items = "not_requested"
    connection_attempted = FALSE_TEXT
    connect_succeeded = FALSE_TEXT
    disconnect_attempted = FALSE_TEXT
    disconnect_succeeded = FALSE_TEXT
    nontrading_info_request_attempted = FALSE_TEXT
    nontrading_info_read_succeeded = FALSE_TEXT
    info_status = SKIPPED_TEXT
    info_evidence = "dry_run_only"

    if execute and not execution_allowed:
        info_status = INFO_READ_BLOCKED
        info_evidence = (
            "execution_blocked;load_error={};final_gate_go={};heartbeat_ready={};"
            "host={};port={};client_id={}"
        ).format(
            str(bool(load_error)).lower(),
            str(final_gate_go).lower(),
            str(heartbeat_ready).lower(),
            host,
            port,
            client_id,
        )

    if execution_allowed:
        connector = None
        connection_attempted = TRUE_TEXT
        disconnect_attempted = TRUE_TEXT
        nontrading_info_request_attempted = TRUE_TEXT
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
            managed_accounts = _read_managed_accounts(connector)
            account_summary_items = _read_account_summary(connector)
            nontrading_info_read_succeeded = TRUE_TEXT
            info_status = PASS_TEXT
            info_evidence = "nontrading_account_server_info_read_only"
        except Exception as exc:
            info_status = FAIL_TEXT
            info_evidence = _diagnose_connection_exception(exc, host, port)
        finally:
            if connector is not None:
                try:
                    connector.disconnect()
                    disconnect_succeeded = TRUE_TEXT
                except Exception as exc:
                    if info_status == PASS_TEXT:
                        info_status = FAIL_TEXT
                    info_evidence = "{};disconnect_failed: {}".format(info_evidence, exc)

    rows.append(
        _make_row(
            "NONTRADING_INFO_READ",
            "First real non-trading account/server info read",
            input_source_text,
            selected_profile,
            execute,
            "Phase 18C",
            info_status,
            host,
            port,
            client_id,
            server_version,
            connection_time,
            managed_accounts,
            account_summary_items,
            connection_attempted,
            connect_succeeded,
            disconnect_attempted,
            disconnect_succeeded,
            nontrading_info_request_attempted,
            nontrading_info_read_succeeded,
            TRUE_TEXT if execution_allowed else FALSE_TEXT,
            info_evidence,
            timestamp_jst,
            timestamp_et,
            ["NONTRADING_INFO_READ_ONLY"],
        )
    )

    final_status = DRY_RUN_READY
    if execute:
        final_status = PASS_TEXT if info_status == PASS_TEXT else FAIL_TEXT

    rows.append(
        _make_row(
            "FINAL",
            "Final non-trading account/server info decision",
            input_source_text,
            selected_profile,
            execute,
            "Phase 18A-18C",
            final_status,
            host,
            port,
            client_id,
            server_version,
            connection_time,
            managed_accounts,
            account_summary_items,
            connection_attempted,
            connect_succeeded,
            disconnect_attempted,
            disconnect_succeeded,
            nontrading_info_request_attempted,
            nontrading_info_read_succeeded,
            TRUE_TEXT if execution_allowed else FALSE_TEXT,
            (
                "execute={};execution_allowed={};final_gate_go={};"
                "heartbeat_ready={};connect_succeeded={};"
                "nontrading_info_read_succeeded={};managed_accounts_available={};"
                "account_summary_available={}"
            ).format(
                str(execute).lower(),
                str(execution_allowed).lower(),
                str(final_gate_go).lower(),
                str(heartbeat_ready).lower(),
                connect_succeeded,
                nontrading_info_read_succeeded,
                str(managed_accounts not in {"not_requested", "unavailable", ""}).lower(),
                str(account_summary_items not in {"not_requested", "unavailable", ""}).lower(),
            ),
            timestamp_jst,
            timestamp_et,
            ["PHASE18A18C_DRY_RUN_READY" if not execute else "PHASE18A18C_EXECUTION_RESULT"],
        )
    )

    return rows


def write_ibkr_readonly_nontrading_account_server_info_pack_csv(
    path: Union[str, Path],
    rows: Iterable[NonTradingAccountServerInfoRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_nontrading_account_server_info_pack_report(
    path: Union[str, Path],
    rows: Iterable[NonTradingAccountServerInfoRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    final_row = row_list[-1] if row_list else None
    selected_profile = final_row.selected_profile if final_row else "unknown"
    final_status = final_row.status if final_row else FAIL_TEXT

    actual_rows = [row for row in row_list if row.row_id == "NONTRADING_INFO_READ"]
    connection_attempt_count = sum(1 for row in actual_rows if row.connection_attempted == TRUE_TEXT)
    connect_success_count = sum(1 for row in actual_rows if row.connect_succeeded == TRUE_TEXT)
    disconnect_success_count = sum(1 for row in actual_rows if row.disconnect_succeeded == TRUE_TEXT)
    info_attempt_count = sum(
        1 for row in actual_rows if row.nontrading_info_request_attempted == TRUE_TEXT
    )
    info_success_count = sum(
        1 for row in actual_rows if row.nontrading_info_read_succeeded == TRUE_TEXT
    )
    current_call_allowed_count = sum(1 for row in actual_rows if row.current_call_allowed == TRUE_TEXT)
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)

    lines = [
        "# Phase 18A-18C IBKR Read-Only Non-Trading Account/Server Info Pack Report",
        "",
        "- phase: Phase 18A-18C",
        "- scope: non-trading account/server info read",
        f"- input_source: {input_source}",
        f"- selected_profile: {selected_profile}",
        f"- row_count: {len(row_list)}",
        f"- final_status: {final_status}",
        f"- connection_attempt_count: {connection_attempt_count}",
        f"- connect_success_count: {connect_success_count}",
        f"- disconnect_success_count: {disconnect_success_count}",
        f"- nontrading_info_attempt_count: {info_attempt_count}",
        f"- nontrading_info_success_count: {info_success_count}",
        f"- current_call_allowed_count: {current_call_allowed_count}",
        "- counter_scope: NONTRADING_INFO_READ row only for actual info-read counters",
        f"- action_allowed_count: {action_allowed_count}",
        "- market_data_request_allowed: false",
        "- historical_data_request_allowed: false",
        "- contract_qualification_allowed: false",
        "- contract_details_request_allowed: false",
        "- order_action_allowed: false",
        "- cancellation_action_allowed: false",
        "- rebalance_action_allowed: false",
        "- auto_trade_allowed: false",
        "- action_allowed: false",
        "",
        "## Rows",
        "",
        "| row_id | component | status | execute_requested | connection_attempted | connect_succeeded | disconnect_succeeded | nontrading_info_request_attempted | nontrading_info_read_succeeded | server_version | connection_time | managed_accounts | account_summary_items | current_call_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
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
                    row.nontrading_info_request_attempted,
                    row.nontrading_info_read_succeeded,
                    row.server_version,
                    row.connection_time,
                    row.managed_accounts,
                    row.account_summary_items,
                    row.current_call_allowed,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Allowlist",
            "",
            "- serverVersion: non-trading connection metadata only.",
            "- connectionTime: non-trading connection metadata only.",
            "- managedAccounts: non-trading account metadata only.",
            "- accountSummary: non-trading account metadata only.",
            "",
            "## Safety Statement",
            "",
            "- no market data request",
            "- no historical data request",
            "- no real contract qualification",
            "- no contract details request",
            "- no order action",
            "- no cancellation action",
            "- no rebalance",
            "- no auto trade",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
