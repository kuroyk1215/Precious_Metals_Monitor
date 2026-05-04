from __future__ import annotations

from typing import Any


def _build_result(
    symbol: str,
    model_type: str,
    actual_price: float | None,
    theoretical_price: float | None,
    metal_price_used: float | None,
    fx_used: float | None,
    conversion_factor: float | None,
    premium_discount_pct: float,
    data_confidence_score: float | None,
    pricing_status: str,
    warning_flags: list[str],
) -> dict[str, Any]:
    deviation_pct = None
    computed_flags = list(warning_flags)
    if actual_price is not None and theoretical_price is not None and theoretical_price != 0:
        deviation_pct = ((actual_price - theoretical_price) / theoretical_price) * 100
        if abs(deviation_pct) > 20:
            computed_flags.append("large_model_deviation")
    return {
        "symbol": symbol,
        "model_type": model_type,
        "actual_price": actual_price,
        "theoretical_price": theoretical_price,
        "deviation_pct": deviation_pct,
        "metal_price_used": metal_price_used,
        "fx_used": fx_used,
        "conversion_factor": conversion_factor,
        "premium_discount_pct": premium_discount_pct,
        "data_confidence_score": data_confidence_score,
        "pricing_status": pricing_status,
        "warning_flags": ",".join(computed_flags) if computed_flags else "none",
    }


def calculate_1540_theoretical_price(
    actual_price: float | None,
    xau_usd: float,
    usd_jpy: float,
    conversion_factor: float | None,
    premium_discount_pct: float,
    data_confidence_score: float | None,
) -> dict[str, Any]:
    if conversion_factor is None:
        return _build_result("1540.T", "gold_etf_jp", actual_price, None, xau_usd, usd_jpy, None, premium_discount_pct, data_confidence_score, "missing_conversion_factor", ["missing_conversion_factor"])
    theoretical_price = xau_usd * usd_jpy * conversion_factor * (1 + premium_discount_pct)
    return _build_result("1540.T", "gold_etf_jp", actual_price, theoretical_price, xau_usd, usd_jpy, conversion_factor, premium_discount_pct, data_confidence_score, "ok", [])


def calculate_1542_theoretical_price(
    actual_price: float | None,
    xag_usd: float,
    usd_jpy: float,
    conversion_factor: float | None,
    premium_discount_pct: float,
    data_confidence_score: float | None,
) -> dict[str, Any]:
    if conversion_factor is None:
        return _build_result("1542.T", "silver_etf_jp", actual_price, None, xag_usd, usd_jpy, None, premium_discount_pct, data_confidence_score, "missing_conversion_factor", ["missing_conversion_factor"])
    theoretical_price = xag_usd * usd_jpy * conversion_factor * (1 + premium_discount_pct)
    return _build_result("1542.T", "silver_etf_jp", actual_price, theoretical_price, xag_usd, usd_jpy, conversion_factor, premium_discount_pct, data_confidence_score, "ok", [])


def calculate_518880_theoretical_price(
    actual_price: float | None,
    xau_usd: float,
    usd_cnh: float,
    conversion_factor: float | None,
    premium_discount_pct: float,
    data_confidence_score: float | None,
    external_price_status: str | None = None,
) -> dict[str, Any]:
    if conversion_factor is None:
        return _build_result("518880.SH", "gold_etf_cn", actual_price, None, xau_usd, usd_cnh, None, premium_discount_pct, data_confidence_score, "missing_conversion_factor", ["missing_conversion_factor"])
    theoretical_price = xau_usd * usd_cnh * conversion_factor * (1 + premium_discount_pct)
    flags: list[str] = []
    if actual_price is None and external_price_status:
        flags.append(external_price_status)
    return _build_result("518880.SH", "gold_etf_cn", actual_price, theoretical_price, xau_usd, usd_cnh, conversion_factor, premium_discount_pct, data_confidence_score, "ok", flags)
