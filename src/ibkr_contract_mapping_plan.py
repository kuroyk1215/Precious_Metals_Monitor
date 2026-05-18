from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv
import yaml


EXPECTED_TARGETS = ["XAUUSD", "XAGUSD", "USDJPY", "USDCNH", "1540.T", "1542.T", "518880.SH"]


@dataclass
class IBKRContractMappingPlanRow:
    target_id: str
    target_type: str
    market: str
    data_role: str
    asset_class: str
    symbol: str
    currency: str
    exchange: str
    primary_exchange: str
    sec_type: str
    contract_status: str
    mapping_status: str
    tws_connection_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    api_request_allowed: str
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
        "phase10h_ibkr_contract_mapping_plan",
        "mapping_plan_only",
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


def load_ibkr_contract_mapping_config(path: str) -> dict[str, Any]:
    if not Path(path).exists():
        return {"providers": {}, "targets": []}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"providers": {}, "targets": []}


def _targets(config: dict[str, Any]) -> list[dict[str, str]]:
    raw = config.get("targets", []) or []
    rows: list[dict[str, str]] = []

    for item in raw:
        target_id = str(item.get("target_id", ""))
        if not target_id:
            continue
        rows.append(
            {
                "target_id": target_id,
                "target_type": str(item.get("target_type", "unknown")),
                "market": str(item.get("market", "UNKNOWN")),
                "data_role": str(item.get("data_role", "unknown")),
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


def _mapping_for_target(target_id: str) -> dict[str, str]:
    if target_id == "USDJPY":
        return {
            "asset_class": "fx",
            "symbol": "USD",
            "currency": "JPY",
            "exchange": "IDEALPRO",
            "primary_exchange": "IDEALPRO",
            "sec_type": "CASH",
            "contract_status": "candidate_mapping",
            "mapping_status": "candidate_mapping_ready",
            "notes": "IBKR FX candidate mapping only; qualification not performed",
        }

    if target_id == "USDCNH":
        return {
            "asset_class": "fx",
            "symbol": "USD",
            "currency": "CNH",
            "exchange": "IDEALPRO",
            "primary_exchange": "IDEALPRO",
            "sec_type": "CASH",
            "contract_status": "candidate_mapping",
            "mapping_status": "candidate_mapping_ready",
            "notes": "IBKR CNH FX candidate mapping only; qualification not performed",
        }

    if target_id == "1540.T":
        return {
            "asset_class": "jp_etf",
            "symbol": "1540",
            "currency": "JPY",
            "exchange": "TSEJ",
            "primary_exchange": "TSEJ",
            "sec_type": "STK",
            "contract_status": "candidate_mapping",
            "mapping_status": "candidate_mapping_ready",
            "notes": "JP ETF candidate mapping only; TWS contract qualification not performed",
        }

    if target_id == "1542.T":
        return {
            "asset_class": "jp_etf",
            "symbol": "1542",
            "currency": "JPY",
            "exchange": "TSEJ",
            "primary_exchange": "TSEJ",
            "sec_type": "STK",
            "contract_status": "candidate_mapping",
            "mapping_status": "candidate_mapping_ready",
            "notes": "JP ETF candidate mapping only; TWS contract qualification not performed",
        }

    if target_id == "518880.SH":
        return {
            "asset_class": "cn_etf",
            "symbol": "518880",
            "currency": "CNY",
            "exchange": "SSE",
            "primary_exchange": "SSE",
            "sec_type": "STK",
            "contract_status": "candidate_mapping",
            "mapping_status": "candidate_review_required",
            "notes": "CN ETF candidate mapping only; broker data availability must be manually verified",
        }

    if target_id == "XAUUSD":
        return {
            "asset_class": "precious_metal_spot",
            "symbol": "XAUUSD",
            "currency": "USD",
            "exchange": "SMART_OR_IDEALPRO_REVIEW",
            "primary_exchange": "REVIEW_REQUIRED",
            "sec_type": "CMDTY_OR_CASH_REVIEW",
            "contract_status": "candidate_mapping",
            "mapping_status": "candidate_review_required",
            "notes": "Spot gold IBKR contract representation requires manual qualification review",
        }

    if target_id == "XAGUSD":
        return {
            "asset_class": "precious_metal_spot",
            "symbol": "XAGUSD",
            "currency": "USD",
            "exchange": "SMART_OR_IDEALPRO_REVIEW",
            "primary_exchange": "REVIEW_REQUIRED",
            "sec_type": "CMDTY_OR_CASH_REVIEW",
            "contract_status": "candidate_mapping",
            "mapping_status": "candidate_review_required",
            "notes": "Spot silver IBKR contract representation requires manual qualification review",
        }

    return {
        "asset_class": "unknown",
        "symbol": target_id,
        "currency": "unknown",
        "exchange": "unknown",
        "primary_exchange": "unknown",
        "sec_type": "unknown",
        "contract_status": "missing_mapping",
        "mapping_status": "manual_review_required",
        "notes": "no candidate mapping rule exists for this target",
    }


def build_ibkr_contract_mapping_plan_rows(
    config: dict[str, Any],
    tz_cfg: dict[str, str],
) -> list[IBKRContractMappingPlanRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[IBKRContractMappingPlanRow] = []

    for target in _targets(config):
        mapping = _mapping_for_target(target["target_id"])
        rows.append(
            IBKRContractMappingPlanRow(
                target_id=target["target_id"],
                target_type=target["target_type"],
                market=target["market"],
                data_role=target["data_role"],
                asset_class=mapping["asset_class"],
                symbol=mapping["symbol"],
                currency=mapping["currency"],
                exchange=mapping["exchange"],
                primary_exchange=mapping["primary_exchange"],
                sec_type=mapping["sec_type"],
                contract_status=mapping["contract_status"],
                mapping_status=mapping["mapping_status"],
                tws_connection_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                warning_flags=_flags(mapping["mapping_status"], mapping["contract_status"]),
                notes=mapping["notes"],
                timestamp_jst=ts_jst,
                timestamp_et=ts_et,
            )
        )

    return rows


def write_ibkr_contract_mapping_plan_csv(path: Path, rows: list[IBKRContractMappingPlanRow]) -> None:
    fields = list(IBKRContractMappingPlanRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_contract_mapping_plan_report(
    path: Path,
    rows: list[IBKRContractMappingPlanRow],
    config_path: str,
) -> None:
    mapping_statuses = sorted({row.mapping_status for row in rows})
    contract_statuses = sorted({row.contract_status for row in rows})
    ready_count = sum(1 for row in rows if row.mapping_status == "candidate_mapping_ready")
    review_count = sum(1 for row in rows if row.mapping_status != "candidate_mapping_ready")

    lines = [
        "# Phase 10H IBKR Contract Mapping Plan Report",
        "",
        "- phase: Phase 10H",
        "- scope: IBKR contract mapping plan only",
        "- config_path: " + config_path,
        "- row_count: " + str(len(rows)),
        "- candidate_mapping_ready_count: " + str(ready_count),
        "- review_required_count: " + str(review_count),
        "- mapping_statuses: " + (",".join(mapping_statuses) if mapping_statuses else "none"),
        "- contract_statuses: " + (",".join(contract_statuses) if contract_statuses else "none"),
        "- tws_connection_allowed: false",
        "- market_data_request_allowed: false",
        "- api_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Contract Mapping Rows",
        "",
        "| target_id | asset_class | symbol | currency | exchange | primary_exchange | sec_type | mapping_status | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.target_id} | {row.asset_class} | {row.symbol} | {row.currency} | {row.exchange} | {row.primary_exchange} | {row.sec_type} | {row.mapping_status} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- IBKR contract mapping plan only",
            "- no TWS connection",
            "- no contract qualification",
            "- no market data request",
            "- no historical data request",
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
