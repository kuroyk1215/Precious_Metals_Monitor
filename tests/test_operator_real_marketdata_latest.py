from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_real_marketdata_latest import LATEST_FIELDS, generate_latest


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_real_marketdata_latest.sh"


def _read_one_csv(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_sources(tmp_path: Path, *, decision: str = "PROCEED_TO_OBSERVATION") -> tuple[Path, Path, Path]:
    summary = tmp_path / "summary.csv"
    archive = tmp_path / "archive.csv"
    decision_csv = tmp_path / "decision.csv"
    summary.write_text(
        "top_level_status,final_safety_status,config_restored,config_file_modified,contract_qualification_allowed,historical_data_request_allowed,trading_actions_allowed,account_read_allowed,position_read_allowed,telegram_send_allowed,req_mkt_data_allowed,req_historical_data_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "REAL_MARKETDATA_SMOKE_AUDIT_READY,PASS_READ_ONLY_MARKETDATA_SMOKE_AUDITED,true,false,false,false,false,false,false,false,true,false,false,false,false\n",
        encoding="utf-8",
    )
    archive.write_text(
        "diagnostic_category,top_level_status,final_safety_status,config_restored,config_file_modified,contract_qualification_allowed,historical_data_request_allowed,trading_actions_allowed,account_read_allowed,position_read_allowed,telegram_send_allowed,req_mkt_data_allowed,req_historical_data_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "PASS_READY,REAL_MARKETDATA_SMOKE_AUDIT_READY,PASS_READ_ONLY_MARKETDATA_SMOKE_AUDITED,true,false,false,false,false,false,false,false,true,false,false,false,false\n",
        encoding="utf-8",
    )
    decision_csv.write_text(
        "operator_decision,source_diagnostic_category,top_level_status,final_safety_status,config_restored,config_file_modified,contract_qualification_allowed,historical_data_request_allowed,trading_actions_allowed,account_read_allowed,position_read_allowed,telegram_send_allowed,req_mkt_data_allowed,req_historical_data_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        f"{decision},PASS_READY,REAL_MARKETDATA_SMOKE_AUDIT_READY,PASS_READ_ONLY_MARKETDATA_SMOKE_AUDITED,true,false,false,false,false,false,false,false,true,false,false,false,false\n",
        encoding="utf-8",
    )
    return summary, archive, decision_csv


def test_latest_csv_and_markdown_generate_from_chain_sources(tmp_path: Path):
    summary, archive, decision = _write_sources(tmp_path)

    latest_status, row = generate_latest(
        source_summary_file=summary,
        source_archive_file=archive,
        source_decision_file=decision,
        output_csv=tmp_path / "operator_real_marketdata_latest.csv",
        output_report=tmp_path / "reports/operator_real_marketdata_latest_report.md",
        latest_generated_at="2026-05-25T00:00:04+00:00",
    )

    assert latest_status == "PROCEED_TO_OBSERVATION"
    assert row["latest_pointer"] == str(decision)
    assert set(_read_one_csv(tmp_path / "operator_real_marketdata_latest.csv")) == set(LATEST_FIELDS)
    assert (tmp_path / "reports/operator_real_marketdata_latest_report.md").exists()


def test_latest_incomplete_when_decision_missing(tmp_path: Path):
    summary, archive, decision = _write_sources(tmp_path)
    decision.unlink()

    latest_status, row = generate_latest(
        source_summary_file=summary,
        source_archive_file=archive,
        source_decision_file=decision,
        output_csv=tmp_path / "latest.csv",
        output_report=tmp_path / "latest.md",
    )

    assert latest_status == "LATEST_INCOMPLETE"
    assert row["decision_exists"] == "false"


def test_latest_wrapper_does_not_read_config_or_runtime_error_log(tmp_path: Path):
    summary, archive, decision = _write_sources(tmp_path)
    (tmp_path / "config.yaml").write_text("must_not_be_read: true\n", encoding="utf-8")
    (tmp_path / "ibkr_market_data_api_errors.csv").write_text("must_not_be_read\n", encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))
    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--source-summary-file",
            str(summary),
            "--source-archive-file",
            str(archive),
            "--source-decision-file",
            str(decision),
            "--output-csv",
            str(tmp_path / "latest.csv"),
            "--output-report",
            str(tmp_path / "latest.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_one_csv(tmp_path / "latest.csv")["latest_status"] == "PROCEED_TO_OBSERVATION"
