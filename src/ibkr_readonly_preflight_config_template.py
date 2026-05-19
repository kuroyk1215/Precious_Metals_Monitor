from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Union
from zoneinfo import ZoneInfo


TRUE_TEXT = "true"
FALSE_TEXT = "false"
TEMPLATE_TEXT = "TEMPLATE"

DEFAULT_WARNING_FLAGS = (
    "PREFLIGHT_CONFIG_TEMPLATE_DEFINED",
    "READ_ONLY_REQUIRED",
    "ACCOUNT_MODE_TEMPLATE_PAPER_DEFAULT",
    "LOCAL_TWS_HOST_TEMPLATE",
    "EXPLICIT_PORT_TEMPLATE",
    "EXPLICIT_CLIENT_ID_TEMPLATE",
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
    "NO_CONFIG_FILE_MODIFICATION",
    "phase14d_ibkr_readonly_preflight_config_template",
)


@dataclass(frozen=True)
class PreflightConfigTemplateRow:
    template_id: str
    template_name: str
    source_layer: str
    input_source: str
    config_key: str
    template_value: str
    template_status: str
    apply_mode: str
    config_file_modified: str
    read_only_required: str
    account_mode_explicit_required: str
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
    "template_id",
    "template_name",
    "source_layer",
    "input_source",
    "config_key",
    "template_value",
    "template_status",
    "apply_mode",
    "config_file_modified",
    "read_only_required",
    "account_mode_explicit_required",
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
    template_id,
    template_name,
    input_source,
    config_key,
    template_value,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return PreflightConfigTemplateRow(
        template_id=template_id,
        template_name=template_name,
        source_layer="Phase 14D",
        input_source=str(input_source),
        config_key=config_key,
        template_value=template_value,
        template_status=TEMPLATE_TEXT,
        apply_mode="template_only",
        config_file_modified=FALSE_TEXT,
        read_only_required=TRUE_TEXT,
        account_mode_explicit_required=TRUE_TEXT,
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
            "Phase 14D read-only preflight config template only. "
            "This creates a safe reference template and does not modify any existing config file. "
            "No TWS connection, no IBKR connection, no IBKR API request, no contract qualification, "
            "no market data request, no historical data request, and no trading action is allowed."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_preflight_config_template_rows(
    input_source: Union[str, Path] = "config.yaml",
):
    timestamp_jst, timestamp_et = _now_pair()
    input_source_text = str(input_source)

    specs = [
        (
            "READ_ONLY_REQUIRED",
            "Read-only required template",
            "ibkr.read_only_required",
            "true",
            ["READ_ONLY_REQUIRED_TEMPLATE"],
        ),
        (
            "ACCOUNT_MODE",
            "Account mode template",
            "ibkr.account_mode",
            "paper",
            ["ACCOUNT_MODE_TEMPLATE_PAPER_DEFAULT"],
        ),
        (
            "HOST",
            "Local TWS host template",
            "ibkr.host",
            "127.0.0.1",
            ["LOCAL_TWS_HOST_TEMPLATE"],
        ),
        (
            "PORT",
            "Paper TWS port template",
            "ibkr.port",
            "7497",
            ["EXPLICIT_PORT_TEMPLATE"],
        ),
        (
            "CLIENT_ID",
            "IBKR client id template",
            "ibkr.client_id",
            "1",
            ["EXPLICIT_CLIENT_ID_TEMPLATE"],
        ),
        (
            "REAL_CONNECTION",
            "Real connection switch template",
            "ibkr.real_connection_allowed",
            "false",
            ["REAL_CONNECTION_BLOCKED"],
        ),
        (
            "CONTRACT_QUALIFICATION",
            "Contract qualification switch template",
            "ibkr.contract_qualification_allowed",
            "false",
            ["CONTRACT_QUALIFICATION_BLOCKED"],
        ),
        (
            "MARKET_DATA",
            "Market data request switch template",
            "ibkr.market_data_request_allowed",
            "false",
            ["MARKET_DATA_REQUEST_BLOCKED"],
        ),
        (
            "HISTORICAL_DATA",
            "Historical data request switch template",
            "ibkr.historical_data_request_allowed",
            "false",
            ["HISTORICAL_DATA_REQUEST_BLOCKED"],
        ),
        (
            "TRADING_ACTIONS",
            "Trading action switch template",
            "ibkr.trading_actions_allowed",
            "false",
            ["ORDER_BLOCKED", "CANCEL_BLOCKED", "REBALANCE_BLOCKED", "AUTO_TRADE_BLOCKED"],
        ),
        (
            "FINAL",
            "Final preflight config template decision",
            "phase14d.preflight_config_template_status",
            "TEMPLATE_ONLY",
            ["PHASE14D_PREFLIGHT_CONFIG_TEMPLATE_ONLY"],
        ),
    ]

    return [
        _make_row(
            template_id=template_id,
            template_name=template_name,
            input_source=input_source_text,
            config_key=config_key,
            template_value=template_value,
            timestamp_jst=timestamp_jst,
            timestamp_et=timestamp_et,
            extra_flags=extra_flags,
        )
        for template_id, template_name, config_key, template_value, extra_flags in specs
    ]


def write_ibkr_readonly_preflight_config_template_csv(
    path: Union[str, Path],
    rows: Iterable[PreflightConfigTemplateRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_preflight_config_template_yaml(
    path: Union[str, Path],
    rows: Iterable[PreflightConfigTemplateRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = list(rows)

    lines = [
        "# Phase 14D IBKR read-only preflight config template",
        "# Template only. This file is not auto-applied to config.yaml.",
        "# No TWS connection / no IBKR connection / no API request / no trading.",
        "ibkr:",
        "  read_only_required: true",
        "  account_mode: paper",
        "  host: 127.0.0.1",
        "  port: 7497",
        "  client_id: 1",
        "  real_connection_allowed: false",
        "  contract_qualification_allowed: false",
        "  market_data_request_allowed: false",
        "  historical_data_request_allowed: false",
        "  trading_actions_allowed: false",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_ibkr_readonly_preflight_config_template_report(
    path: Union[str, Path],
    rows: Iterable[PreflightConfigTemplateRow],
    input_source: Union[str, Path],
    yaml_path: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    template_count = sum(1 for row in row_list if row.template_status == TEMPLATE_TEXT)
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    modified_count = sum(1 for row in row_list if row.config_file_modified == TRUE_TEXT)

    lines = [
        "# Phase 14D IBKR Read-Only Preflight Config Template Report",
        "",
        "- phase: Phase 14D",
        "- scope: IBKR read-only preflight config template",
        f"- input_source: {input_source}",
        f"- template_yaml: {yaml_path}",
        f"- row_count: {len(row_list)}",
        f"- template_count: {template_count}",
        f"- config_file_modified_count: {modified_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- apply_mode: template_only",
        "- config_file_modified: false",
        "- action_allowed: false",
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
        "",
        "## Template Rows",
        "",
        "| template_id | config_key | template_value | template_status | config_file_modified | action_allowed |",
        "|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.template_id,
                    row.config_key,
                    row.template_value,
                    row.template_status,
                    row.config_file_modified,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## YAML Template",
            "",
            "```yaml",
            "ibkr:",
            "  read_only_required: true",
            "  account_mode: paper",
            "  host: 127.0.0.1",
            "  port: 7497",
            "  client_id: 1",
            "  real_connection_allowed: false",
            "  contract_qualification_allowed: false",
            "  market_data_request_allowed: false",
            "  historical_data_request_allowed: false",
            "  trading_actions_allowed: false",
            "```",
            "",
            "## Final Decision",
            "",
            "- Phase 14D status: TEMPLATE_ONLY",
            "- The generated YAML is a reference template only.",
            "- The existing config file is not modified.",
            "- This phase does not authorize a real IBKR connection.",
            "- This phase does not authorize contract qualification, market data requests, historical data requests, or trading actions.",
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
