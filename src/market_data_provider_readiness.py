from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo
import csv


@dataclass
class MarketDataProviderReadinessRow:
    provider_id: str
    provider_type: str
    target_id: str
    target_type: str
    market: str
    data_role: str
    provider_enabled: str
    readiness_status: str
    fallback_provider: str
    source_quality_floor: str
    live_request_allowed: str
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
        "phase9c_config_driven_readiness",
        "phase9a_provider_readiness",
        "planning_only",
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


def load_market_data_provider_readiness_config(path: str) -> dict[str, Any]:
    if not Path(path).exists():
        return {"providers": {}, "targets": []}
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"providers": {}, "targets": []}


def _default_config() -> dict[str, Any]:
    return load_market_data_provider_readiness_config("data/market_data_provider_config.yaml")


def _provider_readiness_status(provider_id: str, provider: dict[str, Any]) -> tuple[str, str]:
    enabled = bool(provider.get("enabled", False))
    live_allowed = bool(provider.get("live_request_allowed", False))
    requires_switch = bool(provider.get("requires_explicit_enable_switch", False))

    if live_allowed:
        return "blocked_live_request_enabled", "live_request_enabled_blocked"
    if provider_id == "manual_csv" and enabled and not live_allowed:
        return "manual_ready", "manual_csv_primary"
    if not enabled and requires_switch and not live_allowed:
        return "disabled_until_explicit_config", "live_provider_disabled;requires_explicit_enable_switch"
    if not enabled and not live_allowed:
        return "disabled_safe", "provider_disabled"
    return "manual_review_required", "provider_config_review_required"


def _target_rows_from_config(config: dict[str, Any]) -> list[dict[str, str]]:
    targets = config.get("targets", []) or []
    return [
        {
            "target_id": str(t.get("target_id", "")),
            "target_type": str(t.get("target_type", "unknown")),
            "market": str(t.get("market", "UNKNOWN")),
            "data_role": str(t.get("data_role", "unknown")),
        }
        for t in targets
        if t.get("target_id")
    ]


def build_market_data_provider_readiness_rows(
    tz_cfg: dict[str, str],
    provider_config: Optional[dict[str, Any]] = None,
) -> list[MarketDataProviderReadinessRow]:
    config = provider_config if provider_config is not None else _default_config()
    providers = config.get("providers", {}) or {}
    targets = _target_rows_from_config(config)

    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[MarketDataProviderReadinessRow] = []

    for target in targets:
        for provider_id in sorted(providers.keys()):
            provider = providers[provider_id] or {}
            status, extra_flags = _provider_readiness_status(provider_id, provider)
            rows.append(
                MarketDataProviderReadinessRow(
                    provider_id=provider_id,
                    provider_type=str(provider.get("provider_type", "unknown")),
                    target_id=target["target_id"],
                    target_type=target["target_type"],
                    market=target["market"],
                    data_role=target["data_role"],
                    provider_enabled=_bool_text(provider.get("enabled", False)),
                    readiness_status=status,
                    fallback_provider=str(provider.get("fallback_provider", "none")),
                    source_quality_floor=str(provider.get("source_quality_floor", "unavailable")),
                    live_request_allowed=_bool_text(provider.get("live_request_allowed", False)),
                    action_allowed="false",
                    warning_flags=_flags(extra_flags),
                    notes=str(provider.get("notes", "none")),
                    timestamp_jst=ts_jst,
                    timestamp_et=ts_et,
                )
            )

    return rows


def write_market_data_provider_readiness_csv(path: Path, rows: list[MarketDataProviderReadinessRow]) -> None:
    fields = list(MarketDataProviderReadinessRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_market_data_provider_readiness_report(path: Path, rows: list[MarketDataProviderReadinessRow]) -> None:
    statuses = sorted({r.readiness_status for r in rows})
    providers = sorted({r.provider_id for r in rows})
    live_enabled_count = sum(1 for r in rows if r.provider_enabled == "true" and r.live_request_allowed == "true")
    status_text = ",".join(statuses) if statuses else "none"
    provider_text = ",".join(providers) if providers else "none"

    lines = [
        "# Phase 9C Config-Driven Market Data Provider Readiness Report",
        "",
        "- phase: Phase 9C",
        "- scope: config-driven market data provider readiness planning only",
        "- live_provider_enabled_count: " + str(live_enabled_count),
        "- providers: " + provider_text,
        "- readiness_statuses: " + status_text,
        "- action_allowed: false",
        "- live_request_allowed: false",
        "",
        "## Provider Readiness Rows",
        "",
        "| provider_id | provider_type | target_id | market | data_role | provider_enabled | readiness_status | fallback_provider | live_request_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.provider_id} | {row.provider_type} | {row.target_id} | {row.market} | {row.data_role} | {row.provider_enabled} | {row.readiness_status} | {row.fallback_provider} | {row.live_request_allowed} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- provider readiness planning only",
            "- config-file driven",
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
