from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import csv


@dataclass
class MarketDataSourcePlanRow:
    target_id: str
    target_type: str
    market: str
    data_role: str
    candidate_source: str
    adapter_status: str
    permission_required: str
    realtime_capability: str
    historical_capability: str
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


def build_market_data_source_plan_rows(tz_cfg: dict[str, str]) -> list[MarketDataSourcePlanRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    safety_scope = "planning_only; no_ibkr_connection; no_reqMktData; no_reqHistoricalData; no_order; no_cancel; no_rebalance; no_auto_trade"

    raw_rows = [
        {
            "target_id": "XAUUSD",
            "target_type": "upstream_factor",
            "market": "GLOBAL",
            "data_role": "gold_spot_usd",
            "candidate_source": "external_market_data_provider_or_manual_csv",
            "adapter_status": "planned",
            "permission_required": "provider_api_or_manual_file",
            "realtime_capability": "candidate",
            "historical_capability": "candidate",
            "planned_priority": 1,
            "blocking_issue": "provider selection and license check required",
            "notes": "used by 1540.T and 518880.SH theoretical pricing proxy",
        },
        {
            "target_id": "XAGUSD",
            "target_type": "upstream_factor",
            "market": "GLOBAL",
            "data_role": "silver_spot_usd",
            "candidate_source": "external_market_data_provider_or_manual_csv",
            "adapter_status": "planned",
            "permission_required": "provider_api_or_manual_file",
            "realtime_capability": "candidate",
            "historical_capability": "candidate",
            "planned_priority": 2,
            "blocking_issue": "provider selection and license check required",
            "notes": "used by 1542.T theoretical pricing proxy",
        },
        {
            "target_id": "USDJPY",
            "target_type": "upstream_factor",
            "market": "FX",
            "data_role": "fx_rate",
            "candidate_source": "external_fx_provider_or_manual_csv",
            "adapter_status": "planned",
            "permission_required": "provider_api_or_manual_file",
            "realtime_capability": "candidate",
            "historical_capability": "candidate",
            "planned_priority": 3,
            "blocking_issue": "provider selection and update frequency policy required",
            "notes": "used by JP ETF theoretical pricing",
        },
        {
            "target_id": "USDCNY",
            "target_type": "upstream_factor",
            "market": "FX",
            "data_role": "fx_rate",
            "candidate_source": "external_fx_provider_or_manual_csv",
            "adapter_status": "planned",
            "permission_required": "provider_api_or_manual_file",
            "realtime_capability": "candidate",
            "historical_capability": "candidate",
            "planned_priority": 4,
            "blocking_issue": "onshore/offshore FX source definition required",
            "notes": "used by 518880.SH external proxy when SGE is unavailable",
        },
        {
            "target_id": "SGE_AU99_99",
            "target_type": "upstream_factor",
            "market": "CN",
            "data_role": "shanghai_gold_benchmark",
            "candidate_source": "sge_official_or_manual_csv",
            "adapter_status": "planned",
            "permission_required": "official_source_access_or_manual_file",
            "realtime_capability": "unknown",
            "historical_capability": "candidate",
            "planned_priority": 5,
            "blocking_issue": "official source access, format, and redistribution rules required",
            "notes": "preferred pricing input for 518880.SH when available",
        },
        {
            "target_id": "1540.T",
            "target_type": "etf_actual_price",
            "market": "JP",
            "data_role": "jp_gold_etf_actual_price",
            "candidate_source": "ibkr_readonly_or_manual_csv",
            "adapter_status": "planned",
            "permission_required": "market_data_subscription_or_manual_file",
            "realtime_capability": "permission_dependent",
            "historical_capability": "candidate",
            "planned_priority": 6,
            "blocking_issue": "TSE ETF market data permission and contract qualification check required",
            "notes": "cash-market ETF; planning only in this phase",
        },
        {
            "target_id": "1542.T",
            "target_type": "etf_actual_price",
            "market": "JP",
            "data_role": "jp_silver_etf_actual_price",
            "candidate_source": "ibkr_readonly_or_manual_csv",
            "adapter_status": "planned",
            "permission_required": "market_data_subscription_or_manual_file",
            "realtime_capability": "permission_dependent",
            "historical_capability": "candidate",
            "planned_priority": 7,
            "blocking_issue": "TSE ETF market data permission and contract qualification check required",
            "notes": "cash-market ETF; planning only in this phase",
        },
        {
            "target_id": "518880.SH",
            "target_type": "etf_actual_price",
            "market": "CN",
            "data_role": "cn_gold_etf_actual_price",
            "candidate_source": "manual_csv_or_cn_market_data_provider",
            "adapter_status": "planned",
            "permission_required": "provider_api_or_manual_file",
            "realtime_capability": "candidate",
            "historical_capability": "candidate",
            "planned_priority": 8,
            "blocking_issue": "CN market data provider selection and license check required",
            "notes": "A-share ETF; planning only in this phase",
        },
        {
            "target_id": "GLD",
            "target_type": "future_extension",
            "market": "US",
            "data_role": "us_gold_etf_reference",
            "candidate_source": "ibkr_readonly_or_external_provider",
            "adapter_status": "future",
            "permission_required": "provider_permission_or_broker_market_data",
            "realtime_capability": "candidate",
            "historical_capability": "candidate",
            "planned_priority": 9,
            "blocking_issue": "not required for current JP/CN ETF pipeline",
            "notes": "future cross-market validation reference",
        },
        {
            "target_id": "SLV",
            "target_type": "future_extension",
            "market": "US",
            "data_role": "us_silver_etf_reference",
            "candidate_source": "ibkr_readonly_or_external_provider",
            "adapter_status": "future",
            "permission_required": "provider_permission_or_broker_market_data",
            "realtime_capability": "candidate",
            "historical_capability": "candidate",
            "planned_priority": 10,
            "blocking_issue": "not required for current JP/CN ETF pipeline",
            "notes": "future cross-market validation reference",
        },
    ]

    return [
        MarketDataSourcePlanRow(
            target_id=str(r["target_id"]),
            target_type=str(r["target_type"]),
            market=str(r["market"]),
            data_role=str(r["data_role"]),
            candidate_source=str(r["candidate_source"]),
            adapter_status=str(r["adapter_status"]),
            permission_required=str(r["permission_required"]),
            realtime_capability=str(r["realtime_capability"]),
            historical_capability=str(r["historical_capability"]),
            planned_priority=int(r["planned_priority"]),
            safety_scope=safety_scope,
            blocking_issue=str(r["blocking_issue"]),
            notes=str(r["notes"]),
            timestamp_jst=ts_jst,
            timestamp_et=ts_et,
        )
        for r in raw_rows
    ]


def write_market_data_source_plan_csv(path: Path, rows: list[MarketDataSourcePlanRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "target_id",
                "target_type",
                "market",
                "data_role",
                "candidate_source",
                "adapter_status",
                "permission_required",
                "realtime_capability",
                "historical_capability",
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
                    r.target_id,
                    r.target_type,
                    r.market,
                    r.data_role,
                    r.candidate_source,
                    r.adapter_status,
                    r.permission_required,
                    r.realtime_capability,
                    r.historical_capability,
                    r.planned_priority,
                    r.safety_scope,
                    r.blocking_issue,
                    r.notes,
                    r.timestamp_jst,
                    r.timestamp_et,
                ]
            )


def write_market_data_source_plan_report(path: Path, rows: list[MarketDataSourcePlanRow]) -> None:
    planned = [r for r in rows if r.adapter_status == "planned"]
    future = [r for r in rows if r.adapter_status == "future"]

    lines = [
        "# Real Market Data Source Adapter Planning Report",
        "",
        "- phase: Phase 6A",
        "- scope: planning only",
        "- no live request is performed in this phase",
        f"- planned_targets: {len(planned)}",
        f"- future_targets: {len(future)}",
        "",
        "## Source Plan Rows",
        "",
        "| priority | target_id | target_type | market | candidate_source | adapter_status | realtime_capability | historical_capability |",
        "|---:|---|---|---|---|---|---|---|",
    ]

    for r in sorted(rows, key=lambda x: x.planned_priority):
        lines.append(
            f"| {r.planned_priority} | {r.target_id} | {r.target_type} | {r.market} | {r.candidate_source} | {r.adapter_status} | {r.realtime_capability} | {r.historical_capability} |"
        )

    lines.extend(
        [
            "",
            "## Blocking Issues",
            "",
            "| target_id | blocking_issue |",
            "|---|---|",
        ]
    )
    for r in sorted(rows, key=lambda x: x.planned_priority):
        lines.append(f"| {r.target_id} | {r.blocking_issue} |")

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- planning only",
            "- no IBKR connection",
            "- no reqMktData",
            "- no reqHistoricalData",
            "- no order",
            "- no cancel",
            "- no rebalance",
            "- no auto trade",
            "- no automatic pipeline chaining",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
