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

ADD_TEXT = "ADD"
UPDATE_TEXT = "UPDATE"
NO_CHANGE_TEXT = "NO_CHANGE"
PLAN_READY_TEXT = "PLAN_READY"
PLAN_BLOCKED_TEXT = "PLAN_BLOCKED"

EXPECTED_CONFIG = [
    ("READ_ONLY_REQUIRED", "Read-only required config", "ibkr.read_only_required", "true"),
    ("ACCOUNT_MODE", "Account mode config", "ibkr.account_mode", "paper"),
    ("HOST", "Local TWS host config", "ibkr.host", "127.0.0.1"),
    ("PORT", "Paper TWS port config", "ibkr.port", "7497"),
    ("CLIENT_ID", "IBKR client id config", "ibkr.client_id", "1"),
    ("REAL_CONNECTION", "Real connection switch config", "ibkr.real_connection_allowed", "false"),
    ("CONTRACT_QUALIFICATION", "Contract qualification switch config", "ibkr.contract_qualification_allowed", "false"),
    ("MARKET_DATA", "Market data request switch config", "ibkr.market_data_request_allowed", "false"),
    ("HISTORICAL_DATA", "Historical data request switch config", "ibkr.historical_data_request_allowed", "false"),
    ("TRADING_ACTIONS", "Trading action switch config", "ibkr.trading_actions_allowed", "false"),
]

DEFAULT_WARNING_FLAGS = (
    "PREFLIGHT_CONFIG_APPLY_PLAN_DEFINED",
    "APPLY_PLAN_ONLY",
    "NO_CONFIG_FILE_MODIFICATION",
    "READ_ONLY_REQUIRED",
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
    "phase14e_ibkr_readonly_preflight_config_apply_plan",
)


@dataclass(frozen=True)
class PreflightConfigApplyPlanRow:
    plan_id: str
    plan_name: str
    source_layer: str
    input_source: str
    config_key: str
    expected_value: str
    actual_value: str
    planned_change: str
    plan_status: str
    apply_mode: str
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
    "plan_id",
    "plan_name",
    "source_layer",
    "input_source",
    "config_key",
    "expected_value",
    "actual_value",
    "planned_change",
    "plan_status",
    "apply_mode",
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


def _expected_matches(actual: Any, expected_text: str) -> bool:
    return _actual_text(actual).lower() == expected_text.lower()


def _planned_change(actual: Any, expected_text: str) -> str:
    if actual == MISSING_TEXT:
        return ADD_TEXT
    if _expected_matches(actual, expected_text):
        return NO_CHANGE_TEXT
    return UPDATE_TEXT


def _make_row(
    plan_id,
    plan_name,
    input_source,
    config_key,
    expected_value,
    actual_value,
    planned_change,
    plan_status,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return PreflightConfigApplyPlanRow(
        plan_id=plan_id,
        plan_name=plan_name,
        source_layer="Phase 14E",
        input_source=str(input_source),
        config_key=config_key,
        expected_value=expected_value,
        actual_value=_actual_text(actual_value),
        planned_change=planned_change,
        plan_status=plan_status,
        apply_mode="plan_only",
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
            "Phase 14E apply plan only. This compares local configuration against the safe "
            "read-only preflight template and does not modify any config file. No TWS connection, "
            "no IBKR connection, no IBKR API request, no contract qualification, no market data request, "
            "no historical data request, and no trading action is allowed."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_preflight_config_apply_plan_rows(
    input_source: Union[str, Path] = "config.yaml",
):
    timestamp_jst, timestamp_et = _now_pair()
    input_source_text = str(input_source)
    config, load_error = _load_config(input_source)

    rows = []

    if load_error:
        rows.append(
            _make_row(
                "INPUT_SOURCE",
                "Input source must exist before apply plan can be reviewed",
                input_source_text,
                "input_source",
                "existing_readable_yaml_file",
                load_error,
                UPDATE_TEXT,
                PLAN_BLOCKED_TEXT,
                timestamp_jst,
                timestamp_et,
                ["INPUT_SOURCE_MISSING"],
            )
        )

    for plan_id, plan_name, config_key, expected_value in EXPECTED_CONFIG:
        actual_value = _get_dotted(config, config_key)
        planned_change = _planned_change(actual_value, expected_value)
        rows.append(
            _make_row(
                plan_id,
                plan_name,
                input_source_text,
                config_key,
                expected_value,
                actual_value,
                planned_change,
                PLAN_READY_TEXT if not load_error else PLAN_BLOCKED_TEXT,
                timestamp_jst,
                timestamp_et,
                [planned_change],
            )
        )

    add_count = sum(1 for row in rows if row.planned_change == ADD_TEXT)
    update_count = sum(1 for row in rows if row.planned_change == UPDATE_TEXT)
    no_change_count = sum(1 for row in rows if row.planned_change == NO_CHANGE_TEXT)
    final_status = PLAN_BLOCKED_TEXT if load_error else PLAN_READY_TEXT
    final_change = NO_CHANGE_TEXT if add_count == 0 and update_count == 0 and not load_error else UPDATE_TEXT

    rows.append(
        _make_row(
            "FINAL",
            "Final read-only preflight config apply plan decision",
            input_source_text,
            "phase14e.preflight_config_apply_plan_status",
            "PLAN_ONLY",
            f"add={add_count};update={update_count};no_change={no_change_count}",
            final_change,
            final_status,
            timestamp_jst,
            timestamp_et,
            ["PHASE14E_PREFLIGHT_CONFIG_APPLY_PLAN_ONLY", final_status],
        )
    )

    return rows


def write_ibkr_readonly_preflight_config_apply_plan_csv(
    path: Union[str, Path],
    rows: Iterable[PreflightConfigApplyPlanRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_preflight_config_apply_plan_report(
    path: Union[str, Path],
    rows: Iterable[PreflightConfigApplyPlanRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    add_count = sum(1 for row in row_list if row.planned_change == ADD_TEXT)
    update_count = sum(1 for row in row_list if row.planned_change == UPDATE_TEXT)
    no_change_count = sum(1 for row in row_list if row.planned_change == NO_CHANGE_TEXT)
    blocked_count = sum(1 for row in row_list if row.plan_status == PLAN_BLOCKED_TEXT)
    modified_count = sum(1 for row in row_list if row.config_file_modified == TRUE_TEXT)
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)

    final_status = PLAN_BLOCKED_TEXT if blocked_count else PLAN_READY_TEXT

    lines = [
        "# Phase 14E IBKR Read-Only Preflight Config Apply Plan Report",
        "",
        "- phase: Phase 14E",
        "- scope: IBKR read-only preflight config apply plan",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- add_count: {add_count}",
        f"- update_count: {update_count}",
        f"- no_change_count: {no_change_count}",
        f"- final_plan_status: {final_status}",
        f"- config_file_modified_count: {modified_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- apply_mode: plan_only",
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
        "## Apply Plan Rows",
        "",
        "| plan_id | config_key | expected_value | actual_value | planned_change | plan_status | config_file_modified | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.plan_id,
                    row.config_key,
                    row.expected_value,
                    row.actual_value,
                    row.planned_change,
                    row.plan_status,
                    row.config_file_modified,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Recommended Safe Config Block",
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
            f"- Phase 14E final plan status: {final_status}",
            "- This phase is a diff/apply plan only.",
            "- The existing config file is not modified.",
            "- ADD means the key is missing and should be reviewed before manual addition.",
            "- UPDATE means the key exists but differs from the safe read-only template.",
            "- NO_CHANGE means the key already matches the safe read-only template.",
            "- This phase does not authorize a real IBKR connection.",
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
