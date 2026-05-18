from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv
import yaml


EXPECTED_TARGETS = ["XAUUSD", "XAGUSD", "USDJPY", "USDCNH", "1540.T", "1542.T", "518880.SH"]
IBKR_PROVIDER_IDS = ["ibkr_readonly_live_provider", "ibkr_live_provider", "live_provider_candidate"]


@dataclass
class IBKRLiveProviderAdapterCheckRow:
    adapter_id: str
    provider_id: str
    provider_type: str
    target_id: str
    target_type: str
    market: str
    data_role: str
    provider_enabled: str
    live_request_allowed: str
    interface_implemented: str
    adapter_status: str
    provider_config_status: str
    tws_connection_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    api_request_allowed: str
    action_allowed: str
    fallback_provider: str
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


def _bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def _flags(*values: str) -> str:
    flags: set[str] = {
        "phase10g_ibkr_live_provider_adapter_skeleton",
        "ibkr_adapter_check_only",
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


def load_ibkr_live_provider_adapter_config(path: str) -> dict[str, Any]:
    if not Path(path).exists():
        return {"providers": {}, "targets": []}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"providers": {}, "targets": []}


def _targets(config: dict[str, Any]) -> list[dict[str, str]]:
    raw_targets = config.get("targets", []) or []
    rows: list[dict[str, str]] = []
    for target in raw_targets:
        target_id = str(target.get("target_id", ""))
        if not target_id:
            continue
        rows.append(
            {
                "target_id": target_id,
                "target_type": str(target.get("target_type", "unknown")),
                "market": str(target.get("market", "UNKNOWN")),
                "data_role": str(target.get("data_role", "unknown")),
            }
        )

    if rows:
        return rows

    return [
        {
            "target_id": target_id,
            "target_type": "unknown",
            "market": "UNKNOWN",
            "data_role": "unknown",
        }
        for target_id in EXPECTED_TARGETS
    ]


def _find_ibkr_provider(config: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    providers = config.get("providers", {}) or {}
    for provider_id in IBKR_PROVIDER_IDS:
        if provider_id in providers:
            return provider_id, providers[provider_id] or {}
    return "ibkr_readonly_live_provider", {}


def _adapter_decision(provider_id: str, provider: dict[str, Any]) -> tuple[str, str, str, str]:
    if not provider:
        return (
            "blocked_provider_not_configured",
            "not_configured",
            "ibkr_provider_not_configured",
            "provider_not_configured",
        )

    provider_type = str(provider.get("provider_type", "unknown"))
    enabled = bool(provider.get("enabled", False))
    live_allowed = bool(provider.get("live_request_allowed", False))
    implemented = bool(provider.get("interface_implemented", False))

    if provider_type == "manual_csv_adapter":
        return (
            "blocked_not_ibkr_provider",
            "wrong_provider_type",
            "provider_is_manual_csv_not_ibkr",
            "not_ibkr_provider",
        )

    if not enabled:
        return (
            "blocked_provider_disabled",
            "configured_disabled",
            "ibkr_provider_disabled",
            "provider_disabled",
        )

    if not live_allowed:
        return (
            "blocked_live_request_not_allowed",
            "configured_live_blocked",
            "live_request_allowed_false",
            "live_request_not_allowed",
        )

    if not implemented:
        return (
            "blocked_interface_not_implemented",
            "configured_interface_missing",
            "ibkr_interface_not_implemented",
            "interface_not_implemented",
        )

    return (
        "blocked_phase10g_skeleton_only",
        "configured_but_skeleton_only",
        "phase10g_does_not_connect_tws_or_request_market_data",
        "phase10g_skeleton_only",
    )


def build_ibkr_live_provider_adapter_check_rows(
    config: dict[str, Any],
    tz_cfg: dict[str, str],
) -> list[IBKRLiveProviderAdapterCheckRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    provider_id, provider = _find_ibkr_provider(config)
    adapter_status, config_status, block_reason, extra_flags = _adapter_decision(provider_id, provider)

    rows: list[IBKRLiveProviderAdapterCheckRow] = []
    for target in _targets(config):
        rows.append(
            IBKRLiveProviderAdapterCheckRow(
                adapter_id="ibkr_readonly_live_provider_adapter_skeleton",
                provider_id=provider_id,
                provider_type=str(provider.get("provider_type", "not_configured")),
                target_id=target["target_id"],
                target_type=target["target_type"],
                market=target["market"],
                data_role=target["data_role"],
                provider_enabled=_bool_text(provider.get("enabled", False)),
                live_request_allowed=_bool_text(provider.get("live_request_allowed", False)),
                interface_implemented=_bool_text(provider.get("interface_implemented", False)),
                adapter_status=adapter_status,
                provider_config_status=config_status,
                tws_connection_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                fallback_provider=str(provider.get("fallback_provider", "manual_csv")),
                block_reason=block_reason,
                warning_flags=_flags(extra_flags),
                notes="IBKR live provider adapter skeleton only; no TWS connection or market data request was made",
                timestamp_jst=ts_jst,
                timestamp_et=ts_et,
            )
        )

    return rows


def write_ibkr_live_provider_adapter_check_csv(
    path: Path,
    rows: list[IBKRLiveProviderAdapterCheckRow],
) -> None:
    fields = list(IBKRLiveProviderAdapterCheckRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_live_provider_adapter_check_report(
    path: Path,
    rows: list[IBKRLiveProviderAdapterCheckRow],
    config_path: str,
) -> None:
    statuses = sorted({row.adapter_status for row in rows})
    provider_ids = sorted({row.provider_id for row in rows})
    tws_allowed_count = sum(1 for row in rows if row.tws_connection_allowed == "true")
    market_data_allowed_count = sum(1 for row in rows if row.market_data_request_allowed == "true")
    api_allowed_count = sum(1 for row in rows if row.api_request_allowed == "true")
    action_allowed_count = sum(1 for row in rows if row.action_allowed == "true")

    lines = [
        "# Phase 10G IBKR Live Provider Adapter Skeleton Report",
        "",
        "- phase: Phase 10G",
        "- scope: IBKR read-only live provider adapter skeleton",
        "- config_path: " + config_path,
        "- provider_ids: " + (",".join(provider_ids) if provider_ids else "none"),
        "- adapter_statuses: " + (",".join(statuses) if statuses else "none"),
        "- tws_connection_allowed_count: " + str(tws_allowed_count),
        "- market_data_request_allowed_count: " + str(market_data_allowed_count),
        "- api_request_allowed_count: " + str(api_allowed_count),
        "- action_allowed_count: " + str(action_allowed_count),
        "",
        "## Adapter Check Rows",
        "",
        "| target_id | market | data_role | provider_id | adapter_status | tws_connection_allowed | market_data_request_allowed | api_request_allowed | action_allowed | block_reason |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.target_id} | {row.market} | {row.data_role} | {row.provider_id} | {row.adapter_status} | {row.tws_connection_allowed} | {row.market_data_request_allowed} | {row.api_request_allowed} | {row.action_allowed} | {row.block_reason} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- IBKR adapter skeleton only",
            "- no TWS connection",
            "- tws_connection_allowed=false for every row",
            "- market_data_request_allowed=false for every row",
            "- historical_data_request_allowed=false for every row",
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
