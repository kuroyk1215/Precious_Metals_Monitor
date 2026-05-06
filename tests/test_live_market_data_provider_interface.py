from pathlib import Path

from src.live_market_data_provider_interface import (
    build_live_provider_interface_check_rows,
    load_live_provider_interface_config,
    write_live_provider_interface_check_csv,
    write_live_provider_interface_check_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_live_provider_interface_default_config_blocks_all_requests():
    config = load_live_provider_interface_config("data/market_data_provider_config.yaml")
    rows = build_live_provider_interface_check_rows(config, TZ)

    assert rows
    by_provider = {row.provider_id: row for row in rows}

    assert "manual_csv" in by_provider
    assert "live_provider_candidate" in by_provider

    for row in rows:
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_api_request" in row.warning_flags

    assert by_provider["manual_csv"].interface_status == "manual_provider_not_live_interface"
    assert by_provider["live_provider_candidate"].interface_status == "blocked_provider_disabled"


def test_live_provider_interface_blocks_even_if_live_request_enabled():
    config = {
        "providers": {
            "unsafe_live": {
                "provider_type": "future_live_adapter",
                "enabled": True,
                "live_request_allowed": True,
                "interface_implemented": True,
                "fallback_provider": "manual_csv",
                "notes": "unsafe test",
            }
        }
    }

    rows = build_live_provider_interface_check_rows(config, TZ)
    row = rows[0]

    assert row.provider_id == "unsafe_live"
    assert row.interface_status == "blocked_live_request_enabled"
    assert row.api_request_allowed == "false"
    assert row.action_allowed == "false"
    assert row.block_reason == "live_request_allowed_true_is_not_allowed_in_phase10a"


def test_live_provider_interface_blocks_not_implemented_provider():
    config = {
        "providers": {
            "future_live": {
                "provider_type": "future_live_adapter",
                "enabled": True,
                "live_request_allowed": False,
                "interface_implemented": False,
                "fallback_provider": "manual_csv",
            }
        }
    }

    rows = build_live_provider_interface_check_rows(config, TZ)
    row = rows[0]

    assert row.interface_status == "blocked_interface_not_implemented"
    assert row.block_reason == "interface_not_implemented"
    assert row.api_request_allowed == "false"


def test_live_provider_interface_writers(tmp_path: Path):
    config = load_live_provider_interface_config("data/market_data_provider_config.yaml")
    rows = build_live_provider_interface_check_rows(config, TZ)

    csv_path = tmp_path / "live_provider_interface_check.csv"
    md_path = tmp_path / "live_provider_interface_check_report.md"

    write_live_provider_interface_check_csv(csv_path, rows)
    write_live_provider_interface_check_report(md_path, rows, "data/market_data_provider_config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "api_request_allowed" in csv_text
    assert "interface_status" in csv_text
    assert "Phase 10A Live Provider Interface Safety Check Report" in md_text
    assert "api_request_allowed_count: 0" in md_text
    assert "no API request" in md_text
    assert "no auto trade" in md_text
