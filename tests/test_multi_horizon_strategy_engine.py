from pathlib import Path

from src.multi_horizon_strategy_engine import (
    build_multi_horizon_strategy_rows,
    write_multi_horizon_strategy_csv,
    write_multi_horizon_strategy_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_multi_horizon_strategy_labels_and_action_false():
    daily_rows = {
        "1540.T": {
            "plan_label": "upper_side_observation",
            "reference_label": "overvalued_watch",
            "deviation_pct": "0.006000",
            "currency": "JPY",
            "confidence": "low",
            "source_quality": "low",
            "warning_flags": "manual_mock_data",
            "notes": "n",
        },
        "1542.T": {
            "plan_label": "neutral_band_observation",
            "reference_label": "no_trade",
            "deviation_pct": "0.000000",
            "currency": "JPY",
            "confidence": "low",
            "source_quality": "low",
            "warning_flags": "manual_mock_data",
            "notes": "n",
        },
        "518880.SH": {
            "plan_label": "lower_side_observation",
            "reference_label": "undervalued_watch",
            "deviation_pct": "-0.006000",
            "currency": "CNY",
            "confidence": "low",
            "source_quality": "low",
            "warning_flags": "external_proxy;manual_mock_data",
            "notes": "n",
        },
    }

    rows = build_multi_horizon_strategy_rows(daily_rows, TZ)
    by_symbol = {r.etf_symbol: r for r in rows}

    assert by_symbol["1540.T"].strategy_label == "upper_side_range_framework"
    assert by_symbol["1542.T"].strategy_label == "neutral_range_framework"
    assert by_symbol["518880.SH"].strategy_label == "lower_side_range_framework"

    for row in rows:
        assert row.action_allowed == "false"
        assert "action_allowed=false" in row.short_term_observation
        assert row.confidence == "low"
        assert row.source_quality == "low"


def test_multi_horizon_strategy_invalid_and_risk_review():
    daily_rows = {
        "A": {
            "plan_label": "data_invalid_no_plan",
            "reference_label": "data_invalid",
            "deviation_pct": "unavailable",
            "currency": "JPY",
            "confidence": "low",
            "source_quality": "low",
            "warning_flags": "manual_mock_data",
            "notes": "invalid",
        },
        "B": {
            "plan_label": "risk_review_only",
            "reference_label": "risk_off",
            "deviation_pct": "0.300000",
            "currency": "JPY",
            "confidence": "low",
            "source_quality": "low",
            "warning_flags": "currency_mismatch",
            "notes": "risk",
        },
    }

    rows = build_multi_horizon_strategy_rows(daily_rows, TZ)
    by_symbol = {r.etf_symbol: r for r in rows}

    assert by_symbol["A"].strategy_label == "no_strategy_data_invalid"
    assert by_symbol["B"].strategy_label == "risk_review_only"
    assert "closed" in by_symbol["B"].risk_close_condition
    assert by_symbol["A"].action_allowed == "false"
    assert by_symbol["B"].action_allowed == "false"


def test_multi_horizon_strategy_review_frequency_by_market():
    daily_rows = {
        "1540.T": {
            "plan_label": "neutral_band_observation",
            "reference_label": "no_trade",
            "deviation_pct": "0.000000",
            "currency": "JPY",
            "confidence": "medium",
            "source_quality": "medium",
            "warning_flags": "none",
        },
        "518880.SH": {
            "plan_label": "neutral_band_observation",
            "reference_label": "no_trade",
            "deviation_pct": "0.000000",
            "currency": "CNY",
            "confidence": "medium",
            "source_quality": "medium",
            "warning_flags": "none",
        },
    }

    rows = build_multi_horizon_strategy_rows(daily_rows, TZ)
    by_symbol = {r.etf_symbol: r for r in rows}

    assert "JST 15:25-15:30" in by_symbol["1540.T"].review_frequency
    assert "CN: daily after A-share close" in by_symbol["518880.SH"].review_frequency


def test_multi_horizon_strategy_writers(tmp_path: Path):
    daily_rows = {
        "1540.T": {
            "plan_label": "neutral_band_observation",
            "reference_label": "no_trade",
            "deviation_pct": "0.000000",
            "currency": "JPY",
            "confidence": "low",
            "source_quality": "low",
            "warning_flags": "manual_mock_data",
            "notes": "n",
        },
    }

    rows = build_multi_horizon_strategy_rows(daily_rows, TZ)
    csv_path = tmp_path / "multi_horizon_strategy_snapshot.csv"
    md_path = tmp_path / "multi_horizon_strategy_report.md"

    write_multi_horizon_strategy_csv(csv_path, rows)
    write_multi_horizon_strategy_report(md_path, rows, "daily_trade_plan_snapshot.csv")

    assert "strategy_label" in csv_path.read_text(encoding="utf-8")
    assert "action_allowed" in csv_path.read_text(encoding="utf-8")
    assert "Multi-Horizon Manual Strategy Report" in md_path.read_text(encoding="utf-8")
    assert "action_allowed=false" in md_path.read_text(encoding="utf-8")
