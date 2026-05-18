from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv
import yaml


@dataclass
class IBKRReadOnlyQualificationPrecheckRow:
    check_id: str
    check_group: str
    requirement: str
    expected_value: str
    observed_value: str
    precheck_status: str
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
        "phase10k_ibkr_readonly_qualification_precheck",
        "precheck_only",
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


def load_ibkr_readonly_qualification_precheck_config(path: str) -> dict[str, Any]:
    if not Path(path).exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _runtime(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("runtime", {}) or {}


def _ibkr_config(config: dict[str, Any]) -> dict[str, Any]:
    runtime = _runtime(config)
    ibkr = runtime.get("ibkr", {}) or {}
    if ibkr:
        return ibkr

    return {
        "host": runtime.get("ibkr_host", "not_configured"),
        "port": runtime.get("ibkr_port", "not_configured"),
        "client_id": runtime.get("ibkr_client_id", "not_configured"),
        "account_mode": runtime.get("account_mode", "not_configured"),
        "read_only_required": runtime.get("read_only_required", False),
    }


def _status_pass_fail(observed: str, expected: str, pass_status: str = "precheck_pass") -> tuple[str, str]:
    if observed == expected:
        return pass_status, "none"
    return "precheck_blocked", "expected_" + expected + "_observed_" + observed


def _row(
    check_id: str,
    check_group: str,
    requirement: str,
    expected_value: str,
    observed_value: str,
    precheck_status: str,
    block_reason: str,
    notes: str,
    ts_jst: str,
    ts_et: str,
) -> IBKRReadOnlyQualificationPrecheckRow:
    return IBKRReadOnlyQualificationPrecheckRow(
        check_id=check_id,
        check_group=check_group,
        requirement=requirement,
        expected_value=expected_value,
        observed_value=observed_value,
        precheck_status=precheck_status,
        qualification_allowed="false",
        tws_connection_allowed="false",
        contract_qualification_allowed="false",
        market_data_request_allowed="false",
        historical_data_request_allowed="false",
        api_request_allowed="false",
        action_allowed="false",
        block_reason=block_reason,
        warning_flags=_flags(precheck_status, block_reason),
        notes=notes,
        timestamp_jst=ts_jst,
        timestamp_et=ts_et,
    )


def build_ibkr_readonly_qualification_precheck_rows(
    config: dict[str, Any],
    tz_cfg: dict[str, str],
) -> list[IBKRReadOnlyQualificationPrecheckRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    ibkr = _ibkr_config(config)

    host = str(ibkr.get("host", "not_configured"))
    port = str(ibkr.get("port", "not_configured"))
    client_id = str(ibkr.get("client_id", "not_configured"))
    account_mode = str(ibkr.get("account_mode", "not_configured"))
    read_only_required = "true" if bool(ibkr.get("read_only_required", False)) else "false"

    rows: list[IBKRReadOnlyQualificationPrecheckRow] = []

    rows.append(
        _row(
            "tws_runtime_state",
            "environment",
            "TWS must be checked manually before any future qualification",
            "manual_check_required",
            "not_checked",
            "precheck_blocked",
            "tws_runtime_state_not_checked",
            "This precheck does not connect to TWS.",
            ts_jst,
            ts_et,
        )
    )

    status, reason = _status_pass_fail(read_only_required, "true")
    rows.append(
        _row(
            "read_only_required",
            "safety",
            "read_only_required must be true",
            "true",
            read_only_required,
            status,
            reason,
            "Read-only mode must be enforced before qualification can be considered.",
            ts_jst,
            ts_et,
        )
    )

    account_status = "precheck_pass" if account_mode in {"live", "paper"} else "precheck_blocked"
    account_reason = "none" if account_status == "precheck_pass" else "account_mode_must_be_live_or_paper_explicit"
    rows.append(
        _row(
            "account_mode",
            "safety",
            "account_mode must be explicitly live or paper",
            "live_or_paper",
            account_mode,
            account_status,
            account_reason,
            "Account mode must be explicit; no implicit account mode is allowed.",
            ts_jst,
            ts_et,
        )
    )

    port_status = "precheck_pass" if port in {"7496", "7497"} else "precheck_blocked"
    port_reason = "none" if port_status == "precheck_pass" else "ibkr_port_must_be_7496_or_7497"
    rows.append(
        _row(
            "ibkr_port",
            "connection_config",
            "IBKR TWS/Gateway port must be reviewed",
            "7496_or_7497",
            port,
            port_status,
            port_reason,
            "7496 is commonly live TWS; 7497 is commonly paper TWS. Manual confirmation is still required.",
            ts_jst,
            ts_et,
        )
    )

    client_status = "precheck_pass" if client_id not in {"", "not_configured", "None"} else "precheck_blocked"
    client_reason = "none" if client_status == "precheck_pass" else "client_id_not_configured"
    rows.append(
        _row(
            "client_id",
            "connection_config",
            "IBKR client_id must be configured",
            "configured",
            client_id,
            client_status,
            client_reason,
            "Client ID must be explicit before any future TWS session.",
            ts_jst,
            ts_et,
        )
    )

    host_status = "precheck_pass" if host not in {"", "not_configured", "None"} else "precheck_blocked"
    host_reason = "none" if host_status == "precheck_pass" else "host_not_configured"
    rows.append(
        _row(
            "host",
            "connection_config",
            "IBKR host must be configured",
            "configured",
            host,
            host_status,
            host_reason,
            "Host should normally be 127.0.0.1 for local TWS/Gateway.",
            ts_jst,
            ts_et,
        )
    )

    fixed_blocks = [
        (
            "request_gate",
            "safety",
            "Live provider request gate must remain active",
            "required",
            "required",
            "precheck_pass",
            "none",
            "Request gate remains a required upstream safety layer.",
        ),
        (
            "explicit_execution_flag",
            "execution_control",
            "Explicit execution flag must remain false in Phase 10K",
            "false",
            "false",
            "precheck_pass",
            "none",
            "Phase 10K does not execute qualification even if future configuration changes.",
        ),
        (
            "qualification_allowed",
            "execution_control",
            "Qualification must remain blocked",
            "false",
            "false",
            "precheck_pass",
            "none",
            "Precheck only; no qualification execution.",
        ),
        (
            "market_data_allowed",
            "execution_control",
            "Market data requests must remain blocked",
            "false",
            "false",
            "precheck_pass",
            "none",
            "Precheck must not request market data.",
        ),
        (
            "order_cancel_allowed",
            "execution_control",
            "Order and cancel operations must remain blocked",
            "false",
            "false",
            "precheck_pass",
            "none",
            "No trading operations are permitted.",
        ),
    ]

    for item in fixed_blocks:
        rows.append(_row(*item, ts_jst, ts_et))

    return rows


def write_ibkr_readonly_qualification_precheck_csv(
    path: Path,
    rows: list[IBKRReadOnlyQualificationPrecheckRow],
) -> None:
    fields = list(IBKRReadOnlyQualificationPrecheckRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_readonly_qualification_precheck_report(
    path: Path,
    rows: list[IBKRReadOnlyQualificationPrecheckRow],
    config_path: str,
) -> None:
    statuses = sorted({row.precheck_status for row in rows})
    blocked_count = sum(1 for row in rows if row.precheck_status == "precheck_blocked")
    pass_count = sum(1 for row in rows if row.precheck_status == "precheck_pass")
    qualification_allowed_count = sum(1 for row in rows if row.qualification_allowed == "true")
    tws_allowed_count = sum(1 for row in rows if row.tws_connection_allowed == "true")

    lines = [
        "# Phase 10K IBKR Read-Only Qualification Precheck Report",
        "",
        "- phase: Phase 10K",
        "- scope: IBKR read-only qualification preconditions checklist",
        "- config_path: " + config_path,
        "- row_count: " + str(len(rows)),
        "- precheck_pass_count: " + str(pass_count),
        "- precheck_blocked_count: " + str(blocked_count),
        "- qualification_allowed_count: " + str(qualification_allowed_count),
        "- tws_connection_allowed_count: " + str(tws_allowed_count),
        "- precheck_statuses: " + (",".join(statuses) if statuses else "none"),
        "- api_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Precheck Rows",
        "",
        "| check_id | check_group | expected_value | observed_value | precheck_status | qualification_allowed | action_allowed | block_reason |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.check_id} | {row.check_group} | {row.expected_value} | {row.observed_value} | {row.precheck_status} | {row.qualification_allowed} | {row.action_allowed} | {row.block_reason} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- IBKR read-only qualification precheck only",
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
