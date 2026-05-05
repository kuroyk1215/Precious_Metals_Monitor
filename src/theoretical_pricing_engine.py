from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo
import csv

from src.pricing_model import (
    calculate_1540_theoretical_price,
    calculate_1542_theoretical_price,
    calculate_518880_theoretical_price,
)


@dataclass
class TheoreticalPriceRow:
    etf_symbol: str
    theoretical_price: str
    currency: str
    pricing_status: str
    metal_factor: str
    metal_value: str
    fx_factor: str
    fx_value: str
    conversion_factor: str
    source_status: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


def _parse_float(value: str) -> Optional[float]:
    if value in (None, "", "unavailable"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_upstream_snapshot(path: str) -> dict[str, dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {str(r["factor"]): {k: str(v) for k, v in r.items()} for r in rows}


def build_theoretical_price_rows(
    snapshot: dict[str, dict[str, str]],
    tz_cfg: dict[str, str],
    conversion_factors: dict[str, float],
) -> list[TheoreticalPriceRow]:
    now_utc = datetime.now(timezone.utc)
    timestamp_jst = now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat()
    timestamp_et = now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat()

    def factor_value(name: str) -> Optional[float]:
        return _parse_float(snapshot.get(name, {}).get("value", "unavailable"))

    def factor_status(name: str) -> str:
        return snapshot.get(name, {}).get("source_status", "unavailable")

    def factor_warning(name: str) -> str:
        return snapshot.get(name, {}).get("warning_flags", "none")

    rows: list[TheoreticalPriceRow] = []

    # 1540.T
    xau, jpy = factor_value("XAUUSD"), factor_value("USDJPY")
    cf_1540 = conversion_factors.get("1540.T")
    warnings_1540 = [w for w in [factor_warning("XAUUSD"), factor_warning("USDJPY")] if w and w != "none"]
    if xau is None or jpy is None:
        status_1540, theo_1540, notes_1540 = "unavailable", "unavailable", "Missing key factor XAUUSD and/or USDJPY"
    elif cf_1540 is None:
        status_1540, theo_1540, notes_1540 = "partial", "unavailable", "Missing conversion_factor for 1540.T"
        warnings_1540.append("missing_conversion_factor")
    else:
        result = calculate_1540_theoretical_price(None, xau, jpy, cf_1540, 0.0, None)
        status_1540 = "ok" if result["pricing_status"] == "ok" else "partial"
        theo_1540 = f"{result['theoretical_price']:.6f}" if result["theoretical_price"] is not None else "unavailable"
        notes_1540 = "theoretical price based on upstream factors"
    rows.append(TheoreticalPriceRow("1540.T", theo_1540, "JPY", status_1540, "XAUUSD", str(xau) if xau is not None else "unavailable", "USDJPY", str(jpy) if jpy is not None else "unavailable", str(cf_1540) if cf_1540 is not None else "unavailable", "ok" if status_1540 == "ok" else "partial", ";".join(sorted(set(warnings_1540))) if warnings_1540 else "none", notes_1540, timestamp_jst, timestamp_et))

    # 1542.T
    xag = factor_value("XAGUSD")
    cf_1542 = conversion_factors.get("1542.T")
    warnings_1542 = [w for w in [factor_warning("XAGUSD"), factor_warning("USDJPY")] if w and w != "none"]
    if xag is None or jpy is None:
        status_1542, theo_1542, notes_1542 = "unavailable", "unavailable", "Missing key factor XAGUSD and/or USDJPY"
    elif cf_1542 is None:
        status_1542, theo_1542, notes_1542 = "partial", "unavailable", "Missing conversion_factor for 1542.T"
        warnings_1542.append("missing_conversion_factor")
    else:
        result = calculate_1542_theoretical_price(None, xag, jpy, cf_1542, 0.0, None)
        status_1542 = "ok" if result["pricing_status"] == "ok" else "partial"
        theo_1542 = f"{result['theoretical_price']:.6f}" if result["theoretical_price"] is not None else "unavailable"
        notes_1542 = "theoretical price based on upstream factors"
    rows.append(TheoreticalPriceRow("1542.T", theo_1542, "JPY", status_1542, "XAGUSD", str(xag) if xag is not None else "unavailable", "USDJPY", str(jpy) if jpy is not None else "unavailable", str(cf_1542) if cf_1542 is not None else "unavailable", "ok" if status_1542 == "ok" else "partial", ";".join(sorted(set(warnings_1542))) if warnings_1542 else "none", notes_1542, timestamp_jst, timestamp_et))

    # 518880.SH
    sge, usdcny = factor_value("SGE_AU99_99"), factor_value("USDCNY")
    cf_cn = conversion_factors.get("518880.SH", 0.001)
    warnings_cn = []
    if factor_warning("SGE_AU99_99") != "none":
        warnings_cn.append(factor_warning("SGE_AU99_99"))

    metal_factor, fx_factor = "SGE_AU99_99", "none"
    metal_val, fx_val = sge, None
    notes_cn = "using domestic SGE factor"

    if sge is None:
        xau_cn = factor_value("XAUUSD")
        if xau_cn is not None and usdcny is not None:
            metal_factor, fx_factor = "XAUUSD", "USDCNY"
            metal_val, fx_val = xau_cn, usdcny
            warnings_cn.append("sge_unavailable_external_proxy")
            notes_cn = "SGE unavailable; use external proxy XAUUSD*USDCNY"
        else:
            rows.append(TheoreticalPriceRow("518880.SH", "unavailable", "CNY", "unavailable", "SGE_AU99_99", "unavailable", "none", "unavailable", str(cf_cn), "unavailable", ";".join(sorted(set(warnings_cn))) if warnings_cn else "none", "Missing SGE and external proxy factors", timestamp_jst, timestamp_et))
            return rows

    if fx_factor == "none":
        theo_cn = metal_val * cf_cn if metal_val is not None else None
    else:
        result = calculate_518880_theoretical_price(None, metal_val, fx_val, cf_cn, 0.0, None, external_price_status="external_proxy")
        theo_cn = result["theoretical_price"]

    rows.append(TheoreticalPriceRow("518880.SH", f"{theo_cn:.6f}" if theo_cn is not None else "unavailable", "CNY", "ok" if theo_cn is not None else "unavailable", metal_factor, str(metal_val) if metal_val is not None else "unavailable", fx_factor, str(fx_val) if fx_val is not None else "unavailable", str(cf_cn), "ok" if theo_cn is not None else "unavailable", ";".join(sorted(set(warnings_cn))) if warnings_cn else "none", notes_cn, timestamp_jst, timestamp_et))

    return rows


def write_theoretical_price_csv(path: Path, rows: list[TheoreticalPriceRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["etf_symbol", "theoretical_price", "currency", "pricing_status", "metal_factor", "metal_value", "fx_factor", "fx_value", "conversion_factor", "source_status", "warning_flags", "notes", "timestamp_jst", "timestamp_et"])
        for r in rows:
            writer.writerow([r.etf_symbol, r.theoretical_price, r.currency, r.pricing_status, r.metal_factor, r.metal_value, r.fx_factor, r.fx_value, r.conversion_factor, r.source_status, r.warning_flags, r.notes, r.timestamp_jst, r.timestamp_et])


def write_theoretical_price_report(path: Path, rows: list[TheoreticalPriceRow], input_snapshot_path: str, cst_time: str) -> None:
    lines = [
        "# ETF Theoretical Pricing Report",
        "",
        f"- input_upstream_snapshot: {input_snapshot_path}",
        f"- current_time_jst: {rows[0].timestamp_jst if rows else 'n/a'}",
        f"- current_time_cst: {cst_time}",
        f"- current_time_et: {rows[0].timestamp_et if rows else 'n/a'}",
        "",
        "| etf_symbol | theoretical_price | currency | pricing_status | metal_factor | metal_value | fx_factor | fx_value | conversion_factor | warning_flags | notes |",
        "|---|---:|---|---|---|---:|---|---:|---:|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r.etf_symbol} | {r.theoretical_price} | {r.currency} | {r.pricing_status} | {r.metal_factor} | {r.metal_value} | {r.fx_factor} | {r.fx_value} | {r.conversion_factor} | {r.warning_flags} | {r.notes} |")

    lines.extend([
        "",
        "## Notes",
        "- 518880.SH prefers SGE_AU99_99; external proxy is clearly labeled when used.",
        "- unavailable / partial entries are not force-calculated.",
        "- Phase 5D will compute actual ETF price vs theoretical price deviation.",
        "",
        "## Safety Statement",
        "- research-only",
        "- no trading",
        "- no order",
        "- no IBKR connection",
        "- no reqHistoricalData",
        "- no auto calibration",
        "- no auto pipeline chaining",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
