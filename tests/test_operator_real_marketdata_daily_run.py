from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_real_marketdata_daily_run import DAILY_FIELDS, generate_daily_summary


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_real_marketdata_daily_run.sh"

SAFE_CONFIG = """ibkr:
  read_only_required: true
  real_connection_allowed: false
  contract_qualification_allowed: false
  market_data_request_allowed: false
  historical_data_request_allowed: false
  trading_actions_allowed: false
"""


def _read_one_csv(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_latest(path: Path, *, decision: str) -> None:
    path.write_text(
        "latest_status,operator_decision,source_diagnostic_category,config_restored,config_file_modified,contract_qualification_allowed,historical_data_request_allowed,trading_actions_allowed,account_read_allowed,position_read_allowed,telegram_send_allowed,req_historical_data_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        f"{decision},{decision},SAFE_FAILURE,true,false,false,false,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )


def test_daily_summary_marks_hold_safe_failure(tmp_path: Path):
    latest = tmp_path / "latest.csv"
    _write_latest(latest, decision="HOLD_SAFE_FAILURE")

    status, row = generate_daily_summary(
        smoke_exit_code=7,
        archive_exit_code=0,
        decision_exit_code=0,
        latest_exit_code=0,
        latest_csv=latest,
        output_csv=tmp_path / "operator_real_marketdata_daily_run_summary.csv",
        output_report=tmp_path / "reports/operator_real_marketdata_daily_run_report.md",
        generated_at="2026-05-25T00:00:05+00:00",
    )

    assert status == "DAILY_OPERATOR_CHAIN_HOLD_SAFE_FAILURE"
    assert row["smoke_exit_code"] == "7"
    assert set(_read_one_csv(tmp_path / "operator_real_marketdata_daily_run_summary.csv")) == set(DAILY_FIELDS)
    assert (tmp_path / "reports/operator_real_marketdata_daily_run_report.md").exists()


def test_daily_wrapper_continues_after_smoke_failure_and_holds_safe(tmp_path: Path):
    config = tmp_path / "config.yaml"
    config.write_text(SAFE_CONFIG, encoding="utf-8")
    smoke_script = tmp_path / "stub_smoke.sh"
    smoke_script.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf 'display_symbol,historical_data_request_triggered,broker_execution_triggered,account_read_triggered,position_read_triggered,telegram_send_triggered\\nGLD,false,false,false,false,false\\n' > "${PHASE442_TEST_SNAPSHOT_CSV:?}"
exit 7
""",
        encoding="utf-8",
    )
    smoke_script.chmod(0o755)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))
    env["PHASE442_SMOKE_SCRIPT"] = str(smoke_script)
    env["PHASE442_TEST_SNAPSHOT_CSV"] = str(tmp_path / "snapshot.csv")
    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--config",
            str(config),
            "--smoke-summary-csv",
            str(tmp_path / "smoke_summary.csv"),
            "--smoke-report",
            str(tmp_path / "smoke_report.md"),
            "--snapshot-csv",
            str(tmp_path / "snapshot.csv"),
            "--archive-csv",
            str(tmp_path / "archive.csv"),
            "--archive-report",
            str(tmp_path / "archive.md"),
            "--decision-csv",
            str(tmp_path / "decision.csv"),
            "--decision-report",
            str(tmp_path / "decision.md"),
            "--latest-csv",
            str(tmp_path / "latest.csv"),
            "--latest-report",
            str(tmp_path / "latest.md"),
            "--summary-csv",
            str(tmp_path / "daily.csv"),
            "--summary-report",
            str(tmp_path / "daily.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert config.read_text(encoding="utf-8") == SAFE_CONFIG
    daily = _read_one_csv(tmp_path / "daily.csv")
    assert daily["daily_run_status"] == "DAILY_OPERATOR_CHAIN_HOLD_SAFE_FAILURE"
    assert daily["smoke_exit_code"] == "7"
    assert daily["operator_decision"] == "HOLD_SAFE_FAILURE"


def test_daily_wrapper_holds_when_smoke_audit_is_safe_but_connection_failed(tmp_path: Path):
    config = tmp_path / "config.yaml"
    config.write_text(SAFE_CONFIG, encoding="utf-8")
    smoke_script = tmp_path / "stub_smoke.sh"
    smoke_script.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf 'display_symbol,connection_succeeded,market_data_request_triggered,historical_data_request_triggered,broker_execution_triggered,account_read_triggered,position_read_triggered,telegram_send_triggered\\nGLD,false,false,false,false,false,false,false\\n' > "${PHASE442_TEST_SNAPSHOT_CSV:?}"
exit 0
""",
        encoding="utf-8",
    )
    smoke_script.chmod(0o755)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))
    env["PHASE442_SMOKE_SCRIPT"] = str(smoke_script)
    env["PHASE442_TEST_SNAPSHOT_CSV"] = str(tmp_path / "snapshot.csv")
    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--config",
            str(config),
            "--smoke-summary-csv",
            str(tmp_path / "smoke_summary.csv"),
            "--smoke-report",
            str(tmp_path / "smoke_report.md"),
            "--snapshot-csv",
            str(tmp_path / "snapshot.csv"),
            "--archive-csv",
            str(tmp_path / "archive.csv"),
            "--archive-report",
            str(tmp_path / "archive.md"),
            "--decision-csv",
            str(tmp_path / "decision.csv"),
            "--decision-report",
            str(tmp_path / "decision.md"),
            "--latest-csv",
            str(tmp_path / "latest.csv"),
            "--latest-report",
            str(tmp_path / "latest.md"),
            "--summary-csv",
            str(tmp_path / "daily.csv"),
            "--summary-report",
            str(tmp_path / "daily.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    daily = _read_one_csv(tmp_path / "daily.csv")
    decision = _read_one_csv(tmp_path / "decision.csv")
    assert daily["daily_run_status"] == "DAILY_OPERATOR_CHAIN_HOLD_SAFE_FAILURE"
    assert daily["smoke_exit_code"] == "0"
    assert daily["operator_decision"] == "HOLD_SAFE_FAILURE"
    assert decision["source_diagnostic_category"] == "PASS_READY"
    assert "connection_succeeded_false" in decision["decision_reason"]
