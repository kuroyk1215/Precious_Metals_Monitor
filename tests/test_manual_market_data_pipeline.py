from pathlib import Path

from src.manual_market_data_pipeline import (
    build_manual_market_data_pipeline_step_row,
    summarize_status,
    write_manual_market_data_pipeline_report,
    write_manual_market_data_pipeline_summary_csv,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_summarize_status():
    assert summarize_status(["ok", "ok"]) == "ok"
    assert summarize_status(["unavailable"]) == "unavailable"
    assert summarize_status(["ok", "unavailable"]) == "partial"
    assert summarize_status(["invalid", "ok"]) == "invalid"
    assert summarize_status([]) == "unavailable"


def test_manual_market_data_pipeline_step_safety():
    row = build_manual_market_data_pipeline_step_row(
        step_order=1,
        phase="Phase 6B",
        step_name="manual_market_data_adapter",
        status="unavailable",
        output_csv="manual_market_data_snapshot.csv",
        output_report="reports/manual_market_data_adapter_report.md",
        row_count=8,
        tz_cfg=TZ,
    )

    assert row.step_order == 1
    assert row.phase == "Phase 6B"
    assert "explicit_manual_csv_pipeline" in row.safety_scope
    assert "action_allowed=false" in row.safety_scope
    assert "no_ibkr_connection" in row.safety_scope
    assert "no_reqMktData" in row.safety_scope
    assert "no_reqHistoricalData" in row.safety_scope


def test_manual_market_data_pipeline_writers(tmp_path: Path):
    rows = [
        build_manual_market_data_pipeline_step_row(
            1,
            "Phase 6B",
            "manual_market_data_adapter",
            "unavailable",
            "manual_market_data_snapshot.csv",
            "reports/manual_market_data_adapter_report.md",
            8,
            TZ,
        ),
        build_manual_market_data_pipeline_step_row(
            2,
            "Phase 6C",
            "manual_market_data_integration",
            "unavailable",
            "manual_market_data_integration_summary.csv",
            "reports/manual_market_data_integration_report.md",
            8,
            TZ,
        ),
    ]

    csv_path = tmp_path / "manual_market_data_pipeline_summary.csv"
    md_path = tmp_path / "manual_market_data_pipeline_report.md"

    write_manual_market_data_pipeline_summary_csv(csv_path, rows)
    write_manual_market_data_pipeline_report(md_path, rows, "data/manual_market_data_template.csv")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "step_order" in csv_text
    assert "safety_scope" in csv_text
    assert "Manual Market Data End-to-End Research Pipeline Report" in md_text
    assert "action_allowed=false" in md_text
    assert "no IBKR connection" in md_text
