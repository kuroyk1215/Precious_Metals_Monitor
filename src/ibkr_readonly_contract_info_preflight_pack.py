from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union
from zoneinfo import ZoneInfo

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
CONTRACT_INFO_READY = "CONTRACT_INFO_READY"
CONTRACT_INFO_BLOCKED = "CONTRACT_INFO_BLOCKED"

DEFAULT_WARNING_FLAGS = (
    "CONTRACT_INFO_PREFLIGHT_PACK_DEFINED",
    "CONTRACT_DETAILS_READ_ONLY",
    "NO_MARKET_DATA_REQUEST",
    "NO_HISTORICAL_DATA_REQUEST",
    "NO_CONTRACT_QUALIFICATION",
    "ORDER_ACTION_BLOCKED",
    "CANCELLATION_ACTION_BLOCKED",
    "REBALANCE_BLOCKED",
    "AUTO_TRADE_BLOCKED",
    "phase19a19c_ibkr_readonly_contract_info_preflight_pack",
)


@dataclass(frozen=True)
class ContractInfoPreflightPackRow:
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
    contract_symbol: str
    contract_sec_type: str
    contract_exchange: str
    contract_currency: str
    contract_primary_exchange: str
    server_version: str
    connection_time: str
    contract_details_count: str
    contract_details_summary: str
    connection_attempted: str
    connect_succeeded: str
    disconnect_attempted: str
    disconnect_succeeded: str
    contract_info_request_attempted: str
    contract_info_read_succeeded: str
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
    "host",
    "port",
    "client_id",
    "contract_symbol",
    "contract_sec_type",
    "contract_exchange",
    "contract_currency",
    "contract_primary_exchange",
    "server_version",
    "connection_time",
    "contract_details_count",
    "contract_details_summary",
    "connection_attempted",
    "connect_succeeded",
    "disconnect_attempted",
    "disconnect_succeeded",
    "contract_info_request_attempted",
    "contract_info_read_succeeded",
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


def _detect_profile(config) -> str:
    account_mode = _actual_text(_get_dotted(config, "ibkr.account_mode")).lower()
    port = _actual_text(_get_dotted(config, "ibkr.port"))
    if account_mode == "live" or port == "7496":
        return "live-readonly"
    return "paper"


def _config_value(config, key: str, fallback: str) -> str:
    value = _actual_text(_get_dotted(config, key))
    if value in {"missing", "null", ""}:
        return fallback
    return value


def _contract_spec(config):
    return {
        "symbol": _config_value(config, "ibkr.contract_info_symbol", "1540"),
        "sec_type": _config_value(config, "ibkr.contract_info_sec_type", "STK"),
        "exchange": _config_value(config, "ibkr.contract_info_exchange", "SMART"),
        "currency": _config_value(config, "ibkr.contract_info_currency", "JPY"),
        "primary_exchange": _config_value(config, "ibkr.contract_info_primary_exchange", "TSEJ"),
    }


def _make_contract(spec):
    try:
        from ib_insync import Contract  # type: ignore
    except Exception as exc:
        raise RuntimeError("ib_insync_contract_import_failed: {}".format(exc)) from exc

    return Contract(
        secType=spec["sec_type"],
        symbol=spec["symbol"],
        exchange=spec["exchange"],
        currency=spec["currency"],
        primaryExchange=spec["primary_exchange"],
    )


def _summarize_contract_details(details: Any) -> tuple[int, str]:
    if details is None:
        return 0, "unavailable"

    try:
        items = list(details)
    except TypeError:
        items = [details]

    if not items:
        return 0, "unavailable"

    summaries = []
    for item in items[:10]:
        contract = getattr(item, "contract", item)
        con_id = getattr(contract, "conId", "")
        symbol = getattr(contract, "symbol", "")
        local_symbol = getattr(contract, "localSymbol", "")
        sec_type = getattr(contract, "secType", "")
        exchange = getattr(contract, "exchange", "")
        primary_exchange = getattr(contract, "primaryExchange", "")
        currency = getattr(contract, "currency", "")
        summaries.append(
            "conId={};symbol={};localSymbol={};secType={};exchange={};primaryExchange={};currency={}".format(
                con_id,
                symbol,
                local_symbol,
                sec_type,
                exchange,
                primary_exchange,
                currency,
            )
        )

    return len(items), ";".join(summaries)


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
    spec,
    server_version,
    connection_time,
    contract_details_count,
    contract_details_summary,
    connection_attempted,
    connect_succeeded,
    disconnect_attempted,
    disconnect_succeeded,
    contract_info_request_attempted,
    contract_info_read_succeeded,
    current_call_allowed,
    evidence,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return ContractInfoPreflightPackRow(
        row_id=row_id,
        row_name=row_name,
        source_layer="Phase 19A-19C",
        input_source=str(input_source),
        selected_profile=selected_profile,
        execute_requested=TRUE_TEXT if execute_requested else FALSE_TEXT,
        component=component,
        status=status,
        host=str(host),
        port=str(port),
        client_id=str(client_id),
        contract_symbol=str(spec["symbol"]),
        contract_sec_type=str(spec["sec_type"]),
        contract_exchange=str(spec["exchange"]),
        contract_currency=str(spec["currency"]),
        contract_primary_exchange=str(spec["primary_exchange"]),
        server_version=str(server_version),
        connection_time=str(connection_time),
        contract_details_count=str(contract_details_count),
        contract_details_summary=str(contract_details_summary),
        connection_attempted=connection_attempted,
        connect_succeeded=connect_succeeded,
        disconnect_attempted=disconnect_attempted,
        disconnect_succeeded=disconnect_succeeded,
        contract_info_request_attempted=contract_info_request_attempted,
        contract_info_read_succeeded=contract_info_read_succeeded,
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
            "Phase 19A-19C read-only contract info preflight pack. Default mode is dry-run. "
            "When explicitly executed, it allows connection metadata and contract details read-only "
            "for one contract specification. It must not request market data, historical data, "
            "contract qualification, or any trading action."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_contract_info_preflight_pack_rows(
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
    spec = _contract_spec(config)

    final_gate_rows = build_ibkr_readonly_preflight_profile_aware_final_gate_rows(
        input_source,
        "auto",
    )
    final_gate = final_gate_rows[-1]
    final_gate_go = final_gate.final_gate_decision == GO_TEXT

    execution_allowed = (
        execute
        and not load_error
        and final_gate_go
        and host in {"127.0.0.1", "localhost"}
        and port not in {"missing", "null", ""}
        and client_id not in {"missing", "null", ""}
    )

    rows = [
        _make_row(
            "CONTRACT_INFO_ALLOWLIST",
            "Contract details read-only allowlist",
            input_source_text,
            selected_profile,
            execute,
            "Phase 19A",
            ALLOWLIST_DEFINED,
            host,
            port,
            client_id,
            spec,
            "not_requested",
            "not_requested",
            "0",
            "not_requested",
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            "contract details read-only allowlist defined; market and historical data remain blocked",
            timestamp_jst,
            timestamp_et,
            ["CONTRACT_INFO_ALLOWLIST_DEFINED"],
        ),
        _make_row(
            "DRY_RUN_GATE",
            "Contract details dry-run gate",
            input_source_text,
            selected_profile,
            execute,
            "Phase 19B",
            EXECUTE_REQUESTED if execute else DRY_RUN_READY,
            host,
            port,
            client_id,
            spec,
            "not_requested",
            "not_requested",
            "0",
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
                "contract_symbol={};contract_exchange={};contract_primary_exchange={}"
            ).format(
                str(execute).lower(),
                str(execution_allowed).lower(),
                str(final_gate_go).lower(),
                spec["symbol"],
                spec["exchange"],
                spec["primary_exchange"],
            ),
            timestamp_jst,
            timestamp_et,
            ["EXECUTE_REQUESTED" if execute else "DRY_RUN_ONLY"],
        ),
    ]

    server_version = "not_requested"
    connection_time = "not_requested"
    contract_details_count = "0"
    contract_details_summary = "not_requested"
    connection_attempted = FALSE_TEXT
    connect_succeeded = FALSE_TEXT
    disconnect_attempted = FALSE_TEXT
    disconnect_succeeded = FALSE_TEXT
    contract_info_request_attempted = FALSE_TEXT
    contract_info_read_succeeded = FALSE_TEXT
    info_status = SKIPPED_TEXT
    info_evidence = "dry_run_only"

    if execute and not execution_allowed:
        info_status = CONTRACT_INFO_BLOCKED
        info_evidence = (
            "execution_blocked;load_error={};final_gate_go={};host={};port={};client_id={}"
        ).format(
            str(bool(load_error)).lower(),
            str(final_gate_go).lower(),
            host,
            port,
            client_id,
        )

    if execution_allowed:
        connector = None
        connection_attempted = TRUE_TEXT
        disconnect_attempted = TRUE_TEXT
        contract_info_request_attempted = TRUE_TEXT
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
            contract = _make_contract(spec)
            details = connector.reqContractDetails(contract)
            count, summary = _summarize_contract_details(details)
            contract_details_count = str(count)
            contract_details_summary = summary
            contract_info_read_succeeded = TRUE_TEXT if count > 0 else FALSE_TEXT
            info_status = PASS_TEXT if count > 0 else FAIL_TEXT
            info_evidence = "contract_details_read_only;details_count={}".format(count)
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
            "CONTRACT_INFO_READ",
            "First real read-only contract details read",
            input_source_text,
            selected_profile,
            execute,
            "Phase 19C",
            info_status,
            host,
            port,
            client_id,
            spec,
            server_version,
            connection_time,
            contract_details_count,
            contract_details_summary,
            connection_attempted,
            connect_succeeded,
            disconnect_attempted,
            disconnect_succeeded,
            contract_info_request_attempted,
            contract_info_read_succeeded,
            TRUE_TEXT if execution_allowed else FALSE_TEXT,
            info_evidence,
            timestamp_jst,
            timestamp_et,
            ["CONTRACT_DETAILS_READ_ONLY"],
        )
    )

    final_status = DRY_RUN_READY
    if execute:
        final_status = PASS_TEXT if info_status == PASS_TEXT else FAIL_TEXT

    rows.append(
        _make_row(
            "FINAL",
            "Final contract info preflight decision",
            input_source_text,
            selected_profile,
            execute,
            "Phase 19A-19C",
            final_status,
            host,
            port,
            client_id,
            spec,
            server_version,
            connection_time,
            contract_details_count,
            contract_details_summary,
            connection_attempted,
            connect_succeeded,
            disconnect_attempted,
            disconnect_succeeded,
            contract_info_request_attempted,
            contract_info_read_succeeded,
            TRUE_TEXT if execution_allowed else FALSE_TEXT,
            (
                "execute={};execution_allowed={};final_gate_go={};connect_succeeded={};"
                "contract_info_read_succeeded={};contract_details_count={}"
            ).format(
                str(execute).lower(),
                str(execution_allowed).lower(),
                str(final_gate_go).lower(),
                connect_succeeded,
                contract_info_read_succeeded,
                contract_details_count,
            ),
            timestamp_jst,
            timestamp_et,
            ["PHASE19A19C_DRY_RUN_READY" if not execute else "PHASE19A19C_EXECUTION_RESULT"],
        )
    )

    return rows


def write_ibkr_readonly_contract_info_preflight_pack_csv(
    path: Union[str, Path],
    rows: Iterable[ContractInfoPreflightPackRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_contract_info_preflight_pack_report(
    path: Union[str, Path],
    rows: Iterable[ContractInfoPreflightPackRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    final_row = row_list[-1] if row_list else None
    selected_profile = final_row.selected_profile if final_row else "unknown"
    final_status = final_row.status if final_row else FAIL_TEXT

    actual_rows = [row for row in row_list if row.row_id == "CONTRACT_INFO_READ"]
    connection_attempt_count = sum(1 for row in actual_rows if row.connection_attempted == TRUE_TEXT)
    connect_success_count = sum(1 for row in actual_rows if row.connect_succeeded == TRUE_TEXT)
    disconnect_success_count = sum(1 for row in actual_rows if row.disconnect_succeeded == TRUE_TEXT)
    contract_info_attempt_count = sum(
        1 for row in actual_rows if row.contract_info_request_attempted == TRUE_TEXT
    )
    contract_info_success_count = sum(
        1 for row in actual_rows if row.contract_info_read_succeeded == TRUE_TEXT
    )
    current_call_allowed_count = sum(1 for row in actual_rows if row.current_call_allowed == TRUE_TEXT)
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)

    lines = [
        "# Phase 19A-19C IBKR Read-Only Contract Info Preflight Pack Report",
        "",
        "- phase: Phase 19A-19C",
        "- scope: read-only contract details",
        f"- input_source: {input_source}",
        f"- selected_profile: {selected_profile}",
        f"- row_count: {len(row_list)}",
        f"- final_status: {final_status}",
        f"- connection_attempt_count: {connection_attempt_count}",
        f"- connect_success_count: {connect_success_count}",
        f"- disconnect_success_count: {disconnect_success_count}",
        f"- contract_info_attempt_count: {contract_info_attempt_count}",
        f"- contract_info_success_count: {contract_info_success_count}",
        f"- current_call_allowed_count: {current_call_allowed_count}",
        "- counter_scope: CONTRACT_INFO_READ row only for actual contract-info counters",
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
        "| row_id | component | status | execute_requested | connection_attempted | connect_succeeded | disconnect_succeeded | contract_info_request_attempted | contract_info_read_succeeded | contract_symbol | contract_exchange | contract_primary_exchange | contract_details_count | current_call_allowed | action_allowed |",
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
                    row.contract_info_request_attempted,
                    row.contract_info_read_succeeded,
                    row.contract_symbol,
                    row.contract_exchange,
                    row.contract_primary_exchange,
                    row.contract_details_count,
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
            "- contract details: read-only contract metadata only.",
            "- market data remains blocked.",
            "- historical data remains blocked.",
            "- contract qualification remains blocked.",
            "- trading actions remain blocked.",
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
