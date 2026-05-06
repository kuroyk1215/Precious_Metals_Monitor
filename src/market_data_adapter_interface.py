from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Protocol
from zoneinfo import ZoneInfo
import csv


@dataclass
class MarketDataAdapterRequest:
    provider_id: str
    target_id: str
    target_type: str
    market: str
    data_role: str
    requested_mode: str
    requested_timeframe: str
    allow_network: bool
    allow_broker_connection: bool
    allow_trading: bool
    notes: str


@dataclass
class MarketDataAdapterResult:
    provider_id: str
    target_id: str
    target_type: str
    market: str
    data_role: str
    value: str
    currency: str
    source: str
    source_status: str
    adapter_status: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


@dataclass
class MarketDataAdapterContractRow:
    field_group: str
    field_name: str
    required: str
    allowed_values: str
    default_value: str
    safety_rule: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


class MarketDataAdapter(Protocol):
    provider_id: str

    def fetch_snapshot(self, request: MarketDataAdapterRequest) -> MarketDataAdapterResult:
        ...


class NoopMarketDataAdapter:
    provider_id = "noop_adapter"

    def __init__(self, tz_cfg: dict[str, str]) -> None:
        self.tz_cfg = tz_cfg

    def fetch_snapshot(self, request: MarketDataAdapterRequest) -> MarketDataAdapterResult:
        ts_jst, ts_et = _now_pair(self.tz_cfg)

        flags = [
            "adapter_interface_skeleton",
            "no_connection",
            "no_api_request",
            "no_ibkr_connection",
            "no_reqMktData",
            "no_reqHistoricalData",
            "no_order",
            "no_auto_trade",
        ]

        return MarketDataAdapterResult(
            provider_id=request.provider_id,
            target_id=request.target_id,
            target_type=request.target_type,
            market=request.market,
            data_role=request.data_role,
            value="unavailable",
            currency="unavailable",
            source="noop_adapter",
            source_status="interface_only",
            adapter_status="not_implemented",
            warning_flags=";".join(flags),
            notes="interface skeleton only; no network or broker request is performed",
            timestamp_jst=ts_jst,
            timestamp_et=ts_et,
        )


def _now_pair(tz_cfg: dict[str, str]) -> tuple[str, str]:
    now_utc = datetime.now(timezone.utc)
    return (
        now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat(),
        now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat(),
    )


def build_default_adapter_request(provider_id: str, target_id: str) -> MarketDataAdapterRequest:
    return MarketDataAdapterRequest(
        provider_id=provider_id,
        target_id=target_id,
        target_type="unknown",
        market="UNKNOWN",
        data_role="unknown",
        requested_mode="snapshot",
        requested_timeframe="latest",
        allow_network=False,
        allow_broker_connection=False,
        allow_trading=False,
        notes="default safe request; all external access disabled",
    )


def validate_adapter_request_safety(request: MarketDataAdapterRequest) -> list[str]:
    violations: list[str] = []

    if request.allow_network:
        violations.append("allow_network_must_be_false")
    if request.allow_broker_connection:
        violations.append("allow_broker_connection_must_be_false")
    if request.allow_trading:
        violations.append("allow_trading_must_be_false")
    if request.requested_mode not in {"snapshot", "historical", "metadata"}:
        violations.append("requested_mode_invalid")
    if not request.provider_id:
        violations.append("provider_id_required")
    if not request.target_id:
        violations.append("target_id_required")

    return violations


def build_market_data_adapter_contract_rows(tz_cfg: dict[str, str]) -> list[MarketDataAdapterContractRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)

    raw_rows = [
        ("request", "provider_id", "true", "registered provider_id", "none", "must match provider registry before real implementation", "provider identifier"),
        ("request", "target_id", "true", "XAUUSD/XAGUSD/USDJPY/USDCNY/SGE_AU99_99/1540.T/1542.T/518880.SH", "none", "target must be explicitly requested", "market data target"),
        ("request", "requested_mode", "true", "snapshot,historical,metadata", "snapshot", "interface only in Phase 7B", "requested data mode"),
        ("request", "allow_network", "true", "false", "false", "must remain false in Phase 7B", "blocks external API calls"),
        ("request", "allow_broker_connection", "true", "false", "false", "must remain false in Phase 7B", "blocks IBKR or broker connections"),
        ("request", "allow_trading", "true", "false", "false", "must remain false permanently for data adapters", "blocks any execution path"),
        ("result", "value", "true", "positive numeric or unavailable", "unavailable", "unavailable allowed when adapter is not implemented", "normalized data value"),
        ("result", "source_status", "true", "ok,partial,unavailable,interface_only,not_implemented", "interface_only", "must be explicit", "source status"),
        ("result", "adapter_status", "true", "ok,partial,unavailable,not_implemented,error", "not_implemented", "must be explicit", "adapter status"),
        ("result", "warning_flags", "true", "semicolon separated flags", "adapter_interface_skeleton", "must include safety flags when not implemented", "diagnostic flags"),
        ("safety", "no_connection", "true", "true", "true", "no connection is performed in Phase 7B", "phase safety boundary"),
        ("safety", "no_api_request", "true", "true", "true", "no API request is performed in Phase 7B", "phase safety boundary"),
        ("safety", "no_ibkr_connection", "true", "true", "true", "no IBKR connection is performed in Phase 7B", "phase safety boundary"),
        ("safety", "no_order", "true", "true", "true", "no order path is allowed", "permanent safety boundary"),
    ]

    return [
        MarketDataAdapterContractRow(
            field_group=field_group,
            field_name=field_name,
            required=required,
            allowed_values=allowed_values,
            default_value=default_value,
            safety_rule=safety_rule,
            notes=notes,
            timestamp_jst=ts_jst,
            timestamp_et=ts_et,
        )
        for field_group, field_name, required, allowed_values, default_value, safety_rule, notes in raw_rows
    ]


def write_market_data_adapter_contract_csv(path: Path, rows: list[MarketDataAdapterContractRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "field_group",
                "field_name",
                "required",
                "allowed_values",
                "default_value",
                "safety_rule",
                "notes",
                "timestamp_jst",
                "timestamp_et",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.field_group,
                    r.field_name,
                    r.required,
                    r.allowed_values,
                    r.default_value,
                    r.safety_rule,
                    r.notes,
                    r.timestamp_jst,
                    r.timestamp_et,
                ]
            )


def write_market_data_adapter_contract_report(path: Path, rows: list[MarketDataAdapterContractRow]) -> None:
    groups = sorted({r.field_group for r in rows})

    lines = [
        "# Market Data Adapter Interface Contract Report",
        "",
        "- phase: Phase 7B",
        "- scope: adapter interface skeleton only",
        "- action: contract/report only; no connection and no data request is performed",
        f"- contract_rows: {len(rows)}",
        f"- field_groups: {','.join(groups)}",
        "",
        "## Contract Rows",
        "",
        "| field_group | field_name | required | default_value | safety_rule |",
        "|---|---|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r.field_group} | {r.field_name} | {r.required} | {r.default_value} | {r.safety_rule} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- interface skeleton only",
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
