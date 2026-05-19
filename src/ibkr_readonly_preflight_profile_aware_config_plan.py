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

PROFILE_PLAN_READY_TEXT = "PROFILE_PLAN_READY"
PROFILE_PLAN_BLOCKED_TEXT = "PROFILE_PLAN_BLOCKED"

AUTO_PROFILE = "auto"
PAPER_PROFILE = "paper"
LIVE_READONLY_PROFILE = "live-readonly"

SUPPORTED_PROFILES = {AUTO_PROFILE, PAPER_PROFILE, LIVE_READONLY_PROFILE}

DANGEROUS_SWITCHES = [
    ("REAL_CONNECTION", "ibkr.real_connection_allowed", "false", "  real_connection_allowed: false"),
    ("CONTRACT_QUALIFICATION", "ibkr.contract_qualification_allowed", "false", "  contract_qualification_allowed: false"),
    ("MARKET_DATA", "ibkr.market_data_request_allowed", "false", "  market_data_request_allowed: false"),
    ("HISTORICAL_DATA", "ibkr.historical_data_request_allowed", "false", "  historical_data_request_allowed: false"),
    ("TRADING_ACTIONS", "ibkr.trading_actions_allowed", "false", "  trading_actions_allowed: false"),
]

DEFAULT_WARNING_FLAGS = (
    "PREFLIGHT_PROFILE_AWARE_CONFIG_PLAN_DEFINED",
    "PROFILE_AWARE_PLAN_ONLY",
    "NO_CONFIG_FILE_MODIFICATION",
    "MANUAL_REVIEW_REQUIRED",
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
    "phase14h_ibkr_readonly_preflight_profile_aware_config_plan",
)


@dataclass(frozen=True)
class ProfileAwareConfigPlanRow:
    profile_plan_id: str
    profile_plan_name: str
    source_layer: str
    input_source: str
    requested_profile: str
    selected_profile: str
    profile_source: str
    config_key: str
    current_value: str
    safe_value: str
    planned_action: str
    would_overwrite_existing: str
    safe_config_line: str
    profile_plan_status: str
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
    "profile_plan_id",
    "profile_plan_name",
    "source_layer",
    "input_source",
    "requested_profile",
    "selected_profile",
    "profile_source",
    "config_key",
    "current_value",
    "safe_value",
    "planned_action",
    "would_overwrite_existing",
    "safe_config_line",
    "profile_plan_status",
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


def _planned_action(current_value: Any, safe_value: str) -> str:
    if current_value == MISSING_TEXT:
        return ADD_TEXT
    if _matches_safe_value(current_value, safe_value):
        return KEEP_TEXT
    return REVIEW_UPDATE_TEXT


def _detect_profile(config) -> str:
    account_mode = _actual_text(_get_dotted(config, "ibkr.account_mode")).lower()
    port = _actual_text(_get_dotted(config, "ibkr.port"))

    if account_mode == "live" or port == "7496":
        return LIVE_READONLY_PROFILE
    if account_mode == "paper" or port == "7497":
        return PAPER_PROFILE
    return PAPER_PROFILE


def _select_profile(config, requested_profile):
    requested = (requested_profile or AUTO_PROFILE).strip().lower()

    if requested == AUTO_PROFILE:
        return _detect_profile(config), "auto_detected"

    if requested in {PAPER_PROFILE, LIVE_READONLY_PROFILE}:
        return requested, "explicit"

    return PAPER_PROFILE, "invalid_requested_profile_fallback_to_paper"


def _profile_items(selected_profile):
    if selected_profile == LIVE_READONLY_PROFILE:
        account_mode = "live"
        port = "7496"
        port_name = "Live TWS port"
    else:
        account_mode = "paper"
        port = "7497"
        port_name = "Paper TWS port"

    return [
        ("READ_ONLY_REQUIRED", "ibkr.read_only_required", "true", "  read_only_required: true"),
        ("ACCOUNT_MODE", "ibkr.account_mode", account_mode, "  account_mode: {}".format(account_mode)),
        ("HOST", "ibkr.host", "127.0.0.1", "  host: 127.0.0.1"),
        ("PORT", "ibkr.port", port, "  port: {}".format(port)),
        ("CLIENT_ID", "ibkr.client_id", "1", "  client_id: 1"),
    ] + DANGEROUS_SWITCHES


def _safe_config_block(selected_profile):
    items = _profile_items(selected_profile)
    lines = ["ibkr:"]
    for _item_id, _key, _safe_value, safe_line in items:
        lines.append(safe_line)
    return "\n".join(lines)


def _make_row(
    profile_plan_id,
    profile_plan_name,
    input_source,
    requested_profile,
    selected_profile,
    profile_source,
    config_key,
    current_value,
    safe_value,
    planned_action,
    would_overwrite_existing,
    safe_config_line,
    profile_plan_status,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return ProfileAwareConfigPlanRow(
        profile_plan_id=profile_plan_id,
        profile_plan_name=profile_plan_name,
        source_layer="Phase 14H",
        input_source=str(input_source),
        requested_profile=requested_profile,
        selected_profile=selected_profile,
        profile_source=profile_source,
        config_key=config_key,
        current_value=_actual_text(current_value),
        safe_value=safe_value,
        planned_action=planned_action,
        would_overwrite_existing=would_overwrite_existing,
        safe_config_line=safe_config_line,
        profile_plan_status=profile_plan_status,
        apply_mode="profile_aware_plan_only",
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
            "Phase 14H profile-aware config plan only. This supports paper and live-readonly "
            "profiles while keeping every execution, market data, historical data, qualification, "
            "and trading switch blocked. It does not modify config files and does not connect to "
            "TWS or IBKR."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_preflight_profile_aware_config_plan_rows(
    input_source: Union[str, Path] = "config.yaml",
    requested_profile: str = AUTO_PROFILE,
):
    timestamp_jst, timestamp_et = _now_pair()
    input_source_text = str(input_source)
    requested_profile_text = requested_profile or AUTO_PROFILE

    config, load_error = _load_config(input_source)
    selected_profile, profile_source = _select_profile(config, requested_profile_text)

    rows = []

    if load_error:
        rows.append(
            _make_row(
                "INPUT_SOURCE",
                "Input source must exist before profile-aware config plan review",
                input_source_text,
                requested_profile_text,
                selected_profile,
                profile_source,
                "input_source",
                load_error,
                "existing_readable_yaml_file",
                REVIEW_UPDATE_TEXT,
                FALSE_TEXT,
                "",
                PROFILE_PLAN_BLOCKED_TEXT,
                timestamp_jst,
                timestamp_et,
                ["INPUT_SOURCE_MISSING"],
            )
        )

    for item_id, config_key, safe_value, safe_config_line in _profile_items(selected_profile):
        current_value = _get_dotted(config, config_key)
        action = _planned_action(current_value, safe_value)
        would_overwrite = TRUE_TEXT if action == REVIEW_UPDATE_TEXT else FALSE_TEXT

        rows.append(
            _make_row(
                item_id,
                "Profile-aware config plan for {}".format(config_key),
                input_source_text,
                requested_profile_text,
                selected_profile,
                profile_source,
                config_key,
                current_value,
                safe_value,
                action,
                would_overwrite,
                safe_config_line,
                PROFILE_PLAN_BLOCKED_TEXT if load_error else PROFILE_PLAN_READY_TEXT,
                timestamp_jst,
                timestamp_et,
                [action, "PROFILE_{}".format(selected_profile.replace("-", "_").upper())],
            )
        )

    add_count = sum(1 for row in rows if row.planned_action == ADD_TEXT)
    keep_count = sum(1 for row in rows if row.planned_action == KEEP_TEXT)
    review_update_count = sum(1 for row in rows if row.planned_action == REVIEW_UPDATE_TEXT)
    overwrite_count = sum(1 for row in rows if row.would_overwrite_existing == TRUE_TEXT)
    final_status = PROFILE_PLAN_BLOCKED_TEXT if load_error else PROFILE_PLAN_READY_TEXT

    if review_update_count:
        final_action = REVIEW_UPDATE_TEXT
    elif add_count:
        final_action = ADD_TEXT
    else:
        final_action = KEEP_TEXT

    rows.append(
        _make_row(
            "FINAL",
            "Final profile-aware config plan decision",
            input_source_text,
            requested_profile_text,
            selected_profile,
            profile_source,
            "phase14h.profile_aware_config_plan_status",
            "add={};keep={};review_update={};overwrite={}".format(
                add_count, keep_count, review_update_count, overwrite_count
            ),
            "PROFILE_AWARE_PLAN_ONLY",
            final_action,
            TRUE_TEXT if overwrite_count else FALSE_TEXT,
            "",
            final_status,
            timestamp_jst,
            timestamp_et,
            ["PHASE14H_PROFILE_AWARE_CONFIG_PLAN_READY" if not load_error else "PHASE14H_PROFILE_AWARE_CONFIG_PLAN_BLOCKED"],
        )
    )

    return rows


def profile_aware_safe_config_block(selected_profile: str = PAPER_PROFILE) -> str:
    profile = selected_profile if selected_profile in {PAPER_PROFILE, LIVE_READONLY_PROFILE} else PAPER_PROFILE
    return _safe_config_block(profile)


def write_ibkr_readonly_preflight_profile_aware_config_plan_csv(
    path: Union[str, Path],
    rows: Iterable[ProfileAwareConfigPlanRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_preflight_profile_aware_config_plan_report(
    path: Union[str, Path],
    rows: Iterable[ProfileAwareConfigPlanRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    selected_profile = row_list[-1].selected_profile if row_list else PAPER_PROFILE
    profile_source = row_list[-1].profile_source if row_list else "unknown"

    add_count = sum(1 for row in row_list if row.planned_action == ADD_TEXT)
    keep_count = sum(1 for row in row_list if row.planned_action == KEEP_TEXT)
    review_update_count = sum(1 for row in row_list if row.planned_action == REVIEW_UPDATE_TEXT)
    overwrite_count = sum(1 for row in row_list if row.would_overwrite_existing == TRUE_TEXT)
    modified_count = sum(1 for row in row_list if row.config_file_modified == TRUE_TEXT)
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    blocked_count = sum(1 for row in row_list if row.profile_plan_status == PROFILE_PLAN_BLOCKED_TEXT)

    final_status = PROFILE_PLAN_BLOCKED_TEXT if blocked_count else PROFILE_PLAN_READY_TEXT

    lines = [
        "# Phase 14H IBKR Read-Only Preflight Profile-Aware Config Plan Report",
        "",
        "- phase: Phase 14H",
        "- scope: IBKR read-only preflight profile-aware config plan",
        f"- input_source: {input_source}",
        f"- selected_profile: {selected_profile}",
        f"- profile_source: {profile_source}",
        f"- row_count: {len(row_list)}",
        f"- add_count: {add_count}",
        f"- keep_count: {keep_count}",
        f"- review_update_count: {review_update_count}",
        f"- overwrite_existing_count: {overwrite_count}",
        f"- final_profile_plan_status: {final_status}",
        f"- config_file_modified_count: {modified_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- apply_mode: profile_aware_plan_only",
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
        "## Profile-Aware Safe Config Block",
        "",
        "```yaml",
        profile_aware_safe_config_block(selected_profile),
        "```",
        "",
        "## Profile Plan Rows",
        "",
        "| profile_plan_id | selected_profile | config_key | current_value | safe_value | planned_action | would_overwrite_existing | config_file_modified | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.profile_plan_id,
                    row.selected_profile,
                    row.config_key,
                    row.current_value,
                    row.safe_value,
                    row.planned_action,
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
            "## Profile Rule",
            "",
            "- auto profile selects live-readonly when current config uses account_mode=live or port=7496.",
            "- auto profile selects paper when current config uses account_mode=paper or port=7497.",
            "- live-readonly keeps account_mode=live and port=7496.",
            "- paper keeps account_mode=paper and port=7497.",
            "- all profiles require read_only_required=true and every execution/request/trading switch=false.",
            "- this phase does not edit config.yaml.",
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
