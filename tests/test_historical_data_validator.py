from pathlib import Path

from src.historical_data_validator import validate_historical_csv, normalize_historical_rows, summarize_data_quality


def test_valid_rows_pass_validation():
    result = validate_historical_csv("data/historical_import_template.csv")
    assert len(result["valid_rows"]) == 9


def test_missing_or_non_positive_actual_price_is_invalid(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("date,symbol,actual_price,metal_price_used,fx_used,premium_discount_pct,data_source,notes\n2026-01-01,1540.T,0,2350,155,0.0,template_sample,n\n", encoding="utf-8")
    result = validate_historical_csv(str(p))
    assert len(result["invalid_rows"]) == 1


def test_invalid_date_is_invalid(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("date,symbol,actual_price,metal_price_used,fx_used,premium_discount_pct,data_source,notes\nBAD,1540.T,2900,2350,155,0.0,template_sample,n\n", encoding="utf-8")
    result = validate_historical_csv(str(p))
    assert "invalid_date" in result["invalid_rows"][0]["errors"]


def test_empty_premium_defaults_to_zero():
    result = validate_historical_csv("data/historical_import_template.csv")
    rows = normalize_historical_rows(result["valid_rows"])
    assert any(r["premium_discount_pct"] == 0.0 for r in rows)


def test_duplicate_date_detected():
    rows = [
        {"date": "2026-01-01", "symbol": "1540.T", "actual_price": 1, "metal_price_used": 1, "fx_used": 1, "premium_discount_pct": 0.0, "data_source": "x", "notes": ""},
        {"date": "2026-01-01", "symbol": "1540.T", "actual_price": 1, "metal_price_used": 1, "fx_used": 1, "premium_discount_pct": 0.0, "data_source": "x", "notes": ""},
    ]
    summary = summarize_data_quality(rows, [])[0]
    assert summary["duplicate_date_count"] == 1


def test_insufficient_history_flag():
    rows = [{"date": f"2026-01-{i:02d}", "symbol": "1540.T", "actual_price": 1, "metal_price_used": 1, "fx_used": 1, "premium_discount_pct": 0.0, "data_source": "x", "notes": ""} for i in range(1, 5)]
    summary = summarize_data_quality(rows, [])[0]
    assert "insufficient_history" in summary["warning_flags"]


def test_data_quality_score_deduction():
    rows = [{"date": "2026-01-01", "symbol": "1540.T", "actual_price": 1, "metal_price_used": 1, "fx_used": 1, "premium_discount_pct": 0.0, "data_source": "x", "notes": ""}]
    invalid = [{"symbol": "1540.T", "errors": "missing_actual_price"}]
    summary = summarize_data_quality(rows, invalid)[0]
    assert summary["data_quality_score"] <= 0.8


def test_no_auto_trading_keywords():
    targets = [Path("src/historical_data_validator.py"), Path("src/monitor.py"), Path("main.py")]
    content = "\n".join(p.read_text(encoding="utf-8") for p in targets)
    banned = ["placeOrder", "cancelOrder", "reqOpenOrders", "bracketOrder", "whatIfOrder", "exerciseOptions", "Order(", "自动买入", "自动卖出", "自动调仓", "自动撤单"]
    for token in banned:
        assert token not in content
