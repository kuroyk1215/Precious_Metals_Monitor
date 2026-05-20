from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Union
from zoneinfo import ZoneInfo

from src.ibkr_readonly_preflight_config_validator import (
    PASS_TEXT,
    build_ibkr_readonly_preflight_config_validator_rows,
)
from src.ibkr_readonly_preflight_profile_aware_config_plan import (
    ADD_TEXT,
    KEEP_TEXT,
    PROFILE_PLAN_BLOCKED_TEXT,
    REVIEW_UPDATE_TEXT,
    SUPPORTED_PROFILES,
    build_ibkr_readonly_preflight_profile_aware_config_plan_rows,
)


TRUE_TEXT = "true"
FALSE_TEXT = "false"

GO_TEXT = "GO"
NO_GO_TEXT = "NO_GO"
PASS_GATE_TEXT = "PASS"
FAIL_GATE_TEXT = "FAIL"

DEFAULT_WARNING_FLAGS = (
    "PROFILE_AWARE_FINAL_GATE_DEFINED",
    "PROFILE_AWARE_FINAL_GATE_ONLY",
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
    "phase14i_ibkr_readonly_preflight_profile_aware_final_gate",
)


@dataclass(frozen=True)
class ProfileAwareFinalGateRow:
    gate_id: str
    gate_name: str
    source_layer: str
    input_source: str
    requested_profile: str
    selected_profile: str
    profile_source: str
    upstream_stage: str
    upstream_status: str
    evidence: str
    gate_status: str
    final_gate_decision: str
    go_allowed: str
    config_ready: str
    profile_plan_clear: str
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
    "gate_id",
    "gate_name",
    "source_layer",
    "input_source",
    "requested_profile",
    "selected_profile",
    "profile_source",
    "upstream_stage",
    "upstream_status",
    "evidence",
    "gate_status",
    "final_gate_decision",
    "go_allowed",
    "config_ready",
    "profile_plan_clear",
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


def _make_row(
    gate_id,
    gate_name,
    input_source,
    requested_profile,
    selected_profile,
    profile_source,
    upstream_stage,
    upstream_status,
    evidence,
    gate_status,
    final_gate_decision,
    go_allowed,
    config_ready,
    profile_plan_clear,
    timestamp_jst,
    timestamp_et,
    extra_flags=(),
):
    return ProfileAwareFinalGateRow(
        gate_id=gate_id,
        gate_name=gate_name,
        source_layer="Phase 14I",
        input_source=str(input_source),
        requested_profile=requested_profile,
        selected_profile=selected_profile,
        profile_source=profile_source,
        upstream_stage=upstream_stage,
        upstream_status=upstream_status,
        evidence=evidence,
        gate_status=gate_status,
        final_gate_decision=final_gate_decision,
        go_allowed=go_allowed,
        config_ready=config_ready,
        profile_plan_clear=profile_plan_clear,
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
            "Phase 14I profile-aware final gate only. This summarizes the local config validator "
            "and Phase 14H profile-aware config plan. It supports paper and live-readonly profiles, "
            "does not modify config files, and does not connect to TWS or IBKR. No API request, "
            "contract qualification, market data request, historical data request, order, cancel, "
            "rebalance, or auto trade is allowed."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def _profile_summary(profile_rows):
    if not profile_rows:
        return "auto", "paper", "unknown"

    final_row = profile_rows[-1]
    return (
        final_row.requested_profile,
        final_row.selected_profile,
        final_row.profile_source,
    )


def build_ibkr_readonly_preflight_profile_aware_final_gate_rows(
    input_source: Union[str, Path] = "config.yaml",
    requested_profile: str = "auto",
):
    timestamp_jst, timestamp_et = _now_pair()
    input_source_text = str(input_source)
    requested_profile_text = requested_profile or "auto"

    validator_rows = build_ibkr_readonly_preflight_config_validator_rows(input_source)
    profile_rows = build_ibkr_readonly_preflight_profile_aware_config_plan_rows(
        input_source,
        requested_profile_text,
    )

    requested_profile_value, selected_profile, profile_source = _profile_summary(profile_rows)

    validator_pass_count = sum(1 for row in validator_rows if row.validation_status == PASS_TEXT)
    validator_fail_count = len(validator_rows) - validator_pass_count
    config_ready = validator_fail_count == 0

    non_final_profile_rows = [
        row
        for row in profile_rows
        if row.profile_plan_id not in {"FINAL", "INPUT_SOURCE"}
    ]
    add_count = sum(1 for row in non_final_profile_rows if row.planned_action == ADD_TEXT)
    keep_count = sum(1 for row in non_final_profile_rows if row.planned_action == KEEP_TEXT)
    review_update_count = sum(
        1 for row in non_final_profile_rows if row.planned_action == REVIEW_UPDATE_TEXT
    )
    blocked_count = sum(
        1 for row in profile_rows if row.profile_plan_status == PROFILE_PLAN_BLOCKED_TEXT
    )
    overwrite_count = sum(1 for row in profile_rows if row.would_overwrite_existing == TRUE_TEXT)

    profile_plan_clear = (
        add_count == 0
        and review_update_count == 0
        and blocked_count == 0
    )

    final_go = config_ready and profile_plan_clear
    final_decision = GO_TEXT if final_go else NO_GO_TEXT
    final_gate_status = PASS_GATE_TEXT if final_go else FAIL_GATE_TEXT

    rows = [
        _make_row(
            "CONFIG_VALIDATOR",
            "Phase 14C config validator gate",
            input_source_text,
            requested_profile_value,
            selected_profile,
            profile_source,
            "Phase 14C",
            PASS_GATE_TEXT if config_ready else FAIL_GATE_TEXT,
            "validator_pass={};validator_fail={}".format(
                validator_pass_count,
                validator_fail_count,
            ),
            PASS_GATE_TEXT if config_ready else FAIL_GATE_TEXT,
            GO_TEXT if config_ready else NO_GO_TEXT,
            TRUE_TEXT if config_ready else FALSE_TEXT,
            TRUE_TEXT if config_ready else FALSE_TEXT,
            FALSE_TEXT,
            timestamp_jst,
            timestamp_et,
            ["CONFIG_VALIDATOR_PASS" if config_ready else "CONFIG_VALIDATOR_FAIL"],
        ),
        _make_row(
            "PROFILE_AWARE_CONFIG_PLAN",
            "Phase 14H profile-aware config plan gate",
            input_source_text,
            requested_profile_value,
            selected_profile,
            profile_source,
            "Phase 14H",
            PASS_GATE_TEXT if profile_plan_clear else FAIL_GATE_TEXT,
            "add={};keep={};review_update={};blocked={};overwrite={}".format(
                add_count,
                keep_count,
                review_update_count,
                blocked_count,
                overwrite_count,
            ),
            PASS_GATE_TEXT if profile_plan_clear else FAIL_GATE_TEXT,
            GO_TEXT if profile_plan_clear else NO_GO_TEXT,
            TRUE_TEXT if profile_plan_clear else FALSE_TEXT,
            FALSE_TEXT,
            TRUE_TEXT if profile_plan_clear else FALSE_TEXT,
            timestamp_jst,
            timestamp_et,
            ["PROFILE_PLAN_CLEAR" if profile_plan_clear else "PROFILE_PLAN_NEEDS_REVIEW"],
        ),
        _make_row(
            "SAFETY_BOUNDARY",
            "Execution safety boundary gate",
            input_source_text,
            requested_profile_value,
            selected_profile,
            profile_source,
            "Phase 14I",
            PASS_GATE_TEXT,
            (
                "real_connection_allowed=false;tws_connection_allowed=false;"
                "ibkr_api_request_allowed=false;action_allowed=false"
            ),
            PASS_GATE_TEXT,
            GO_TEXT,
            FALSE_TEXT,
            TRUE_TEXT if config_ready else FALSE_TEXT,
            TRUE_TEXT if profile_plan_clear else FALSE_TEXT,
            timestamp_jst,
            timestamp_et,
            ["SAFETY_BOUNDARY_LOCKED"],
        ),
        _make_row(
            "FINAL",
            "Final IBKR read-only profile-aware preflight gate decision",
            input_source_text,
            requested_profile_value,
            selected_profile,
            profile_source,
            "Phase 14I",
            final_gate_status,
            (
                "selected_profile={};config_ready={};profile_plan_clear={};"
                "validator_fail={};add={};review_update={};blocked={};overwrite={}"
            ).format(
                selected_profile,
                str(config_ready).lower(),
                str(profile_plan_clear).lower(),
                validator_fail_count,
                add_count,
                review_update_count,
                blocked_count,
                overwrite_count,
            ),
            final_gate_status,
            final_decision,
            TRUE_TEXT if final_go else FALSE_TEXT,
            TRUE_TEXT if config_ready else FALSE_TEXT,
            TRUE_TEXT if profile_plan_clear else FALSE_TEXT,
            timestamp_jst,
            timestamp_et,
            ["PHASE14I_PROFILE_AWARE_FINAL_GATE_GO" if final_go else "PHASE14I_PROFILE_AWARE_FINAL_GATE_NO_GO"],
        ),
    ]

    return rows


def write_ibkr_readonly_preflight_profile_aware_final_gate_csv(
    path: Union[str, Path],
    rows: Iterable[ProfileAwareFinalGateRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_preflight_profile_aware_final_gate_report(
    path: Union[str, Path],
    rows: Iterable[ProfileAwareFinalGateRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    final_rows = [row for row in row_list if row.gate_id == "FINAL"]
    final_decision = final_rows[0].final_gate_decision if final_rows else NO_GO_TEXT
    selected_profile = final_rows[0].selected_profile if final_rows else "unknown"
    profile_source = final_rows[0].profile_source if final_rows else "unknown"

    go_count = sum(1 for row in row_list if row.final_gate_decision == GO_TEXT)
    no_go_count = sum(1 for row in row_list if row.final_gate_decision == NO_GO_TEXT)
    modified_count = sum(1 for row in row_list if row.config_file_modified == TRUE_TEXT)
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)

    lines = [
        "# Phase 14I IBKR Read-Only Preflight Profile-Aware Final Gate Report",
        "",
        "- phase: Phase 14I",
        "- scope: IBKR read-only preflight profile-aware final gate",
        f"- input_source: {input_source}",
        f"- selected_profile: {selected_profile}",
        f"- profile_source: {profile_source}",
        f"- row_count: {len(row_list)}",
        f"- final_gate_decision: {final_decision}",
        f"- go_count: {go_count}",
        f"- no_go_count: {no_go_count}",
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
        "## Profile-Aware Final Gate Rows",
        "",
        "| gate_id | selected_profile | upstream_stage | upstream_status | evidence | gate_status | final_gate_decision | go_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.gate_id,
                    row.selected_profile,
                    row.upstream_stage,
                    row.upstream_status,
                    row.evidence,
                    row.gate_status,
                    row.final_gate_decision,
                    row.go_allowed,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Gate Rule",
            "",
            "- GO requires Phase 14C config validator PASS.",
            "- GO requires Phase 14H profile-aware config plan to have no ADD and no REVIEW_UPDATE rows.",
            "- live-readonly accepts account_mode=live and port=7496.",
            "- paper accepts account_mode=paper and port=7497.",
            "- all profiles require read_only_required=true and every execution/request/trading switch=false.",
            "- GO only means ready for the next review phase. It does not authorize a live connection.",
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
