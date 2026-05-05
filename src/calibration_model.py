from __future__ import annotations

from typing import Any, Optional
import statistics


def _to_float(v: Any) ->Optional[float]:
    if v is None or v == "":
        return None
    return float(v)


def calculate_conversion_factor(row: dict[str, Any]) -> dict[str, Any]:
    actual_price = _to_float(row.get("actual_price"))
    metal_price_used = _to_float(row.get("metal_price_used"))
    fx_used = _to_float(row.get("fx_used"))
    premium_discount_pct = _to_float(row.get("premium_discount_pct")) or 0.0
    if actual_price is None or metal_price_used is None or fx_used is None:
        return {**row, "conversion_factor": None, "calibration_status": "missing_required_input"}

    denominator = metal_price_used * fx_used * (1 + premium_discount_pct)
    if denominator == 0:
        return {**row, "conversion_factor": None, "calibration_status": "missing_required_input"}
    return {**row, "conversion_factor": actual_price / denominator, "calibration_status": "ok"}


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def summarize_conversion_factors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row.get("symbol", "UNKNOWN"), []).append(row)

    out: list[dict[str, Any]] = []
    for symbol, items in grouped.items():
        valid = [float(r["conversion_factor"]) for r in items if r.get("conversion_factor") is not None and r.get("calibration_status") == "ok"]
        missing_count = len(items) - len(valid)
        warning_flags: list[str] = []

        if not valid:
            out.append({
                "symbol": symbol,
                "observation_count": 0,
                "mean_conversion_factor": None,
                "median_conversion_factor": None,
                "std_conversion_factor": None,
                "min_conversion_factor": None,
                "max_conversion_factor": None,
                "p10_conversion_factor": None,
                "p90_conversion_factor": None,
                "latest_conversion_factor": None,
                "stability_score": 0.3,
                "recommended_conversion_factor": None,
                "calibration_status": "missing_required_input",
                "warning_flags": "missing_data_risk,insufficient_history",
            })
            continue

        mean_v = statistics.fmean(valid)
        median_v = statistics.median(valid)
        std_v = statistics.pstdev(valid) if len(valid) > 1 else 0.0
        min_v = min(valid)
        max_v = max(valid)
        p10_v = _percentile(valid, 0.1)
        p90_v = _percentile(valid, 0.9)
        latest_v = next((r.get("conversion_factor") for r in reversed(items) if r.get("conversion_factor") is not None), None)

        if len(valid) < 20:
            warning_flags.append("insufficient_history")

        ratio = std_v / median_v if median_v else 999.0
        if ratio > 0.05:
            warning_flags.append("unstable_conversion_factor")

        if missing_count / len(items) > 0.2:
            warning_flags.append("missing_data_risk")

        if len(valid) < 20:
            stability_score = 0.3
        elif ratio <= 0.01:
            stability_score = 0.9
        elif ratio <= 0.03:
            stability_score = 0.75
        elif ratio <= 0.05:
            stability_score = 0.6
        else:
            stability_score = 0.4

        out.append({
            "symbol": symbol,
            "observation_count": len(valid),
            "mean_conversion_factor": mean_v,
            "median_conversion_factor": median_v,
            "std_conversion_factor": std_v,
            "min_conversion_factor": min_v,
            "max_conversion_factor": max_v,
            "p10_conversion_factor": p10_v,
            "p90_conversion_factor": p90_v,
            "latest_conversion_factor": latest_v,
            "stability_score": stability_score,
            "recommended_conversion_factor": median_v,
            "calibration_status": "ok",
            "warning_flags": ",".join(warning_flags) if warning_flags else "none",
        })
    return out
