from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union
from zoneinfo import ZoneInfo

from src.ibkr_readonly_market_data_snapshot_preflight_pack import (
    DRY_RUN_READY,
    PASS_STATUS,
    build_ibkr_readonly_market_data_snapshot_preflight_pack_rows,
)


TRUE_TEXT = "true"
FALSE_TEXT = "false"

DIAGNOSTIC_READY = "DIAGNOSTIC_READY"
DIAGNOSTIC_EXECUTED = "DIAGNOSTIC_EXECUTED"
NO_MARKET_DATA_SUBSCRIPTION = "NO_MARKET_DATA_SUBSCRIPTION"
PRICE_AVAILABLE = "PRICE_AVAILABLE"
PRICE_UNAVAILABLE = "PRICE_UNAVAILABLE"
SNAPSHOT_NOT_EXECUTED = "SNAPSHOT_NOT_EXECUTED"
SNAPSHOT_FAILED = "SNAPSHOT_FAILED"

IBKR_10168 = "10168"
UNKNOWN_TEXT = "unknown"

DEFAULT_WARNING_FLAGS = (
    "MARKET_DATA_ENTITLEMENT_DIAGNOSTIC_DEFINED",
    "SNAPSHOT_DIAGNOSTIC_ONLY",
    "NO_STREAMING_MARKET_DATA",
    "NO_HISTORICAL_DATA_REQUEST",
    "NO_CONTRACT_QUALIFICATION",
    "ORDER_ACTION_BLOCKED",
    "CANCELLATION_ACTION_BLOCKED",
    "REBALANCE_BLOCKED",
    "AUTO_TRADE_BLOCKED",
    "phase20d_ibkr_readonly_market_data_entitlement_diagnostic",
)


@dataclass(frozen=True)
class MarketDataEntitlementDiagnosticRow:
    row_id: str
    row_name: str
    source_layer: str
    input_source: str
    selected_profile: str
    execute_requested: str
    component: str
    diagnostic_status: str
    market_data_status: str
    ibkr_error_code: str
    ibkr_error_message: str
    delayed_data_enabled: str
    snapshot_request_succeeded: str
    price_available: str
    price_status: str
    next_action: str
    contract_symbol: str
    contract_exchange: str
    contract_primary_exchange: str
    snapshot_bid: str
    snapshot_ask: str
    snapshot_last: str
    snapshot_close: str
    snapshot_market_price: str
    connection_attempted: str
    connect_succeeded: str
    disconnect_succeeded: str
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
    "diagnostic_status",
    "market_data_status",
    "ibkr_error_code",
    "ibkr_error_message",
    "delayed_data_enabled",
    "snapshot_request_succeeded",
    "price_available",
    "price_status",
    "next_action",
    "contract_symbol",
    "contract_exchange",
    "contract_primary_exchange",
    "snapshot_bid",
    "snapshot_ask",
    "snapshot_last",
    "snapshot_close",
    "snapshot_market_price",
    "connection_attempted",
    "connect_succeeded",
    "disconnect_succeeded",
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


def _snapshot_row(rows):
    matches = [row for row in rows if row.row_id == "MARKET_DATA_SNAPSHOT_READ"]
    return matches[0] if matches else rows[-1]


def _classify_market_data_status(snapshot_row, execute: bool):
    if not execute:
        return (
            SNAPSHOT_NOT_EXECUTED,
            "none",
            "not_executed",
            UNKNOWN_TEXT,
            "Run with explicit execute flag when TWS/API and data permissions are ready.",
        )

    if snapshot_row.market_data_snapshot_read_succeeded != TRUE_TEXT:
        return (
            SNAPSHOT_FAILED,
            "unknown",
            snapshot_row.evidence,
            UNKNOWN_TEXT,
            "Inspect snapshot failure evidence before retrying.",
        )

    if snapshot_row.price_available == TRUE_TEXT:
        return (
            PRICE_AVAILABLE,
            "none",
            "price_available",
            UNKNOWN_TEXT,
            "No entitlement action required for this snapshot.",
        )

    return (
        NO_MARKET_DATA_SUBSCRIPTION,
        IBKR_10168,
        "requested market data is not subscribed; delayed market data is not enabled",
        FALSE_TEXT,
        "Enable delayed market data or subscribe to the relevant market data package, then retry one snapshot.",
    )


def _make_row(
    row_id,
    row_name,
    input_source,
    selected_profile,
    execute_requested,
    component,
    diagnostic_status,
    market_data_status,
    ibkr_error_code,
    ibkr_error_message,
    delayed_data_enabled,
    snapshot_row,
    next_action,
    evidence,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return MarketDataEntitlementDiagnosticRow(
        row_id=row_id,
        row_name=row_name,
        source_layer="Phase 20D",
        input_source=str(input_source),
        selected_profile=selected_profile,
        execute_requested=TRUE_TEXT if execute_requested else FALSE_TEXT,
        component=component,
        diagnostic_status=diagnostic_status,
        market_data_status=market_data_status,
        ibkr_error_code=str(ibkr_error_code),
        ibkr_error_message=str(ibkr_error_message),
        delayed_data_enabled=str(delayed_data_enabled),
        snapshot_request_succeeded=snapshot_row.market_data_snapshot_read_succeeded,
        price_available=snapshot_row.price_available,
        price_status=snapshot_row.price_status,
        next_action=next_action,
        contract_symbol=snapshot_row.contract_symbol,
        contract_exchange=snapshot_row.contract_exchange,
        contract_primary_exchange=snapshot_row.contract_primary_exchange,
        snapshot_bid=snapshot_row.snapshot_bid,
        snapshot_ask=snapshot_row.snapshot_ask,
        snapshot_last=snapshot_row.snapshot_last,
        snapshot_close=snapshot_row.snapshot_close,
        snapshot_market_price=snapshot_row.snapshot_market_price,
        connection_attempted=snapshot_row.connection_attempted,
        connect_succeeded=snapshot_row.connect_succeeded,
        disconnect_succeeded=snapshot_row.disconnect_succeeded,
        current_call_allowed=snapshot_row.current_call_allowed,
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
            "Phase 20D market data entitlement diagnostic only. It classifies the result of a "
            "single-contract non-streaming snapshot attempt. It must not request historical data, "
            "streaming market data, contract qualification, or any trading action."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_market_data_entitlement_diagnostic_rows(
    input_source: Union[str, Path] = "config.yaml",
    execute: bool = False,
    connector_factory: Optional[Callable[[], Any]] = None,
):
    timestamp_jst, timestamp_et = _now_pair()
    input_source_text = str(input_source)

    snapshot_rows = build_ibkr_readonly_market_data_snapshot_preflight_pack_rows(
        input_source,
        execute=execute,
        connector_factory=connector_factory,
    )
    snapshot_final = snapshot_rows[-1]
    snapshot_actual = _snapshot_row(snapshot_rows)

    (
        market_data_status,
        ibkr_error_code,
        ibkr_error_message,
        delayed_data_enabled,
        next_action,
    ) = _classify_market_data_status(snapshot_actual, execute)

    diagnostic_status = DIAGNOSTIC_READY if not execute else DIAGNOSTIC_EXECUTED

    rows = [
        _make_row(
            "SNAPSHOT_RESULT_SUMMARY",
            "Phase 20 snapshot result summary",
            input_source_text,
            snapshot_final.selected_profile,
            execute,
            "Phase 20A-20C",
            diagnostic_status,
            market_data_status,
            ibkr_error_code,
            ibkr_error_message,
            delayed_data_enabled,
            snapshot_actual,
            next_action,
            snapshot_actual.evidence,
            timestamp_jst,
            timestamp_et,
            ["SNAPSHOT_RESULT_SUMMARY"],
        ),
        _make_row(
            "ENTITLEMENT_DIAGNOSTIC",
            "Market data entitlement diagnostic",
            input_source_text,
            snapshot_final.selected_profile,
            execute,
            "Phase 20D",
            diagnostic_status,
            market_data_status,
            ibkr_error_code,
            ibkr_error_message,
            delayed_data_enabled,
            snapshot_actual,
            next_action,
            (
                "snapshot_request_succeeded={};price_available={};"
                "market_data_status={};ibkr_error_code={};delayed_data_enabled={}"
            ).format(
                snapshot_actual.market_data_snapshot_read_succeeded,
                snapshot_actual.price_available,
                market_data_status,
                ibkr_error_code,
                delayed_data_enabled,
            ),
            timestamp_jst,
            timestamp_et,
            ["MARKET_DATA_ENTITLEMENT_DIAGNOSTIC"],
        ),
        _make_row(
            "FINAL",
            "Final market data entitlement diagnostic decision",
            input_source_text,
            snapshot_final.selected_profile,
            execute,
            "final",
            diagnostic_status,
            market_data_status,
            ibkr_error_code,
            ibkr_error_message,
            delayed_data_enabled,
            snapshot_actual,
            next_action,
            (
                "execute={};snapshot_status={};snapshot_request_succeeded={};"
                "price_available={};market_data_status={};next_action={}"
            ).format(
                str(execute).lower(),
                snapshot_final.status,
                snapshot_actual.market_data_snapshot_read_succeeded,
                snapshot_actual.price_available,
                market_data_status,
                next_action,
            ),
            timestamp_jst,
            timestamp_et,
            ["PHASE20D_DIAGNOSTIC_READY" if not execute else "PHASE20D_DIAGNOSTIC_EXECUTED"],
        ),
    ]

    return rows


def write_ibkr_readonly_market_data_entitlement_diagnostic_csv(
    path: Union[str, Path],
    rows: Iterable[MarketDataEntitlementDiagnosticRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_market_data_entitlement_diagnostic_report(
    path: Union[str, Path],
    rows: Iterable[MarketDataEntitlementDiagnosticRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    final_row = row_list[-1] if row_list else None
    selected_profile = final_row.selected_profile if final_row else "unknown"
    diagnostic_status = final_row.diagnostic_status if final_row else DIAGNOSTIC_READY
    market_data_status = final_row.market_data_status if final_row else UNKNOWN_TEXT
    ibkr_error_code = final_row.ibkr_error_code if final_row else UNKNOWN_TEXT
    delayed_data_enabled = final_row.delayed_data_enabled if final_row else UNKNOWN_TEXT

    actual_rows = [row for row in row_list if row.row_id == "SNAPSHOT_RESULT_SUMMARY"]
    snapshot_success_count = sum(
        1 for row in actual_rows if row.snapshot_request_succeeded == TRUE_TEXT
    )
    price_available_count = sum(1 for row in actual_rows if row.price_available == TRUE_TEXT)
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)

    lines = [
        "# Phase 20D IBKR Market Data Entitlement Diagnostic Report",
        "",
        "- phase: Phase 20D",
        "- scope: market data entitlement / delayed-data diagnostic",
        f"- input_source: {input_source}",
        f"- selected_profile: {selected_profile}",
        f"- row_count: {len(row_list)}",
        f"- diagnostic_status: {diagnostic_status}",
        f"- market_data_status: {market_data_status}",
        f"- ibkr_error_code: {ibkr_error_code}",
        f"- delayed_data_enabled: {delayed_data_enabled}",
        f"- snapshot_success_count: {snapshot_success_count}",
        f"- price_available_count: {price_available_count}",
        "- counter_scope: SNAPSHOT_RESULT_SUMMARY row only for snapshot counters",
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
        "| row_id | diagnostic_status | market_data_status | ibkr_error_code | delayed_data_enabled | snapshot_request_succeeded | price_available | price_status | next_action | current_call_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.row_id,
                    row.diagnostic_status,
                    row.market_data_status,
                    row.ibkr_error_code,
                    row.delayed_data_enabled,
                    row.snapshot_request_succeeded,
                    row.price_available,
                    row.price_status,
                    row.next_action,
                    row.current_call_allowed,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Diagnostic Rule",
            "",
            "- If snapshot request succeeds but no valid price is returned, classify as market data entitlement or delayed-data issue.",
            "- IBKR error 10168 is represented as no market data subscription / delayed data not enabled.",
            "- This phase does not enable delayed data, does not subscribe to market data, and does not retry streaming data.",
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
