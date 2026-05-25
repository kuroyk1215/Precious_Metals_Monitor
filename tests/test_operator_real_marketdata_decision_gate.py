from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_real_marketdata_decision_gate import (
    BLOCK_CONFIG_RESTORE_FAILURE,
    BLOCK_FORBIDDEN_ACTION_RISK,
    BLOCK_MISSING_SOURCE,
    DECISION_FIELDS,
    HOLD_SAFE_FAILURE,
    PROCEED_TO_OBSERVATION,
    generate_decision,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_real_marketdata_decision_gate.sh"

ARCHIVE_HEADER = (
    "archive_generated_at,source_summary_file,source_report_file,source_exists,top_level_status,"
    "final_safety_status,config_restored,config_file_modified,real_connection_allowed_during_run,"
    "market_data_request_allowed_during_run,contract_qualification_allowed,historical_data_request_allowed,"
    "trading_actions_allowed,account_read_allowed,position_read_allowed,telegram_send_allowed,"
    "req_mkt_data_allowed,req_historical_data_allowed,order_action_allowed,cancel_action_allowed,"
    "rebalance_action_allowed,diagnostic_category,diagnostic_reason,operator_next_step\n"
)


def _read_one_csv(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_archive(path: Path, *, category: str, config_restored: str = "true", config_file_modified: str = "false", historical_allowed: str = "false") -> None:
    path.write_text(
        ARCHIVE_HEADER
        + (
            "2026-05-25T00:00:02+00:00,summary.csv,report.md,true,"
            "REAL_MARKETDATA_SMOKE_AUDIT_READY,PASS_READ_ONLY_MARKETDATA_SMOKE_AUDITED,"
            f"{config_restored},{config_file_modified},true,true,false,{historical_allowed},false,"
            f"false,false,false,true,false,false,false,false,{category},reason,next\n"
        ),
        encoding="utf-8",
    )


def _write_summary(path: Path, *, connection_succeeded: str = "true", market_data_request_triggered: str = "true", snapshot_rows_detected: str = "3", smoke_exit_code: str = "0") -> None:
    path.write_text(
        "smoke_exit_code,snapshot_rows_detected,connection_succeeded,market_data_request_triggered\n"
        f"{smoke_exit_code},{snapshot_rows_detected},{connection_succeeded},{market_data_request_triggered}\n",
        encoding="utf-8",
    )


def test_decision_proceeds_from_pass_ready_archive(tmp_path: Path):
    archive = tmp_path / "archive.csv"
    _write_archive(archive, category="PASS_READY")
    _write_summary(tmp_path / "summary.csv")

    decision, row = generate_decision(
        source_archive_file=archive,
        output_csv=tmp_path / "operator_real_marketdata_decision_gate.csv",
        output_report=tmp_path / "reports/operator_real_marketdata_decision_gate_report.md",
        decision_generated_at="2026-05-25T00:00:03+00:00",
    )

    assert decision == PROCEED_TO_OBSERVATION
    assert row["operator_decision"] == PROCEED_TO_OBSERVATION
    assert set(_read_one_csv(tmp_path / "operator_real_marketdata_decision_gate.csv")) == set(DECISION_FIELDS)
    assert (tmp_path / "reports/operator_real_marketdata_decision_gate_report.md").exists()


def test_decision_holds_pass_ready_archive_when_connection_failed(tmp_path: Path):
    archive = tmp_path / "archive.csv"
    _write_archive(archive, category="PASS_READY")
    _write_summary(tmp_path / "summary.csv", connection_succeeded="false")

    decision, row = generate_decision(source_archive_file=archive, output_csv=tmp_path / "decision.csv", output_report=tmp_path / "decision.md")

    assert decision == HOLD_SAFE_FAILURE
    assert row["source_diagnostic_category"] == "PASS_READY"
    assert row["connection_succeeded"] == "false"
    assert "connection_succeeded_false" in row["decision_reason"]


def test_decision_holds_pass_ready_archive_when_quote_result_missing(tmp_path: Path):
    archive = tmp_path / "archive.csv"
    _write_archive(archive, category="PASS_READY")
    _write_summary(tmp_path / "summary.csv", market_data_request_triggered="false", snapshot_rows_detected="0")

    decision, row = generate_decision(source_archive_file=archive, output_csv=tmp_path / "decision.csv", output_report=tmp_path / "decision.md")

    assert decision == HOLD_SAFE_FAILURE
    assert "market_data_request_triggered_false" in row["decision_reason"]
    assert "snapshot_rows_missing" in row["decision_reason"]


def test_decision_holds_safe_failure_when_smoke_failed_but_gates_preserved(tmp_path: Path):
    archive = tmp_path / "archive.csv"
    _write_archive(archive, category="SAFE_FAILURE")

    decision, row = generate_decision(source_archive_file=archive, output_csv=tmp_path / "decision.csv", output_report=tmp_path / "decision.md")

    assert decision == HOLD_SAFE_FAILURE
    assert row["operator_next_step"] == "hold_and_inspect_ibkr_permissions"


def test_decision_blocks_restore_failure(tmp_path: Path):
    archive = tmp_path / "archive.csv"
    _write_archive(archive, category="CONFIG_RESTORE_FAILURE", config_restored="false")

    decision, row = generate_decision(source_archive_file=archive, output_csv=tmp_path / "decision.csv", output_report=tmp_path / "decision.md")

    assert decision == BLOCK_CONFIG_RESTORE_FAILURE
    assert row["config_restored"] == "false"


def test_decision_blocks_forbidden_action_risk(tmp_path: Path):
    archive = tmp_path / "archive.csv"
    _write_archive(archive, category="PASS_READY", historical_allowed="true")

    decision, row = generate_decision(source_archive_file=archive, output_csv=tmp_path / "decision.csv", output_report=tmp_path / "decision.md")

    assert decision == BLOCK_FORBIDDEN_ACTION_RISK
    assert row["historical_data_request_allowed"] == "true"


def test_decision_blocks_missing_source(tmp_path: Path):
    decision, row = generate_decision(source_archive_file=tmp_path / "missing.csv", output_csv=tmp_path / "decision.csv", output_report=tmp_path / "decision.md")

    assert decision == BLOCK_MISSING_SOURCE
    assert row["source_exists"] == "false"


def test_wrapper_generates_decision_without_config_or_runtime_error_log(tmp_path: Path):
    archive = tmp_path / "archive.csv"
    _write_archive(archive, category="PASS_READY")
    _write_summary(tmp_path / "summary.csv")
    (tmp_path / "config.yaml").write_text("must_not_be_read: true\n", encoding="utf-8")
    (tmp_path / "ibkr_market_data_api_errors.csv").write_text("must_not_be_read\n", encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))
    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--source-archive-file",
            str(archive),
            "--output-csv",
            str(tmp_path / "decision.csv"),
            "--output-report",
            str(tmp_path / "decision.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_one_csv(tmp_path / "decision.csv")["operator_decision"] == PROCEED_TO_OBSERVATION
