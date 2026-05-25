from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_real_market_mvp_status import MVP_STATUS_FIELDS, generate_mvp_status


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_real_market_mvp_status.sh"


def _read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_safe_unavailable_sources(tmp_path: Path) -> None:
    (tmp_path / "operator_real_marketdata_smoke_summary.csv").write_text(
        "top_level_status,final_safety_status,config_restored,config_file_modified,contract_qualification_allowed,historical_data_request_allowed,trading_actions_allowed,account_read_allowed,position_read_allowed,telegram_send_allowed,req_historical_data_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed,historical_data_request_triggered,broker_execution_triggered,account_read_triggered,position_read_triggered,telegram_send_triggered\n"
        "REAL_MARKETDATA_SMOKE_AUDIT_READY,PASS_READ_ONLY_MARKETDATA_SMOKE_AUDITED,true,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_marketdata_smoke_archive.csv").write_text(
        "diagnostic_category,top_level_status,config_restored,config_file_modified,contract_qualification_allowed,historical_data_request_allowed,trading_actions_allowed,account_read_allowed,position_read_allowed,telegram_send_allowed,req_historical_data_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "PASS_READY,REAL_MARKETDATA_SMOKE_AUDIT_READY,true,false,false,false,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_marketdata_decision_gate.csv").write_text(
        "operator_decision,decision_reason,config_restored,config_file_modified,contract_qualification_allowed,historical_data_request_allowed,trading_actions_allowed,account_read_allowed,position_read_allowed,telegram_send_allowed,req_historical_data_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "HOLD_SAFE_FAILURE,connection_succeeded_false,true,false,false,false,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_marketdata_latest.csv").write_text(
        "latest_status,operator_decision,config_restored,config_file_modified,contract_qualification_allowed,historical_data_request_allowed,trading_actions_allowed,account_read_allowed,position_read_allowed,telegram_send_allowed,req_historical_data_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "HOLD_SAFE_FAILURE,HOLD_SAFE_FAILURE,true,false,false,false,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_marketdata_daily_run_summary.csv").write_text(
        "daily_run_status,latest_status,operator_decision,config_restored,config_file_modified,contract_qualification_allowed,historical_data_request_allowed,trading_actions_allowed,account_read_allowed,position_read_allowed,telegram_send_allowed,req_historical_data_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "DAILY_OPERATOR_CHAIN_HOLD_SAFE_FAILURE,HOLD_SAFE_FAILURE,HOLD_SAFE_FAILURE,true,false,false,false,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_quote_normalization.csv").write_text(
        "symbol,quote_status,normalized_status,diagnostic_category,diagnostic_reason,connection_succeeded,market_data_request_triggered,snapshot_rows_detected\n"
        "GLD,UNAVAILABLE,SAFE_UNAVAILABLE,PERMISSION_OR_CONNECTION_FAILURE,real_marketdata_connection_or_request_not_confirmed,false,false,0\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_quote_signal_bridge.csv").write_text(
        "symbol,signal_bridge_status,manual_action_allowed,auto_trade_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "GLD,HOLD_NO_REAL_QUOTE,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_daily_real_market_report.csv").write_text(
        "symbol,real_quote_state,manual_review_only,permission_or_connection_failure,safe_unavailable,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "GLD,PERMISSION_OR_CONNECTION_FAILURE,true,true,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )


def test_missing_source_outputs_mvp_missing_source(tmp_path: Path):
    rows = generate_mvp_status(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_real_market_mvp_status.csv",
        output_report=tmp_path / "reports/operator_real_market_mvp_status_report.md",
        generated_at="2026-05-25T00:00:00+00:00",
    )

    assert rows["mvp_status"] == "MVP_MISSING_SOURCE"
    assert "missing_source_files" in rows["diagnostic_reason"]
    assert _read_one(tmp_path / "operator_real_market_mvp_status.csv")["mvp_status"] == "MVP_MISSING_SOURCE"
    assert set(_read_one(tmp_path / "operator_real_market_mvp_status.csv")) == set(MVP_STATUS_FIELDS)


def test_safe_unavailable_outputs_mvp_safe_unavailable(tmp_path: Path):
    _write_safe_unavailable_sources(tmp_path)

    row = generate_mvp_status(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_real_market_mvp_status.csv",
        output_report=tmp_path / "reports/operator_real_market_mvp_status_report.md",
        generated_at="2026-05-25T00:00:01+00:00",
    )

    assert row["mvp_status"] == "MVP_SAFE_UNAVAILABLE"
    assert row["safety_clean"] == "true"
    assert row["safe_unavailable"] == "true"
    assert row["permission_or_connection_failure"] == "true"
    assert row["real_quote_available"] == "false"
    assert row["auto_trade_allowed"] == "false"
    assert row["account_read_allowed"] == "false"
    assert row["position_read_allowed"] == "false"
    assert row["historical_data_request_allowed"] == "false"
    assert row["telegram_send_allowed"] == "false"
    assert row["order_action_allowed"] == "false"
    assert row["cancel_action_allowed"] == "false"
    assert row["rebalance_action_allowed"] == "false"

    report = (tmp_path / "reports/operator_real_market_mvp_status_report.md").read_text(encoding="utf-8")
    assert "mvp_status=MVP_SAFE_UNAVAILABLE" in report
    assert "no account reads" in report


def test_mvp_status_wrapper_generates_csv(tmp_path: Path):
    _write_safe_unavailable_sources(tmp_path)
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
            str(tmp_path / "mvp.csv"),
            "--output-report",
            str(tmp_path / "mvp.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_one(tmp_path / "mvp.csv")["mvp_status"] == "MVP_SAFE_UNAVAILABLE"
