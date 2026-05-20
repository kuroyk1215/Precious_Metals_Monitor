from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Union
from zoneinfo import ZoneInfo

from src.ibkr_readonly_preflight_config_validator import (
    MISSING_TEXT,
    _actual_text,
    _get_dotted,
    _load_config,
)


TRUE_TEXT = "true"
FALSE_TEXT = "false"

CHECKLIST_READY_TEXT = "READY_FOR_MANUAL_REVIEW"
CHECKLIST_BLOCKED_TEXT = "BLOCKED"
MANUAL_REQUIRED_TEXT = "MANUAL_REQUIRED"
CONFIG_OK_TEXT = "CONFIG_OK"
CONFIG_REVIEW_TEXT = "CONFIG_REVIEW"

PAPER_PROFILE = "paper"
LIVE_READONLY_PROFILE = "live-readonly"

DEFAULT_WARNING_FLAGS = (
    "TWS_ENVIRONMENT_CHECKLIST_DEFINED",
    "MANUAL_EXTERNAL_REVIEW_REQUIRED",
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
    "phase15a_ibkr_readonly_tws_environment_checklist",
)


@dataclass(frozen=True)
class TwsEnvironmentChecklistRow:
    checklist_id: str
    checklist_name: str
    source_layer: str
    input_source: str
    selected_profile: str
    external_item: str
    expected_setting: str
    actual_config_value: str
    checklist_status: str
    manual_check_required: str
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
    "checklist_id",
    "checklist_name",
    "source_layer",
    "input_source",
    "selected_profile",
    "external_item",
    "expected_setting",
    "actual_config_value",
    "checklist_status",
    "manual_check_required",
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


def _detect_profile(config) -> str:
    account_mode = _actual_text(_get_dotted(config, "ibkr.account_mode")).lower()
    port = _actual_text(_get_dotted(config, "ibkr.port"))

    if account_mode == "live" or port == "7496":
        return LIVE_READONLY_PROFILE
    return PAPER_PROFILE


def _expected_port(profile: str) -> str:
    return "7496" if profile == LIVE_READONLY_PROFILE else "7497"


def _expected_account_mode(profile: str) -> str:
    return "live" if profile == LIVE_READONLY_PROFILE else "paper"


def _config_matches(value: Any, expected: str) -> bool:
    return _actual_text(value).lower() == expected.lower()


def _make_row(
    checklist_id,
    checklist_name,
    input_source,
    selected_profile,
    external_item,
    expected_setting,
    actual_config_value,
    checklist_status,
    manual_check_required,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return TwsEnvironmentChecklistRow(
        checklist_id=checklist_id,
        checklist_name=checklist_name,
        source_layer="Phase 15A",
        input_source=str(input_source),
        selected_profile=selected_profile,
        external_item=external_item,
        expected_setting=expected_setting,
        actual_config_value=_actual_text(actual_config_value),
        checklist_status=checklist_status,
        manual_check_required=manual_check_required,
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
            "Phase 15A TWS environment checklist only. This produces manual external checks "
            "for TWS and IBKR Gateway/TWS settings before any later read-only connection phase. "
            "It does not connect to TWS or IBKR, does not modify config files, does not request "
            "market data or historical data, and does not allow any trading action."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_tws_environment_checklist_rows(
    input_source: Union[str, Path] = "config.yaml",
):
    timestamp_jst, timestamp_et = _now_pair()
    input_source_text = str(input_source)
    config, load_error = _load_config(input_source)
    selected_profile = _detect_profile(config)

    rows = []

    if load_error:
        rows.append(
            _make_row(
                "INPUT_SOURCE",
                "Input source must exist before environment checklist review",
                input_source_text,
                selected_profile,
                "config.yaml readability",
                "existing_readable_yaml_file",
                load_error,
                CHECKLIST_BLOCKED_TEXT,
                TRUE_TEXT,
                timestamp_jst,
                timestamp_et,
                ["INPUT_SOURCE_MISSING"],
            )
        )

    account_mode = _get_dotted(config, "ibkr.account_mode")
    port = _get_dotted(config, "ibkr.port")
    host = _get_dotted(config, "ibkr.host")
    client_id = _get_dotted(config, "ibkr.client_id")

    expected_account_mode = _expected_account_mode(selected_profile)
    expected_port = _expected_port(selected_profile)

    account_mode_status = (
        CONFIG_OK_TEXT if _config_matches(account_mode, expected_account_mode) else CONFIG_REVIEW_TEXT
    )
    port_status = CONFIG_OK_TEXT if _config_matches(port, expected_port) else CONFIG_REVIEW_TEXT
    host_status = CONFIG_OK_TEXT if _actual_text(host) in {"127.0.0.1", "localhost"} else CONFIG_REVIEW_TEXT
    client_id_status = CONFIG_OK_TEXT if _actual_text(client_id) != MISSING_TEXT else CONFIG_REVIEW_TEXT

    rows.extend(
        [
            _make_row(
                "TWS_INSTALLATION",
                "TWS or IB Gateway must be installed locally",
                input_source_text,
                selected_profile,
                "TWS / IB Gateway installation",
                "installed_and_startable_on_local_machine",
                "manual_external_check",
                MANUAL_REQUIRED_TEXT,
                TRUE_TEXT,
                timestamp_jst,
                timestamp_et,
                ["TWS_INSTALLATION_MANUAL_CHECK_REQUIRED"],
            ),
            _make_row(
                "TWS_LOGIN_MODE",
                "TWS login mode must match selected profile",
                input_source_text,
                selected_profile,
                "TWS login mode",
                expected_account_mode,
                account_mode,
                account_mode_status,
                TRUE_TEXT,
                timestamp_jst,
                timestamp_et,
                ["TWS_LOGIN_MODE_REVIEW"],
            ),
            _make_row(
                "TWS_API_ENABLED",
                "TWS API socket setting must be enabled manually",
                input_source_text,
                selected_profile,
                "Enable ActiveX and Socket Clients",
                "enabled_in_TWS_API_settings",
                "manual_external_check",
                MANUAL_REQUIRED_TEXT,
                TRUE_TEXT,
                timestamp_jst,
                timestamp_et,
                ["TWS_API_ENABLED_MANUAL_CHECK_REQUIRED"],
            ),
            _make_row(
                "TWS_READ_ONLY_API",
                "TWS API must be read-only before any later connection phase",
                input_source_text,
                selected_profile,
                "Read-Only API",
                "enabled_or_equivalent_safety_setting",
                "manual_external_check",
                MANUAL_REQUIRED_TEXT,
                TRUE_TEXT,
                timestamp_jst,
                timestamp_et,
                ["TWS_READ_ONLY_API_MANUAL_CHECK_REQUIRED"],
            ),
            _make_row(
                "TWS_SOCKET_PORT",
                "TWS socket port must match selected profile",
                input_source_text,
                selected_profile,
                "Socket port",
                expected_port,
                port,
                port_status,
                TRUE_TEXT,
                timestamp_jst,
                timestamp_et,
                ["TWS_SOCKET_PORT_REVIEW"],
            ),
            _make_row(
                "TWS_TRUSTED_IP",
                "Trusted IP must be limited to local access",
                input_source_text,
                selected_profile,
                "Trusted IP / allowed client IP",
                "127.0.0.1_or_localhost_only",
                host,
                host_status,
                TRUE_TEXT,
                timestamp_jst,
                timestamp_et,
                ["TWS_TRUSTED_IP_REVIEW"],
            ),
            _make_row(
                "IBKR_CLIENT_ID",
                "IBKR client id must be fixed and reviewed",
                input_source_text,
                selected_profile,
                "client_id",
                "explicit_stable_integer",
                client_id,
                client_id_status,
                TRUE_TEXT,
                timestamp_jst,
                timestamp_et,
                ["IBKR_CLIENT_ID_REVIEW"],
            ),
            _make_row(
                "ORDER_SAFETY_BOUNDARY",
                "TWS/order execution safety boundary must remain closed",
                input_source_text,
                selected_profile,
                "order/cancel/rebalance/auto trade",
                "blocked_in_application_and_not_authorized_by_this_phase",
                "application_flags_false",
                MANUAL_REQUIRED_TEXT,
                TRUE_TEXT,
                timestamp_jst,
                timestamp_et,
                ["ORDER_SAFETY_BOUNDARY_MANUAL_CHECK_REQUIRED"],
            ),
        ]
    )

    blocked = any(row.checklist_status == CHECKLIST_BLOCKED_TEXT for row in rows)
    config_review_count = sum(1 for row in rows if row.checklist_status == CONFIG_REVIEW_TEXT)
    manual_required_count = sum(1 for row in rows if row.manual_check_required == TRUE_TEXT)

    final_status = CHECKLIST_BLOCKED_TEXT if blocked else CHECKLIST_READY_TEXT

    rows.append(
        _make_row(
            "FINAL",
            "Final TWS environment checklist decision",
            input_source_text,
            selected_profile,
            "phase15a.tws_environment_checklist_status",
            "manual_review_required_before_any_connection_phase",
            "config_review={};manual_required={}".format(
                config_review_count,
                manual_required_count,
            ),
            final_status,
            TRUE_TEXT,
            timestamp_jst,
            timestamp_et,
            ["PHASE15A_TWS_ENVIRONMENT_CHECKLIST_READY" if not blocked else "PHASE15A_TWS_ENVIRONMENT_CHECKLIST_BLOCKED"],
        )
    )

    return rows


def write_ibkr_readonly_tws_environment_checklist_csv(
    path: Union[str, Path],
    rows: Iterable[TwsEnvironmentChecklistRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_tws_environment_checklist_report(
    path: Union[str, Path],
    rows: Iterable[TwsEnvironmentChecklistRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    selected_profile = row_list[-1].selected_profile if row_list else "unknown"
    ready_count = sum(1 for row in row_list if row.checklist_status == CHECKLIST_READY_TEXT)
    blocked_count = sum(1 for row in row_list if row.checklist_status == CHECKLIST_BLOCKED_TEXT)
    manual_required_count = sum(1 for row in row_list if row.manual_check_required == TRUE_TEXT)
    config_review_count = sum(1 for row in row_list if row.checklist_status == CONFIG_REVIEW_TEXT)
    modified_count = sum(1 for row in row_list if row.config_file_modified == TRUE_TEXT)
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    final_status = CHECKLIST_BLOCKED_TEXT if blocked_count else CHECKLIST_READY_TEXT

    lines = [
        "# Phase 15A IBKR Read-Only TWS Environment Checklist Report",
        "",
        "- phase: Phase 15A",
        "- scope: IBKR read-only TWS environment checklist",
        f"- input_source: {input_source}",
        f"- selected_profile: {selected_profile}",
        f"- row_count: {len(row_list)}",
        f"- ready_count: {ready_count}",
        f"- blocked_count: {blocked_count}",
        f"- config_review_count: {config_review_count}",
        f"- manual_required_count: {manual_required_count}",
        f"- final_checklist_status: {final_status}",
        f"- config_file_modified_count: {modified_count}",
        f"- action_allowed_count: {action_allowed_count}",
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
        "## Checklist Rows",
        "",
        "| checklist_id | selected_profile | external_item | expected_setting | actual_config_value | checklist_status | manual_check_required | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.checklist_id,
                    row.selected_profile,
                    row.external_item,
                    row.expected_setting,
                    row.actual_config_value,
                    row.checklist_status,
                    row.manual_check_required,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Manual External Checks",
            "",
            "- Confirm TWS or IB Gateway is installed and can be started locally.",
            "- Confirm the selected profile matches the login mode.",
            "- For live-readonly, account_mode should be live and socket port should be 7496.",
            "- For paper, account_mode should be paper and socket port should be 7497.",
            "- Confirm API socket clients are enabled in TWS settings.",
            "- Confirm read-only API or equivalent account-side safety is enabled before any later connection phase.",
            "- Confirm trusted IP / allowed client IP is limited to localhost / 127.0.0.1.",
            "- Confirm no order, cancel, rebalance, or auto-trade permission is enabled by this project.",
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
