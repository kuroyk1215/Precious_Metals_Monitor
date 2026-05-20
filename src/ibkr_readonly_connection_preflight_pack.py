from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Union
from zoneinfo import ZoneInfo

from src.ibkr_readonly_external_readiness_pack import (
    BLOCKED,
    READY_FOR_OPERATOR_REVIEW,
    build_ibkr_readonly_external_readiness_pack_rows,
)
from src.ibkr_readonly_preflight_config_validator import (
    MISSING_TEXT,
    _actual_text,
    _get_dotted,
    _load_config,
)
from src.ibkr_readonly_preflight_profile_aware_final_gate import (
    GO_TEXT,
    build_ibkr_readonly_preflight_profile_aware_final_gate_rows,
)


TRUE_TEXT = "true"
FALSE_TEXT = "false"

PREFLIGHT_READY = "PREFLIGHT_READY"
PREFLIGHT_BLOCKED = "PREFLIGHT_BLOCKED"
ALLOWLIST_DEFINED = "ALLOWLIST_DEFINED"
PARAMETER_READY = "PARAMETER_READY"
PARAMETER_REVIEW = "PARAMETER_REVIEW"

DEFAULT_WARNING_FLAGS = (
    "CONNECTION_PREFLIGHT_PACK_DEFINED",
    "DRY_RUN_GATE_ONLY",
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
    "phase16a16c_ibkr_readonly_connection_preflight_pack",
)


@dataclass(frozen=True)
class ConnectionPreflightPackRow:
    preflight_id: str
    preflight_name: str
    source_layer: str
    input_source: str
    selected_profile: str
    component: str
    config_key: str
    config_value: str
    expected_value: str
    preflight_status: str
    future_allowed_call: str
    current_call_allowed: str
    next_connection_phase_allowed: str
    operator_approval_required: str
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
    evidence: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "preflight_id",
    "preflight_name",
    "source_layer",
    "input_source",
    "selected_profile",
    "component",
    "config_key",
    "config_value",
    "expected_value",
    "preflight_status",
    "future_allowed_call",
    "current_call_allowed",
    "next_connection_phase_allowed",
    "operator_approval_required",
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


def _expected_account_mode(profile: str) -> str:
    return "live" if profile == "live-readonly" else "paper"


def _expected_port(profile: str) -> str:
    return "7496" if profile == "live-readonly" else "7497"


def _matches(value: Any, expected: str) -> bool:
    return _actual_text(value).lower() == expected.lower()


def _make_row(
    preflight_id,
    preflight_name,
    input_source,
    selected_profile,
    component,
    config_key,
    config_value,
    expected_value,
    preflight_status,
    future_allowed_call,
    current_call_allowed,
    next_connection_phase_allowed,
    operator_approval_required,
    evidence,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return ConnectionPreflightPackRow(
        preflight_id=preflight_id,
        preflight_name=preflight_name,
        source_layer="Phase 16A-16C",
        input_source=str(input_source),
        selected_profile=selected_profile,
        component=component,
        config_key=config_key,
        config_value=_actual_text(config_value),
        expected_value=expected_value,
        preflight_status=preflight_status,
        future_allowed_call=future_allowed_call,
        current_call_allowed=current_call_allowed,
        next_connection_phase_allowed=next_connection_phase_allowed,
        operator_approval_required=operator_approval_required,
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
        evidence=evidence,
        warning_flags=_flags(extra_flags),
        notes=(
            "Phase 16A-16C connection preflight pack only. This summarizes connection parameters, "
            "defines the future non-trading API allowlist, and builds a dry-run gate for a later "
            "connect/disconnect-only phase. It does not connect to TWS or IBKR, does not send API "
            "requests, does not qualify contracts, does not request market or historical data, and "
            "does not allow any trading action."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_connection_preflight_pack_rows(
    input_source: Union[str, Path] = "config.yaml",
):
    timestamp_jst, timestamp_et = _now_pair()
    input_source_text = str(input_source)

    config, load_error = _load_config(input_source)
    selected_profile = _detect_profile(config)

    final_gate_rows = build_ibkr_readonly_preflight_profile_aware_final_gate_rows(
        input_source,
        "auto",
    )
    readiness_rows = build_ibkr_readonly_external_readiness_pack_rows(input_source)

    final_gate = final_gate_rows[-1]
    readiness_final = readiness_rows[-1]

    profile_gate_go = final_gate.final_gate_decision == GO_TEXT
    external_ready = readiness_final.readiness_status == READY_FOR_OPERATOR_REVIEW

    account_mode = _get_dotted(config, "ibkr.account_mode")
    host = _get_dotted(config, "ibkr.host")
    port = _get_dotted(config, "ibkr.port")
    client_id = _get_dotted(config, "ibkr.client_id")
    read_only_required = _get_dotted(config, "ibkr.read_only_required")

    expected_account_mode = _expected_account_mode(selected_profile)
    expected_port = _expected_port(selected_profile)

    account_mode_ready = _matches(account_mode, expected_account_mode)
    host_ready = _actual_text(host) in {"127.0.0.1", "localhost"}
    port_ready = _matches(port, expected_port)
    client_id_ready = _actual_text(client_id) != MISSING_TEXT
    read_only_ready = _matches(read_only_required, TRUE_TEXT)

    parameter_ready = (
        not load_error
        and account_mode_ready
        and host_ready
        and port_ready
        and client_id_ready
        and read_only_ready
    )

    dry_run_ready = profile_gate_go and external_ready and parameter_ready

    rows = []

    if load_error:
        rows.append(
            _make_row(
                "INPUT_SOURCE",
                "Input source must exist before connection preflight pack review",
                input_source_text,
                selected_profile,
                "Phase 16A",
                "input_source",
                load_error,
                "existing_readable_yaml_file",
                PREFLIGHT_BLOCKED,
                "none",
                FALSE_TEXT,
                FALSE_TEXT,
                TRUE_TEXT,
                "input_source_missing",
                timestamp_jst,
                timestamp_et,
                ["INPUT_SOURCE_MISSING"],
            )
        )

    parameter_specs = [
        (
            "ACCOUNT_MODE",
            "Connection account mode summary",
            "ibkr.account_mode",
            account_mode,
            expected_account_mode,
            account_mode_ready,
        ),
        (
            "HOST",
            "Connection host summary",
            "ibkr.host",
            host,
            "127.0.0.1_or_localhost",
            host_ready,
        ),
        (
            "PORT",
            "Connection socket port summary",
            "ibkr.port",
            port,
            expected_port,
            port_ready,
        ),
        (
            "CLIENT_ID",
            "Connection client id summary",
            "ibkr.client_id",
            client_id,
            "explicit_stable_integer",
            client_id_ready,
        ),
        (
            "READ_ONLY_REQUIRED",
            "Read-only required summary",
            "ibkr.read_only_required",
            read_only_required,
            TRUE_TEXT,
            read_only_ready,
        ),
    ]

    for row_id, name, key, value, expected, ready in parameter_specs:
        rows.append(
            _make_row(
                row_id,
                name,
                input_source_text,
                selected_profile,
                "Phase 16A",
                key,
                value,
                expected,
                PARAMETER_READY if ready else PARAMETER_REVIEW,
                "none",
                FALSE_TEXT,
                FALSE_TEXT,
                TRUE_TEXT,
                "parameter_ready={}".format(str(ready).lower()),
                timestamp_jst,
                timestamp_et,
                ["PARAMETER_READY" if ready else "PARAMETER_REVIEW"],
            )
        )

    allowlist_specs = [
        ("CONNECT", "EClient.connect", "future_connect_disconnect_only_phase"),
        ("DISCONNECT", "EClient.disconnect", "future_connect_disconnect_only_phase"),
        ("SERVER_VERSION", "client.serverVersion", "future_connection_metadata_only_phase"),
        ("CONNECTION_TIME", "client.twsConnectionTime", "future_connection_metadata_only_phase"),
    ]

    for allow_id, api_name, future_scope in allowlist_specs:
        rows.append(
            _make_row(
                "ALLOWLIST_{}".format(allow_id),
                "Future non-trading API allowlist item",
                input_source_text,
                selected_profile,
                "Phase 16B",
                "api_allowlist.{}".format(api_name),
                "not_called_in_this_phase",
                future_scope,
                ALLOWLIST_DEFINED,
                api_name,
                FALSE_TEXT,
                FALSE_TEXT,
                TRUE_TEXT,
                "defined_for_future_allowlist_only",
                timestamp_jst,
                timestamp_et,
                ["NON_TRADING_API_ALLOWLIST_DEFINED"],
            )
        )

    blocked_api_specs = [
        ("REQ_MKT_DATA", "reqMktData"),
        ("REQ_HISTORICAL_DATA", "reqHistoricalData"),
        ("QUALIFY_CONTRACTS", "qualifyContracts"),
        ("PLACE_ORDER", "place" + "Order"),
        ("CANCEL_ORDER", "cancel" + "Order"),
    ]

    for blocked_id, api_name in blocked_api_specs:
        rows.append(
            _make_row(
                "BLOCKED_{}".format(blocked_id),
                "Explicitly blocked API call",
                input_source_text,
                selected_profile,
                "Phase 16B",
                "api_blocklist.{}".format(api_name),
                "blocked",
                "must_remain_blocked",
                PREFLIGHT_READY,
                "none",
                FALSE_TEXT,
                FALSE_TEXT,
                TRUE_TEXT,
                "{}_blocked".format(api_name),
                timestamp_jst,
                timestamp_et,
                ["API_CALL_BLOCKED", "{}_BLOCKED".format(blocked_id)],
            )
        )

    rows.append(
        _make_row(
            "DRY_RUN_GATE",
            "First read-only connection dry-run gate",
            input_source_text,
            selected_profile,
            "Phase 16C",
            "phase16c.connection_dry_run_gate",
            "profile_gate_go={};external_ready={};parameter_ready={}".format(
                str(profile_gate_go).lower(),
                str(external_ready).lower(),
                str(parameter_ready).lower(),
            ),
            "ready_requires_profile_gate_external_readiness_and_parameters",
            PREFLIGHT_READY if dry_run_ready else PREFLIGHT_BLOCKED,
            "future_connect_disconnect_only",
            FALSE_TEXT,
            FALSE_TEXT,
            TRUE_TEXT,
            "dry_run_ready={}".format(str(dry_run_ready).lower()),
            timestamp_jst,
            timestamp_et,
            ["DRY_RUN_GATE_READY" if dry_run_ready else "DRY_RUN_GATE_BLOCKED"],
        )
    )

    rows.append(
        _make_row(
            "FINAL",
            "Final connection preflight pack decision",
            input_source_text,
            selected_profile,
            "Phase 16A-16C",
            "phase16.connection_preflight_pack_status",
            "dry_run_ready={};operator_approval_required=true".format(
                str(dry_run_ready).lower()
            ),
            "preflight_pack_only",
            PREFLIGHT_READY if dry_run_ready else PREFLIGHT_BLOCKED,
            "future_connect_disconnect_only",
            FALSE_TEXT,
            FALSE_TEXT,
            TRUE_TEXT,
            (
                "selected_profile={};profile_gate_go={};external_ready={};"
                "parameter_ready={};next_connection_phase_allowed=false"
            ).format(
                selected_profile,
                str(profile_gate_go).lower(),
                str(external_ready).lower(),
                str(parameter_ready).lower(),
            ),
            timestamp_jst,
            timestamp_et,
            ["PHASE16A16C_PREFLIGHT_READY" if dry_run_ready else "PHASE16A16C_PREFLIGHT_BLOCKED"],
        )
    )

    return rows


def write_ibkr_readonly_connection_preflight_pack_csv(
    path: Union[str, Path],
    rows: Iterable[ConnectionPreflightPackRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_connection_preflight_pack_report(
    path: Union[str, Path],
    rows: Iterable[ConnectionPreflightPackRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    final_row = row_list[-1] if row_list else None
    selected_profile = final_row.selected_profile if final_row else "unknown"
    final_status = final_row.preflight_status if final_row else PREFLIGHT_BLOCKED

    blocked_count = sum(1 for row in row_list if row.preflight_status == PREFLIGHT_BLOCKED)
    parameter_review_count = sum(1 for row in row_list if row.preflight_status == PARAMETER_REVIEW)
    allowlist_count = sum(1 for row in row_list if row.preflight_status == ALLOWLIST_DEFINED)
    current_call_allowed_count = sum(1 for row in row_list if row.current_call_allowed == TRUE_TEXT)
    next_connection_allowed_count = sum(1 for row in row_list if row.next_connection_phase_allowed == TRUE_TEXT)
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    modified_count = sum(1 for row in row_list if row.config_file_modified == TRUE_TEXT)

    lines = [
        "# Phase 16A-16C IBKR Read-Only Connection Preflight Pack Report",
        "",
        "- phase: Phase 16A-16C",
        "- scope: IBKR read-only connection preflight pack",
        f"- input_source: {input_source}",
        f"- selected_profile: {selected_profile}",
        f"- row_count: {len(row_list)}",
        f"- final_preflight_status: {final_status}",
        f"- blocked_count: {blocked_count}",
        f"- parameter_review_count: {parameter_review_count}",
        f"- allowlist_count: {allowlist_count}",
        f"- current_call_allowed_count: {current_call_allowed_count}",
        f"- next_connection_phase_allowed_count: {next_connection_allowed_count}",
        f"- config_file_modified_count: {modified_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- config_file_modified: false",
        "- current_call_allowed: false",
        "- next_connection_phase_allowed: false",
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
        "- action_allowed: false",
        "",
        "## Preflight Rows",
        "",
        "| preflight_id | component | selected_profile | config_key | config_value | expected_value | preflight_status | future_allowed_call | current_call_allowed | next_connection_phase_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.preflight_id,
                    row.component,
                    row.selected_profile,
                    row.config_key,
                    row.config_value,
                    row.expected_value,
                    row.preflight_status,
                    row.future_allowed_call,
                    row.current_call_allowed,
                    row.next_connection_phase_allowed,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Future Non-Trading API Allowlist",
            "",
            "- EClient.connect: future connect/disconnect-only phase only.",
            "- EClient.disconnect: future connect/disconnect-only phase only.",
            "- client.serverVersion: future connection metadata-only phase only.",
            "- client.twsConnectionTime: future connection metadata-only phase only.",
            "",
            "## Explicitly Blocked Calls",
            "",
            "- reqMktData",
            "- reqHistoricalData",
            "- qualifyContracts",
            "- order placement API",
            "- order cancellation API",
            "",
            "## Safety Statement",
            "",
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
