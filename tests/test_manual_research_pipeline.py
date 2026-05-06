from pathlib import Path

from src.manual_research_pipeline import (
    build_pipeline_step_row,
    write_pipeline_summary_csv,
    write_pipeline_summary_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_pipeline_step_row_safety_scope():
    row = build_pipeline_step_row(
        step_order=1,
        phase="Phase 5B",
        step_name="upstream_factors",
        status="partial",
        output_csv="upstream_factor_snapshot.csv",
        output_report="reports/upstream_factor_report.md",
        row_count=5,
        tz_cfg=TZ,
    )

    assert row.step_order == 1
    assert row.phase == "Phase 5B"
    assert row.status == "partial"
    assert "manual_research_only" in row.safety_scope
    assert "action_allowed=false" in row.safety_scope
    assert "no_ibkr_connection" in row.safety_scope


def test_pipeline_summary_writers(tmp_path: Path):
    rows = [
        build_pipeline_step_row(1, "Phase 5B", "upstream_factors", "partial", "upstream_factor_snapshot.csv", "reports/upstream_factor_report.md", 5, TZ),
        build_pipeline_step_row(2, "Phase 5C", "theoretical_pricing", "ok", "theoretical_price_snapshot.csv", "reports/theoretical_price_report.md", 3, TZ),
    ]

    csv_path = tmp_path / "manual_research_pipeline_summary.csv"
    md_path = tmp_path / "manual_research_pipeline_report.md"

    write_pipeline_summary_csv(csv_path, rows)
    write_pipeline_summary_report(md_path, rows)

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "step_order" in csv_text
    assert "safety_scope" in csv_text
    assert "End-to-End Manual Research Pipeline Report" in md_text
    assert "action_allowed=false" in md_text
    assert "no IBKR connection" in md_text
