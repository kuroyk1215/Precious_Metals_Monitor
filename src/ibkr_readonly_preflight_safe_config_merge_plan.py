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
KEEP_TEXT = "KEEP"
REVIEW_UPDATE_TEXT = "REVIEW_UPDATE"
MERGE_PLAN_READY_TEXT = "MERGE_PLAN_READY"
MERGE_PLAN_BLOCKED_TEXT = "MERGE_PLAN_BLOCKED"

SAFE_CONFIG_ITEMS = [
    ("READ_ONLY_REQUIRED", "ibkr.read_only_required", "true", "  read_only_required: true"),
    ("ACCOUNT_MODE", "ibkr.account_mode", "paper", "  account_mode: paper"),
    ("HOST", "ibkr.host", "127.0.0.1", "  host: 127.0.0.1"),
    ("PORT", "ibkr.port", "7497", "  port: 7497"),
    ("CLIENT_ID", "ibkr.client_id", "1", "  client_id: 1"),
    ("REAL_CONNECTION", "ibkr.real_connection_allowed", "false", "  real_connection_allowed: false"),
    ("CONTRACT_QUALIFICATION", "ibkr.contract_qualification_allowed", "false", "  contract_qualification_allowed: false"),
    ("MARKET_DATA", "ibkr.market_data_request_allowed", "false", "  market_data_request_allowed: false"),
    ("HISTORICAL_DATA", "ibkr.historical_data_request_allowed", "false", "  historical_data_request_allowed: false"),
    ("TRADING_ACTIONS", "ibkr.trading_actions_allowed", "false", "  trading_actions_allowed: false"),
]

DEFAULT_WARNING_FLAGS = (
    "PREFLIGHT_SAFE_CONFIG_MERGE_PLAN_DEFINED",
    "MERGE_PLAN_ONLY",
    "NO_CONFIG_FILE_MODIFICATION",
    "MANUAL_COPY_REQUIRED",
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
    "phase14g_ibkr_readonly_preflight_safe_config_merge_plan",
)


@dataclass(frozen=True)
class SafeConfigMergePlanRow:
    merge_id: str
    merge_name: str
    source_layer: str
    input_source: str
    config_key: str
    current_value: str
    safe_value: str
    merge_action: str
    would_overwrite_existing: str
    safe_config_line: str
    merge_plan_status: str
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
    "merge_id",
    "merge_name",
    "source_layer",
    "input_source",
    "config_key",
    "current_value",
    "safe_value",
    "merge_action",
    "would_overwrite_existing",
    "safe_config_line",
    "merge_plan_status",
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


def _matches_safe_value(current_value: Any, safe_value: str) -> bool:
    return _actual_text(current_value).lower() == safe_value.lower()


def _merge_action(current_value: Any, safe_value: str) -> str:
    if current_value == MISSING_TEXT:
        return ADD_TEXT
    if _matches_safe_value(current_value, safe_value):
        return KEEP_TEXT
    return REVIEW_UPDATE_TEXT


def _make_row(
    merge_id,
    merge_name,
    input_source,
    config_key,
    current_value,
    safe_value,
    merge_action,
    would_overwrite_existing,
    safe_config_line,
    merge_plan_status,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return SafeConfigMergePlanRow(
        merge_id=merge_id,
        merge_name=merge_name,
        source_layer="Phase 14G",
        input_source=str(input_source),
        config_key=config_key,
        current_value=_actual_text(current_value),
        safe_value=safe_value,
        merge_action=merge_action,
        would_overwrite_existing=would_overwrite_existing,
        safe_config_line=safe_config_line,
        merge_plan_status=merge_plan_status,
        apply_mode="manual_merge_plan_only",
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
            "Phase 14G safe config merge plan only. This produces a manual copy block and "
            "overwrite review list. It does not modify config files. No TWS connection, no IBKR "
            "connection, no API request, no contract qualification, no market data request, "
            "no historical data request, and no trading action is allowed."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_preflight_safe_config_merge_plan_rows(
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
                "Input source must exist before manual merge plan review",
                input_source_text,
                "input_source",
                load_error,
                "existing_readable_yaml_file",
                REVIEW_UPDATE_TEXT,
                FALSE_TEXT,
                "",
                MERGE_PLAN_BLOCKED_TEXT,
                timestamp_jst,
                timestamp_et,
                ["INPUT_SOURCE_MISSING"],
            )
        )

    for merge_id, config_key, safe_value, safe_config_line in SAFE_CONFIG_ITEMS:
        current_value = _get_dotted(config, config_key)
        action = _merge_action(current_value, safe_value)
        would_overwrite = TRUE_TEXT if action == REVIEW_UPDATE_TEXT else FALSE_TEXT
        rows.append(
            _make_row(
                merge_id,
                "Safe config merge plan for {}".format(config_key),
                input_source_text,
                config_key,
                current_value,
                safe_value,
                action,
                would_overwrite,
                safe_config_line,
                MERGE_PLAN_BLOCKED_TEXT if load_error else MERGE_PLAN_READY_TEXT,
                timestamp_jst,
                timestamp_et,
                [action],
            )
        )

    add_count = sum(1 for row in rows if row.merge_action == ADD_TEXT)
    keep_count = sum(1 for row in rows if row.merge_action == KEEP_TEXT)
    review_update_count = sum(1 for row in rows if row.merge_action == REVIEW_UPDATE_TEXT)
    overwrite_count = sum(1 for row in rows if row.would_overwrite_existing == TRUE_TEXT)
    final_status = MERGE_PLAN_BLOCKED_TEXT if load_error else MERGE_PLAN_READY_TEXT

    rows.append(
        _make_row(
            "FINAL",
            "Final safe config manual merge plan decision",
            input_source_text,
            "phase14g.safe_config_merge_plan_status",
            "add={};keep={};review_update={};overwrite={}".format(
                add_count, keep_count, review_update_count, overwrite_count
            ),
            "MANUAL_MERGE_PLAN_ONLY",
            REVIEW_UPDATE_TEXT if review_update_count else (ADD_TEXT if add_count else KEEP_TEXT),
            TRUE_TEXT if overwrite_count else FALSE_TEXT,
            "",
            final_status,
            timestamp_jst,
            timestamp_et,
            ["PHASE14G_SAFE_CONFIG_MERGE_PLAN_READY" if not load_error else "PHASE14G_SAFE_CONFIG_MERGE_PLAN_BLOCKED"],
        )
    )

    return rows


def safe_config_merge_block() -> str:
    lines = [
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
    ]
    return "\n".join(lines)


def write_ibkr_readonly_preflight_safe_config_merge_plan_csv(
    path: Union[str, Path],
    rows: Iterable[SafeConfigMergePlanRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_preflight_safe_config_merge_plan_report(
    path: Union[str, Path],
    rows: Iterable[SafeConfigMergePlanRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    add_count = sum(1 for row in row_list if row.merge_action == ADD_TEXT)
    keep_count = sum(1 for row in row_list if row.merge_action == KEEP_TEXT)
    review_update_count = sum(1 for row in row_list if row.merge_action == REVIEW_UPDATE_TEXT)
    overwrite_count = sum(1 for row in row_list if row.would_overwrite_existing == TRUE_TEXT)
    modified_count = sum(1 for row in row_list if row.config_file_modified == TRUE_TEXT)
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    blocked_count = sum(1 for row in row_list if row.merge_plan_status == MERGE_PLAN_BLOCKED_TEXT)

    final_status = MERGE_PLAN_BLOCKED_TEXT if blocked_count else MERGE_PLAN_READY_TEXT

    lines = [
        "# Phase 14G IBKR Read-Only Preflight Safe Config Merge Plan Report",
        "",
        "- phase: Phase 14G",
        "- scope: IBKR read-only preflight safe config merge plan",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- add_count: {add_count}",
        f"- keep_count: {keep_count}",
        f"- review_update_count: {review_update_count}",
        f"- overwrite_existing_count: {overwrite_count}",
        f"- final_merge_plan_status: {final_status}",
        f"- config_file_modified_count: {modified_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- apply_mode: manual_merge_plan_only",
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
        "## Safe Config Block",
        "",
        "```yaml",
        safe_config_merge_block(),
        "```",
        "",
        "## Merge Plan Rows",
        "",
        "| merge_id | config_key | current_value | safe_value | merge_action | would_overwrite_existing | config_file_modified | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.merge_id,
                    row.config_key,
                    row.current_value,
                    row.safe_value,
                    row.merge_action,
                    row.would_overwrite_existing,
                    row.config_file_modified,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Manual Review Rule",
            "",
            "- ADD means the key is missing and can be manually added after review.",
            "- KEEP means the existing value already matches the safe template.",
            "- REVIEW_UPDATE means the key exists but differs from the safe template.",
            "- would_overwrite_existing=true means manual overwrite review is required.",
            "- This phase does not edit config.yaml.",
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
