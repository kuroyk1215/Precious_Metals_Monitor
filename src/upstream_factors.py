from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Protocol
from zoneinfo import ZoneInfo


FACTOR_DEFS = [
    {"factor": "XAUUSD", "currency": "USD", "unit": "USD/oz"},
    {"factor": "XAGUSD", "currency": "USD", "unit": "USD/oz"},
    {"factor": "USDJPY", "currency": "JPY", "unit": "JPY/USD"},
    {"factor": "USDCNY", "currency": "CNY", "unit": "CNY/USD"},
    {"factor": "SGE_AU99_99", "currency": "CNY", "unit": "CNY/g"},
]


@dataclass
class FactorSnapshotRow:
    factor: str
    value: str
    currency: str
    unit: str
    source: str
    source_status: str
    timestamp_jst: str
    timestamp_et: str
    warning_flags: str
    notes: str


class UpstreamFactorProvider(Protocol):
    def fetch(self, factor: str) -> dict[str, Any]:
        ...


class ManualUpstreamFactorProvider:
    """Manual/mock provider used for framework wiring only."""

    def __init__(self, values: Optional[dict[str, float]] = None):
        self.values = values or {
            "XAUUSD": 2350.0,
            "XAGUSD": 28.5,
            "USDJPY": 155.0,
            "USDCNY": 7.2,
        }

    def fetch(self, factor: str) -> dict[str, Any]:
        if factor in self.values:
            return {
                "value": self.values[factor],
                "source": "manual_mock_provider",
                "source_status": "ok",
                "warning_flags": "manual_mock_data",
                "notes": "Research-only manual/mock snapshot. Not real-time market data.",
            }
        return {
            "value": None,
            "source": "placeholder",
            "source_status": "unavailable",
            "warning_flags": "no_realtime_source",
            "notes": "Placeholder factor in Phase 5B. No connected upstream feed yet.",
        }


def build_upstream_factor_snapshot(
    tz_cfg: dict[str, str],
    provider: UpstreamFactorProvider,
    factors: Optional[list[dict[str, str]]] = None,
) -> list[FactorSnapshotRow]:
    now_utc = datetime.now(timezone.utc)
    timestamp_jst = now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat()
    timestamp_et = now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat()

    rows: list[FactorSnapshotRow] = []
    for item in (factors or FACTOR_DEFS):
        factor = item["factor"]
        payload = provider.fetch(factor)
        value = payload.get("value")
        rows.append(
            FactorSnapshotRow(
                factor=factor,
                value="unavailable" if value is None else str(value),
                currency=item["currency"],
                unit=item["unit"],
                source=str(payload.get("source", "unknown")),
                source_status=str(payload.get("source_status", "unavailable")),
                timestamp_jst=timestamp_jst,
                timestamp_et=timestamp_et,
                warning_flags=str(payload.get("warning_flags", "none")),
                notes=str(payload.get("notes", "")),
            )
        )
    return rows
