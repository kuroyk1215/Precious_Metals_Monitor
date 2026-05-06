from pathlib import Path

from src.manual_research_trading_pipeline import (
    build_manual_research_trading_pipeline_step_row,
    summarize_step_status,
    write_manual_research_trading_pipeline_report,
    write_manual_research_trading_pipeline_summary_csv,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_summarize_step_status():
    assert summarize_step_status([]) == "none"
    assert summarize_step_status(["ok", "ok"]) == "ok"
    assert summarize_step_status(["neutral_range_trade_reference"]) == "neutral_range_trade_reference"
    assert summarize_step_status(["ok", "partial"]) == "ok,partial"


def test_manual_research_trading_pipeline_writers(tmp_path: Path):
    rows = [
        build_manual_research_trading_pipeline_step_row(
            1,
            "Phase 6D",
            "manual_market_data_pipeline",
            "ok",
            "manual_market_data_pipeline_summary.csv",
            "reports/manual_market_data_pipeline_report.md",
            7,
            TZ,
            "sample",
        ),
        build_manual_research_trading_pipeline_step_row(
            2,
            "Phase 8A",
            "research_trading_plan",
            "neutral_range_trade_reference",
            "research_trading_plan.csv",
            "reports/research_trading_plan_report.md",
            3,
            TZ,
            "sample",
        ),
    ]

    csv_path = tmp_path / "manual_research_trading_pipeline_summary.csv"
    md_path = tmp_path / "manual_research_trading_pipeline_report.md"

    write_manual_research_trading_pipeline_summary_csv(csv_path, rows)
    write_manual_research_trading_pipeline_report(md_path, rows, "data/manual_market_data_sample_valid.csv")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "step_name" in csv_text
    assert "research_trading_plan" in csv_text
    assert "Phase 8C Manual Research Trading Pipeline Report" in md_text
    assert "action_allowed=false" in md_text
    assert "no IBKR connection" in md_text
    assert "no auto trade" in md_text
