from pathlib import Path

from src.manual_market_data_review_pack import (
    build_manual_market_data_review_pack_rows,
    load_csv_by_key,
    write_manual_market_data_review_pack_csv,
    write_manual_market_data_review_pack_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_build_manual_market_data_review_pack_rows():
    actual = {
        "1540.T": {
            "actual_price": "36425.0",
            "currency": "JPY",
            "warning_flags": "manual_csv",
            "notes": "actual",
        }
    }
    theoretical = {
        "1540.T": {
            "theoretical_price": "36425.000000",
            "currency": "JPY",
            "warning_flags": "none",
            "notes": "theoretical",
        }
    }
    deviation = {
        "1540.T": {
            "deviation_pct": "0.000000",
            "currency": "JPY",
            "warning_flags": "none",
            "notes": "deviation",
        }
    }
    reference = {
        "1540.T": {
            "reference_label": "no_trade",
            "action_allowed": "false",
            "confidence": "medium",
            "source_quality": "medium",
            "risk_flag": "none",
            "warning_flags": "none",
        }
    }
    daily = {
        "1540.T": {
            "plan_label": "neutral_band_observation",
            "action_allowed": "false",
            "confidence": "medium",
            "source_quality": "medium",
            "risk_flag": "none",
            "warning_flags": "none",
        }
    }
    strategy = {
        "1540.T": {
            "strategy_label": "neutral_range_framework",
            "action_allowed": "false",
            "confidence": "medium",
            "source_quality": "medium",
            "warning_flags": "none",
        }
    }

    rows = build_manual_market_data_review_pack_rows(
        actual,
        theoretical,
        deviation,
        reference,
        daily,
        strategy,
        TZ,
    )

    assert len(rows) == 1
    row = rows[0]
    assert row.etf_symbol == "1540.T"
    assert row.actual_price == "36425.0"
    assert row.theoretical_price == "36425.000000"
    assert row.deviation_pct == "0.000000"
    assert row.reference_label == "no_trade"
    assert row.daily_plan_label == "neutral_band_observation"
    assert row.strategy_label == "neutral_range_framework"
    assert row.action_allowed == "false"
    assert "action_allowed=false" in row.review_summary
    assert "manual_review_pack" in row.warning_flags


def test_load_csv_by_key(tmp_path: Path):
    p = tmp_path / "rows.csv"
    p.write_text("etf_symbol,value\n1540.T,1\n1542.T,2\n", encoding="utf-8")

    rows = load_csv_by_key(str(p), "etf_symbol")
    assert rows["1540.T"]["value"] == "1"
    assert rows["1542.T"]["value"] == "2"


def test_manual_market_data_review_pack_writers(tmp_path: Path):
    rows = build_manual_market_data_review_pack_rows(
        {"1540.T": {"actual_price": "1", "currency": "JPY"}},
        {"1540.T": {"theoretical_price": "1", "currency": "JPY"}},
        {"1540.T": {"deviation_pct": "0.000000", "currency": "JPY"}},
        {"1540.T": {"reference_label": "no_trade", "action_allowed": "false"}},
        {"1540.T": {"plan_label": "neutral_band_observation", "action_allowed": "false"}},
        {"1540.T": {"strategy_label": "neutral_range_framework", "action_allowed": "false"}},
        TZ,
    )

    csv_path = tmp_path / "manual_market_data_review_pack.csv"
    md_path = tmp_path / "manual_market_data_review_pack_report.md"

    write_manual_market_data_review_pack_csv(csv_path, rows)
    write_manual_market_data_review_pack_report(md_path, rows, "data/manual_market_data_sample_valid.csv")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "review_summary" in csv_text
    assert "Manual CSV Pipeline Output Review Pack" in md_text
    assert "action_allowed=false" in md_text
    assert "no IBKR connection" in md_text
