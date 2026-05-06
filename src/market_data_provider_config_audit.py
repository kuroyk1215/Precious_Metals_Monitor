from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Any
import csv


@dataclass
class MarketDataProviderConfigAuditRow:
    provider_id: str
    provider_type: str
    enabled: str
    live_request_allowed: str
    fallback_provider: str
    source_quality_floor: str
    requires_explicit_enable_switch: str
    config_status: str
    action_allowed: str
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
        "phase9b_provider_config_audit",
        "config_file_driven",
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


def load_market_data_provider_config(path: str) -> dict[str, Any]:
    if not Path(path).exists():
        return {"providers": {}, "targets": []}
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def _config_status(provider_id: str, provider: dict[str, Any]) -> tuple[str, str]:
    enabled = bool(provider.get("enabled", False))
    live_allowed = bool(provider.get("live_request_allowed", False))
    requires_switch = bool(provider.get("requires_explicit_enable_switch", False))

    if live_allowed:
        return "blocked_live_request_enabled", "live_request_enabled_blocked"
    if provider_id == "manual_csv" and enabled and not live_allowed:
        return "manual_config_ready", "manual_csv_primary"
    if not enabled and requires_switch and not live_allowed:
        return "disabled_safe_until_explicit_enable", "live_provider_disabled;requires_explicit_enable_switch"
    if not enabled and not live_allowed:
        return "disabled_safe", "provider_disabled"
    return "manual_review_required", "provider_config_review_required"


def build_market_data_provider_config_audit_rows(
    config: dict[str, Any],
    tz_cfg: dict[str, str],
) -> list[MarketDataProviderConfigAuditRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[MarketDataProviderConfigAuditRow] = []

    providers = config.get("providers", {}) or {}
    for provider_id in sorted(providers.keys()):
        provider = providers[provider_id] or {}
        status, extra_flags = _config_status(provider_id, provider)
        rows.append(
            MarketDataProviderConfigAuditRow(
                provider_id=provider_id,
                provider_type=str(provider.get("provider_type", "unknown")),
                enabled=_bool_text(provider.get("enabled", False)),
                live_request_allowed=_bool_text(provider.get("live_request_allowed", False)),
                fallback_provider=str(provider.get("fallback_provider", "none")),
                source_quality_floor=str(provider.get("source_quality_floor", "unavailable")),
                requires_explicit_enable_switch=_bool_text(provider.get("requires_explicit_enable_switch", False)),
                config_status=status,
                action_allowed="false",
                warning_flags=_flags(extra_flags),
                notes=str(provider.get("notes", "none")),
                timestamp_jst=ts_jst,
                timestamp_et=ts_et,
            )
        )

    return rows


def write_market_data_provider_config_audit_csv(
    path: Path,
    rows: list[MarketDataProviderConfigAuditRow],
) -> None:
    fields = list(MarketDataProviderConfigAuditRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_market_data_provider_config_audit_report(
    path: Path,
    rows: list[MarketDataProviderConfigAuditRow],
    config_path: str,
) -> None:
    statuses = sorted({r.config_status for r in rows})
    providers = sorted({r.provider_id for r in rows})
    live_allowed_count = sum(1 for r in rows if r.live_request_allowed == "true")
    status_text = ",".join(statuses) if statuses else "none"
    provider_text = ",".join(providers) if providers else "none"

    lines = [
        "# Phase 9B Market Data Provider Config Audit Report",
        "",
        "- phase: Phase 9B",
        "- scope: market data provider config-file audit",
        "- config_path: " + config_path,
        "- providers: " + provider_text,
        "- config_statuses: " + status_text,
        "- live_request_allowed_count: " + str(live_allowed_count),
        "- action_allowed: false",
        "",
        "## Provider Config Audit Rows",
        "",
        "| provider_id | provider_type | enabled | live_request_allowed | fallback_provider | config_status | action_allowed |",
        "|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.provider_id} | {row.provider_type} | {row.enabled} | {row.live_request_allowed} | {row.fallback_provider} | {row.config_status} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- config audit only",
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
