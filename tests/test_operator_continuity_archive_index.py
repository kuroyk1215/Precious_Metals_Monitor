from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_continuity_archive_index import CONTINUITY_FIELDS, generate_continuity_archive_index


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_continuity_archive_index.sh"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_continuity_index_single_run_baseline(tmp_path: Path):
    (tmp_path / "operator_daily_master_run_summary.csv").write_text(
        "generated_at,master_status,safety_clean\n"
        "2026-05-25T00:00:00+00:00,MASTER_SAFE_UNAVAILABLE,true\n",
        encoding="utf-8",
    )

    rows = generate_continuity_archive_index(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_continuity_archive_index.csv",
        output_report=tmp_path / "reports/operator_continuity_archive_index_report.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )

    assert rows
    assert {row["continuity_status"] for row in rows} == {"SINGLE_RUN_BASELINE"}
    assert {row["operator_next_step"] for row in rows} == {"continue_daily_collection"}
    existing = [row for row in rows if row["source_file"] == "operator_daily_master_run_summary.csv"][0]
    assert existing["source_exists"] == "true"
    assert existing["detected_status"] == "MASTER_SAFE_UNAVAILABLE"
    assert set(_read_rows(tmp_path / "operator_continuity_archive_index.csv")[0]) == set(CONTINUITY_FIELDS)
    report = (tmp_path / "reports/operator_continuity_archive_index_report.md").read_text(encoding="utf-8")
    assert "continuity_status=SINGLE_RUN_BASELINE" in report


def test_continuity_wrapper_generates_index(tmp_path: Path):
    (tmp_path / "operator_real_market_mvp_status.csv").write_text(
        "generated_at,mvp_status\n"
        "2026-05-25T00:00:00+00:00,MVP_SAFE_UNAVAILABLE\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))

    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--base-dir",
            str(tmp_path),
            "--output-csv",
            str(tmp_path / "index.csv"),
            "--output-report",
            str(tmp_path / "index.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_rows(tmp_path / "index.csv")[0]["continuity_status"] == "SINGLE_RUN_BASELINE"
