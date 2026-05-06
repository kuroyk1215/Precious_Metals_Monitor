from pathlib import Path

from src.live_provider_request_gate import (
    REQUEST_TYPES,
    build_live_provider_request_gate_rows,
    load_live_provider_request_gate_config,
    write_live_provider_request_gate_csv,
    write_live_provider_request_gate_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_request_gate_default_config_blocks_everything():
    config = load_live_provider_request_gate_config("data/market_data_provider_config.yaml")
    rows = build_live_provider_request_gate_rows(config, TZ)

    assert rows
    assert len(rows) == 2 * len(REQUEST_TYPES)

    for row in rows:
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_api_request" in row.warning_flags

    statuses = {row.gate_status for row in rows}
    assert "blocked_manual_provider_not_live" in statuses
    assert "blocked_provider_disabled" in statuses
    assert "blocked_trading_request" in statuses


def test_request_gate_blocks_live_even_when_config_looks_ready():
    config = {
        "providers": {
            "future_live": {
                "provider_type": "future_live_adapter",
                "enabled": True,
                "live_request_allowed": True,
                "interface_implemented": True,
                "credential_ref": "dummy_ref",
                "fallback_provider": "manual_csv",
            }
        }
    }

    rows = build_live_provider_request_gate_rows(config, TZ)
    quote_row = [r for r in rows if r.request_type == "quote"][0]

    assert quote_row.gate_status == "blocked_phase10b_dry_run_only"
    assert quote_row.api_request_allowed == "false"
    assert quote_row.action_allowed == "false"
    assert quote_row.block_reason == "phase10b_does_not_permit_real_api_request"


def test_request_gate_blocks_missing_credentials():
    config = {
        "providers": {
            "future_live": {
                "provider_type": "future_live_adapter",
                "enabled": True,
                "live_request_allowed": True,
                "interface_implemented": True,
                "fallback_provider": "manual_csv",
            }
        }
    }

    rows = build_live_provider_request_gate_rows(config, TZ)
    quote_row = [r for r in rows if r.request_type == "quote"][0]

    assert quote_row.gate_status == "blocked_missing_credentials"
    assert quote_row.block_reason == "credential_not_configured"
    assert quote_row.api_request_allowed == "false"


def test_request_gate_writers(tmp_path: Path):
    config = load_live_provider_request_gate_config("data/market_data_provider_config.yaml")
    rows = build_live_provider_request_gate_rows(config, TZ)

    csv_path = tmp_path / "live_provider_request_gate.csv"
    md_path = tmp_path / "live_provider_request_gate_report.md"

    write_live_provider_request_gate_csv(csv_path, rows)
    write_live_provider_request_gate_report(md_path, rows, "data/market_data_provider_config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "gate_status" in csv_text
    assert "api_request_allowed" in csv_text
    assert "Phase 10B Live Provider Request Gate Report" in md_text
    assert "api_request_allowed_count: 0" in md_text
    assert "action_allowed_count: 0" in md_text
    assert "no API request" in md_text
    assert "no auto trade" in md_text
