from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_real_market_archive_compare import ARCHIVE_COMPARE_FIELDS, generate_archive_compare


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_real_market_archive_compare.sh"


def _read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_single_run_sources(tmp_path: Path) -> None:
    (tmp_path / "operator_real_market_mvp_status.csv").write_text(
        "generated_at,mvp_status,safety_clean,real_quote_available,safe_unavailable,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,MVP_SAFE_UNAVAILABLE,true,false,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_daily_real_market_report.csv").write_text(
        "generated_at,symbol,real_quote_state,quote_status,normalized_status,signal_bridge_status,safe_unavailable,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,GLD,SAFE_UNAVAILABLE,UNAVAILABLE,SAFE_UNAVAILABLE,HOLD_NO_REAL_QUOTE,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_quote_normalization.csv").write_text(
        "generated_at,symbol,quote_status,normalized_status,diagnostic_reason\n"
        "2026-05-25T00:00:00+00:00,GLD,UNAVAILABLE,SAFE_UNAVAILABLE,no_real_quote\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_quote_signal_bridge.csv").write_text(
        "generated_at,symbol,signal_bridge_status,auto_trade_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,GLD,HOLD_NO_REAL_QUOTE,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_marketdata_decision_gate.csv").write_text(
        "generated_at,operator_decision,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,HOLD_SAFE_FAILURE,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )


def test_single_run_archive_compare_outputs_insufficient_history(tmp_path: Path):
    _write_single_run_sources(tmp_path)

    row = generate_archive_compare(
        base_dir=tmp_path,
        output_csv=tmp_path / "archive.csv",
        output_report=tmp_path / "reports/archive.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )

    assert row["comparison_window"] == "SINGLE_RUN"
    assert row["status_consistency"] == "INSUFFICIENT_HISTORY"
    assert row["operator_next_step"] == "continue_daily_collection"
    assert row["safety_consistency"] == "SAFETY_CONSISTENT_FALSE_ACTIONS"
    assert set(_read_one(tmp_path / "archive.csv")) == set(ARCHIVE_COMPARE_FIELDS)


def test_archive_compare_wrapper_generates_report(tmp_path: Path):
    _write_single_run_sources(tmp_path)
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
            str(tmp_path / "archive.csv"),
            "--output-report",
            str(tmp_path / "archive.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_one(tmp_path / "archive.csv")["status_consistency"] == "INSUFFICIENT_HISTORY"
    assert "no auto trading" in (tmp_path / "archive.md").read_text(encoding="utf-8")
