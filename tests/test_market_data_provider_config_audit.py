from pathlib import Path

from src.market_data_provider_config_audit import (
    build_market_data_provider_config_audit_rows,
    load_market_data_provider_config,
    write_market_data_provider_config_audit_csv,
    write_market_data_provider_config_audit_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_provider_config_audit_default_file_loads():
    config = load_market_data_provider_config("data/market_data_provider_config.yaml")
    rows = build_market_data_provider_config_audit_rows(config, TZ)

    by_provider = {r.provider_id: r for r in rows}

    assert "manual_csv" in by_provider
    assert "live_provider_candidate" in by_provider
    assert by_provider["manual_csv"].config_status == "manual_config_ready"
    assert by_provider["manual_csv"].live_request_allowed == "false"
    assert by_provider["live_provider_candidate"].config_status == "disabled_safe_until_explicit_enable"
    assert by_provider["live_provider_candidate"].enabled == "false"
    assert by_provider["live_provider_candidate"].action_allowed == "false"


def test_provider_config_audit_blocks_live_request_enabled():
    config = {
        "providers": {
            "unsafe_live": {
                "provider_type": "future_live_adapter",
                "enabled": True,
                "live_request_allowed": True,
                "fallback_provider": "manual_csv",
                "source_quality_floor": "live",
                "requires_explicit_enable_switch": True,
                "notes": "unsafe test",
            }
        }
    }

    rows = build_market_data_provider_config_audit_rows(config, TZ)
    row = rows[0]

    assert row.config_status == "blocked_live_request_enabled"
    assert row.live_request_allowed == "true"
    assert row.action_allowed == "false"
    assert "live_request_enabled_blocked" in row.warning_flags


def test_provider_config_audit_writers(tmp_path: Path):
    config = load_market_data_provider_config("data/market_data_provider_config.yaml")
    rows = build_market_data_provider_config_audit_rows(config, TZ)

    csv_path = tmp_path / "market_data_provider_config_audit.csv"
    md_path = tmp_path / "market_data_provider_config_audit_report.md"

    write_market_data_provider_config_audit_csv(csv_path, rows)
    write_market_data_provider_config_audit_report(md_path, rows, "data/market_data_provider_config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "config_status" in csv_text
    assert "Phase 9B Market Data Provider Config Audit Report" in md_text
    assert "live_request_allowed_count: 0" in md_text
    assert "no API request" in md_text
    assert "no auto trade" in md_text
