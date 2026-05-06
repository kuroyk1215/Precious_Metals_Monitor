from pathlib import Path

from src.market_data_adapter_interface import (
    NoopMarketDataAdapter,
    build_default_adapter_request,
    build_market_data_adapter_contract_rows,
    validate_adapter_request_safety,
    write_market_data_adapter_contract_csv,
    write_market_data_adapter_contract_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_default_adapter_request_is_safe():
    request = build_default_adapter_request("manual_csv", "XAUUSD")
    violations = validate_adapter_request_safety(request)

    assert violations == []
    assert request.allow_network is False
    assert request.allow_broker_connection is False
    assert request.allow_trading is False


def test_adapter_request_safety_detects_violations():
    request = build_default_adapter_request("ibkr_readonly", "1540.T")
    request.allow_network = True
    request.allow_broker_connection = True
    request.allow_trading = True
    request.requested_mode = "trade"

    violations = validate_adapter_request_safety(request)

    assert "allow_network_must_be_false" in violations
    assert "allow_broker_connection_must_be_false" in violations
    assert "allow_trading_must_be_false" in violations
    assert "requested_mode_invalid" in violations


def test_noop_adapter_returns_not_implemented_without_connection():
    request = build_default_adapter_request("external_fx_provider", "USDJPY")
    adapter = NoopMarketDataAdapter(TZ)

    result = adapter.fetch_snapshot(request)

    assert result.provider_id == "external_fx_provider"
    assert result.target_id == "USDJPY"
    assert result.value == "unavailable"
    assert result.source_status == "interface_only"
    assert result.adapter_status == "not_implemented"
    assert "no_connection" in result.warning_flags
    assert "no_api_request" in result.warning_flags
    assert "no_ibkr_connection" in result.warning_flags
    assert "no_order" in result.warning_flags


def test_market_data_adapter_contract_rows_cover_safety_fields():
    rows = build_market_data_adapter_contract_rows(TZ)
    by_field = {(r.field_group, r.field_name): r for r in rows}

    assert ("request", "provider_id") in by_field
    assert ("request", "allow_network") in by_field
    assert ("request", "allow_broker_connection") in by_field
    assert ("request", "allow_trading") in by_field
    assert ("result", "adapter_status") in by_field
    assert ("safety", "no_connection") in by_field
    assert ("safety", "no_api_request") in by_field
    assert ("safety", "no_ibkr_connection") in by_field
    assert ("safety", "no_order") in by_field


def test_market_data_adapter_contract_writers(tmp_path: Path):
    rows = build_market_data_adapter_contract_rows(TZ)

    csv_path = tmp_path / "market_data_adapter_contract.csv"
    md_path = tmp_path / "market_data_adapter_contract_report.md"

    write_market_data_adapter_contract_csv(csv_path, rows)
    write_market_data_adapter_contract_report(md_path, rows)

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "field_group" in csv_text
    assert "safety_rule" in csv_text
    assert "Market Data Adapter Interface Contract Report" in md_text
    assert "no API request" in md_text
    assert "no IBKR connection" in md_text
