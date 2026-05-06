from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo
import csv


UPSTREAM_TARGETS = {
    "XAUUSD": ("XAUUSD", "USD", "usd_per_oz"),
    "XAGUSD": ("XAGUSD", "USD", "usd_per_oz"),
    "USDJPY": ("USDJPY", "JPY", "fx_rate"),
    "USDCNY": ("USDCNY", "CNY", "fx_rate"),
    "SGE_AU99_99": ("SGE_AU99_99", "CNY", "cny_per_gram"),
}

ACTUAL_ETF_TARGETS = {
    "1540.T": "JPY",
    "1542.T": "JPY",
    "518880.SH": "CNY",
}


@dataclass
class IntegratedUpstreamFactorRow:
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


@dataclass
class IntegratedActualEtfPriceRow:
    etf_symbol: str
    actual_price: str
    currency: str
    source: str
    source_status: str
    timestamp_jst: str
    timestamp_et: str
    warning_flags: str
    notes: str


@dataclass
class ManualMarketDataIntegrationSummaryRow:
    target_id: str
    output_type: str
    output_id: str
    input_status: str
    output_status: str
    included: str
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


def _parse_positive_float(value: object) -> Optional[float]:
    if value in (None, "", "unavailable", "nan", "NaN"):
        return None
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def _split_flags(flags: str) -> set[str]:
    if not flags or flags == "none":
        return set()
    return {flag.strip() for flag in flags.split(";") if flag.strip()}


def load_manual_market_data_snapshot(path: str) -> dict[str, dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return {
            str(row.get("target_id", "")): {k: str(v) if v is not None else "" for k, v in row.items()}
            for row in reader
        }


def _is_usable_manual_row(row: dict[str, str]) -> bool:
    return row.get("normalized_status") == "ok" and _parse_positive_float(row.get("value")) is not None


def _warning_flags_for(row: dict[str, str], missing: bool, usable: bool) -> str:
    flags = _split_flags(row.get("warning_flags", "none"))
    flags.add("manual_market_data_integration")
    flags.add("manual_csv")
    flags.add("no_realtime_source")

    if missing:
        flags.add("missing_manual_market_data_target")
    if not usable:
        flags.add("manual_market_data_unavailable_or_invalid")

    return ";".join(sorted(flags)) if flags else "none"


def _source_for(row: dict[str, str], usable: bool) -> tuple[str, str]:
    if usable:
        source = row.get("source", "manual_csv") or "manual_csv"
        source_status = row.get("source_status", "manual_csv") or "manual_csv"
        return source, source_status
    return "manual_market_data_integration", "unavailable"


def build_integrated_market_data_rows(
    snapshot: dict[str, dict[str, str]],
    tz_cfg: dict[str, str],
) -> tuple[
    list[IntegratedUpstreamFactorRow],
    list[IntegratedActualEtfPriceRow],
    list[ManualMarketDataIntegrationSummaryRow],
]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    upstream_rows: list[IntegratedUpstreamFactorRow] = []
    actual_rows: list[IntegratedActualEtfPriceRow] = []
    summary_rows: list[ManualMarketDataIntegrationSummaryRow] = []

    for target_id, (factor, fallback_currency, unit) in UPSTREAM_TARGETS.items():
        row = snapshot.get(target_id, {})
        missing = target_id not in snapshot
        usable = _is_usable_manual_row(row)
        source, source_status = _source_for(row, usable)
        flags = _warning_flags_for(row, missing, usable)
        value = row.get("value", "unavailable") if usable else "unavailable"
        currency = row.get("currency", fallback_currency) if usable else fallback_currency
        notes = row.get("notes", "none") if usable else ("missing target" if missing else row.get("notes", "manual row unavailable/invalid"))

        upstream_rows.append(
            IntegratedUpstreamFactorRow(
                factor=factor,
                value=value,
                currency=currency,
                unit=unit,
                source=source,
                source_status=source_status,
                timestamp_jst=row.get("timestamp_jst", ts_jst),
                timestamp_et=row.get("timestamp_et", ts_et),
                warning_flags=flags,
                notes=notes or "none",
            )
        )
        summary_rows.append(
            ManualMarketDataIntegrationSummaryRow(
                target_id=target_id,
                output_type="upstream_factor",
                output_id=factor,
                input_status=row.get("normalized_status", "missing"),
                output_status="ok" if usable else "unavailable",
                included="true" if usable else "false",
                warning_flags=flags,
                notes=notes or "none",
                timestamp_jst=row.get("timestamp_jst", ts_jst),
                timestamp_et=row.get("timestamp_et", ts_et),
            )
        )

    for target_id, fallback_currency in ACTUAL_ETF_TARGETS.items():
        row = snapshot.get(target_id, {})
        missing = target_id not in snapshot
        usable = _is_usable_manual_row(row)
        source, source_status = _source_for(row, usable)
        flags = _warning_flags_for(row, missing, usable)
        actual_price = row.get("value", "unavailable") if usable else "unavailable"
        currency = row.get("currency", fallback_currency) if usable else fallback_currency
        notes = row.get("notes", "none") if usable else ("missing target" if missing else row.get("notes", "manual row unavailable/invalid"))

        actual_rows.append(
            IntegratedActualEtfPriceRow(
                etf_symbol=target_id,
                actual_price=actual_price,
                currency=currency,
                source=source,
                source_status=source_status,
                timestamp_jst=row.get("timestamp_jst", ts_jst),
                timestamp_et=row.get("timestamp_et", ts_et),
                warning_flags=flags,
                notes=notes or "none",
            )
        )
        summary_rows.append(
            ManualMarketDataIntegrationSummaryRow(
                target_id=target_id,
                output_type="actual_etf_price",
                output_id=target_id,
                input_status=row.get("normalized_status", "missing"),
                output_status="ok" if usable else "unavailable",
                included="true" if usable else "false",
                warning_flags=flags,
                notes=notes or "none",
                timestamp_jst=row.get("timestamp_jst", ts_jst),
                timestamp_et=row.get("timestamp_et", ts_et),
            )
        )

    return upstream_rows, actual_rows, summary_rows


def write_integrated_upstream_factor_csv(path: Path, rows: list[IntegratedUpstreamFactorRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["factor", "value", "currency", "unit", "source", "source_status", "timestamp_jst", "timestamp_et", "warning_flags", "notes"])
        for r in rows:
            writer.writerow([r.factor, r.value, r.currency, r.unit, r.source, r.source_status, r.timestamp_jst, r.timestamp_et, r.warning_flags, r.notes])


def write_integrated_actual_etf_price_csv(path: Path, rows: list[IntegratedActualEtfPriceRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["etf_symbol", "actual_price", "currency", "source", "source_status", "timestamp_jst", "timestamp_et", "warning_flags", "notes"])
        for r in rows:
            writer.writerow([r.etf_symbol, r.actual_price, r.currency, r.source, r.source_status, r.timestamp_jst, r.timestamp_et, r.warning_flags, r.notes])


def write_manual_market_data_integration_summary_csv(path: Path, rows: list[ManualMarketDataIntegrationSummaryRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["target_id", "output_type", "output_id", "input_status", "output_status", "included", "warning_flags", "notes", "timestamp_jst", "timestamp_et"])
        for r in rows:
            writer.writerow([r.target_id, r.output_type, r.output_id, r.input_status, r.output_status, r.included, r.warning_flags, r.notes, r.timestamp_jst, r.timestamp_et])


def write_manual_market_data_integration_report(
    path: Path,
    rows: list[ManualMarketDataIntegrationSummaryRow],
    input_path: str,
    upstream_csv: str,
    actual_csv: str,
) -> None:
    included_count = sum(1 for r in rows if r.included == "true")
    unavailable_count = sum(1 for r in rows if r.output_status == "unavailable")

    lines = [
        "# Manual Market Data Snapshot Integration Report",
        "",
        "- phase: Phase 6C",
        "- scope: manual market data snapshot integration only",
        f"- input_snapshot: {input_path}",
        f"- upstream_output: {upstream_csv}",
        f"- actual_etf_output: {actual_csv}",
        f"- included_count: {included_count}",
        f"- unavailable_count: {unavailable_count}",
        "",
        "## Integration Rows",
        "",
        "| target_id | output_type | output_id | input_status | output_status | included | warning_flags |",
        "|---|---|---|---|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r.target_id} | {r.output_type} | {r.output_id} | {r.input_status} | {r.output_status} | {r.included} | {r.warning_flags} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- manual snapshot integration only",
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
