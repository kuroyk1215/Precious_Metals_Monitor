from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_real_market_mvp_regression import REGRESSION_FIELDS, generate_regression_report


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_real_market_mvp_regression_check.sh"


def _read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def test_regression_csv_and_markdown_generate(tmp_path: Path):
    row = generate_regression_report(
        repo_root=REPO_ROOT,
        output_csv=tmp_path / "operator_real_market_mvp_regression.csv",
        output_report=tmp_path / "reports/operator_real_market_mvp_regression_report.md",
        generated_at="2026-05-25T00:00:03+00:00",
    )

    assert row["artifact_status"] in {"PASS", "FAIL"}
    assert row["py_compile_status"] == "SKIPPED"
    assert row["pytest_status"] == "SKIPPED"
    assert row["auto_trade_allowed"] == "false"
    assert row["account_read_allowed"] == "false"
    assert row["position_read_allowed"] == "false"
    assert row["historical_data_request_allowed"] == "false"
    assert row["telegram_send_allowed"] == "false"
    assert row["order_action_allowed"] == "false"
    assert row["cancel_action_allowed"] == "false"
    assert row["rebalance_action_allowed"] == "false"
    assert set(_read_one(tmp_path / "operator_real_market_mvp_regression.csv")) == set(REGRESSION_FIELDS)

    report = (tmp_path / "reports/operator_real_market_mvp_regression_report.md").read_text(encoding="utf-8")
    assert "regression_status=" in report
    assert "no real market data request" in report


def test_regression_wrapper_generates_csv(tmp_path: Path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))

    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--repo-root",
            str(REPO_ROOT),
            "--output-csv",
            str(tmp_path / "regression.csv"),
            "--output-report",
            str(tmp_path / "regression.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode in {0, 1}, result.stdout
    assert _read_one(tmp_path / "regression.csv")["auto_trade_allowed"] == "false"
