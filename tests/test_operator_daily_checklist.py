from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_daily_checklist import CHECKLIST_FIELDS, CHECKS, generate_daily_checklist


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_daily_checklist.sh"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_checklist_csv_and_markdown_generate_in_required_order(tmp_path: Path):
    rows = generate_daily_checklist(
        output_csv=tmp_path / "operator_daily_checklist.csv",
        output_report=tmp_path / "reports/operator_daily_checklist.md",
        generated_at="2026-05-25T00:00:02+00:00",
    )

    assert [row["check_name"] for row in rows] == [name for name, _ in CHECKS]
    assert rows[0]["check_name"] == "git status safety check"
    assert rows[-1]["check_name"] == "do not trade automatically"
    assert all(row["auto_trade_allowed"] == "false" for row in rows)
    assert all(row["account_read_allowed"] == "false" for row in rows)
    assert all(row["position_read_allowed"] == "false" for row in rows)
    assert all(row["historical_data_request_allowed"] == "false" for row in rows)
    assert all(row["telegram_send_allowed"] == "false" for row in rows)
    assert all(row["order_action_allowed"] == "false" for row in rows)
    assert all(row["cancel_action_allowed"] == "false" for row in rows)
    assert all(row["rebalance_action_allowed"] == "false" for row in rows)
    assert set(_read_rows(tmp_path / "operator_daily_checklist.csv")[0]) == set(CHECKLIST_FIELDS)

    report = (tmp_path / "reports/operator_daily_checklist.md").read_text(encoding="utf-8")
    assert "1. git status safety check" in report
    assert "10. do not trade automatically" in report
    assert "no historical data requests" in report


def test_checklist_wrapper_generates_csv(tmp_path: Path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))

    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--output-csv",
            str(tmp_path / "checklist.csv"),
            "--output-report",
            str(tmp_path / "checklist.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert len(_read_rows(tmp_path / "checklist.csv")) == 10
