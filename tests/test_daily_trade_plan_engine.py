from pathlib import Path

from src.daily_trade_plan_engine import (
    build_daily_trade_plan_rows,
    write_daily_trade_plan_csv,
    write_daily_trade_plan_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_daily_trade_plan_labels_and_action_false():
    reference_rows = {
        "1540.T": {
            "reference_label": "overvalued_watch",
            "action_allowed": "false",
            "deviation_pct": "0.006000",
            "currency": "JPY",
            "confidence": "low",
            "source_quality": "low",
            "warning_flags": "manual_mock_data",
            "notes": "n",
        },
        "1542.T": {
            "reference_label": "no_trade",
            "action_allowed": "false",
            "deviation_pct": "0.000000",
            "currency": "JPY",
            "confidence": "low",
            "source_quality": "low",
            "warning_flags": "manual_mock_data",
            "notes": "n",
        },
        "518880.SH": {
            "reference_label": "undervalued_watch",
            "action_allowed": "false",
            "deviation_pct": "-0.006000",
            "currency": "CNY",
            "confidence": "low",
            "source_quality": "low",
            "warning_flags": "external_proxy;manual_mock_data",
            "notes": "n",
        },
    }

    rows = build_daily_trade_plan_rows(reference_rows, TZ)
    by_symbol = {r.etf_symbol: r for r in rows}

    assert by_symbol["1540.T"].plan_label == "upper_side_observation"
    assert by_symbol["1542.T"].plan_label == "neutral_band_observation"
    assert by_symbol["518880.SH"].plan_label == "lower_side_observation"

    for row in rows:
        assert row.action_allowed == "false"
        assert "action_allowed=false" in row.entry_observation or "neutral band" in row.entry_observation or "observation zone" in row.entry_observation
        assert row.confidence == "low"
        assert row.source_quality == "low"


def test_daily_trade_plan_risk_and_invalid_close_plan():
    reference_rows = {
        "A": {
            "reference_label": "data_invalid",
            "action_allowed": "false",
            "deviation_pct": "unavailable",
            "currency": "JPY",
            "confidence": "low",
            "source_quality": "low",
            "warning_flags": "manual_mock_data",
            "notes": "invalid",
        },
        "B": {
            "reference_label": "risk_off",
            "action_allowed": "false",
            "deviation_pct": "0.300000",
            "currency": "JPY",
            "confidence": "low",
            "source_quality": "low",
            "warning_flags": "currency_mismatch",
            "notes": "risk",
        },
    }

    rows = build_daily_trade_plan_rows(reference_rows, TZ)
    by_symbol = {r.etf_symbol: r for r in rows}

    assert by_symbol["A"].plan_label == "data_invalid_no_plan"
    assert by_symbol["A"].risk_close_condition == "keep plan closed until deviation_status and price inputs are valid"

    assert by_symbol["B"].plan_label == "risk_review_only"
    assert "risk" in by_symbol["B"].risk_close_condition
    assert by_symbol["B"].action_allowed == "false"


def test_daily_trade_plan_market_time_triggers():
    reference_rows = {
        "1540.T": {
            "reference_label": "no_trade",
            "deviation_pct": "0.000000",
            "currency": "JPY",
            "confidence": "medium",
            "source_quality": "medium",
            "warning_flags": "none",
        },
        "518880.SH": {
            "reference_label": "no_trade",
            "deviation_pct": "0.000000",
            "currency": "CNY",
            "confidence": "medium",
            "source_quality": "medium",
            "warning_flags": "none",
        },
    }

    rows = build_daily_trade_plan_rows(reference_rows, TZ)
    by_symbol = {r.etf_symbol: r for r in rows}

    assert "JST 15:25-15:30" in by_symbol["1540.T"].time_trigger
    assert "CST 14:50-15:00" in by_symbol["518880.SH"].time_trigger


def test_daily_trade_plan_writers(tmp_path: Path):
    reference_rows = {
        "1540.T": {
            "reference_label": "no_trade",
            "action_allowed": "false",
            "deviation_pct": "0.000000",
            "currency": "JPY",
            "confidence": "low",
            "source_quality": "low",
            "warning_flags": "manual_mock_data",
            "notes": "n",
        },
    }

    rows = build_daily_trade_plan_rows(reference_rows, TZ)
    csv_path = tmp_path / "daily_trade_plan_snapshot.csv"
    md_path = tmp_path / "daily_trade_plan_report.md"

    write_daily_trade_plan_csv(csv_path, rows)
    write_daily_trade_plan_report(md_path, rows, "reference_signal_snapshot.csv")

    assert "plan_label" in csv_path.read_text(encoding="utf-8")
    assert "action_allowed" in csv_path.read_text(encoding="utf-8")
    assert "Daily Manual Trade Plan Report" in md_path.read_text(encoding="utf-8")
    assert "action_allowed=false" in md_path.read_text(encoding="utf-8")
