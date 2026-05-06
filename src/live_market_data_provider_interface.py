from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo
import csv
import yaml


@dataclass
class LiveProviderInterfaceCheckRow:
    provider_id: str
    provider_type: str
    enabled: str
    live_request_allowed: str
    interface_implemented: str
    interface_status: str
    request_status: str
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
    flags: set[str] = {
        "phase10a_live_provider_interface",
        "interface_safety_check_only",
        "no_api_request",
        "no_ibkr_connection",
        "no_reqMktData",
        "no_reqHistoricalData",
        "no_order",
        "no_auto_trade",
    }
    for value in values:
        if not value or value == "none":
            continue
        flags.update(flag.strip() for flag in value.split(";") if flag.strip())
    return ";".join(sorted(flags))


def load_live_provider_interface_config(path: str) -> dict[str, Any]:
    if not Path(path).exists():
        return {"providers": {}, "targets": []}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"providers": {}, "targets": []}


def _interface_decision(provider_id: str, provider: dict[str, Any]) -> tuple[str, str, str, str]:
    provider_type = str(provider.get("provider_type", "unknown"))
    enabled = bool(provider.get("enabled", False))
    live_allowed = bool(provider.get("live_request_allowed", False))
    implemented = bool(provider.get("interface_implemented", False))

    if provider_type == "manual_csv_adapter":
        return (
            "manual_provider_not_live_interface",
            "blocked_manual_provider",
            "manual_csv_is_not_live_provider",
            "manual_csv_reference_only",
        )

    if live_allowed:
        return (
            "blocked_live_request_enabled",
            "blocked",
            "live_request_allowed_true_is_not_allowed_in_phase10a",
            "live_request_enabled_blocked",
        )

    if not enabled:
        return (
            "blocked_provider_disabled",
            "blocked",
            "provider_disabled",
            "live_provider_disabled",
        )

    if not implemented:
        return (
            "blocked_interface_not_implemented",
            "blocked",
            "interface_not_implemented",
            "interface_not_implemented",
        )

    return (
        "blocked_phase10a_no_live_requests",
        "blocked",
        "phase10a_does_not_permit_live_api_requests",
        "phase10a_live_request_block",
    )


def build_live_provider_interface_check_rows(
    config: dict[str, Any],
    tz_cfg: dict[str, str],
) -> list[LiveProviderInterfaceCheckRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[LiveProviderInterfaceCheckRow] = []
    providers = config.get("providers", {}) or {}

    for provider_id in sorted(providers.keys()):
        provider = providers[provider_id] or {}
        interface_status, request_status, block_reason, extra_flags = _interface_decision(provider_id, provider)

        rows.append(
            LiveProviderInterfaceCheckRow(
                provider_id=provider_id,
                provider_type=str(provider.get("provider_type", "unknown")),
                enabled=_bool_text(provider.get("enabled", False)),
                live_request_allowed=_bool_text(provider.get("live_request_allowed", False)),
                interface_implemented=_bool_text(provider.get("interface_implemented", False)),
                interface_status=interface_status,
                request_status=request_status,
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


def write_live_provider_interface_check_csv(
    path: Path,
    rows: list[LiveProviderInterfaceCheckRow],
) -> None:
    fields = list(LiveProviderInterfaceCheckRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_live_provider_interface_check_report(
    path: Path,
    rows: list[LiveProviderInterfaceCheckRow],
    config_path: str,
) -> None:
    statuses = sorted({row.interface_status for row in rows})
    providers = sorted({row.provider_id for row in rows})
    api_allowed_count = sum(1 for row in rows if row.api_request_allowed == "true")
    status_text = ",".join(statuses) if statuses else "none"
    provider_text = ",".join(providers) if providers else "none"

    lines = [
        "# Phase 10A Live Provider Interface Safety Check Report",
        "",
        "- phase: Phase 10A",
        "- scope: live provider interface safety skeleton",
        "- config_path: " + config_path,
        "- providers: " + provider_text,
        "- interface_statuses: " + status_text,
        "- api_request_allowed_count: " + str(api_allowed_count),
        "- action_allowed: false",
        "",
        "## Interface Check Rows",
        "",
        "| provider_id | provider_type | enabled | live_request_allowed | interface_implemented | interface_status | request_status | api_request_allowed | block_reason | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.provider_id} | {row.provider_type} | {row.enabled} | {row.live_request_allowed} | {row.interface_implemented} | {row.interface_status} | {row.request_status} | {row.api_request_allowed} | {row.block_reason} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- interface safety check only",
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
