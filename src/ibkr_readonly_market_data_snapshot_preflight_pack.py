from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union
from zoneinfo import ZoneInfo

from src.ibkr_readonly_contract_info_preflight_pack import (
    PASS_TEXT,
    _contract_spec,
    _make_contract,
    build_ibkr_readonly_contract_info_preflight_pack_rows,
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
PASS_STATUS = "PASS"
FAIL_STATUS = "FAIL"
SKIPPED_STATUS = "SKIPPED"
ALLOWLIST_DEFINED = "ALLOWLIST_DEFINED"
SNAPSHOT_READY = "SNAPSHOT_READY"
SNAPSHOT_BLOCKED = "SNAPSHOT_BLOCKED"

DEFAULT_WARNING_FLAGS = (
    "MARKET_DATA_SNAPSHOT_PREFLIGHT_PACK_DEFINED",
    "SINGLE_CONTRACT_SNAPSHOT_ONLY",
    "NON_STREAMING_MARKET_DATA_ONLY",
    "NO_HISTORICAL_DATA_REQUEST",
    "NO_CONTRACT_QUALIFICATION",
    "ORDER_ACTION_BLOCKED",
    "CANCELLATION_ACTION_BLOCKED",
    "REBALANCE_BLOCKED",
    "AUTO_TRADE_BLOCKED",
    "phase20a20c_ibkr_readonly_market_data_snapshot_preflight_pack",
)


@dataclass(frozen=True)
class MarketDataSnapshotPreflightPackRow:
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
    snapshot_bid: str
    snapshot_ask: str
    snapshot_last: str
    snapshot_close: str
    snapshot_market_price: str
    price_available: str
    price_status: str
    connection_attempted: str
    connect_succeeded: str
    disconnect_attempted: str
    disconnect_succeeded: str
    market_data_snapshot_request_attempted: str
    market_data_snapshot_read_succeeded: str
    current_call_allowed: str
    streaming_market_data_allowed: str
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
    "snapshot_bid",
    "snapshot_ask",
    "snapshot_last",
    "snapshot_close",
    "snapshot_market_price",
    "price_available",
    "price_status",
    "connection_attempted",
    "connect_succeeded",
    "disconnect_attempted",
    "disconnect_succeeded",
    "market_data_snapshot_request_attempted",
    "market_data_snapshot_read_succeeded",
    "current_call_allowed",
    "streaming_market_data_allowed",
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


def _is_valid_number(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0


def _text_number(value: Any) -> str:
    if value is None:
        return "unavailable"
    try:
        number = float(value)
    except (TypeError, ValueError):
        text = str(value)
        return text if text else "unavailable"
    if not math.isfinite(number):
        return "unavailable"
    return str(number)


def _read_market_price(ticker: Any) -> str:
    method = getattr(ticker, "marketPrice", None)
    if callable(method):
        try:
            return _text_number(method())
        except Exception:
            return "unavailable"
    return "unavailable"


def _snapshot_values(ticker: Any):
    bid = _text_number(getattr(ticker, "bid", None))
    ask = _text_number(getattr(ticker, "ask", None))
    last = _text_number(getattr(ticker, "last", None))
    close = _text_number(getattr(ticker, "close", None))
    market_price = _read_market_price(ticker)

    candidates = [bid, ask, last, close, market_price]
    price_available = any(_is_valid_number(value) for value in candidates)
    price_status = "PRICE_AVAILABLE" if price_available else "PRICE_UNAVAILABLE"

    return bid, ask, last, close, market_price, price_available, price_status


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
    snapshot_bid,
    snapshot_ask,
    snapshot_last,
    snapshot_close,
    snapshot_market_price,
    price_available,
    price_status,
    connection_attempted,
    connect_succeeded,
    disconnect_attempted,
    disconnect_succeeded,
    market_data_snapshot_request_attempted,
    market_data_snapshot_read_succeeded,
    current_call_allowed,
    evidence,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return MarketDataSnapshotPreflightPackRow(
        row_id=row_id,
        row_name=row_name,
        source_layer="Phase 20A-20C",
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
        snapshot_bid=str(snapshot_bid),
        snapshot_ask=str(snapshot_ask),
        snapshot_last=str(snapshot_last),
        snapshot_close=str(snapshot_close),
        snapshot_market_price=str(snapshot_market_price),
        price_available=TRUE_TEXT if price_available else FALSE_TEXT,
        price_status=str(price_status),
        connection_attempted=connection_attempted,
        connect_succeeded=connect_succeeded,
        disconnect_attempted=disconnect_attempted,
        disconnect_succeeded=disconnect_succeeded,
        market_data_snapshot_request_attempted=market_data_snapshot_request_attempted,
        market_data_snapshot_read_succeeded=market_data_snapshot_read_succeeded,
        current_call_allowed=current_call_allowed,
        streaming_market_data_allowed=FALSE_TEXT,
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
            "Phase 20A-20C read-only market data snapshot preflight pack. Default mode is dry-run. "
            "When explicitly executed, it allows one non-streaming market data snapshot for one "
            "contract specification. It must not request historical data, contract qualification, "
            "streaming market data, or any trading action."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_market_data_snapshot_preflight_pack_rows(
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

    contract_info_rows = build_ibkr_readonly_contract_info_preflight_pack_rows(
        input_source,
        execute=False,
    )
    contract_info_final = contract_info_rows[-1]
    contract_info_ready = contract_info_final.status in {DRY_RUN_READY, PASS_TEXT}

    execution_allowed = (
        execute
        and not load_error
        and final_gate_go
        and contract_info_ready
        and host in {"127.0.0.1", "localhost"}
        and port not in {"missing", "null", ""}
        and client_id not in {"missing", "null", ""}
    )

    rows = [
        _make_row(
            "MARKET_DATA_SNAPSHOT_ALLOWLIST",
            "Single-contract non-streaming market data snapshot allowlist",
            input_source_text,
            selected_profile,
            execute,
            "Phase 20A",
            ALLOWLIST_DEFINED,
            host,
            port,
            client_id,
            spec,
            "not_requested",
            "not_requested",
            "not_requested",
            "not_requested",
            "not_requested",
            "not_requested",
            "not_requested",
            False,
            "not_requested",
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            FALSE_TEXT,
            "single snapshot allowlist defined; streaming and historical data remain blocked",
            timestamp_jst,
            timestamp_et,
            ["MARKET_DATA_SNAPSHOT_ALLOWLIST_DEFINED"],
        ),
        _make_row(
            "DRY_RUN_GATE",
            "Market data snapshot dry-run gate",
            input_source_text,
            selected_profile,
            execute,
            "Phase 20B",
            EXECUTE_REQUESTED if execute else DRY_RUN_READY,
            host,
            port,
            client_id,
            spec,
            "not_requested",
            "not_requested",
            "not_requested",
            "not_requested",
            "not_requested",
            "not_requested",
            "not_requested",
            False,
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
                "contract_info_ready={};snapshot_only=true;streaming=false"
            ).format(
                str(execute).lower(),
                str(execution_allowed).lower(),
                str(final_gate_go).lower(),
                str(contract_info_ready).lower(),
            ),
            timestamp_jst,
            timestamp_et,
            ["EXECUTE_REQUESTED" if execute else "DRY_RUN_ONLY"],
        ),
    ]

    server_version = "not_requested"
    connection_time = "not_requested"
    snapshot_bid = "not_requested"
    snapshot_ask = "not_requested"
    snapshot_last = "not_requested"
    snapshot_close = "not_requested"
    snapshot_market_price = "not_requested"
    price_available = False
    price_status = "not_requested"
    connection_attempted = FALSE_TEXT
    connect_succeeded = FALSE_TEXT
    disconnect_attempted = FALSE_TEXT
    disconnect_succeeded = FALSE_TEXT
    market_data_snapshot_request_attempted = FALSE_TEXT
    market_data_snapshot_read_succeeded = FALSE_TEXT
    snapshot_status = SKIPPED_STATUS
    snapshot_evidence = "dry_run_only"

    if execute and not execution_allowed:
        snapshot_status = SNAPSHOT_BLOCKED
        snapshot_evidence = (
            "execution_blocked;load_error={};final_gate_go={};contract_info_ready={};"
            "host={};port={};client_id={}"
        ).format(
            str(bool(load_error)).lower(),
            str(final_gate_go).lower(),
            str(contract_info_ready).lower(),
            host,
            port,
            client_id,
        )

    if execution_allowed:
        connector = None
        connection_attempted = TRUE_TEXT
        disconnect_attempted = TRUE_TEXT
        market_data_snapshot_request_attempted = TRUE_TEXT
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
            ticker = connector.reqMktData(
                contract,
                genericTickList="",
                snapshot=True,
                regulatorySnapshot=False,
            )
            sleep_method = getattr(connector, "sleep", None)
            if callable(sleep_method):
                sleep_method(2)
            (
                snapshot_bid,
                snapshot_ask,
                snapshot_last,
                snapshot_close,
                snapshot_market_price,
                price_available,
                price_status,
            ) = _snapshot_values(ticker)
            market_data_snapshot_read_succeeded = TRUE_TEXT
            snapshot_status = PASS_STATUS
            snapshot_evidence = (
                "market_data_snapshot_request_completed;price_available={};price_status={}"
            ).format(str(price_available).lower(), price_status)
        except Exception as exc:
            snapshot_status = FAIL_STATUS
            snapshot_evidence = _diagnose_connection_exception(exc, host, port)
        finally:
            if connector is not None:
                try:
                    connector.disconnect()
                    disconnect_succeeded = TRUE_TEXT
                except Exception as exc:
                    if snapshot_status == PASS_STATUS:
                        snapshot_status = FAIL_STATUS
                    snapshot_evidence = "{};disconnect_failed: {}".format(snapshot_evidence, exc)

    rows.append(
        _make_row(
            "MARKET_DATA_SNAPSHOT_READ",
            "First real read-only market data snapshot read",
            input_source_text,
            selected_profile,
            execute,
            "Phase 20C",
            snapshot_status,
            host,
            port,
            client_id,
            spec,
            server_version,
            connection_time,
            snapshot_bid,
            snapshot_ask,
            snapshot_last,
            snapshot_close,
            snapshot_market_price,
            price_available,
            price_status,
            connection_attempted,
            connect_succeeded,
            disconnect_attempted,
            disconnect_succeeded,
            market_data_snapshot_request_attempted,
            market_data_snapshot_read_succeeded,
            TRUE_TEXT if execution_allowed else FALSE_TEXT,
            snapshot_evidence,
            timestamp_jst,
            timestamp_et,
            ["MARKET_DATA_SNAPSHOT_READ_ONLY"],
        )
    )

    final_status = DRY_RUN_READY
    if execute:
        final_status = PASS_STATUS if snapshot_status == PASS_STATUS else FAIL_STATUS

    rows.append(
        _make_row(
            "FINAL",
            "Final market data snapshot preflight decision",
            input_source_text,
            selected_profile,
            execute,
            "Phase 20A-20C",
            final_status,
            host,
            port,
            client_id,
            spec,
            server_version,
            connection_time,
            snapshot_bid,
            snapshot_ask,
            snapshot_last,
            snapshot_close,
            snapshot_market_price,
            price_available,
            price_status,
            connection_attempted,
            connect_succeeded,
            disconnect_attempted,
            disconnect_succeeded,
            market_data_snapshot_request_attempted,
            market_data_snapshot_read_succeeded,
            TRUE_TEXT if execution_allowed else FALSE_TEXT,
            (
                "execute={};execution_allowed={};final_gate_go={};contract_info_ready={};"
                "connect_succeeded={};market_data_snapshot_read_succeeded={};"
                "price_available={};price_status={}"
            ).format(
                str(execute).lower(),
                str(execution_allowed).lower(),
                str(final_gate_go).lower(),
                str(contract_info_ready).lower(),
                connect_succeeded,
                market_data_snapshot_read_succeeded,
                str(price_available).lower(),
                price_status,
            ),
            timestamp_jst,
            timestamp_et,
            ["PHASE20A20C_DRY_RUN_READY" if not execute else "PHASE20A20C_EXECUTION_RESULT"],
        )
    )

    return rows


def write_ibkr_readonly_market_data_snapshot_preflight_pack_csv(
    path: Union[str, Path],
    rows: Iterable[MarketDataSnapshotPreflightPackRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_market_data_snapshot_preflight_pack_report(
    path: Union[str, Path],
    rows: Iterable[MarketDataSnapshotPreflightPackRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    final_row = row_list[-1] if row_list else None
    selected_profile = final_row.selected_profile if final_row else "unknown"
    final_status = final_row.status if final_row else FAIL_STATUS

    actual_rows = [row for row in row_list if row.row_id == "MARKET_DATA_SNAPSHOT_READ"]
    connection_attempt_count = sum(1 for row in actual_rows if row.connection_attempted == TRUE_TEXT)
    connect_success_count = sum(1 for row in actual_rows if row.connect_succeeded == TRUE_TEXT)
    disconnect_success_count = sum(1 for row in actual_rows if row.disconnect_succeeded == TRUE_TEXT)
    snapshot_attempt_count = sum(
        1 for row in actual_rows if row.market_data_snapshot_request_attempted == TRUE_TEXT
    )
    snapshot_success_count = sum(
        1 for row in actual_rows if row.market_data_snapshot_read_succeeded == TRUE_TEXT
    )
    price_available_count = sum(1 for row in actual_rows if row.price_available == TRUE_TEXT)
    current_call_allowed_count = sum(1 for row in actual_rows if row.current_call_allowed == TRUE_TEXT)
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)

    lines = [
        "# Phase 20A-20C IBKR Read-Only Market Data Snapshot Preflight Pack Report",
        "",
        "- phase: Phase 20A-20C",
        "- scope: read-only single-contract market data snapshot",
        f"- input_source: {input_source}",
        f"- selected_profile: {selected_profile}",
        f"- row_count: {len(row_list)}",
        f"- final_status: {final_status}",
        f"- connection_attempt_count: {connection_attempt_count}",
        f"- connect_success_count: {connect_success_count}",
        f"- disconnect_success_count: {disconnect_success_count}",
        f"- market_data_snapshot_attempt_count: {snapshot_attempt_count}",
        f"- market_data_snapshot_success_count: {snapshot_success_count}",
        f"- price_available_count: {price_available_count}",
        f"- current_call_allowed_count: {current_call_allowed_count}",
        "- counter_scope: MARKET_DATA_SNAPSHOT_READ row only for actual snapshot counters",
        f"- action_allowed_count: {action_allowed_count}",
        "- streaming_market_data_allowed: false",
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
        "| row_id | component | status | execute_requested | connection_attempted | connect_succeeded | disconnect_succeeded | market_data_snapshot_request_attempted | market_data_snapshot_read_succeeded | contract_symbol | snapshot_bid | snapshot_ask | snapshot_last | snapshot_close | snapshot_market_price | price_status | current_call_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
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
                    row.market_data_snapshot_request_attempted,
                    row.market_data_snapshot_read_succeeded,
                    row.contract_symbol,
                    row.snapshot_bid,
                    row.snapshot_ask,
                    row.snapshot_last,
                    row.snapshot_close,
                    row.snapshot_market_price,
                    row.price_status,
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
            "- market data snapshot: one contract, non-streaming, read-only.",
            "- historical data remains blocked.",
            "- contract qualification remains blocked.",
            "- streaming market data remains blocked.",
            "- trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- no streaming market data",
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
