from pathlib import Path

from src.market_data_source_plan import (
    build_market_data_source_plan_rows,
    write_market_data_source_plan_csv,
    write_market_data_source_plan_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_market_data_source_plan_targets_and_safety():
    rows = build_market_data_source_plan_rows(TZ)
    by_target = {r.target_id: r for r in rows}

    required = {
        "XAUUSD",
        "XAGUSD",
        "USDJPY",
        "USDCNY",
        "SGE_AU99_99",
        "1540.T",
        "1542.T",
        "518880.SH",
    }

    assert required.issubset(set(by_target.keys()))
    assert by_target["1540.T"].market == "JP"
    assert by_target["518880.SH"].market == "CN"
    assert by_target["SGE_AU99_99"].candidate_source == "sge_official_or_manual_csv"

    for row in rows:
        assert "planning_only" in row.safety_scope
        assert "no_ibkr_connection" in row.safety_scope
        assert "no_reqMktData" in row.safety_scope
        assert "no_reqHistoricalData" in row.safety_scope
        assert row.adapter_status in {"planned", "future"}


def test_market_data_source_plan_priority_order():
    rows = build_market_data_source_plan_rows(TZ)
    priorities = [r.planned_priority for r in rows]
    assert priorities == sorted(priorities)
    assert len(set(priorities)) == len(priorities)


def test_market_data_source_plan_writers(tmp_path: Path):
    rows = build_market_data_source_plan_rows(TZ)
    csv_path = tmp_path / "market_data_source_plan.csv"
    md_path = tmp_path / "market_data_source_plan_report.md"

    write_market_data_source_plan_csv(csv_path, rows)
    write_market_data_source_plan_report(md_path, rows)

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "target_id" in csv_text
    assert "candidate_source" in csv_text
    assert "Real Market Data Source Adapter Planning Report" in md_text
    assert "no IBKR connection" in md_text
    assert "no reqMktData" in md_text
