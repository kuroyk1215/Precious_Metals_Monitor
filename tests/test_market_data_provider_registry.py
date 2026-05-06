from pathlib import Path

from src.market_data_provider_registry import (
    build_market_data_provider_registry_rows,
    write_market_data_provider_registry_csv,
    write_market_data_provider_registry_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_market_data_provider_registry_contains_required_providers():
    rows = build_market_data_provider_registry_rows(TZ)
    by_provider = {r.provider_id: r for r in rows}

    required = {
        "manual_csv",
        "ibkr_readonly",
        "external_precious_metals_provider",
        "external_fx_provider",
        "sge_official_or_manual",
        "cn_market_data_provider",
    }

    assert required.issubset(set(by_provider.keys()))
    assert by_provider["manual_csv"].provider_status == "ready"
    assert by_provider["ibkr_readonly"].provider_status == "planned"
    assert "1540.T" in by_provider["ibkr_readonly"].target_scope
    assert "518880.SH" in by_provider["cn_market_data_provider"].target_scope


def test_market_data_provider_registry_safety_boundaries():
    rows = build_market_data_provider_registry_rows(TZ)

    for row in rows:
        assert "registry_only" in row.safety_scope
        assert "no_connection" in row.safety_scope
        assert "no_api_request" in row.safety_scope
        assert "no_ibkr_connection" in row.safety_scope
        assert "no_reqMktData" in row.safety_scope
        assert "no_reqHistoricalData" in row.safety_scope
        assert "no_order" in row.safety_scope
        assert "no_auto_trade" in row.safety_scope


def test_market_data_provider_registry_priority_order():
    rows = build_market_data_provider_registry_rows(TZ)
    priorities = [r.planned_priority for r in rows]

    assert priorities == sorted(priorities)
    assert len(set(priorities)) == len(priorities)


def test_market_data_provider_registry_writers(tmp_path: Path):
    rows = build_market_data_provider_registry_rows(TZ)

    csv_path = tmp_path / "market_data_provider_registry.csv"
    md_path = tmp_path / "market_data_provider_registry_report.md"

    write_market_data_provider_registry_csv(csv_path, rows)
    write_market_data_provider_registry_report(md_path, rows)

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "provider_id" in csv_text
    assert "permission_status" in csv_text
    assert "Market Data Provider Registry Report" in md_text
    assert "no IBKR connection" in md_text
    assert "no API request" in md_text
