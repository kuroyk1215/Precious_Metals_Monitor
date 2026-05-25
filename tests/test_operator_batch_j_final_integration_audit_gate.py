from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_batch_j_final_integration_audit_gate import (
    AUDIT_FIELDS,
    generate_batch_j_final_integration_audit_gate,
)
from src.operator_batch_j_strategy_threshold_refinement import generate_batch_j_strategy_threshold_refinement
from src.operator_final_daily_packet import generate_final_daily_packet


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_batch_j_final_integration_audit_gate.sh"


def _read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_final_packet_sources(tmp_path: Path) -> None:
    (tmp_path / "operator_daily_master_run_summary.csv").write_text(
        "generated_at,master_status,safety_clean,real_quote_available,quote_unavailable,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,MASTER_SAFE_UNAVAILABLE,true,false,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_mvp_readiness_report.csv").write_text(
        "generated_at,readiness_status,safety_clean,real_quote_available,safe_unavailable,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,MVP_SAFE_UNAVAILABLE,true,false,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_strategy_explanation_upgrade.csv").write_text(
        "generated_at,symbol,explanation_status,manual_review_required,strategy_explanation,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,GLD,WHY_HOLD_SAFE_UNAVAILABLE,true,Real quote context unavailable; review only,false,false,false,false,false,false,false,false\n"
        "2026-05-25T00:00:00+00:00,SLV,WHY_HOLD_SAFE_UNAVAILABLE,true,Real quote context unavailable; review only,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_strategy_quality_report.csv").write_text(
        "generated_at,quality_status,data_unavailable_but_safe,manual_review_only,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,DATA_UNAVAILABLE_BUT_SAFE,true,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_daily_checklist.csv").write_text(
        "generated_at,step_order,check_name,manual_review_only,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,1,review packet,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_market_mvp_status.csv").write_text(
        "generated_at,mvp_status,real_quote_available,safe_unavailable,manual_review_only,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,MVP_SAFE_UNAVAILABLE,false,true,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "reports").mkdir(exist_ok=True)
    (tmp_path / "operator_batch_i_final_integration_audit_gate.csv").write_text(
        "generated_at,audit_gate_status,batch_i_gate_status,final_packet_batch_i_gate_status,batch_i_status_consistent,safe_unavailable_preserved,production_ready_claim_detected,trading_actions_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,manual_only,research_only,observation_only,diagnostic_reason\n"
        "2026-05-25T00:02:00+00:00,PASS,SAFE_UNAVAILABLE_REVIEW_REQUIRED,SAFE_UNAVAILABLE_REVIEW_REQUIRED,true,true,false,false,false,false,false,false,false,false,false,true,true,true,integration_audit_pass_only_not_live_production_or_real_market_data_pass\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_final_daily_packet.csv").write_text(
        "generated_at,batch_i_env_gate_status,trading_actions_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:01:00+00:00,SAFE_UNAVAILABLE_REVIEW_REQUIRED,false,false,false,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )
    (tmp_path / "reports/operator_final_daily_packet.md").write_text(
        "# Operator Final Daily Packet\n\n- batch_i_env_gate_status=SAFE_UNAVAILABLE_REVIEW_REQUIRED\n",
        encoding="utf-8",
    )
    generate_batch_j_strategy_threshold_refinement(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_batch_j_strategy_threshold_refinement.csv",
        output_report=tmp_path / "reports/operator_batch_j_strategy_threshold_refinement_report.md",
        gate_csv=tmp_path / "operator_batch_j_strategy_threshold_gate.csv",
        gate_report=tmp_path / "reports/operator_batch_j_strategy_threshold_gate_report.md",
        generated_at="2026-05-25T00:03:00+00:00",
    )
    generate_final_daily_packet(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_final_daily_packet.csv",
        output_report=tmp_path / "reports/operator_final_daily_packet.md",
        generated_at="2026-05-25T00:04:00+00:00",
    )


def test_batch_j_final_integration_audit_passes_only_integration_gate(tmp_path: Path):
    _write_final_packet_sources(tmp_path)

    row = generate_batch_j_final_integration_audit_gate(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_batch_j_final_integration_audit_gate.csv",
        output_report=tmp_path / "reports/operator_batch_j_final_integration_audit_gate_report.md",
        generated_at="2026-05-25T00:05:00+00:00",
    )

    assert row["audit_gate_status"] == "PASS"
    assert row["batch_j_gate_status"] == "PASS"
    assert row["final_packet_batch_j_gate_status"] == "PASS"
    assert row["batch_j_threshold_profile_status"] == "BATCH_J_THRESHOLD_PROFILE_REVIEW_ONLY"
    assert row["final_packet_batch_j_threshold_profile_status"] == "BATCH_J_THRESHOLD_PROFILE_REVIEW_ONLY"
    assert row["batch_j_status_consistent"] == "true"
    assert row["safe_unavailable_preserved"] == "true"
    assert row["review_only_preserved"] == "true"
    assert row["production_ready_claim_detected"] == "false"
    for field in (
        "strategy_auto_execution_allowed",
        "trading_actions_allowed",
        "order_action_allowed",
        "cancel_action_allowed",
        "rebalance_action_allowed",
        "account_read_allowed",
        "position_read_allowed",
        "historical_data_request_allowed",
        "telegram_real_send_allowed",
    ):
        assert row[field] == "false"
    for field in ("manual_only", "research_only", "observation_only"):
        assert row[field] == "true"
    assert set(_read_one(tmp_path / "operator_batch_j_final_integration_audit_gate.csv")) == set(AUDIT_FIELDS)
    report = (tmp_path / "reports/operator_batch_j_final_integration_audit_gate_report.md").read_text(encoding="utf-8")
    assert "not live production PASS" in report
    assert "not real market data PASS" in report
    assert "not strategy execution PASS" in report
    assert "trading_actions_allowed=false" in report


def test_batch_j_final_integration_audit_detects_final_packet_mismatch(tmp_path: Path):
    _write_final_packet_sources(tmp_path)
    packet_path = tmp_path / "operator_final_daily_packet.csv"
    packet_path.write_text(packet_path.read_text(encoding="utf-8").replace(",PASS,", ",LIVE_READY,", 1), encoding="utf-8")

    row = generate_batch_j_final_integration_audit_gate(
        base_dir=tmp_path,
        output_csv=tmp_path / "audit.csv",
        output_report=tmp_path / "audit.md",
    )

    assert row["audit_gate_status"] == "BATCH_J_FINAL_INTEGRATION_AUDIT_REVIEW_REQUIRED"
    assert row["batch_j_status_consistent"] == "false"
    assert row["production_ready_claim_detected"] == "true"


def test_batch_j_final_integration_main_cli_generates_outputs(tmp_path: Path):
    _write_final_packet_sources(tmp_path)
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
            "--batch-j-final-integration-audit-gate",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "audit_gate_status=PASS" in result.stdout
    assert _read_one(tmp_path / "operator_batch_j_final_integration_audit_gate.csv")["audit_gate_status"] == "PASS"


def test_batch_j_final_integration_wrapper_generates_csv(tmp_path: Path):
    _write_final_packet_sources(tmp_path)
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
            str(tmp_path / "audit.csv"),
            "--output-report",
            str(tmp_path / "audit.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_one(tmp_path / "audit.csv")["audit_gate_status"] == "PASS"
