from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo
import csv


@dataclass
class ActualEtfPriceRow:
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
class DeviationRow:
    etf_symbol: str
    actual_price: str
    theoretical_price: str
    deviation_pct: str
    currency: str
    deviation_status: str
    actual_source_status: str
    theoretical_source_status: str
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


def _parse_float(value: str) -> Optional[float]:
    if value in (None, "", "unavailable"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _split_flags(flags: str) -> set[str]:
    if not flags or flags == "none":
        return set()
    return {f.strip() for f in flags.split(";") if f.strip()}


def build_manual_actual_price_rows(tz_cfg: dict[str, str]) -> list[ActualEtfPriceRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    return [
        ActualEtfPriceRow("1540.T", "2912.5", "JPY", "manual_mock_provider", "manual_mock_data", ts_jst, ts_et, "manual_mock_data", "manual/mock placeholder only, not real-time market data"),
        ActualEtfPriceRow("1542.T", "441.8", "JPY", "manual_mock_provider", "manual_mock_data", ts_jst, ts_et, "manual_mock_data", "manual/mock placeholder only, not real-time market data"),
        ActualEtfPriceRow("518880.SH", "5.135", "CNY", "manual_mock_provider", "manual_mock_data", ts_jst, ts_et, "manual_mock_data", "manual/mock placeholder only, not real-time market data"),
    ]


def load_snapshot_by_symbol(path: str, key_field: str) -> dict[str, dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {str(r[key_field]): {k: str(v) for k, v in r.items()} for r in rows}


def build_deviation_rows(theoretical: dict[str, dict[str, str]], actual: dict[str, dict[str, str]], tz_cfg: dict[str, str]) -> list[DeviationRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    symbols = sorted(set(theoretical.keys()) | set(actual.keys()))
    rows: list[DeviationRow] = []

    for symbol in symbols:
        t = theoretical.get(symbol, {})
        a = actual.get(symbol, {})
        theo_price = t.get("theoretical_price", "unavailable")
        actual_price = a.get("actual_price", "unavailable")
        theo_currency = t.get("currency", "")
        actual_currency = a.get("currency", "")
        currency = actual_currency or theo_currency or "unavailable"

        theo_val = _parse_float(theo_price)
        actual_val = _parse_float(actual_price)

        flags = set()
        flags |= _split_flags(t.get("warning_flags", "none"))
        flags |= _split_flags(a.get("warning_flags", "none"))

        actual_status = a.get("source_status", "unavailable")
        theoretical_status = t.get("source_status", t.get("pricing_status", "unavailable"))

        if actual_status in {"manual", "mock", "manual_mock_data"}:
            flags.add("manual_mock_data")
        if actual_status.startswith("manual") or actual_status.startswith("mock"):
            flags.add("not_realtime_market_data")

        notes = []
        if a.get("notes"):
            notes.append(a["notes"])
        if t.get("notes"):
            notes.append(t["notes"])

        status = "ok"
        deviation_pct = "unavailable"
        if actual_val is None or actual_val <= 0:
            status = "unavailable"
            notes.append("actual_price unavailable/invalid")
        if theo_val is None or theo_val <= 0:
            status = "unavailable"
            notes.append("theoretical_price unavailable/invalid")
        if actual_currency and theo_currency and actual_currency != theo_currency:
            status = "unavailable"
            flags.add("currency_mismatch")
            notes.append("currency mismatch between actual and theoretical")

        if status != "unavailable":
            deviation_pct = f"{((actual_val / theo_val) - 1):.6f}"

        rows.append(
            DeviationRow(
                etf_symbol=symbol,
                actual_price=actual_price,
                theoretical_price=theo_price,
                deviation_pct=deviation_pct,
                currency=currency,
                deviation_status=status,
                actual_source_status=actual_status,
                theoretical_source_status=theoretical_status,
                warning_flags=";".join(sorted(flags)) if flags else "none",
                notes="; ".join(notes) if notes else "none",
                timestamp_jst=a.get("timestamp_jst", t.get("timestamp_jst", ts_jst)),
                timestamp_et=a.get("timestamp_et", t.get("timestamp_et", ts_et)),
            )
        )

    return rows


def write_actual_price_csv(path: Path, rows: list[ActualEtfPriceRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["etf_symbol", "actual_price", "currency", "source", "source_status", "timestamp_jst", "timestamp_et", "warning_flags", "notes"])
        for r in rows:
            writer.writerow([r.etf_symbol, r.actual_price, r.currency, r.source, r.source_status, r.timestamp_jst, r.timestamp_et, r.warning_flags, r.notes])


def write_actual_price_report(path: Path, rows: list[ActualEtfPriceRow]) -> None:
    lines = [
        "# Actual ETF Price Snapshot (Manual/Mock)",
        "",
        "manual/mock only; not real-time market data.",
        "",
        "| etf_symbol | actual_price | currency | source | source_status | warning_flags | notes |",
        "|---|---:|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r.etf_symbol} | {r.actual_price} | {r.currency} | {r.source} | {r.source_status} | {r.warning_flags} | {r.notes} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_deviation_csv(path: Path, rows: list[DeviationRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["etf_symbol", "actual_price", "theoretical_price", "deviation_pct", "currency", "deviation_status", "actual_source_status", "theoretical_source_status", "warning_flags", "notes", "timestamp_jst", "timestamp_et"])
        for r in rows:
            writer.writerow([r.etf_symbol, r.actual_price, r.theoretical_price, r.deviation_pct, r.currency, r.deviation_status, r.actual_source_status, r.theoretical_source_status, r.warning_flags, r.notes, r.timestamp_jst, r.timestamp_et])


def write_deviation_report(path: Path, rows: list[DeviationRow], theoretical_path: str, actual_path: str) -> None:
    lines = [
        "# ETF Actual vs Theoretical Deviation Report",
        "",
        f"- theoretical_input: {theoretical_path}",
        f"- actual_input: {actual_path}",
        "- no buy/sell/trade action in this phase",
        "",
        "| etf_symbol | actual_price | theoretical_price | deviation_pct | currency | deviation_status | warning_flags |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r.etf_symbol} | {r.actual_price} | {r.theoretical_price} | {r.deviation_pct} | {r.currency} | {r.deviation_status} | {r.warning_flags} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
