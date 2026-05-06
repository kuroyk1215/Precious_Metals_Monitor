from pathlib import Path

from src.generated_output_guard import (
    scan_generated_outputs,
    write_generated_output_guard_csv,
    write_generated_output_guard_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_scan_generated_outputs_detects_runtime_files(tmp_path: Path):
    (tmp_path / "reports").mkdir()
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "manual_market_data_snapshot.csv").write_text("x\n", encoding="utf-8")
    (tmp_path / "reports" / "manual_market_data_pipeline_report.md").write_text("report\n", encoding="utf-8")
    (tmp_path / "data" / "raw" / "candidate.csv").write_text("raw\n", encoding="utf-8")

    rows = scan_generated_outputs(tmp_path, TZ)
    by_path = {r.path: r for r in rows}

    assert "manual_market_data_snapshot.csv" in by_path
    assert "reports/manual_market_data_pipeline_report.md" in by_path
    assert "data/raw/candidate.csv" in by_path

    for row in rows:
        assert row.safe_to_commit == "false"
        assert row.recommendation == "remove_before_commit"
        assert row.removal_command.startswith("rm -f ")


def test_scan_generated_outputs_allows_static_manual_csv_files(tmp_path: Path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "manual_market_data_template.csv").write_text("template\n", encoding="utf-8")
    (tmp_path / "data" / "manual_market_data_sample_valid.csv").write_text("sample\n", encoding="utf-8")

    rows = scan_generated_outputs(tmp_path, TZ)
    assert rows == []


def test_generated_output_guard_writers(tmp_path: Path):
    (tmp_path / "reports").mkdir()
    (tmp_path / "deviation_snapshot.csv").write_text("x\n", encoding="utf-8")

    rows = scan_generated_outputs(tmp_path, TZ)

    csv_path = tmp_path / "generated_output_guard.csv"
    md_path = tmp_path / "generated_output_guard_report.md"

    write_generated_output_guard_csv(csv_path, rows)
    write_generated_output_guard_report(md_path, rows)

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "safe_to_commit" in csv_text
    assert "Generated Output Cleanup Guard Report" in md_text
    assert "no IBKR connection" in md_text
    assert "no file deletion" in md_text
