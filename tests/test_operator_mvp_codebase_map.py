from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_mvp_codebase_map import CODEBASE_MAP_FIELDS, generate_mvp_codebase_map


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_mvp_codebase_map.sh"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_codebase_map_generates_required_modules(tmp_path: Path):
    rows = generate_mvp_codebase_map(
        output_csv=tmp_path / "operator_mvp_codebase_map.csv",
        output_report=tmp_path / "reports/operator_mvp_codebase_map.md",
        generated_at="2026-05-25T00:00:00+00:00",
    )

    module_names = {row["module_name"] for row in rows}
    expected = {
        "real marketdata smoke",
        "archive",
        "decision gate",
        "latest",
        "daily run",
        "quote normalization",
        "signal bridge",
        "daily real-market report",
        "MVP status",
        "checklist",
        "regression",
        "strategy quality",
        "master run",
        "continuity index",
        "readiness report",
        "GLD/SLV spread",
        "range framework",
        "strategy explanation",
        "final daily packet",
        "latest strategy decision",
        "completion gate",
    }
    assert expected <= module_names
    assert set(_read_rows(tmp_path / "operator_mvp_codebase_map.csv")[0]) == set(CODEBASE_MAP_FIELDS)
    report = (tmp_path / "reports/operator_mvp_codebase_map.md").read_text(encoding="utf-8")
    assert "daily master run is the primary daily command" in report
    assert "final daily packet is the final manual observation packet" in report


def test_codebase_map_forbidden_action_fields_are_false_by_boundary(tmp_path: Path):
    rows = generate_mvp_codebase_map(output_csv=tmp_path / "map.csv", output_report=tmp_path / "map.md")
    for row in rows:
        boundary = row["safety_boundary"]
        assert "no auto trading" in boundary
        assert "no account reads" in boundary
        assert "no position reads" in boundary
        assert "no historical data requests" in boundary
        assert "no Telegram real send" in boundary


def test_codebase_map_output_has_no_trade_execution_words(tmp_path: Path):
    generate_mvp_codebase_map(output_csv=tmp_path / "map.csv", output_report=tmp_path / "map.md")
    text = (tmp_path / "map.csv").read_text(encoding="utf-8") + (tmp_path / "map.md").read_text(encoding="utf-8")
    forbidden = ["B" + "UY", "S" + "ELL", "O" + "RDER", "E" + "XECUTE"]
    assert not any(word in text for word in forbidden)


def test_codebase_map_wrapper_generates_csv(tmp_path: Path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))

    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--output-csv",
            str(tmp_path / "map.csv"),
            "--output-report",
            str(tmp_path / "map.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_rows(tmp_path / "map.csv")
