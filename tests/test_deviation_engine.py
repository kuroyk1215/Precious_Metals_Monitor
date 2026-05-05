from src.deviation_engine import build_deviation_rows


def test_deviation_three_symbols_and_formula():
    theoretical = {
        "1540.T": {"theoretical_price": "2900", "currency": "JPY", "source_status": "ok", "warning_flags": "none", "notes": "t"},
        "1542.T": {"theoretical_price": "440", "currency": "JPY", "source_status": "ok", "warning_flags": "none", "notes": "t"},
        "518880.SH": {"theoretical_price": "5.1", "currency": "CNY", "source_status": "ok", "warning_flags": "external_proxy", "notes": "t"},
    }
    actual = {
        "1540.T": {"actual_price": "2914.5", "currency": "JPY", "source_status": "manual_mock_data", "warning_flags": "manual_mock_data", "notes": "a"},
        "1542.T": {"actual_price": "440", "currency": "JPY", "source_status": "manual_mock_data", "warning_flags": "manual_mock_data", "notes": "a"},
        "518880.SH": {"actual_price": "5.151", "currency": "CNY", "source_status": "manual_mock_data", "warning_flags": "manual_mock_data", "notes": "a"},
    }
    rows = build_deviation_rows(theoretical, actual, {"jst": "Asia/Tokyo", "et": "America/New_York"})
    assert len(rows) == 3
    by_symbol = {r.etf_symbol: r for r in rows}
    assert by_symbol["1540.T"].deviation_pct == "0.005000"
    assert by_symbol["1542.T"].deviation_pct == "0.000000"
    assert by_symbol["518880.SH"].deviation_pct == "0.010000"
    assert "external_proxy" in by_symbol["518880.SH"].warning_flags


def test_unavailable_and_currency_mismatch_and_warning_inherit():
    theoretical = {
        "1540.T": {"theoretical_price": "2900", "currency": "JPY", "source_status": "ok", "warning_flags": "no_realtime_source", "notes": "t"},
        "1542.T": {"theoretical_price": "unavailable", "currency": "JPY", "source_status": "unavailable", "warning_flags": "manual_mock_data", "notes": "t"},
        "518880.SH": {"theoretical_price": "5.2", "currency": "CNY", "source_status": "partial", "warning_flags": "external_proxy", "notes": "t"},
    }
    actual = {
        "1540.T": {"actual_price": "", "currency": "JPY", "source_status": "manual", "warning_flags": "manual_mock_data", "notes": "a"},
        "1542.T": {"actual_price": "441", "currency": "JPY", "source_status": "mock", "warning_flags": "manual_mock_data", "notes": "a"},
        "518880.SH": {"actual_price": "5.2", "currency": "JPY", "source_status": "manual_mock_data", "warning_flags": "manual_mock_data", "notes": "a"},
    }
    rows = build_deviation_rows(theoretical, actual, {"jst": "Asia/Tokyo", "et": "America/New_York"})
    by_symbol = {r.etf_symbol: r for r in rows}
    assert by_symbol["1540.T"].deviation_status == "unavailable"
    assert by_symbol["1542.T"].deviation_status == "unavailable"
    assert by_symbol["518880.SH"].deviation_status == "unavailable"
    assert "currency_mismatch" in by_symbol["518880.SH"].warning_flags
    assert "no_realtime_source" in by_symbol["1540.T"].warning_flags
    assert "manual_mock_data" in by_symbol["1542.T"].warning_flags
    assert "not_realtime_market_data" in by_symbol["1542.T"].warning_flags
