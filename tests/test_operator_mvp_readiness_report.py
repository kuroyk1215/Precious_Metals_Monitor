from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_mvp_readiness_report import READINESS_FIELDS, generate_mvp_readiness_report


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_mvp_readiness_report.sh"


def _read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_readiness_sources(tmp_path: Path) -> None:
    (tmp_path / "operator_daily_master_run_summary.csv").write_text(
        "generated_at,master_status,safety_clean,real_quote_available,quote_unavailable,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,MASTER_SAFE_UNAVAILABLE,true,false,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_continuity_archive_index.csv").write_text(
        "generated_at,source_file,source_exists,source_type,detected_status,detected_timestamp,archive_role,continuity_status,operator_next_step\n"
        "2026-05-25T00:00:00+00:00,operator_daily_master_run_summary.csv,true,csv,MASTER_SAFE_UNAVAILABLE,2026-05-25T00:00:00+00:00,master_run,SINGLE_RUN_BASELINE,continue_daily_collection\n",
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


def test_readiness_report_outputs_safe_unavailable(tmp_path: Path):
    _write_readiness_sources(tmp_path)

    row = generate_mvp_readiness_report(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_mvp_readiness_report.csv",
        output_report=tmp_path / "reports/operator_mvp_readiness_report.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )

    assert row["readiness_status"] == "MVP_SAFE_UNAVAILABLE"
    assert row["safety_clean"] == "true"
    assert row["safe_unavailable"] == "true"
    assert row["auto_trade_allowed"] == "false"
    assert row["account_read_allowed"] == "false"
    assert row["position_read_allowed"] == "false"
    assert row["historical_data_request_allowed"] == "false"
    assert row["telegram_real_send_allowed"] == "false"
    assert row["order_action_allowed"] == "false"
    assert row["cancel_action_allowed"] == "false"
    assert row["rebalance_action_allowed"] == "false"
    assert set(_read_one(tmp_path / "operator_mvp_readiness_report.csv")) == set(READINESS_FIELDS)
    report = (tmp_path / "reports/operator_mvp_readiness_report.md").read_text(encoding="utf-8")
    assert "readiness_status=MVP_SAFE_UNAVAILABLE" in report
    assert "no auto trading" in report
    assert "no account reads" in report
    assert "no position reads" in report
    assert "no historical data requests" in report
    assert "no Telegram real send" in report
    assert "no order/cancel/rebalance" in report


def test_readiness_report_missing_source_status(tmp_path: Path):
    row = generate_mvp_readiness_report(
        base_dir=tmp_path,
        output_csv=tmp_path / "readiness.csv",
        output_report=tmp_path / "readiness.md",
    )

    assert row["readiness_status"] == "MVP_MISSING_SOURCE"


def test_readiness_wrapper_generates_csv(tmp_path: Path):
    _write_readiness_sources(tmp_path)
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
            str(tmp_path / "readiness.csv"),
            "--output-report",
            str(tmp_path / "readiness.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_one(tmp_path / "readiness.csv")["readiness_status"] == "MVP_SAFE_UNAVAILABLE"
