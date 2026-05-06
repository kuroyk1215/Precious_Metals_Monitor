from pathlib import Path

from src.live_provider_mock_adapter import (
    build_live_provider_mock_adapter_rows,
    load_live_provider_mock_adapter_config,
)
from src.live_data_quality_gate import build_live_data_quality_gate_rows
from src.live_research_review_pack import build_live_research_review_pack_rows
from src.live_final_research_review_pack import (
    build_live_final_research_review_pack_rows,
    write_live_final_research_review_pack_csv,
    write_live_final_research_review_pack_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def _research_rows_by_target():
    config = load_live_provider_mock_adapter_config("data/market_data_provider_config.yaml")
    mock_rows = build_live_provider_mock_adapter_rows(config, TZ)
    mock_by_target = {row.target_id: row.__dict__ for row in mock_rows}
    quality_rows = build_live_data_quality_gate_rows(mock_by_target, TZ)
    research_rows = build_live_research_review_pack_rows(quality_rows, TZ)
    return {row.target_id: row.__dict__ for row in research_rows}


def test_live_final_research_review_pack_outputs_etf_rows():
    rows = build_live_final_research_review_pack_rows(_research_rows_by_target(), TZ)

    assert len(rows) == 3
    by_symbol = {row.etf_symbol: row for row in rows}

    assert by_symbol["1540.T"].lot_size == "100"
    assert by_symbol["1542.T"].currency == "JPY"
    assert by_symbol["518880.SH"].currency == "CNY"

    for row in rows:
        assert row.final_plan_status == "live_mock_final_reference"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert row.today_buy_reference_zone != "closed"
        assert row.today_sell_reference_zone != "closed"
        assert "phase10f_live_final_research_review_pack" in row.warning_flags


def test_live_final_research_review_pack_closes_missing_symbol():
    source = _research_rows_by_target()
    source.pop("1540.T")

    rows = build_live_final_research_review_pack_rows(source, TZ)
    by_symbol = {row.etf_symbol: row for row in rows}

    assert by_symbol["1540.T"].final_plan_status == "closed_missing_research_pack"
    assert by_symbol["1540.T"].today_buy_reference_zone == "closed"
    assert by_symbol["1540.T"].action_allowed == "false"


def test_live_final_research_review_pack_closes_failed_research_status():
    source = _research_rows_by_target()
    source["1540.T"]["research_pack_status"] = "excluded_quality_gate_failed"

    rows = build_live_final_research_review_pack_rows(source, TZ)
    by_symbol = {row.etf_symbol: row for row in rows}

    assert by_symbol["1540.T"].final_plan_status == "closed_quality_gate_failed"
    assert by_symbol["1540.T"].rolling_t_buy_reference_zone == "closed"


def test_live_final_research_review_pack_writers(tmp_path: Path):
    rows = build_live_final_research_review_pack_rows(_research_rows_by_target(), TZ)

    csv_path = tmp_path / "live_final_research_review_pack.csv"
    md_path = tmp_path / "live_final_research_review_pack_report.md"

    write_live_final_research_review_pack_csv(csv_path, rows)
    write_live_final_research_review_pack_report(md_path, rows, "data/market_data_provider_config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "final_plan_status" in csv_text
    assert "today_buy_reference_zone" in csv_text
    assert "Phase 10F Live Final Research Review Pack Report" in md_text
    assert "included_count: 3" in md_text
    assert "no API request" in md_text
    assert "no auto trade" in md_text
