from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv
import yaml

from src.ibkr_readonly_qualification_config_template import default_ibkr_readonly_qualification_template


@dataclass
class IBKRReadOnlyQualificationConfigAuditRow:
    config_key: str
    config_group: str
    observed_value: str
    required_safe_value: str
    config_audit_status: str
    violation_detected: str
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
        "phase11b_ibkr_readonly_qualification_config_audit",
        "config_audit_only",
        "explicit_config_required",
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


def load_ibkr_readonly_qualification_config_audit_config(path: str) -> dict[str, Any]:
    if not Path(path).exists():
        return default_ibkr_readonly_qualification_template()

    with open(path, "r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f) or {}

    if "runtime" not in loaded or "ibkr_readonly_qualification" not in (loaded.get("runtime") or {}):
        return default_ibkr_readonly_qualification_template()

    return loaded


def _qualification_config(config: dict[str, Any]) -> dict[str, Any]:
    return (config.get("runtime", {}) or {}).get("ibkr_readonly_qualification", {}) or {}


def _bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def _value_text(value: Any) -> str:
    if isinstance(value, bool):
        return _bool_text(value)
    if value is None:
        return "not_configured"
    return str(value)


def _audit_bool_false(observed: Any, reason: str) -> tuple[str, str, str]:
    if bool(observed):
        return "config_violation_blocked", "true", reason
    return "blocked_or_disabled", "false", "safe_disabled"


def _audit_bool_true(observed: Any, reason: str) -> tuple[str, str, str]:
    if bool(observed):
        return "required_true", "false", "none"
    return "config_violation_blocked", "true", reason


def _audit_account_mode(observed: Any) -> tuple[str, str, str]:
    value = _value_text(observed)
    if value in {"live", "paper"}:
        return "explicit_value_configured", "false", "none"
    return "manual_config_required", "false", "account_mode_requires_live_or_paper_explicit"


def _audit_port(observed: Any) -> tuple[str, str, str]:
    value = _value_text(observed)
    if value in {"7496", "7497"}:
        return "explicit_value_configured", "false", "none"
    return "manual_config_required", "false", "port_requires_7496_or_7497_explicit"


def _audit_client_id(observed: Any) -> tuple[str, str, str]:
    value = _value_text(observed)
    if value not in {"", "not_configured", "None", "explicit_required"}:
        return "explicit_value_configured", "false", "none"
    return "manual_config_required", "false", "client_id_requires_explicit_value"


def _audit_host(observed: Any) -> tuple[str, str, str]:
    value = _value_text(observed)
    if value not in {"", "not_configured", "None"}:
        return "candidate_value_configured", "false", "none"
    return "manual_config_required", "false", "host_requires_explicit_value"


def _definition_rows() -> list[tuple[str, str, str, str]]:
    return [
        ("enabled", "execution_control", "false", "template_or_runtime_must_keep_disabled_until_future_explicit_phase"),
        ("explicit_execution_flag", "execution_control", "false", "explicit_execution_flag_must_remain_false"),
        ("operator_manual_approval", "execution_control", "false", "manual_approval_must_remain_false"),
        ("read_only_required", "safety", "true", "read_only_required_must_be_true"),
        ("account_mode", "connection_config", "live_or_paper_explicit", "account_mode_requires_live_or_paper_explicit"),
        ("host", "connection_config", "configured", "host_requires_explicit_value"),
        ("port", "connection_config", "7496_or_7497", "port_requires_7496_or_7497_explicit"),
        ("client_id", "connection_config", "configured", "client_id_requires_explicit_value"),
        ("allow_tws_connection", "permission", "false", "tws_connection_must_remain_blocked"),
        ("allow_contract_qualification", "permission", "false", "contract_qualification_must_remain_blocked"),
        ("allow_market_data_request", "permission", "false", "market_data_request_must_remain_blocked"),
        ("allow_historical_data_request", "permission", "false", "historical_data_request_must_remain_blocked"),
        ("allow_order", "permission", "false", "order_must_remain_blocked"),
        ("allow_cancel", "permission", "false", "cancel_must_remain_blocked"),
        ("allow_rebalance", "permission", "false", "rebalance_must_remain_blocked"),
        ("allow_auto_trade", "permission", "false", "auto_trade_must_remain_blocked"),
    ]


def _audit_value(key: str, observed: Any, reason: str) -> tuple[str, str, str]:
    if key in {
        "enabled",
        "explicit_execution_flag",
        "operator_manual_approval",
        "allow_tws_connection",
        "allow_contract_qualification",
        "allow_market_data_request",
        "allow_historical_data_request",
        "allow_order",
        "allow_cancel",
        "allow_rebalance",
        "allow_auto_trade",
    }:
        return _audit_bool_false(observed, reason)

    if key == "read_only_required":
        return _audit_bool_true(observed, reason)

    if key == "account_mode":
        return _audit_account_mode(observed)

    if key == "host":
        return _audit_host(observed)

    if key == "port":
        return _audit_port(observed)

    if key == "client_id":
        return _audit_client_id(observed)

    return "manual_config_required", "false", "unknown_config_key"


def build_ibkr_readonly_qualification_config_audit_rows(
    config: dict[str, Any],
    tz_cfg: dict[str, str],
) -> list[IBKRReadOnlyQualificationConfigAuditRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    qcfg = _qualification_config(config)
    rows: list[IBKRReadOnlyQualificationConfigAuditRow] = []

    for key, group, required_safe_value, default_reason in _definition_rows():
        observed_raw = qcfg.get(key)
        status, violation, block_reason = _audit_value(key, observed_raw, default_reason)

        rows.append(
            IBKRReadOnlyQualificationConfigAuditRow(
                config_key=key,
                config_group=group,
                observed_value=_value_text(observed_raw),
                required_safe_value=required_safe_value,
                config_audit_status=status,
                violation_detected=violation,
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                block_reason=block_reason,
                warning_flags=_flags(status, block_reason),
                notes="Configuration audit only; this command never connects to TWS or IBKR.",
                timestamp_jst=ts_jst,
                timestamp_et=ts_et,
            )
        )

    return rows


def write_ibkr_readonly_qualification_config_audit_csv(
    path: Path,
    rows: list[IBKRReadOnlyQualificationConfigAuditRow],
) -> None:
    fields = list(IBKRReadOnlyQualificationConfigAuditRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_readonly_qualification_config_audit_report(
    path: Path,
    rows: list[IBKRReadOnlyQualificationConfigAuditRow],
    config_path: str,
) -> None:
    statuses = sorted({row.config_audit_status for row in rows})
    violation_count = sum(1 for row in rows if row.violation_detected == "true")
    manual_required_count = sum(1 for row in rows if row.config_audit_status == "manual_config_required")
    blocked_or_disabled_count = sum(1 for row in rows if row.config_audit_status == "blocked_or_disabled")
    qualification_allowed_count = sum(1 for row in rows if row.qualification_allowed == "true")
    tws_allowed_count = sum(1 for row in rows if row.tws_connection_allowed == "true")
    api_allowed_count = sum(1 for row in rows if row.api_request_allowed == "true")
    action_allowed_count = sum(1 for row in rows if row.action_allowed == "true")

    final_status = "config_violation_blocked" if violation_count else "blocked_or_disabled"

    lines = [
        "# Phase 11B IBKR Read-Only Qualification Config Audit Report",
        "",
        "- phase: Phase 11B",
        "- scope: IBKR read-only qualification explicit config audit",
        "- config_path: " + config_path,
        "- row_count: " + str(len(rows)),
        "- final_config_audit_status: " + final_status,
        "- violation_count: " + str(violation_count),
        "- manual_required_count: " + str(manual_required_count),
        "- blocked_or_disabled_count: " + str(blocked_or_disabled_count),
        "- qualification_allowed_count: " + str(qualification_allowed_count),
        "- tws_connection_allowed_count: " + str(tws_allowed_count),
        "- api_request_allowed_count: " + str(api_allowed_count),
        "- action_allowed_count: " + str(action_allowed_count),
        "- config_audit_statuses: " + (",".join(statuses) if statuses else "none"),
        "",
        "## Config Audit Rows",
        "",
        "| config_key | config_group | observed_value | required_safe_value | config_audit_status | violation_detected | qualification_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.config_key} | {row.config_group} | {row.observed_value} | {row.required_safe_value} | {row.config_audit_status} | {row.violation_detected} | {row.qualification_allowed} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- IBKR read-only qualification config audit only",
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
