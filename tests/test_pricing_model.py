from pathlib import Path

from src.pricing_model import calculate_1540_theoretical_price, calculate_1542_theoretical_price, calculate_518880_theoretical_price


def test_missing_conversion_factor_status():
    row = calculate_1540_theoretical_price(actual_price=100.0, xau_usd=4000.0, usd_jpy=155.0, conversion_factor=None, premium_discount_pct=0.0, data_confidence_score=0.7)
    assert row["pricing_status"] == "missing_conversion_factor"
    assert row["theoretical_price"] is None


def test_actual_price_none_allows_theoretical_price_and_empty_deviation():
    row = calculate_518880_theoretical_price(actual_price=None, xau_usd=4000.0, usd_cnh=7.2, conversion_factor=0.00025, premium_discount_pct=0.0, data_confidence_score=0.4, external_price_status="missing_actual_price")
    assert row["theoretical_price"] == 4000.0 * 7.2 * 0.00025
    assert row["deviation_pct"] is None


def test_formula_1540():
    row = calculate_1540_theoretical_price(actual_price=21893.0, xau_usd=4000.0, usd_jpy=155.0, conversion_factor=0.035, premium_discount_pct=0.0, data_confidence_score=0.7)
    assert row["theoretical_price"] == 4000.0 * 155.0 * 0.035


def test_formula_1542():
    row = calculate_1542_theoretical_price(actual_price=34935.0, xag_usd=48.0, usd_jpy=155.0, conversion_factor=470.0, premium_discount_pct=0.0, data_confidence_score=0.7)
    assert row["theoretical_price"] == 48.0 * 155.0 * 470.0


def test_formula_518880():
    row = calculate_518880_theoretical_price(actual_price=None, xau_usd=4000.0, usd_cnh=7.2, conversion_factor=0.00025, premium_discount_pct=0.0, data_confidence_score=0.4)
    assert row["theoretical_price"] == 4000.0 * 7.2 * 0.00025


def test_no_auto_trading_keywords():
    targets = [Path("src/pricing_model.py"), Path("main.py"), Path("README.md"), Path("config.yaml"), Path("watchlist.yaml")]
    content = "\n".join(p.read_text(encoding="utf-8") for p in targets)
    banned = ["placeOrder", "cancelOrder", "reqOpenOrders", "bracketOrder", "whatIfOrder", "exerciseOptions", "Order("]
    for token in banned:
        assert token not in content
