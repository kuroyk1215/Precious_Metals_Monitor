from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv
import yaml


@dataclass
class IBKRReadOnlyQualificationConfigTemplateRow:
    config_key: str
    config_group: str
    template_value: str
    required_value: str
    template_status: str
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
        "phase11a_ibkr_readonly_qualification_config_template",
        "config_template_only",
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


def default_ibkr_readonly_qualification_template() -> dict[str, Any]:
    return {
        "runtime": {
            "ibkr_readonly_qualification": {
                "enabled": False,
                "explicit_execution_flag": False,
                "operator_manual_approval": False,
                "read_only_required": True,
                "account_mode": "paper_or_live_explicit_required",
                "host": "127.0.0.1",
                "port": "7496_or_7497_explicit_required",
                "client_id": "explicit_required",
                "allow_tws_connection": False,
                "allow_contract_qualification": False,
                "allow_market_data_request": False,
                "allow_historical_data_request": False,
                "allow_order": False,
                "allow_cancel": False,
                "allow_rebalance": False,
                "allow_auto_trade": False,
            }
        }
    }


def write_ibkr_readonly_qualification_template_yaml(path: Path) -> None:
    template = default_ibkr_readonly_qualification_template()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(template, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _template_rows() -> list[tuple[str, str, str, str, str, str]]:
    return [
        ("enabled", "execution_control", "false", "false", "template_safe_disabled", "template_keeps_qualification_disabled"),
        ("explicit_execution_flag", "execution_control", "false", "false", "template_safe_disabled", "explicit_execution_flag_false"),
        ("operator_manual_approval", "execution_control", "false", "false", "template_safe_disabled", "manual_approval_not_granted"),
        ("read_only_required", "safety", "true", "true", "template_required_true", "read_only_required_true"),
        ("account_mode", "connection_config", "paper_or_live_explicit_required", "live_or_paper_explicit", "template_requires_manual_config", "account_mode_requires_explicit_value"),
        ("host", "connection_config", "127.0.0.1", "configured", "template_candidate_value", "host_template_localhost"),
        ("port", "connection_config", "7496_or_7497_explicit_required", "7496_or_7497", "template_requires_manual_config", "port_requires_explicit_value"),
        ("client_id", "connection_config", "explicit_required", "configured", "template_requires_manual_config", "client_id_requires_explicit_value"),
        ("allow_tws_connection", "permission", "false", "false", "template_safe_disabled", "tws_connection_blocked"),
        ("allow_contract_qualification", "permission", "false", "false", "template_safe_disabled", "contract_qualification_blocked"),
        ("allow_market_data_request", "permission", "false", "false", "template_safe_disabled", "market_data_request_blocked"),
        ("allow_historical_data_request", "permission", "false", "false", "template_safe_disabled", "historical_data_request_blocked"),
        ("allow_order", "permission", "false", "false", "template_safe_disabled", "order_blocked"),
        ("allow_cancel", "permission", "false", "false", "template_safe_disabled", "cancel_blocked"),
        ("allow_rebalance", "permission", "false", "false", "template_safe_disabled", "rebalance_blocked"),
        ("allow_auto_trade", "permission", "false", "false", "template_safe_disabled", "auto_trade_blocked"),
    ]


def build_ibkr_readonly_qualification_config_template_rows(
    tz_cfg: dict[str, str],
) -> list[IBKRReadOnlyQualificationConfigTemplateRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[IBKRReadOnlyQualificationConfigTemplateRow] = []

    for key, group, template_value, required_value, status, reason in _template_rows():
        rows.append(
            IBKRReadOnlyQualificationConfigTemplateRow(
                config_key=key,
                config_group=group,
                template_value=template_value,
                required_value=required_value,
                template_status=status,
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                block_reason=reason,
                warning_flags=_flags(status, reason),
                notes="Explicit configuration template only; this command never connects to TWS or IBKR.",
                timestamp_jst=ts_jst,
                timestamp_et=ts_et,
            )
        )

    return rows


def write_ibkr_readonly_qualification_config_template_csv(
    path: Path,
    rows: list[IBKRReadOnlyQualificationConfigTemplateRow],
) -> None:
    fields = list(IBKRReadOnlyQualificationConfigTemplateRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_readonly_qualification_config_template_report(
    path: Path,
    rows: list[IBKRReadOnlyQualificationConfigTemplateRow],
    template_path: str,
) -> None:
    statuses = sorted({row.template_status for row in rows})
    safe_disabled_count = sum(1 for row in rows if row.template_status == "template_safe_disabled")
    manual_config_count = sum(1 for row in rows if row.template_status == "template_requires_manual_config")
    qualification_allowed_count = sum(1 for row in rows if row.qualification_allowed == "true")
    tws_allowed_count = sum(1 for row in rows if row.tws_connection_allowed == "true")
    api_allowed_count = sum(1 for row in rows if row.api_request_allowed == "true")
    action_allowed_count = sum(1 for row in rows if row.action_allowed == "true")

    lines = [
        "# Phase 11A IBKR Read-Only Qualification Config Template Report",
        "",
        "- phase: Phase 11A",
        "- scope: IBKR read-only qualification explicit config template",
        "- template_path: " + template_path,
        "- row_count: " + str(len(rows)),
        "- safe_disabled_count: " + str(safe_disabled_count),
        "- manual_config_count: " + str(manual_config_count),
        "- qualification_allowed_count: " + str(qualification_allowed_count),
        "- tws_connection_allowed_count: " + str(tws_allowed_count),
        "- api_request_allowed_count: " + str(api_allowed_count),
        "- action_allowed_count: " + str(action_allowed_count),
        "- template_statuses: " + (",".join(statuses) if statuses else "none"),
        "",
        "## Config Template Rows",
        "",
        "| config_key | config_group | template_value | required_value | template_status | qualification_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.config_key} | {row.config_group} | {row.template_value} | {row.required_value} | {row.template_status} | {row.qualification_allowed} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- IBKR read-only qualification config template only",
            "- generated template remains disabled by default",
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
