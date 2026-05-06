from pathlib import Path

from src.manual_csv_smoke import (
    build_manual_csv_smoke_step_row,
    summarize_guard_status,
    summarize_review_pack_status,
    summarize_validation_status,
    write_manual_csv_smoke_report,
    write_manual_csv_smoke_summary_csv,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


class ValidationRow:
    def __init__(self, status: str):
        self.status = status


class ReviewRow:
    def __init__(self, action_allowed: str):
        self.action_allowed = action_allowed


def test_manual_csv_smoke_status_summaries():
    assert summarize_guard_status([]) == "ok"
    assert summarize_guard_status([object()]) == "generated_outputs_detected"

    assert summarize_validation_status([ValidationRow("pass"), ValidationRow("pass")]) == "pass"
    assert summarize_validation_status([ValidationRow("pass"), ValidationRow("fail")]) == "fail"
    assert summarize_validation_status([]) == "fail"

    assert summarize_review_pack_status([ReviewRow("false"), ReviewRow("false")]) == "ok"
    assert summarize_review_pack_status([ReviewRow("true")]) == "check_required"
    assert summarize_review_pack_status([]) == "check_required"


def test_manual_csv_smoke_step_safety_scope():
    row = build_manual_csv_smoke_step_row(
        1,
        "generated_output_guard",
        "ok",
        "generated_output_guard.csv",
        "reports/generated_output_guard_report.md",
        0,
        TZ,
    )

    assert row.step_order == 1
    assert row.step_name == "generated_output_guard"
    assert "manual_csv_smoke_only" in row.safety_scope
    assert "action_allowed=false" in row.safety_scope
    assert "no_ibkr_connection" in row.safety_scope
    assert "no_reqMktData" in row.safety_scope
    assert "no_reqHistoricalData" in row.safety_scope


def test_manual_csv_smoke_writers(tmp_path: Path):
    rows = [
        build_manual_csv_smoke_step_row(
            1,
            "generated_output_guard",
            "ok",
            "generated_output_guard.csv",
            "reports/generated_output_guard_report.md",
            0,
            TZ,
        ),
        build_manual_csv_smoke_step_row(
            2,
            "filled_manual_scenario_validation",
            "pass",
            "filled_manual_scenario_validation.csv",
            "reports/filled_manual_scenario_validation_report.md",
            8,
            TZ,
        ),
        build_manual_csv_smoke_step_row(
            3,
            "manual_market_data_review_pack",
            "ok",
            "manual_market_data_review_pack.csv",
            "reports/manual_market_data_review_pack_report.md",
            3,
            TZ,
        ),
    ]

    csv_path = tmp_path / "manual_csv_smoke_summary.csv"
    md_path = tmp_path / "manual_csv_smoke_report.md"

    write_manual_csv_smoke_summary_csv(csv_path, rows)
    write_manual_csv_smoke_report(md_path, rows, "data/manual_market_data_sample_valid.csv")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "step_name" in csv_text
    assert "Final Manual CSV Workflow Smoke Report" in md_text
    assert "action_allowed=false" in md_text
    assert "no IBKR connection" in md_text
