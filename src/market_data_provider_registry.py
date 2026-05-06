from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import csv


@dataclass
class MarketDataProviderRegistryRow:
    provider_id: str
    provider_type: str
    target_scope: str
    provider_status: str
    connection_mode: str
    requires_credentials: str
    supports_realtime: str
    supports_historical: str
    permission_status: str
    planned_priority: int
    safety_scope: str
    blocking_issue: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


def _now_pair(tz_cfg: dict[str, str]) -> tuple[str, str]:
    now_utc = datetime.now(timezone.utc)
    return (
        now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat(),
        now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat(),
    )


def build_market_data_provider_registry_rows(tz_cfg: dict[str, str]) -> list[MarketDataProviderRegistryRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    safety_scope = (
        "registry_only; no_connection; no_api_request; no_ibkr_connection; "
        "no_reqMktData; no_reqHistoricalData; no_order; no_cancel; "
        "no_rebalance; no_auto_trade; no_automatic_execution"
    )

    raw_rows = [
        {
            "provider_id": "manual_csv",
            "provider_type": "local_file",
            "target_scope": "XAUUSD,XAGUSD,USDJPY,USDCNY,SGE_AU99_99,1540.T,1542.T,518880.SH",
            "provider_status": "ready",
            "connection_mode": "local_csv",
            "requires_credentials": "false",
            "supports_realtime": "false",
            "supports_historical": "manual_only",
            "permission_status": "not_required",
            "planned_priority": 1,
            "blocking_issue": "none",
            "notes": "current stable offline research workflow",
        },
        {
            "provider_id": "ibkr_readonly",
            "provider_type": "broker_readonly",
            "target_scope": "1540.T,1542.T,GLD,SLV,FX_if_permissioned",
            "provider_status": "planned",
            "connection_mode": "readonly_adapter_future",
            "requires_credentials": "true",
            "supports_realtime": "permission_dependent",
            "supports_historical": "permission_dependent",
            "permission_status": "subscription_and_contract_check_required",
            "planned_priority": 2,
            "blocking_issue": "market data permissions, contract qualification, and read-only enforcement must be verified",
            "notes": "future read-only adapter only; no trading path",
        },
        {
            "provider_id": "external_precious_metals_provider",
            "provider_type": "external_api",
            "target_scope": "XAUUSD,XAGUSD",
            "provider_status": "planned",
            "connection_mode": "api_adapter_future",
            "requires_credentials": "provider_dependent",
            "supports_realtime": "provider_dependent",
            "supports_historical": "provider_dependent",
            "permission_status": "provider_selection_required",
            "planned_priority": 3,
            "blocking_issue": "provider selection, license, rate limit, and redistribution rules required",
            "notes": "candidate source for upstream metals factors",
        },
        {
            "provider_id": "external_fx_provider",
            "provider_type": "external_api",
            "target_scope": "USDJPY,USDCNY",
            "provider_status": "planned",
            "connection_mode": "api_adapter_future",
            "requires_credentials": "provider_dependent",
            "supports_realtime": "provider_dependent",
            "supports_historical": "provider_dependent",
            "permission_status": "provider_selection_required",
            "planned_priority": 4,
            "blocking_issue": "provider selection and onshore/offshore FX definition required",
            "notes": "candidate source for FX factors",
        },
        {
            "provider_id": "sge_official_or_manual",
            "provider_type": "official_or_manual_source",
            "target_scope": "SGE_AU99_99",
            "provider_status": "planned",
            "connection_mode": "official_file_or_manual_adapter_future",
            "requires_credentials": "unknown",
            "supports_realtime": "unknown",
            "supports_historical": "candidate",
            "permission_status": "official_access_and_terms_check_required",
            "planned_priority": 5,
            "blocking_issue": "official source access, format stability, and redistribution terms required",
            "notes": "preferred domestic factor for 518880.SH when available",
        },
        {
            "provider_id": "cn_market_data_provider",
            "provider_type": "external_cn_market_data",
            "target_scope": "518880.SH",
            "provider_status": "planned",
            "connection_mode": "api_adapter_future",
            "requires_credentials": "provider_dependent",
            "supports_realtime": "provider_dependent",
            "supports_historical": "provider_dependent",
            "permission_status": "provider_selection_required",
            "planned_priority": 6,
            "blocking_issue": "CN provider license, API contract, and data usage limits required",
            "notes": "candidate source for CN ETF actual price",
        },
        {
            "provider_id": "public_research_sources",
            "provider_type": "public_reference",
            "target_scope": "supplemental_reference_only",
            "provider_status": "future",
            "connection_mode": "manual_or_scrape_prohibited_until_terms_checked",
            "requires_credentials": "unknown",
            "supports_realtime": "unknown",
            "supports_historical": "unknown",
            "permission_status": "terms_check_required",
            "planned_priority": 7,
            "blocking_issue": "terms of service and data usage restrictions must be checked before implementation",
            "notes": "not a production data source until legal and technical checks are complete",
        },
    ]

    rows: list[MarketDataProviderRegistryRow] = []
    for r in raw_rows:
        rows.append(
            MarketDataProviderRegistryRow(
                provider_id=str(r["provider_id"]),
                provider_type=str(r["provider_type"]),
                target_scope=str(r["target_scope"]),
                provider_status=str(r["provider_status"]),
                connection_mode=str(r["connection_mode"]),
                requires_credentials=str(r["requires_credentials"]),
                supports_realtime=str(r["supports_realtime"]),
                supports_historical=str(r["supports_historical"]),
                permission_status=str(r["permission_status"]),
                planned_priority=int(r["planned_priority"]),
                safety_scope=safety_scope,
                blocking_issue=str(r["blocking_issue"]),
                notes=str(r["notes"]),
                timestamp_jst=ts_jst,
                timestamp_et=ts_et,
            )
        )
    return rows


def write_market_data_provider_registry_csv(path: Path, rows: list[MarketDataProviderRegistryRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "provider_id",
                "provider_type",
                "target_scope",
                "provider_status",
                "connection_mode",
                "requires_credentials",
                "supports_realtime",
                "supports_historical",
                "permission_status",
                "planned_priority",
                "safety_scope",
                "blocking_issue",
                "notes",
                "timestamp_jst",
                "timestamp_et",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.provider_id,
                    r.provider_type,
                    r.target_scope,
                    r.provider_status,
                    r.connection_mode,
                    r.requires_credentials,
                    r.supports_realtime,
                    r.supports_historical,
                    r.permission_status,
                    r.planned_priority,
                    r.safety_scope,
                    r.blocking_issue,
                    r.notes,
                    r.timestamp_jst,
                    r.timestamp_et,
                ]
            )


def write_market_data_provider_registry_report(path: Path, rows: list[MarketDataProviderRegistryRow]) -> None:
    statuses = sorted({r.provider_status for r in rows})
    ready_count = sum(1 for r in rows if r.provider_status == "ready")
    planned_count = sum(1 for r in rows if r.provider_status == "planned")
    future_count = sum(1 for r in rows if r.provider_status == "future")

    lines = [
        "# Market Data Provider Registry Report",
        "",
        "- phase: Phase 7A",
        "- scope: provider registry skeleton only",
        "- action: registry only; no connection and no data request is performed",
        f"- provider_count: {len(rows)}",
        f"- statuses: {','.join(statuses) if statuses else 'none'}",
        f"- ready_count: {ready_count}",
        f"- planned_count: {planned_count}",
        f"- future_count: {future_count}",
        "",
        "## Provider Registry",
        "",
        "| priority | provider_id | provider_type | provider_status | target_scope | permission_status |",
        "|---:|---|---|---|---|---|",
    ]

    for r in sorted(rows, key=lambda x: x.planned_priority):
        lines.append(
            f"| {r.planned_priority} | {r.provider_id} | {r.provider_type} | {r.provider_status} | {r.target_scope} | {r.permission_status} |"
        )

    lines.extend(
        [
            "",
            "## Blocking Issues",
            "",
            "| provider_id | blocking_issue |",
            "|---|---|",
        ]
    )

    for r in sorted(rows, key=lambda x: x.planned_priority):
        lines.append(f"| {r.provider_id} | {r.blocking_issue} |")

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- registry only",
            "- no connection",
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
