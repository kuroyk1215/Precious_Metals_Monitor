from pathlib import Path

from src.calibration_model import calculate_conversion_factor, summarize_conversion_factors


def test_single_row_conversion_factor_formula():
    row = calculate_conversion_factor({"symbol": "1540.T", "date": "2026-01-01", "actual_price": 2900, "metal_price_used": 2350, "fx_used": 155, "premium_discount_pct": 0.001})
    assert row["calibration_status"] == "ok"
    assert round(row["conversion_factor"], 10) == round(2900 / (2350 * 155 * 1.001), 10)


def test_missing_actual_price_returns_missing_required_input():
    row = calculate_conversion_factor({"symbol": "1540.T", "date": "2026-01-01", "actual_price": None, "metal_price_used": 2350, "fx_used": 155, "premium_discount_pct": 0.0})
    assert row["calibration_status"] == "missing_required_input"


def test_insufficient_history_warning():
    rows = [calculate_conversion_factor({"symbol": "1540.T", "date": str(i), "actual_price": 2900 + i, "metal_price_used": 2350, "fx_used": 155, "premium_discount_pct": 0.0}) for i in range(5)]
    summary = summarize_conversion_factors(rows)[0]
    assert "insufficient_history" in summary["warning_flags"]


def test_unstable_conversion_factor_warning():
    vals = [1000, 1500, 700, 1600, 500, 1800, 400, 1900, 350, 2000, 300, 2100, 250, 2200, 200, 2300, 180, 2400, 160, 2500]
    rows = [calculate_conversion_factor({"symbol": "1542.T", "date": str(i), "actual_price": v, "metal_price_used": 10, "fx_used": 10, "premium_discount_pct": 0.0}) for i, v in enumerate(vals)]
    summary = summarize_conversion_factors(rows)[0]
    assert "unstable_conversion_factor" in summary["warning_flags"]


def test_recommended_equals_median():
    rows = [calculate_conversion_factor({"symbol": "518880.SH", "date": str(i), "actual_price": 100+i, "metal_price_used": 10, "fx_used": 10, "premium_discount_pct": 0.0}) for i in range(20)]
    summary = summarize_conversion_factors(rows)[0]
    assert summary["recommended_conversion_factor"] == summary["median_conversion_factor"]


def test_stability_score_bands():
    stable = [calculate_conversion_factor({"symbol": "A", "date": str(i), "actual_price": 1000 + (i % 2), "metal_price_used": 10, "fx_used": 10, "premium_discount_pct": 0.0}) for i in range(20)]
    assert summarize_conversion_factors(stable)[0]["stability_score"] == 0.9
    insufficient = [calculate_conversion_factor({"symbol": "B", "date": str(i), "actual_price": 1000, "metal_price_used": 10, "fx_used": 10, "premium_discount_pct": 0.0}) for i in range(10)]
    assert summarize_conversion_factors(insufficient)[0]["stability_score"] == 0.3


def test_no_auto_trading_keywords():
    targets = [Path("src/calibration_model.py"), Path("src/monitor.py"), Path("main.py")]
    content = "\n".join(p.read_text(encoding="utf-8") for p in targets)
    banned = ["placeOrder", "cancelOrder", "reqOpenOrders", "bracketOrder", "whatIfOrder", "exerciseOptions", "Order(", "自动买入", "自动卖出", "自动调仓", "自动撤单"]
    for token in banned:
        assert token not in content
