from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo


TRUE_TEXT = "true"
FALSE_TEXT = "false"

DEFAULT_WARNING_FLAGS = (
    "PREFLIGHT_CONFIG_CONTRACT_DEFINED",
    "READ_ONLY_REQUIRED",
    "ACCOUNT_MODE_EXPLICIT_REQUIRED",
    "REAL_CONNECTION_BLOCKED",
    "TWS_CONNECTION_BLOCKED",
    "IBKR_API_REQUEST_BLOCKED",
    "CONTRACT_QUALIFICATION_BLOCKED",
    "MARKET_DATA_REQUEST_BLOCKED",
    "HISTORICAL_DATA_REQUEST_BLOCKED",
    "ORDER_BLOCKED",
    "CANCEL_BLOCKED",
    "REBALANCE_BLOCKED",
    "AUTO_TRADE_BLOCKED",
    "phase14b_ibkr_readonly_preflight_config_contract",
)


@dataclass(frozen=True)
class PreflightConfigContractRow:
    contract_id: str
    contract_name: str
    source_layer: str
    preflight_config_contract_status: str
    required_config_key: str
    required_config_value: str
    prohibited_config_values: str
    read_only_required: str
    account_mode_explicit_required: str
    trading_permissions_must_be_disabled: str
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
    contract_decision: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "contract_id",
    "contract_name",
    "source_layer",
    "preflight_config_contract_status",
    "required_config_key",
    "required_config_value",
    "prohibited_config_values",
    "read_only_required",
    "account_mode_explicit_required",
    "trading_permissions_must_be_disabled",
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
    "contract_decision",
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


def _make_row(
    contract_id: str,
    contract_name: str,
    required_config_key: str,
    required_config_value: str,
    prohibited_config_values: str,
    contract_decision: str,
    timestamp_jst: str,
    timestamp_et: str,
) -> PreflightConfigContractRow:
    return PreflightConfigContractRow(
        contract_id=contract_id,
        contract_name=contract_name,
        source_layer="Phase 14B",
        preflight_config_contract_status="DEFINED",
        required_config_key=required_config_key,
        required_config_value=required_config_value,
        prohibited_config_values=prohibited_config_values,
        read_only_required=TRUE_TEXT,
        account_mode_explicit_required=TRUE_TEXT,
        trading_permissions_must_be_disabled=TRUE_TEXT,
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
        contract_decision=contract_decision,
        warning_flags=_flags([contract_decision]),
        notes=(
            "Phase 14B preflight config contract only. This defines required future configuration "
            "keys and forbidden runtime capabilities before any real read-only connection can be considered. "
            "No TWS connection, no IBKR connection, no IBKR API request, no real contract qualification, "
            "no market data request, no historical data request, and no trading action is allowed."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_preflight_config_contract_rows(
    input_source: str | Path = "data/market_data_provider_config.yaml",
) -> list[PreflightConfigContractRow]:
    timestamp_jst, timestamp_et = _now_pair()
    _ = str(input_source)

    return [
        _make_row(
            "READ_ONLY_REQUIRED",
            "Read-only required configuration contract",
            "ibkr.read_only_required",
            "true",
            "false,missing,null",
            "read_only_required_must_be_true_before_any_future_connection",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "ACCOUNT_MODE",
            "Account mode explicit configuration contract",
            "ibkr.account_mode",
            "explicit_live_or_paper",
            "missing,null,unknown",
            "account_mode_must_be_explicit_before_any_future_connection",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "HOST",
            "TWS host configuration contract",
            "ibkr.host",
            "explicit_localhost_only",
            "missing,null,0.0.0.0,remote_host",
            "host_must_be_explicit_and_local_before_any_future_connection",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "PORT",
            "TWS port configuration contract",
            "ibkr.port",
            "explicit_tws_port",
            "missing,null,unknown",
            "port_must_be_explicit_before_any_future_connection",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "CLIENT_ID",
            "IBKR client id configuration contract",
            "ibkr.client_id",
            "explicit_integer",
            "missing,null,unknown",
            "client_id_must_be_explicit_before_any_future_connection",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "CONNECTION",
            "Real connection switch configuration contract",
            "ibkr.real_connection_allowed",
            "false",
            "true",
            "real_connection_switch_must_remain_false_in_contract_phase",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "QUALIFICATION",
            "Contract qualification switch configuration contract",
            "ibkr.contract_qualification_allowed",
            "false",
            "true",
            "real_contract_qualification_switch_must_remain_false",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "MARKET_DATA",
            "Market data request switch configuration contract",
            "ibkr.market_data_request_allowed",
            "false",
            "true",
            "market_data_request_switch_must_remain_false",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "HISTORICAL_DATA",
            "Historical data request switch configuration contract",
            "ibkr.historical_data_request_allowed",
            "false",
            "true",
            "historical_data_request_switch_must_remain_false",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "TRADING_ACTIONS",
            "Trading action switch configuration contract",
            "ibkr.trading_actions_allowed",
            "false",
            "true",
            "order_cancel_rebalance_auto_trade_switches_must_remain_false",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "FINAL",
            "Final preflight config contract",
            "phase14b.preflight_config_contract_status",
            "DEFINED",
            "execution_enabled,connection_enabled,trading_enabled",
            "phase14b_preflight_config_contract_defined_but_execution_blocked",
            timestamp_jst,
            timestamp_et,
        ),
    ]


def write_ibkr_readonly_preflight_config_contract_csv(
    path: str | Path,
    rows: Iterable[PreflightConfigContractRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_preflight_config_contract_report(
    path: str | Path,
    rows: Iterable[PreflightConfigContractRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    defined_count = sum(1 for row in row_list if row.preflight_config_contract_status == "DEFINED")
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    statuses = sorted({row.preflight_config_contract_status for row in row_list}) or ["none"]

    lines = [
        "# Phase 14B IBKR Read-Only Preflight Config Contract Report",
        "",
        "- phase: Phase 14B",
        "- scope: IBKR read-only preflight config contract",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- preflight_config_contract_statuses: {','.join(statuses)}",
        f"- defined_count: {defined_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- preflight_config_contract_status: DEFINED",
        "- read_only_required: true",
        "- account_mode_explicit_required: true",
        "- trading_permissions_must_be_disabled: true",
        "- real_connection_allowed: false",
        "- tws_connection_allowed: false",
        "- ibkr_api_request_allowed: false",
        "- contract_qualification_allowed: false",
        "- market_data_request_allowed: false",
        "- historical_data_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Preflight Config Contract Rows",
        "",
        "| contract_id | required_config_key | required_config_value | prohibited_config_values | real_connection_allowed | tws_connection_allowed | ibkr_api_request_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.contract_id,
                    row.required_config_key,
                    row.required_config_value,
                    row.prohibited_config_values,
                    row.real_connection_allowed,
                    row.tws_connection_allowed,
                    row.ibkr_api_request_allowed,
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
            "- Preflight config contract status: DEFINED",
            "- read_only_required must be true before any future real read-only connection.",
            "- account_mode must be explicit before any future real read-only connection.",
            "- Real connection allowed: false",
            "- TWS connection allowed: false",
            "- IBKR API request allowed: false",
            "- Contract qualification allowed: false",
            "- Market data requests remain blocked.",
            "- Historical data requests remain blocked.",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- Phase 14B preflight config contract report only",
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
