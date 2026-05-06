from pathlib import Path

from src.market_data_provider_selector import (
    build_market_data_provider_selector_rows,
    load_market_data_provider_selector_config,
    write_market_data_provider_selector_csv,
    write_market_data_provider_selector_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_selector_default_config_selects_manual_csv():
    config = load_market_data_provider_selector_config("data/market_data_provider_config.yaml")
    rows = build_market_data_provider_selector_rows(config, TZ)

    assert rows
    targets = {row.target_id for row in rows}
    assert "1540.T" in targets
    assert "1542.T" in targets
    assert "518880.SH" in targets
    assert "XAUUSD" in targets

    for row in rows:
        assert row.selected_provider == "manual_csv"
        assert row.selection_status == "selected_manual_csv"
        assert row.live_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "live_provider_candidate" in row.blocked_provider


def test_selector_blocks_when_no_safe_provider():
    config = {
        "providers": {
            "manual_csv": {
                "provider_type": "manual_csv_adapter",
                "enabled": False,
                "live_request_allowed": False,
                "fallback_provider": "sample_static",
            },
            "unsafe_live": {
                "provider_type": "future_live_adapter",
                "enabled": True,
                "live_request_allowed": True,
                "fallback_provider": "manual_csv",
            },
        },
        "targets": [
            {
                "target_id": "CUSTOM_XAU",
                "target_type": "upstream_factor",
                "market": "GLOBAL",
                "data_role": "gold_spot_usd",
            }
        ],
    }

    rows = build_market_data_provider_selector_rows(config, TZ)
    row = rows[0]

    assert row.selected_provider == "none"
    assert row.selection_status == "blocked_no_provider"
    assert row.action_allowed == "false"
    assert "unsafe_live" in row.blocked_provider
    assert "live_request_allowed_blocked" in row.blocked_reason


def test_selector_writers(tmp_path: Path):
    config = load_market_data_provider_selector_config("data/market_data_provider_config.yaml")
    rows = build_market_data_provider_selector_rows(config, TZ)

    csv_path = tmp_path / "market_data_provider_selector.csv"
    md_path = tmp_path / "market_data_provider_selector_report.md"

    write_market_data_provider_selector_csv(csv_path, rows)
    write_market_data_provider_selector_report(md_path, rows, "data/market_data_provider_config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "selected_provider" in csv_text
    assert "blocked_reason" in csv_text
    assert "Phase 9D Market Data Provider Selector Report" in md_text
    assert "selected_providers: manual_csv" in md_text
    assert "no API request" in md_text
    assert "no auto trade" in md_text
