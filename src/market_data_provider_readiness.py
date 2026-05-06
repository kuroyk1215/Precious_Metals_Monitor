from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
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


def _flags(*values: str) -> str:
    flags: set[str] = {
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


def _target_rows() -> list[dict[str, str]]:
    return [
        {"target_id": "XAUUSD", "target_type": "upstream_factor", "market": "GLOBAL", "data_role": "gold_spot_usd"},
        {"target_id": "XAGUSD", "target_type": "upstream_factor", "market": "GLOBAL", "data_role": "silver_spot_usd"},
        {"target_id": "USDJPY", "target_type": "upstream_factor", "market": "FX", "data_role": "fx_rate"},
        {"target_id": "USDCNH", "target_type": "upstream_factor", "market": "FX", "data_role": "fx_rate"},
        {"target_id": "1540.T", "target_type": "etf_actual_price", "market": "JP", "data_role": "jp_gold_etf_actual_price"},
        {"target_id": "1542.T", "target_type": "etf_actual_price", "market": "JP", "data_role": "jp_silver_etf_actual_price"},
        {"target_id": "518880.SH", "target_type": "etf_actual_price", "market": "CN", "data_role": "cn_gold_etf_actual_price"},
    ]


def build_market_data_provider_readiness_rows(tz_cfg: dict[str, str]) -> list[MarketDataProviderReadinessRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[MarketDataProviderReadinessRow] = []

    for target in _target_rows():
        rows.append(
            MarketDataProviderReadinessRow(
                provider_id="manual_csv",
                provider_type="manual_csv_adapter",
                target_id=target["target_id"],
                target_type=target["target_type"],
                market=target["market"],
                data_role=target["data_role"],
                provider_enabled="true",
                readiness_status="manual_ready",
                fallback_provider="sample_static",
                source_quality_floor="manual_or_sample",
                live_request_allowed="false",
                action_allowed="false",
                warning_flags=_flags("manual_csv_primary"),
                notes="manual CSV remains the primary safe provider before live market data is explicitly enabled",
                timestamp_jst=ts_jst,
                timestamp_et=ts_et,
            )
        )

        rows.append(
            MarketDataProviderReadinessRow(
                provider_id="live_provider_candidate",
                provider_type="future_live_adapter",
                target_id=target["target_id"],
                target_type=target["target_type"],
                market=target["market"],
                data_role=target["data_role"],
                provider_enabled="false",
                readiness_status="disabled_until_explicit_config",
                fallback_provider="manual_csv",
                source_quality_floor="unavailable_until_enabled",
                live_request_allowed="false",
                action_allowed="false",
                warning_flags=_flags("live_provider_disabled", "requires_explicit_enable_switch"),
                notes="future live provider placeholder only; no API request or market data request is allowed in Phase 9A",
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
    live_enabled_count = sum(1 for r in rows if r.provider_enabled == "true" and r.provider_type == "future_live_adapter")
    status_text = ",".join(statuses) if statuses else "none"
    provider_text = ",".join(providers) if providers else "none"

    lines = [
        "# Phase 9A Market Data Provider Readiness Report",
        "",
        "- phase: Phase 9A",
        "- scope: market data provider readiness planning only",
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
