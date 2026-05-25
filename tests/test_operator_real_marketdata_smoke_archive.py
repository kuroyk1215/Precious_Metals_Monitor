from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_real_marketdata_smoke_archive import (
    ARCHIVE_FIELDS,
    FORBIDDEN_ACTION_RISK,
    MISSING_SOURCE,
    PASS_READY,
    SAFE_FAILURE,
    generate_archive,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_real_marketdata_smoke_archive.sh"


BASE_SUMMARY_HEADER = (
    "run_id,started_at,ended_at,top_level_status,wrapper_exit_code,smoke_exit_code,"
    "read_only_required,real_connection_allowed_during_run,market_data_request_allowed_during_run,"
    "contract_qualification_allowed,historical_data_request_allowed,trading_actions_allowed,"
    "account_read_allowed,position_read_allowed,telegram_send_allowed,config_restored,"
    "config_file_modified,ibkr_api_request_allowed,req_mkt_data_allowed,req_historical_data_allowed,"
    "order_action_allowed,cancel_action_allowed,rebalance_action_allowed,final_safety_status,"
    "snapshot_rows_detected,connection_succeeded,market_data_request_triggered,"
    "historical_data_request_triggered,broker_execution_triggered,account_read_triggered,"
    "position_read_triggered,telegram_send_triggered,notes\n"
)


def _read_one_csv(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_report(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Operator Real Marketdata Smoke Report\n", encoding="utf-8")


def _write_summary(path: Path, *, top_level_status: str, final_safety_status: str, config_restored: str = "true", config_file_modified: str = "false", historical_allowed: str = "false") -> None:
    path.write_text(
        BASE_SUMMARY_HEADER
        + (
            "run,2026-05-25T00:00:00+00:00,2026-05-25T00:00:01+00:00,"
            f"{top_level_status},0,0,true,true,true,false,{historical_allowed},false,"
            f"false,false,false,{config_restored},{config_file_modified},true,true,false,"
            f"false,false,false,{final_safety_status},0,false,false,false,false,false,false,false,notes\n"
        ),
        encoding="utf-8",
    )


def test_archive_csv_and_markdown_generate_from_phase442_sources(tmp_path: Path):
    summary = tmp_path / "operator_real_marketdata_smoke_summary.csv"
    report = tmp_path / "reports/operator_real_marketdata_smoke_report.md"
    _write_summary(
        summary,
        top_level_status="REAL_MARKETDATA_SMOKE_AUDIT_READY",
        final_safety_status="PASS_READ_ONLY_MARKETDATA_SMOKE_AUDITED",
    )
    _write_report(report)

    category, row = generate_archive(
        source_summary_file=summary,
        source_report_file=report,
        output_csv=tmp_path / "operator_real_marketdata_smoke_archive.csv",
        output_report=tmp_path / "reports/operator_real_marketdata_smoke_archive_report.md",
        archive_generated_at="2026-05-25T00:00:02+00:00",
    )

    assert category == PASS_READY
    assert row["diagnostic_category"] == PASS_READY
    assert set(_read_one_csv(tmp_path / "operator_real_marketdata_smoke_archive.csv")) == set(ARCHIVE_FIELDS)
    assert (tmp_path / "reports/operator_real_marketdata_smoke_archive_report.md").exists()


def test_missing_source_files_generate_missing_source_diagnostic(tmp_path: Path):
    category, row = generate_archive(
        source_summary_file=tmp_path / "missing_summary.csv",
        source_report_file=tmp_path / "reports/missing_report.md",
        output_csv=tmp_path / "archive.csv",
        output_report=tmp_path / "archive.md",
    )

    assert category == MISSING_SOURCE
    assert row["source_exists"] == "false"
    assert row["diagnostic_category"] == MISSING_SOURCE
    assert _read_one_csv(tmp_path / "archive.csv")["diagnostic_category"] == MISSING_SOURCE


def test_safe_failure_classification_when_phase442_failed_but_gates_preserved(tmp_path: Path):
    summary = tmp_path / "summary.csv"
    report = tmp_path / "report.md"
    _write_summary(
        summary,
        top_level_status="REAL_MARKETDATA_SMOKE_AUDIT_FAILED",
        final_safety_status="AUDIT_FAILED_SAFE_DEFAULTS_RESTORED",
    )
    _write_report(report)

    category, row = generate_archive(
        source_summary_file=summary,
        source_report_file=report,
        output_csv=tmp_path / "archive.csv",
        output_report=tmp_path / "archive.md",
    )

    assert category == SAFE_FAILURE
    assert row["diagnostic_category"] == SAFE_FAILURE
    assert row["operator_next_step"] == "inspect_ibkr_permissions"


def test_forbidden_action_risk_field_true_is_not_safe_failure(tmp_path: Path):
    summary = tmp_path / "summary.csv"
    report = tmp_path / "report.md"
    _write_summary(
        summary,
        top_level_status="REAL_MARKETDATA_SMOKE_AUDIT_READY",
        final_safety_status="SAFETY_REVIEW_REQUIRED",
        historical_allowed="true",
    )
    _write_report(report)

    category, row = generate_archive(
        source_summary_file=summary,
        source_report_file=report,
        output_csv=tmp_path / "archive.csv",
        output_report=tmp_path / "archive.md",
    )

    assert category == FORBIDDEN_ACTION_RISK
    assert row["historical_data_request_allowed"] == "true"
    assert "historical_data_request_allowed_true" in row["diagnostic_reason"]


def test_forbidden_action_risk_fields_remain_false_for_ready_archive(tmp_path: Path):
    summary = tmp_path / "summary.csv"
    report = tmp_path / "report.md"
    _write_summary(
        summary,
        top_level_status="REAL_MARKETDATA_SMOKE_AUDIT_READY",
        final_safety_status="PASS_READ_ONLY_MARKETDATA_SMOKE_AUDITED",
    )
    _write_report(report)

    _, row = generate_archive(
        source_summary_file=summary,
        source_report_file=report,
        output_csv=tmp_path / "archive.csv",
        output_report=tmp_path / "archive.md",
    )

    for field in (
        "contract_qualification_allowed",
        "historical_data_request_allowed",
        "trading_actions_allowed",
        "account_read_allowed",
        "position_read_allowed",
        "telegram_send_allowed",
        "req_historical_data_allowed",
        "order_action_allowed",
        "cancel_action_allowed",
        "rebalance_action_allowed",
    ):
        assert row[field] == "false"


def test_wrapper_generates_archive_without_config_or_runtime_error_log(tmp_path: Path):
    summary = tmp_path / "summary.csv"
    report = tmp_path / "report.md"
    _write_summary(
        summary,
        top_level_status="REAL_MARKETDATA_SMOKE_AUDIT_READY",
        final_safety_status="PASS_READ_ONLY_MARKETDATA_SMOKE_AUDITED",
    )
    _write_report(report)
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
            "--source-report-file",
            str(report),
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
    assert _read_one_csv(tmp_path / "archive.csv")["diagnostic_category"] == PASS_READY
