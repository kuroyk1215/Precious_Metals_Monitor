from pathlib import Path

from src.market_data_provider_readiness import (
    build_market_data_provider_readiness_rows,
    write_market_data_provider_readiness_csv,
    write_market_data_provider_readiness_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_provider_readiness_rows_include_manual_and_disabled_live():
    rows = build_market_data_provider_readiness_rows(TZ)

    assert rows
    by_provider = {r.provider_id for r in rows}
    targets = {r.target_id for r in rows}

    assert "manual_csv" in by_provider
    assert "live_provider_candidate" in by_provider
    assert "1540.T" in targets
    assert "1542.T" in targets
    assert "518880.SH" in targets
    assert "XAUUSD" in targets

    live_rows = [r for r in rows if r.provider_id == "live_provider_candidate"]
    assert live_rows
    for row in live_rows:
        assert row.provider_enabled == "false"
        assert row.live_request_allowed == "false"
        assert row.action_allowed == "false"
        assert row.readiness_status == "disabled_until_explicit_config"
        assert "no_api_request" in row.warning_flags


def test_provider_readiness_manual_rows_are_safe_primary():
    rows = build_market_data_provider_readiness_rows(TZ)
    manual_rows = [r for r in rows if r.provider_id == "manual_csv"]

    assert manual_rows
    for row in manual_rows:
        assert row.provider_enabled == "true"
        assert row.readiness_status == "manual_ready"
        assert row.live_request_allowed == "false"
        assert row.action_allowed == "false"
        assert row.fallback_provider == "sample_static"


def test_provider_readiness_writers(tmp_path: Path):
    rows = build_market_data_provider_readiness_rows(TZ)
    csv_path = tmp_path / "market_data_provider_readiness.csv"
    md_path = tmp_path / "market_data_provider_readiness_report.md"

    write_market_data_provider_readiness_csv(csv_path, rows)
    write_market_data_provider_readiness_report(md_path, rows)

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "provider_enabled" in csv_text
    assert "live_request_allowed" in csv_text
    assert "Phase 9C Config-Driven Market Data Provider Readiness Report" in md_text
    assert "live_provider_enabled_count: 0" in md_text
    assert "no API request" in md_text
    assert "no auto trade" in md_text


def test_provider_readiness_uses_external_provider_config():
    custom_config = {
        "providers": {
            "manual_csv": {
                "provider_type": "manual_csv_adapter",
                "enabled": True,
                "live_request_allowed": False,
                "fallback_provider": "sample_static",
                "source_quality_floor": "manual_or_sample",
                "requires_explicit_enable_switch": False,
                "notes": "manual",
            },
            "disabled_vendor": {
                "provider_type": "future_live_adapter",
                "enabled": False,
                "live_request_allowed": False,
                "fallback_provider": "manual_csv",
                "source_quality_floor": "unavailable_until_enabled",
                "requires_explicit_enable_switch": True,
                "notes": "disabled",
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

    rows = build_market_data_provider_readiness_rows(TZ, custom_config)
    by_provider = {r.provider_id: r for r in rows}

    assert set(by_provider.keys()) == {"manual_csv", "disabled_vendor"}
    assert by_provider["manual_csv"].target_id == "CUSTOM_XAU"
    assert by_provider["manual_csv"].readiness_status == "manual_ready"
    assert by_provider["disabled_vendor"].readiness_status == "disabled_until_explicit_config"
    assert by_provider["disabled_vendor"].live_request_allowed == "false"
    assert by_provider["disabled_vendor"].action_allowed == "false"
    assert "phase9c_config_driven_readiness" in by_provider["disabled_vendor"].warning_flags
