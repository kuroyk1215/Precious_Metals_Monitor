from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_daily_master_run import MASTER_RUN_FIELDS, MASTER_WRAPPERS, generate_master_run


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_daily_master_run.sh"


def _read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_safe_unavailable_sources(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir()
    for wrapper in MASTER_WRAPPERS:
        (tmp_path / "scripts" / wrapper).write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (tmp_path / "operator_real_quote_normalization.csv").write_text(
        "generated_at,symbol,quote_status,normalized_status,diagnostic_category\n"
        "2026-05-25T00:00:00+00:00,GLD,UNAVAILABLE,SAFE_UNAVAILABLE,NO_REAL_QUOTE_SNAPSHOT\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_quote_signal_bridge.csv").write_text(
        "generated_at,symbol,signal_bridge_status,auto_trade_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,GLD,HOLD_NO_REAL_QUOTE,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_daily_real_market_report.csv").write_text(
        "generated_at,symbol,real_quote_state,safe_unavailable,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,GLD,SAFE_UNAVAILABLE,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_market_mvp_status.csv").write_text(
        "generated_at,mvp_status,real_quote_available,safe_unavailable,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,MVP_SAFE_UNAVAILABLE,false,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_strategy_quality_report.csv").write_text(
        "generated_at,quality_status,data_unavailable_but_safe,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,DATA_UNAVAILABLE_BUT_SAFE,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_market_mvp_regression.csv").write_text(
        "generated_at,regression_status,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,PASS,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )


def test_master_run_safe_unavailable_completes_after_wrapper_failures(tmp_path: Path):
    _write_safe_unavailable_sources(tmp_path)
    calls: list[list[str]] = []

    def fake_runner(command, cwd):
        calls.append(list(command))
        return 1 if command[-1].endswith("operator_real_marketdata_daily_run.sh") else 0

    row = generate_master_run(
        repo_root=tmp_path,
        output_csv=tmp_path / "operator_daily_master_run_summary.csv",
        output_report=tmp_path / "reports/operator_daily_master_run_report.md",
        command_runner=fake_runner,
        generated_at="2026-05-25T00:01:00+00:00",
    )

    assert len(calls) == len(MASTER_WRAPPERS)
    assert row["master_status"] == "MASTER_SAFE_UNAVAILABLE"
    assert row["quote_unavailable"] == "true"
    assert row["safety_clean"] == "true"
    assert row["auto_trade_allowed"] == "false"
    assert row["account_read_allowed"] == "false"
    assert row["position_read_allowed"] == "false"
    assert row["historical_data_request_allowed"] == "false"
    assert row["telegram_real_send_allowed"] == "false"
    assert row["order_action_allowed"] == "false"
    assert row["cancel_action_allowed"] == "false"
    assert row["rebalance_action_allowed"] == "false"
    assert set(_read_one(tmp_path / "operator_daily_master_run_summary.csv")) == set(MASTER_RUN_FIELDS)
    report = (tmp_path / "reports/operator_daily_master_run_report.md").read_text(encoding="utf-8")
    assert "master_status=MASTER_SAFE_UNAVAILABLE" in report
    assert "no historical data requests" in report


def test_master_wrapper_can_skip_existing_wrappers(tmp_path: Path):
    _write_safe_unavailable_sources(tmp_path)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))

    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--repo-root",
            str(tmp_path),
            "--output-csv",
            str(tmp_path / "master.csv"),
            "--output-report",
            str(tmp_path / "master.md"),
            "--skip-wrappers",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_one(tmp_path / "master.csv")["master_status"] == "MASTER_SAFE_UNAVAILABLE"
