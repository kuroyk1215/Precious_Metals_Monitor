from pathlib import Path

from src.reference_signal_engine import (
    build_reference_signal_rows,
    write_reference_signal_csv,
    write_reference_signal_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_reference_signal_allowed_labels_and_action_false():
    deviation_rows = {
        "1540.T": {
            "actual_price": "2914.5",
            "theoretical_price": "2900",
            "deviation_pct": "0.005000",
            "currency": "JPY",
            "deviation_status": "ok",
            "actual_source_status": "manual_mock_data",
            "theoretical_source_status": "ok",
            "warning_flags": "manual_mock_data",
            "notes": "a",
        },
        "1542.T": {
            "actual_price": "440",
            "theoretical_price": "440",
            "deviation_pct": "0.000000",
            "currency": "JPY",
            "deviation_status": "ok",
            "actual_source_status": "manual_mock_data",
            "theoretical_source_status": "ok",
            "warning_flags": "manual_mock_data",
            "notes": "a",
        },
        "518880.SH": {
            "actual_price": "5.0745",
            "theoretical_price": "5.1",
            "deviation_pct": "-0.005000",
            "currency": "CNY",
            "deviation_status": "ok",
            "actual_source_status": "manual_mock_data",
            "theoretical_source_status": "partial",
            "warning_flags": "manual_mock_data;external_proxy",
            "notes": "a",
        },
    }

    rows = build_reference_signal_rows(deviation_rows, TZ)
    by_symbol = {r.etf_symbol: r for r in rows}

    assert by_symbol["1540.T"].reference_label == "overvalued_watch"
    assert by_symbol["1542.T"].reference_label == "no_trade"
    assert by_symbol["518880.SH"].reference_label == "undervalued_watch"

    allowed = {"data_invalid", "no_trade", "undervalued_watch", "overvalued_watch", "risk_off"}
    forbidden_exact_labels = {"buy", "sell", "trade", "order", "rebalance", "建仓", "平仓", "加仓", "减仓", "调仓"}

    for row in rows:
        assert row.reference_label in allowed
        assert row.reference_label not in forbidden_exact_labels
        assert row.action_allowed == "false"


def test_reference_signal_invalid_risk_and_low_quality():
    deviation_rows = {
        "A": {
            "actual_price": "",
            "theoretical_price": "100",
            "deviation_pct": "unavailable",
            "currency": "JPY",
            "deviation_status": "unavailable",
            "actual_source_status": "manual_mock_data",
            "theoretical_source_status": "ok",
            "warning_flags": "manual_mock_data",
            "notes": "invalid actual",
        },
        "B": {
            "actual_price": "100",
            "theoretical_price": "100",
            "deviation_pct": "0.000000",
            "currency": "JPY",
            "deviation_status": "unavailable",
            "actual_source_status": "manual_mock_data",
            "theoretical_source_status": "ok",
            "warning_flags": "currency_mismatch",
            "notes": "currency mismatch",
        },
        "C": {
            "actual_price": "130",
            "theoretical_price": "100",
            "deviation_pct": "0.300000",
            "currency": "JPY",
            "deviation_status": "ok",
            "actual_source_status": "manual_mock_data",
            "theoretical_source_status": "ok",
            "warning_flags": "manual_mock_data",
            "notes": "extreme",
        },
    }

    rows = build_reference_signal_rows(deviation_rows, TZ)
    by_symbol = {r.etf_symbol: r for r in rows}

    assert by_symbol["A"].reference_label == "data_invalid"
    assert by_symbol["B"].reference_label == "risk_off"
    assert by_symbol["C"].reference_label == "risk_off"

    for row in rows:
        assert row.source_quality == "low"
        assert row.confidence == "low"
        assert row.action_allowed == "false"


def test_reference_signal_writers(tmp_path: Path):
    deviation_rows = {
        "1540.T": {
            "actual_price": "2914.5",
            "theoretical_price": "2900",
            "deviation_pct": "0.005000",
            "currency": "JPY",
            "deviation_status": "ok",
            "actual_source_status": "manual_mock_data",
            "theoretical_source_status": "ok",
            "warning_flags": "manual_mock_data",
            "notes": "a",
        },
    }

    rows = build_reference_signal_rows(deviation_rows, TZ)
    csv_path = tmp_path / "reference_signal_snapshot.csv"
    md_path = tmp_path / "reference_signal_report.md"

    write_reference_signal_csv(csv_path, rows)
    write_reference_signal_report(md_path, rows, "deviation_snapshot.csv")

    assert "reference_label" in csv_path.read_text(encoding="utf-8")
    assert "action_allowed" in csv_path.read_text(encoding="utf-8")
    assert "Manual Reference Signal Report" in md_path.read_text(encoding="utf-8")
    assert "action_allowed: false" in md_path.read_text(encoding="utf-8")
