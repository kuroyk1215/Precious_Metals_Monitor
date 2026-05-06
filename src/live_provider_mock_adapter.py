from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo
import csv
import yaml


@dataclass
class LiveProviderMockAdapterRow:
    provider_id: str
    provider_type: str
    target_id: str
    target_type: str
    market: str
    data_role: str
    mock_value: str
    currency: str
    data_status: str
    source_quality: str
    api_request_allowed: str
    action_allowed: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


MOCK_VALUES = {
    "XAUUSD": ("3400.00", "USD"),
    "XAGUSD": ("40.00", "USD"),
    "USDJPY": ("155.0000", "JPY"),
    "USDCNH": ("7.2500", "CNH"),
    "1540.T": ("36425.0", "JPY"),
    "1542.T": ("441.75", "JPY"),
    "518880.SH": ("5.2000", "CNY"),
}


def _now_pair(tz_cfg: dict[str, str]) -> tuple[str, str]:
    now_utc = datetime.now(timezone.utc)
    return (
        now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat(),
        now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat(),
    )


def _flags(*values: str) -> str:
    flags: set[str] = {
        "phase10c_live_provider_mock_adapter",
        "mock_only",
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


def load_live_provider_mock_adapter_config(path: str) -> dict[str, Any]:
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
    return rows


def _mock_value_for_target(target_id: str) -> tuple[str, str, str]:
    if target_id in MOCK_VALUES:
        value, currency = MOCK_VALUES[target_id]
        return value, currency, "mock_live_adapter"
    return "unavailable", "unavailable", "mock_missing_target"


def build_live_provider_mock_adapter_rows(
    config: dict[str, Any],
    tz_cfg: dict[str, str],
    provider_id: str = "live_provider_mock_adapter",
) -> list[LiveProviderMockAdapterRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[LiveProviderMockAdapterRow] = []

    for target in _targets(config):
        value, currency, data_status = _mock_value_for_target(target["target_id"])
        rows.append(
            LiveProviderMockAdapterRow(
                provider_id=provider_id,
                provider_type="mock_live_adapter",
                target_id=target["target_id"],
                target_type=target["target_type"],
                market=target["market"],
                data_role=target["data_role"],
                mock_value=value,
                currency=currency,
                data_status=data_status,
                source_quality="mock_only",
                api_request_allowed="false",
                action_allowed="false",
                warning_flags=_flags(data_status),
                notes="mock live provider adapter output only; no real API request was made",
                timestamp_jst=ts_jst,
                timestamp_et=ts_et,
            )
        )

    return rows


def write_live_provider_mock_adapter_csv(
    path: Path,
    rows: list[LiveProviderMockAdapterRow],
) -> None:
    fields = list(LiveProviderMockAdapterRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_live_provider_mock_adapter_report(
    path: Path,
    rows: list[LiveProviderMockAdapterRow],
    config_path: str,
) -> None:
    statuses = sorted({row.data_status for row in rows})
    targets = sorted({row.target_id for row in rows})
    api_allowed_count = sum(1 for row in rows if row.api_request_allowed == "true")
    action_allowed_count = sum(1 for row in rows if row.action_allowed == "true")

    lines = [
        "# Phase 10C Live Provider Mock Adapter Report",
        "",
        "- phase: Phase 10C",
        "- scope: mock live provider adapter output",
        "- config_path: " + config_path,
        "- target_count: " + str(len(targets)),
        "- data_statuses: " + (",".join(statuses) if statuses else "none"),
        "- api_request_allowed_count: " + str(api_allowed_count),
        "- action_allowed_count: " + str(action_allowed_count),
        "",
        "## Mock Adapter Rows",
        "",
        "| target_id | market | data_role | mock_value | currency | data_status | source_quality | api_request_allowed | action_allowed |",
        "|---|---|---|---:|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.target_id} | {row.market} | {row.data_role} | {row.mock_value} | {row.currency} | {row.data_status} | {row.source_quality} | {row.api_request_allowed} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- mock adapter only",
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
