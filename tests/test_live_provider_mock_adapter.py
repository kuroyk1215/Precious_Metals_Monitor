from pathlib import Path

from src.live_provider_mock_adapter import (
    build_live_provider_mock_adapter_rows,
    load_live_provider_mock_adapter_config,
    write_live_provider_mock_adapter_csv,
    write_live_provider_mock_adapter_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_mock_adapter_default_config_outputs_expected_targets():
    config = load_live_provider_mock_adapter_config("data/market_data_provider_config.yaml")
    rows = build_live_provider_mock_adapter_rows(config, TZ)

    assert len(rows) == 7

    by_target = {row.target_id: row for row in rows}

    assert by_target["XAUUSD"].mock_value == "3400.00"
    assert by_target["XAUUSD"].currency == "USD"
    assert by_target["USDJPY"].currency == "JPY"
    assert by_target["1540.T"].mock_value == "36425.0"
    assert by_target["1542.T"].mock_value == "441.75"
    assert by_target["518880.SH"].currency == "CNY"

    for row in rows:
        assert row.provider_type == "mock_live_adapter"
        assert row.data_status == "mock_live_adapter"
        assert row.source_quality == "mock_only"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_api_request" in row.warning_flags


def test_mock_adapter_marks_unknown_target():
    config = {
        "targets": [
            {
                "target_id": "UNKNOWN_TARGET",
                "target_type": "upstream_factor",
                "market": "GLOBAL",
                "data_role": "unknown",
            }
        ]
    }

    rows = build_live_provider_mock_adapter_rows(config, TZ)
    row = rows[0]

    assert row.target_id == "UNKNOWN_TARGET"
    assert row.mock_value == "unavailable"
    assert row.currency == "unavailable"
    assert row.data_status == "mock_missing_target"
    assert row.api_request_allowed == "false"


def test_mock_adapter_writers(tmp_path: Path):
    config = load_live_provider_mock_adapter_config("data/market_data_provider_config.yaml")
    rows = build_live_provider_mock_adapter_rows(config, TZ)

    csv_path = tmp_path / "live_provider_mock_adapter.csv"
    md_path = tmp_path / "live_provider_mock_adapter_report.md"

    write_live_provider_mock_adapter_csv(csv_path, rows)
    write_live_provider_mock_adapter_report(md_path, rows, "data/market_data_provider_config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "mock_value" in csv_text
    assert "mock_live_adapter" in csv_text
    assert "Phase 10C Live Provider Mock Adapter Report" in md_text
    assert "api_request_allowed_count: 0" in md_text
    assert "action_allowed_count: 0" in md_text
    assert "no API request" in md_text
    assert "no auto trade" in md_text
