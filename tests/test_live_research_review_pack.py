from pathlib import Path

from src.live_provider_mock_adapter import (
    build_live_provider_mock_adapter_rows,
    load_live_provider_mock_adapter_config,
)
from src.live_data_quality_gate import build_live_data_quality_gate_rows
from src.live_research_review_pack import (
    build_live_research_review_pack_rows,
    write_live_research_review_pack_csv,
    write_live_research_review_pack_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def _quality_rows():
    config = load_live_provider_mock_adapter_config("data/market_data_provider_config.yaml")
    mock_rows = build_live_provider_mock_adapter_rows(config, TZ)
    mock_by_target = {row.target_id: row.__dict__ for row in mock_rows}
    return build_live_data_quality_gate_rows(mock_by_target, TZ)


def test_live_research_review_pack_includes_passed_quality_rows():
    rows = build_live_research_review_pack_rows(_quality_rows(), TZ)

    assert len(rows) == 7

    by_target = {row.target_id: row for row in rows}
    assert by_target["XAUUSD"].research_value == "3400.00"
    assert by_target["1540.T"].currency == "JPY"

    for row in rows:
        assert row.research_pack_status == "included_for_research"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "phase10e_live_research_review_pack" in row.warning_flags


def test_live_research_review_pack_excludes_failed_quality_row():
    quality_rows = _quality_rows()
    quality_rows[0].usable_for_research = "false"
    quality_rows[0].quality_status = "fail_quality_gate"

    rows = build_live_research_review_pack_rows(quality_rows, TZ)

    assert rows[0].research_pack_status == "excluded_quality_gate_failed"
    assert rows[0].api_request_allowed == "false"
    assert rows[0].action_allowed == "false"


def test_live_research_review_pack_writers(tmp_path: Path):
    rows = build_live_research_review_pack_rows(_quality_rows(), TZ)

    csv_path = tmp_path / "live_research_review_pack.csv"
    md_path = tmp_path / "live_research_review_pack_report.md"

    write_live_research_review_pack_csv(csv_path, rows)
    write_live_research_review_pack_report(md_path, rows, "data/market_data_provider_config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "research_pack_status" in csv_text
    assert "included_for_research" in csv_text
    assert "Phase 10E Live Research Review Pack Report" in md_text
    assert "included_for_research_count: 7" in md_text
    assert "no API request" in md_text
    assert "no auto trade" in md_text
