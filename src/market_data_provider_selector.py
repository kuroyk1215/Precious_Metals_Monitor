from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv
import yaml


@dataclass
class MarketDataProviderSelectorRow:
    target_id: str
    target_type: str
    market: str
    data_role: str
    selected_provider: str
    selected_provider_type: str
    selection_status: str
    fallback_provider: str
    blocked_provider: str
    blocked_reason: str
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


def _bool(value: Any) -> bool:
    return bool(value)


def _bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def _flags(*values: str) -> str:
    flags: set[str] = {
        "phase9d_provider_selector",
        "selector_planning_only",
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


def load_market_data_provider_selector_config(path: str) -> dict[str, Any]:
    if not Path(path).exists():
        return {"providers": {}, "targets": []}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"providers": {}, "targets": []}


def _targets(config: dict[str, Any]) -> list[dict[str, str]]:
    raw = config.get("targets", []) or []
    return [
        {
            "target_id": str(item.get("target_id", "")),
            "target_type": str(item.get("target_type", "unknown")),
            "market": str(item.get("market", "UNKNOWN")),
            "data_role": str(item.get("data_role", "unknown")),
        }
        for item in raw
        if item.get("target_id")
    ]


def _provider_enabled(provider: dict[str, Any]) -> bool:
    return _bool(provider.get("enabled", False))


def _provider_live_allowed(provider: dict[str, Any]) -> bool:
    return _bool(provider.get("live_request_allowed", False))


def _select_for_target(
    target: dict[str, str],
    providers: dict[str, dict[str, Any]],
    ts_jst: str,
    ts_et: str,
) -> MarketDataProviderSelectorRow:
    blocked: list[str] = []
    reasons: list[str] = []

    for provider_id in sorted(providers.keys()):
        provider = providers[provider_id] or {}
        if provider_id == "manual_csv":
            continue

        if _provider_live_allowed(provider):
            blocked.append(provider_id)
            reasons.append(provider_id + ":live_request_allowed_blocked")
        elif not _provider_enabled(provider):
            blocked.append(provider_id)
            reasons.append(provider_id + ":provider_disabled")
        else:
            blocked.append(provider_id)
            reasons.append(provider_id + ":live_adapter_not_enabled_for_requests")

    manual = providers.get("manual_csv", {}) or {}
    manual_enabled = _provider_enabled(manual)
    manual_live_allowed = _provider_live_allowed(manual)

    if manual_enabled and not manual_live_allowed:
        return MarketDataProviderSelectorRow(
            target_id=target["target_id"],
            target_type=target["target_type"],
            market=target["market"],
            data_role=target["data_role"],
            selected_provider="manual_csv",
            selected_provider_type=str(manual.get("provider_type", "manual_csv_adapter")),
            selection_status="selected_manual_csv",
            fallback_provider=str(manual.get("fallback_provider", "sample_static")),
            blocked_provider=";".join(blocked) if blocked else "none",
            blocked_reason=";".join(reasons) if reasons else "none",
            live_request_allowed="false",
            action_allowed="false",
            warning_flags=_flags("manual_csv_selected", "live_provider_not_selected"),
            notes="manual_csv selected as safe provider; live providers remain blocked or disabled",
            timestamp_jst=ts_jst,
            timestamp_et=ts_et,
        )

    if manual_live_allowed:
        blocked.append("manual_csv")
        reasons.append("manual_csv:live_request_allowed_blocked")

    return MarketDataProviderSelectorRow(
        target_id=target["target_id"],
        target_type=target["target_type"],
        market=target["market"],
        data_role=target["data_role"],
        selected_provider="none",
        selected_provider_type="none",
        selection_status="blocked_no_provider",
        fallback_provider="none",
        blocked_provider=";".join(blocked) if blocked else "none",
        blocked_reason=";".join(reasons) if reasons else "no_enabled_safe_provider",
        live_request_allowed="false",
        action_allowed="false",
        warning_flags=_flags("blocked_no_provider"),
        notes="no safe provider selected; manual review required",
        timestamp_jst=ts_jst,
        timestamp_et=ts_et,
    )


def build_market_data_provider_selector_rows(
    config: dict[str, Any],
    tz_cfg: dict[str, str],
) -> list[MarketDataProviderSelectorRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    providers = config.get("providers", {}) or {}
    return [_select_for_target(target, providers, ts_jst, ts_et) for target in _targets(config)]


def write_market_data_provider_selector_csv(
    path: Path,
    rows: list[MarketDataProviderSelectorRow],
) -> None:
    fields = list(MarketDataProviderSelectorRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_market_data_provider_selector_report(
    path: Path,
    rows: list[MarketDataProviderSelectorRow],
    config_path: str,
) -> None:
    statuses = sorted({row.selection_status for row in rows})
    selected = sorted({row.selected_provider for row in rows})
    status_text = ",".join(statuses) if statuses else "none"
    selected_text = ",".join(selected) if selected else "none"

    lines = [
        "# Phase 9D Market Data Provider Selector Report",
        "",
        "- phase: Phase 9D",
        "- scope: provider selector and fallback planning",
        "- config_path: " + config_path,
        "- selected_providers: " + selected_text,
        "- selection_statuses: " + status_text,
        "- live_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Selector Rows",
        "",
        "| target_id | market | data_role | selected_provider | selection_status | fallback_provider | blocked_provider | blocked_reason | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.target_id} | {row.market} | {row.data_role} | {row.selected_provider} | {row.selection_status} | {row.fallback_provider} | {row.blocked_provider} | {row.blocked_reason} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- selector planning only",
            "- live providers are not selected when disabled or live_request_allowed=false",
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
