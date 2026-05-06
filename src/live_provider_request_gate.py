from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv
import yaml


REQUEST_TYPES = ["quote", "upstream_factor", "account", "order", "cancel", "rebalance"]
REQUEST_WHITELIST = {"quote", "upstream_factor"}
TRADING_REQUEST_TYPES = {"account", "order", "cancel", "rebalance"}


@dataclass
class LiveProviderRequestGateRow:
    provider_id: str
    provider_type: str
    request_type: str
    enabled: str
    live_request_allowed: str
    interface_implemented: str
    credential_configured: str
    request_whitelisted: str
    gate_status: str
    api_request_allowed: str
    action_allowed: str
    block_reason: str
    fallback_provider: str
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


def _bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def _flags(*values: str) -> str:
    flags = {
        "phase10b_live_provider_request_gate",
        "request_gate_safety_check_only",
        "no_api_request",
        "no_ibkr_connection",
        "no_reqMktData",
        "no_reqHistoricalData",
        "no_order",
        "no_auto_trade",
    }
    for value in values:
        if value and value != "none":
            flags.update(v.strip() for v in value.split(";") if v.strip())
    return ";".join(sorted(flags))


def load_live_provider_request_gate_config(path: str) -> dict[str, Any]:
    if not Path(path).exists():
        return {"providers": {}, "targets": []}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"providers": {}, "targets": []}


def _credential_configured(provider: dict[str, Any]) -> bool:
    return bool(provider.get("credential_configured", False) or provider.get("credential_ref"))


def _gate_decision(provider: dict[str, Any], request_type: str) -> tuple[str, str, str]:
    provider_type = str(provider.get("provider_type", "unknown"))
    enabled = bool(provider.get("enabled", False))
    live_allowed = bool(provider.get("live_request_allowed", False))
    implemented = bool(provider.get("interface_implemented", False))
    credential_ok = _credential_configured(provider)

    if request_type in TRADING_REQUEST_TYPES:
        return "blocked_trading_request", "trading_or_account_request_blocked", "trading_request_blocked"

    if request_type not in REQUEST_WHITELIST:
        return "blocked_request_not_whitelisted", "request_type_not_whitelisted", "request_not_whitelisted"

    if provider_type == "manual_csv_adapter":
        return "blocked_manual_provider_not_live", "manual_csv_is_not_live_provider", "manual_csv_not_live_provider"

    if not enabled:
        return "blocked_provider_disabled", "provider_disabled", "live_provider_disabled"

    if not live_allowed:
        return "blocked_live_request_not_allowed", "live_request_allowed_false", "live_request_not_allowed"

    if not implemented:
        return "blocked_interface_not_implemented", "interface_not_implemented", "interface_not_implemented"

    if not credential_ok:
        return "blocked_missing_credentials", "credential_not_configured", "missing_credentials"

    return "blocked_phase10b_dry_run_only", "phase10b_does_not_permit_real_api_request", "phase10b_dry_run_only"


def build_live_provider_request_gate_rows(
    config: dict[str, Any],
    tz_cfg: dict[str, str],
) -> list[LiveProviderRequestGateRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    providers = config.get("providers", {}) or {}
    rows: list[LiveProviderRequestGateRow] = []

    for provider_id in sorted(providers.keys()):
        provider = providers[provider_id] or {}
        for request_type in REQUEST_TYPES:
            gate_status, block_reason, extra_flags = _gate_decision(provider, request_type)
            rows.append(
                LiveProviderRequestGateRow(
                    provider_id=provider_id,
                    provider_type=str(provider.get("provider_type", "unknown")),
                    request_type=request_type,
                    enabled=_bool_text(provider.get("enabled", False)),
                    live_request_allowed=_bool_text(provider.get("live_request_allowed", False)),
                    interface_implemented=_bool_text(provider.get("interface_implemented", False)),
                    credential_configured=_bool_text(_credential_configured(provider)),
                    request_whitelisted=_bool_text(request_type in REQUEST_WHITELIST),
                    gate_status=gate_status,
                    api_request_allowed="false",
                    action_allowed="false",
                    block_reason=block_reason,
                    fallback_provider=str(provider.get("fallback_provider", "none")),
                    warning_flags=_flags(extra_flags),
                    notes=str(provider.get("notes", "none")),
                    timestamp_jst=ts_jst,
                    timestamp_et=ts_et,
                )
            )

    return rows


def write_live_provider_request_gate_csv(path: Path, rows: list[LiveProviderRequestGateRow]) -> None:
    fields = list(LiveProviderRequestGateRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_live_provider_request_gate_report(
    path: Path,
    rows: list[LiveProviderRequestGateRow],
    config_path: str,
) -> None:
    statuses = sorted({row.gate_status for row in rows})
    providers = sorted({row.provider_id for row in rows})
    api_allowed_count = sum(1 for row in rows if row.api_request_allowed == "true")
    action_allowed_count = sum(1 for row in rows if row.action_allowed == "true")

    lines = [
        "# Phase 10B Live Provider Request Gate Report",
        "",
        "- phase: Phase 10B",
        "- scope: live provider request gate safety layer",
        "- config_path: " + config_path,
        "- providers: " + (",".join(providers) if providers else "none"),
        "- gate_statuses: " + (",".join(statuses) if statuses else "none"),
        "- api_request_allowed_count: " + str(api_allowed_count),
        "- action_allowed_count: " + str(action_allowed_count),
        "",
        "## Request Gate Rows",
        "",
        "| provider_id | provider_type | request_type | gate_status | api_request_allowed | action_allowed | block_reason | fallback_provider |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.provider_id} | {row.provider_type} | {row.request_type} | {row.gate_status} | {row.api_request_allowed} | {row.action_allowed} | {row.block_reason} | {row.fallback_provider} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- request gate safety check only",
            "- api_request_allowed=false for every row",
            "- action_allowed=false for every row",
            "- no API request",
            "- no IBKR connection",
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
