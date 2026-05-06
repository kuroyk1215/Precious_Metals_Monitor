from pathlib import Path

from src.manual_csv_market_data_adapter import (
    ManualCsvMarketDataAdapter,
    build_manual_csv_adapter_requests,
    write_manual_csv_adapter_interface_csv,
    write_manual_csv_adapter_interface_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_build_manual_csv_adapter_requests_are_safe():
    requests = build_manual_csv_adapter_requests()
    by_target = {r.target_id: r for r in requests}

    assert "XAUUSD" in by_target
    assert "1540.T" in by_target
    assert "518880.SH" in by_target

    for request in requests:
        assert request.provider_id == "manual_csv"
        assert request.requested_mode == "snapshot"
        assert request.allow_network is False
        assert request.allow_broker_connection is False
        assert request.allow_trading is False


def test_manual_csv_adapter_returns_ok_for_valid_row(tmp_path: Path):
    input_csv = tmp_path / "manual.csv"
    input_csv.write_text(
        "target_id,target_type,market,data_role,value,currency,source,source_status,source_timestamp,notes\n"
        "XAUUSD,upstream_factor,GLOBAL,gold_spot_usd,2350.0,USD,manual_csv,manual_csv,2026-05-06T00:00:00Z,valid\n",
        encoding="utf-8",
    )

    adapter = ManualCsvMarketDataAdapter(str(input_csv), TZ)
    request = [r for r in build_manual_csv_adapter_requests() if r.target_id == "XAUUSD"][0]
    result = adapter.fetch_snapshot(request)

    assert result.provider_id == "manual_csv"
    assert result.target_id == "XAUUSD"
    assert result.value == "2350.0"
    assert result.currency == "USD"
    assert result.adapter_status == "ok"
    assert "manual_csv_adapter" in result.warning_flags
    assert "no_api_request" in result.warning_flags
    assert "no_ibkr_connection" in result.warning_flags


def test_manual_csv_adapter_returns_unavailable_for_missing_target(tmp_path: Path):
    input_csv = tmp_path / "manual.csv"
    input_csv.write_text(
        "target_id,target_type,market,data_role,value,currency,source,source_status,source_timestamp,notes\n"
        "XAUUSD,upstream_factor,GLOBAL,gold_spot_usd,2350.0,USD,manual_csv,manual_csv,2026-05-06T00:00:00Z,valid\n",
        encoding="utf-8",
    )

    adapter = ManualCsvMarketDataAdapter(str(input_csv), TZ)
    request = [r for r in build_manual_csv_adapter_requests() if r.target_id == "1540.T"][0]
    result = adapter.fetch_snapshot(request)

    assert result.adapter_status == "unavailable"
    assert result.source_status == "missing_target"
    assert result.value == "unavailable"
    assert "missing_manual_csv_target" in result.warning_flags


def test_manual_csv_adapter_blocks_unsafe_request(tmp_path: Path):
    input_csv = tmp_path / "manual.csv"
    input_csv.write_text(
        "target_id,target_type,market,data_role,value,currency,source,source_status,source_timestamp,notes\n"
        "USDJPY,upstream_factor,FX,fx_rate,155.0,JPY,manual_csv,manual_csv,2026-05-06T00:00:00Z,valid\n",
        encoding="utf-8",
    )

    adapter = ManualCsvMarketDataAdapter(str(input_csv), TZ)
    request = [r for r in build_manual_csv_adapter_requests() if r.target_id == "USDJPY"][0]
    request.allow_network = True

    result = adapter.fetch_snapshot(request)

    assert result.adapter_status == "blocked_by_safety_violation"
    assert result.source_status == "blocked_by_safety_violation"
    assert "allow_network_must_be_false" in result.warning_flags


def test_manual_csv_adapter_interface_writers(tmp_path: Path):
    input_csv = tmp_path / "manual.csv"
    input_csv.write_text(
        "target_id,target_type,market,data_role,value,currency,source,source_status,source_timestamp,notes\n"
        "USDJPY,upstream_factor,FX,fx_rate,155.0,JPY,manual_csv,manual_csv,2026-05-06T00:00:00Z,valid\n",
        encoding="utf-8",
    )

    adapter = ManualCsvMarketDataAdapter(str(input_csv), TZ)
    rows = [adapter.fetch_snapshot(r) for r in build_manual_csv_adapter_requests()]

    csv_path = tmp_path / "manual_csv_adapter_interface_snapshot.csv"
    md_path = tmp_path / "manual_csv_adapter_interface_report.md"

    write_manual_csv_adapter_interface_csv(csv_path, rows)
    write_manual_csv_adapter_interface_report(md_path, rows, str(input_csv))

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "adapter_status" in csv_text
    assert "Manual CSV Market Data Adapter Interface Report" in md_text
    assert "no API request" in md_text
    assert "no IBKR connection" in md_text
