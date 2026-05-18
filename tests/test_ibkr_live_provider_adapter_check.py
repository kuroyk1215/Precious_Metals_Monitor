from pathlib import Path

from src.ibkr_live_provider_adapter_check import (
    build_ibkr_live_provider_adapter_check_rows,
    load_ibkr_live_provider_adapter_config,
    write_ibkr_live_provider_adapter_check_csv,
    write_ibkr_live_provider_adapter_check_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_ibkr_adapter_default_config_is_blocked_without_ibkr_provider():
    config = load_ibkr_live_provider_adapter_config("data/market_data_provider_config.yaml")
    rows = build_ibkr_live_provider_adapter_check_rows(config, TZ)

    assert len(rows) == 7

    targets = {row.target_id for row in rows}
    assert "XAUUSD" in targets
    assert "1540.T" in targets
    assert "518880.SH" in targets

    for row in rows:
        assert row.adapter_status == "blocked_provider_disabled"
        assert row.tws_connection_allowed == "false"
        assert row.market_data_request_allowed == "false"
        assert row.historical_data_request_allowed == "false"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_ibkr_connection" in row.warning_flags


def test_ibkr_adapter_blocks_when_provider_missing_entirely():
    config = {"providers": {}, "targets": [{"target_id": "XAUUSD", "target_type": "upstream_factor", "market": "GLOBAL", "data_role": "gold_spot_usd"}]}
    rows = build_ibkr_live_provider_adapter_check_rows(config, TZ)
    row = rows[0]

    assert row.adapter_status == "blocked_provider_not_configured"
    assert row.provider_config_status == "not_configured"
    assert row.block_reason == "ibkr_provider_not_configured"
    assert row.tws_connection_allowed == "false"


def test_ibkr_adapter_blocks_even_when_config_looks_ready():
    config = {
        "providers": {
            "ibkr_readonly_live_provider": {
                "provider_type": "ibkr_readonly_live_adapter",
                "enabled": True,
                "live_request_allowed": True,
                "interface_implemented": True,
                "fallback_provider": "manual_csv",
            }
        },
        "targets": [
            {
                "target_id": "1540.T",
                "target_type": "etf_actual_price",
                "market": "JP",
                "data_role": "jp_gold_etf_actual_price",
            }
        ],
    }

    rows = build_ibkr_live_provider_adapter_check_rows(config, TZ)
    row = rows[0]

    assert row.adapter_status == "blocked_phase10g_skeleton_only"
    assert row.block_reason == "phase10g_does_not_connect_tws_or_request_market_data"
    assert row.tws_connection_allowed == "false"
    assert row.market_data_request_allowed == "false"
    assert row.action_allowed == "false"


def test_ibkr_adapter_writers(tmp_path: Path):
    config = load_ibkr_live_provider_adapter_config("data/market_data_provider_config.yaml")
    rows = build_ibkr_live_provider_adapter_check_rows(config, TZ)

    csv_path = tmp_path / "ibkr_live_provider_adapter_check.csv"
    md_path = tmp_path / "ibkr_live_provider_adapter_check_report.md"

    write_ibkr_live_provider_adapter_check_csv(csv_path, rows)
    write_ibkr_live_provider_adapter_check_report(md_path, rows, "data/market_data_provider_config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "tws_connection_allowed" in csv_text
    assert "market_data_request_allowed" in csv_text
    assert "Phase 10G IBKR Live Provider Adapter Skeleton Report" in md_text
    assert "tws_connection_allowed_count: 0" in md_text
    assert "market_data_request_allowed_count: 0" in md_text
    assert "no IBKR connection" in md_text
    assert "no auto trade" in md_text
