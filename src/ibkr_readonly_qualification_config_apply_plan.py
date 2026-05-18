from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv


@dataclass
class IBKRReadOnlyQualificationConfigApplyPlanRow:
    config_key: str
    config_group: str
    observed_value: str
    required_safe_value: str
    config_audit_status: str
    apply_plan_status: str
    operator_action_required: str
    proposed_value: str
    apply_allowed: str
    qualification_allowed: str
    tws_connection_allowed: str
    contract_qualification_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    api_request_allowed: str
    action_allowed: str
    block_reason: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


def _now_pair(tz_cfg: dict[str, str]) -> tuple[str, str]:
    now_utc = datetime.now(timezone.utc)
    return (
        now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat(),
        now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat(),
    )


def _flags(*values: str) -> str:
    flags: set[str] = {
        "phase11c_ibkr_readonly_qualification_config_apply_plan",
        "apply_plan_only",
        "manual_apply_required",
        "no_tws_connection",
        "no_contract_qualification",
        "no_api_request",
        "no_ibkr_connection",
        "no_reqMktData",
        "no_reqHistoricalData",
        "no_order",
        "no_auto_trade",
    }
    for value in values:
        if value and value != "none":
            flags.update(flag.strip() for flag in value.split(";") if flag.strip())
    return ";".join(sorted(flags))


def _row_dict(item: Any) -> dict[str, str]:
    raw = item if isinstance(item, dict) else item.__dict__
    return {str(k): str(v) for k, v in raw.items()}


def _plan_decision(row: dict[str, str]) -> tuple[str, str, str, str]:
    key = row.get("config_key", "unknown")
    audit_status = row.get("config_audit_status", "unknown")

    if audit_status == "config_violation_blocked":
        return (
            "blocked_config_violation",
            "true",
            row.get("required_safe_value", "safe_value_required"),
            "unsafe_true_permission_must_be_reverted_before_any_future_phase",
        )

    if audit_status == "manual_config_required":
        return (
            "blocked_manual_config_required",
            "true",
            row.get("required_safe_value", "explicit_value_required"),
            "manual_explicit_config_required",
        )

    if audit_status == "candidate_value_configured":
        return (
            "manual_review_candidate_value",
            "true",
            row.get("observed_value", "candidate_value"),
            "candidate_value_requires_operator_review",
        )

    if audit_status == "required_true":
        return (
            "keep_required_true",
            "false",
            row.get("observed_value", "true"),
            "required_true_already_set",
        )

    if audit_status == "blocked_or_disabled":
        return (
            "keep_disabled",
            "false",
            row.get("observed_value", "false"),
            "safe_disabled_do_not_enable_in_phase11c",
        )

    return (
        "blocked_unknown_audit_status",
        "true",
        row.get("required_safe_value", "manual_review_required"),
        "unknown_audit_status_requires_review_for_" + key,
    )


def build_ibkr_readonly_qualification_config_apply_plan_rows(
    audit_rows: list[Any],
    tz_cfg: dict[str, str],
) -> list[IBKRReadOnlyQualificationConfigApplyPlanRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[IBKRReadOnlyQualificationConfigApplyPlanRow] = []

    for item in audit_rows:
        row = _row_dict(item)
        status, action_required, proposed_value, reason = _plan_decision(row)

        rows.append(
            IBKRReadOnlyQualificationConfigApplyPlanRow(
                config_key=row.get("config_key", "unknown"),
                config_group=row.get("config_group", "unknown"),
                observed_value=row.get("observed_value", "unknown"),
                required_safe_value=row.get("required_safe_value", "unknown"),
                config_audit_status=row.get("config_audit_status", "unknown"),
                apply_plan_status=status,
                operator_action_required=action_required,
                proposed_value=proposed_value,
                apply_allowed="false",
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                block_reason=reason,
                warning_flags=_flags(status, reason, row.get("warning_flags", "none")),
                notes="Configuration apply plan only; no file mutation, no TWS connection, and no IBKR API request is performed.",
                timestamp_jst=row.get("timestamp_jst", ts_jst) or ts_jst,
                timestamp_et=row.get("timestamp_et", ts_et) or ts_et,
            )
        )

    return rows


def load_ibkr_readonly_qualification_config_audit_rows_by_key(path: str) -> dict[str, dict[str, str]]:
    if not Path(path).exists():
        return {}

    with open(path, "r", encoding="utf-8", newline="") as f:
        return {
            str(row.get("config_key", "")): {k: str(v) if v is not None else "" for k, v in row.items()}
            for row in csv.DictReader(f)
            if row.get("config_key")
        }


def write_ibkr_readonly_qualification_config_apply_plan_csv(
    path: Path,
    rows: list[IBKRReadOnlyQualificationConfigApplyPlanRow],
) -> None:
    fields = list(IBKRReadOnlyQualificationConfigApplyPlanRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_readonly_qualification_config_apply_plan_report(
    path: Path,
    rows: list[IBKRReadOnlyQualificationConfigApplyPlanRow],
    input_source: str,
) -> None:
    statuses = sorted({row.apply_plan_status for row in rows})
    action_required_count = sum(1 for row in rows if row.operator_action_required == "true")
    keep_disabled_count = sum(1 for row in rows if row.apply_plan_status == "keep_disabled")
    manual_required_count = sum(1 for row in rows if row.apply_plan_status == "blocked_manual_config_required")
    review_count = sum(1 for row in rows if row.apply_plan_status == "manual_review_candidate_value")
    violation_count = sum(1 for row in rows if row.apply_plan_status == "blocked_config_violation")
    apply_allowed_count = sum(1 for row in rows if row.apply_allowed == "true")
    qualification_allowed_count = sum(1 for row in rows if row.qualification_allowed == "true")
    tws_allowed_count = sum(1 for row in rows if row.tws_connection_allowed == "true")
    api_allowed_count = sum(1 for row in rows if row.api_request_allowed == "true")
    action_allowed_count = sum(1 for row in rows if row.action_allowed == "true")

    final_status = "blocked_manual_config_required"
    if violation_count:
        final_status = "blocked_config_violation"

    lines = [
        "# Phase 11C IBKR Read-Only Qualification Config Apply Plan Report",
        "",
        "- phase: Phase 11C",
        "- scope: IBKR read-only qualification config apply plan only",
        "- input_source: " + input_source,
        "- row_count: " + str(len(rows)),
        "- final_apply_plan_status: " + final_status,
        "- operator_action_required_count: " + str(action_required_count),
        "- keep_disabled_count: " + str(keep_disabled_count),
        "- manual_required_count: " + str(manual_required_count),
        "- review_count: " + str(review_count),
        "- violation_count: " + str(violation_count),
        "- apply_allowed_count: " + str(apply_allowed_count),
        "- qualification_allowed_count: " + str(qualification_allowed_count),
        "- tws_connection_allowed_count: " + str(tws_allowed_count),
        "- api_request_allowed_count: " + str(api_allowed_count),
        "- action_allowed_count: " + str(action_allowed_count),
        "- apply_plan_statuses: " + (",".join(statuses) if statuses else "none"),
        "",
        "## Config Apply Plan Rows",
        "",
        "| config_key | config_group | observed_value | proposed_value | apply_plan_status | operator_action_required | apply_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.config_key} | {row.config_group} | {row.observed_value} | {row.proposed_value} | {row.apply_plan_status} | {row.operator_action_required} | {row.apply_allowed} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- IBKR read-only qualification config apply plan only",
            "- no configuration file is modified",
            "- apply_allowed=false for every row",
            "- no TWS connection",
            "- no IBKR connection",
            "- no real contract qualification",
            "- qualification_allowed=false for every row",
            "- contract_qualification_allowed=false for every row",
            "- market_data_request_allowed=false for every row",
            "- historical_data_request_allowed=false for every row",
            "- api_request_allowed=false for every row",
            "- action_allowed=false for every row",
            "- no reqMktData",
            "- no reqHistoricalData",
            "- no order",
            "- no cancel",
            "- no rebalance",
            "- no auto trade",
            "- no automatic execution",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
