from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_multi_market_final_audit_freeze_summary import (
    AUDIT_FIELDS,
    READY_STATUS,
    build_multi_market_final_audit_row,
    generate_multi_market_final_audit_freeze_summary,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_multi_market_final_audit_freeze_summary.sh"


def _read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_sources(tmp_path: Path) -> None:
    (tmp_path / "reports").mkdir(exist_ok=True)
    (tmp_path / "operator_batch_i_final_integration_audit_gate.csv").write_text(
        "generated_at,audit_gate_status,batch_i_gate_status,final_packet_batch_i_gate_status,trading_actions_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:00:00+00:00,PASS,SAFE_UNAVAILABLE_REVIEW_REQUIRED,SAFE_UNAVAILABLE_REVIEW_REQUIRED,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_batch_j_final_integration_audit_gate.csv").write_text(
        "generated_at,audit_gate_status,batch_j_gate_status,final_packet_batch_j_gate_status,batch_j_threshold_profile_status,strategy_auto_execution_allowed,trading_actions_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:01:00+00:00,PASS,PASS,PASS,BATCH_J_THRESHOLD_PROFILE_REVIEW_ONLY,false,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_dashboard_artifact_reader.csv").write_text(
        "generated_at,dashboard_status,final_packet_status,multi_market_schema_gate_status,multi_market_adapter_gate_status,real_market_data_verified,strategy_execution_ready,trading_actions_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:02:00+00:00,DASHBOARD_ARTIFACT_READER_READY,FINAL_PACKET_SAFE_UNAVAILABLE,MULTI_MARKET_SYMBOL_SCHEMA_READY,MULTI_MARKET_ADAPTER_SKELETON_READY,false,false,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_telegram_dry_run_payload.csv").write_text(
        "generated_at,telegram_payload_status,no_real_send,telegram_real_send_allowed,trading_actions_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:03:00+00:00,TELEGRAM_DRY_RUN_READY,true,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_telegram_approval_gate.csv").write_text(
        "generated_at,approval_gate_status,telegram_payload_status,no_real_send,telegram_real_send_allowed,trading_actions_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:04:00+00:00,TELEGRAM_APPROVAL_REVIEW_REQUIRED,TELEGRAM_DRY_RUN_READY,true,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_telegram_manual_send_archive.csv").write_text(
        "generated_at,manual_send_archive_status,telegram_payload_status,approval_gate_status,no_real_send,send_executed,telegram_real_send_allowed,trading_actions_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:05:00+00:00,TELEGRAM_MANUAL_SEND_ARCHIVE_READY,TELEGRAM_DRY_RUN_READY,TELEGRAM_APPROVAL_REVIEW_REQUIRED,true,false,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_multi_market_symbol_schema_gate.csv").write_text(
        "generated_at,schema_gate_status,no_account_or_position_read,no_historical_data_request,no_real_telegram_send,manual_only,research_only,observation_only\n"
        "2026-05-25T00:06:00+00:00,MULTI_MARKET_SYMBOL_SCHEMA_READY,true,true,true,true,true,true\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_multi_market_adapter_gate.csv").write_text(
        "generated_at,adapter_gate_status,multi_market_schema_gate_status,no_real_market_data_request,no_contract_qualification,no_account_or_position_read,no_historical_data_request,no_real_telegram_send,no_trading_actions,manual_only,research_only,observation_only\n"
        "2026-05-25T00:07:00+00:00,MULTI_MARKET_ADAPTER_SKELETON_READY,MULTI_MARKET_SYMBOL_SCHEMA_READY,true,true,true,true,true,true,true,true,true\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_final_daily_packet.csv").write_text(
        "generated_at,final_packet_status,real_market_data_verified,strategy_execution_ready,trading_actions_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:08:00+00:00,FINAL_PACKET_SAFE_UNAVAILABLE,false,false,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )
    for report in (
        "operator_final_daily_packet.md",
        "operator_dashboard_artifact_reader.md",
        "operator_telegram_manual_send_archive_report.md",
        "operator_multi_market_adapter_gate_report.md",
    ):
        (tmp_path / "reports" / report).write_text(
            "# Report\n\n- manual-only\n- not live production\n- auto_trade_allowed=false\n",
            encoding="utf-8",
        )


def test_final_audit_ready_outputs_csv_report_and_freeze_summary(tmp_path: Path) -> None:
    _write_sources(tmp_path)

    row = generate_multi_market_final_audit_freeze_summary(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_multi_market_final_audit_gate.csv",
        output_report=tmp_path / "reports/operator_multi_market_final_audit_gate_report.md",
        freeze_summary=tmp_path / "Precious_Metals_Monitor_Phase468-512_Post_MVP_Multi_Market_Freeze_Summary.md",
        generated_at="2026-05-25T00:09:00+00:00",
    )

    assert row["final_audit_status"] == READY_STATUS
    assert row["batch_i_status"] == "PASS"
    assert row["batch_j_status"] == "PASS"
    assert row["batch_k_dashboard_status"] == "DASHBOARD_ARTIFACT_READER_READY"
    assert row["batch_l_telegram_status"] == "TELEGRAM_DRY_RUN_APPROVAL_ARCHIVE_READY"
    assert row["batch_m_schema_status"] == "MULTI_MARKET_SYMBOL_SCHEMA_READY"
    assert row["batch_m_adapter_status"] == "MULTI_MARKET_ADAPTER_SKELETON_READY"
    for field in (
        "real_market_data_verified",
        "live_production_ready",
        "strategy_execution_ready",
        "auto_trade_allowed",
        "telegram_real_send_allowed",
        "account_read_allowed",
        "position_read_allowed",
        "historical_data_request_allowed",
        "trading_actions_allowed",
    ):
        assert row[field] == "false"
    for field in ("manual_only", "research_only", "observation_only"):
        assert row[field] == "true"

    csv_row = _read_one(tmp_path / "operator_multi_market_final_audit_gate.csv")
    assert set(csv_row) == set(AUDIT_FIELDS)
    report = (tmp_path / "reports/operator_multi_market_final_audit_gate_report.md").read_text(encoding="utf-8")
    summary = (tmp_path / "Precious_Metals_Monitor_Phase468-512_Post_MVP_Multi_Market_Freeze_Summary.md").read_text(encoding="utf-8")
    assert "POST_MVP_MULTI_MARKET_FREEZE_READY" in report
    assert "POST_MVP_MULTI_MARKET_FREEZE_READY" in summary
    assert "manual-only" in report
    assert "manual-only" in summary
    assert "not live production" in report
    assert "not live production" in summary
    assert "auto_trade_allowed=false" in report
    assert "account_read_allowed=false" in report
    assert "position_read_allowed=false" in report
    assert "historical_data_request_allowed=false" in report
    assert "telegram_real_send_allowed=false" in report
    assert "trading_actions_allowed=false" in report
    assert "PR #185" in summary
    assert "PR #195" in summary


def test_final_audit_review_required_when_required_artifact_missing(tmp_path: Path) -> None:
    _write_sources(tmp_path)
    (tmp_path / "operator_dashboard_artifact_reader.csv").unlink()

    row = build_multi_market_final_audit_row(base_dir=tmp_path, generated_at="2026-05-25T00:09:00+00:00")

    assert row["final_audit_status"] == "POST_MVP_MULTI_MARKET_FREEZE_REVIEW_REQUIRED"
    assert "operator_dashboard_artifact_reader.csv" in row["diagnostic_reason"]


def test_final_audit_no_go_when_auto_trade_allowed(tmp_path: Path) -> None:
    _write_sources(tmp_path)
    packet = tmp_path / "operator_final_daily_packet.csv"
    packet.write_text(
        "generated_at,final_packet_status,auto_trade_allowed,trading_actions_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:08:00+00:00,FINAL_PACKET_SAFE_UNAVAILABLE,true,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )

    row = build_multi_market_final_audit_row(base_dir=tmp_path, generated_at="2026-05-25T00:09:00+00:00")

    assert row["final_audit_status"] == "POST_MVP_MULTI_MARKET_FREEZE_NO_GO"
    assert row["auto_trade_allowed"] == "true"


def test_final_audit_main_cli_and_wrapper(tmp_path: Path) -> None:
    _write_sources(tmp_path)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))

    result = subprocess.run(
        [
            env["PYTHON"],
            str(REPO_ROOT / "main.py"),
            "--config",
            str(REPO_ROOT / "config.yaml"),
            "--watchlist",
            str(REPO_ROOT / "watchlist.yaml"),
            "--multi-market-final-audit-freeze-summary",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "final_audit_status=POST_MVP_MULTI_MARKET_FREEZE_READY" in result.stdout
    assert (tmp_path / "operator_multi_market_final_audit_gate.csv").exists()
    assert (tmp_path / "reports/operator_multi_market_final_audit_gate_report.md").exists()
    assert (tmp_path / "Precious_Metals_Monitor_Phase468-512_Post_MVP_Multi_Market_Freeze_Summary.md").exists()

    wrapper_result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--base-dir",
            str(tmp_path),
            "--output-csv",
            str(tmp_path / "wrapper_audit.csv"),
            "--output-report",
            str(tmp_path / "reports/wrapper_audit.md"),
            "--freeze-summary",
            str(tmp_path / "wrapper_summary.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert wrapper_result.returncode == 0, wrapper_result.stdout
    assert _read_one(tmp_path / "wrapper_audit.csv")["final_audit_status"] == READY_STATUS
