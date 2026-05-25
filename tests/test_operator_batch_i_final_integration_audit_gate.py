from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_batch_i_final_integration_audit_gate import (
    AUDIT_FIELDS,
    generate_batch_i_final_integration_audit_gate,
)
from src.operator_batch_i_real_market_env_check import generate_batch_i_real_market_env_check
from src.operator_final_daily_packet import generate_final_daily_packet


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_batch_i_final_integration_audit_gate.sh"


def _read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_safe_unavailable_sources(tmp_path: Path) -> None:
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


def _write_batch_i_safe_unavailable_sources(tmp_path: Path) -> None:
    _write_safe_unavailable_sources(tmp_path)
    config = tmp_path / "config.yaml"
    errors = tmp_path / "ibkr_market_data_api_errors.csv"
    config.write_text(
        "\n".join(
            [
                "ibkr:",
                "  host: 127.0.0.1",
                "  port: 7496",
                "  client_id: 1",
                "  readonly: true",
                "  read_only_required: true",
                "  real_connection_allowed: false",
                "  market_data_request_allowed: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    errors.write_text(
        "symbol,error_code,error_message,status\n"
        "GLD,10089,Market data subscription missing,SAFE_UNAVAILABLE\n",
        encoding="utf-8",
    )
    generate_batch_i_real_market_env_check(
        config_path=config,
        api_errors_csv=errors,
        env_csv=tmp_path / "operator_batch_i_real_market_env_check.csv",
        permission_csv=tmp_path / "operator_batch_i_marketdata_permission_check.csv",
        review_csv=tmp_path / "operator_batch_i_safe_unavailable_review.csv",
        gate_csv=tmp_path / "operator_batch_i_real_market_env_gate.csv",
        env_report=tmp_path / "reports/operator_batch_i_real_market_env_check.md",
        permission_report=tmp_path / "reports/operator_batch_i_marketdata_permission_check.md",
        review_report=tmp_path / "reports/operator_batch_i_safe_unavailable_review.md",
        gate_report=tmp_path / "reports/operator_batch_i_real_market_env_gate_report.md",
        generated_at="2026-05-25T00:00:00+00:00",
    )
    generate_final_daily_packet(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_final_daily_packet.csv",
        output_report=tmp_path / "reports/operator_final_daily_packet.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )


def test_batch_i_final_integration_audit_passes_only_integration_gate(tmp_path: Path):
    _write_batch_i_safe_unavailable_sources(tmp_path)

    row = generate_batch_i_final_integration_audit_gate(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_batch_i_final_integration_audit_gate.csv",
        output_report=tmp_path / "reports/operator_batch_i_final_integration_audit_gate_report.md",
        generated_at="2026-05-25T00:02:00+00:00",
    )

    assert row["audit_gate_status"] == "PASS"
    assert row["batch_i_gate_status"] == "SAFE_UNAVAILABLE_REVIEW_REQUIRED"
    assert row["final_packet_batch_i_gate_status"] == "SAFE_UNAVAILABLE_REVIEW_REQUIRED"
    assert row["batch_i_status_consistent"] == "true"
    assert row["safe_unavailable_preserved"] == "true"
    assert row["production_ready_claim_detected"] == "false"
    for field in (
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
    assert set(_read_one(tmp_path / "operator_batch_i_final_integration_audit_gate.csv")) == set(AUDIT_FIELDS)

    report = (tmp_path / "reports/operator_batch_i_final_integration_audit_gate_report.md").read_text(encoding="utf-8")
    assert "not live production PASS" in report
    assert "not real market data PASS" in report
    assert "trading_actions_allowed=false" in report


def test_batch_i_final_integration_audit_detects_batch_i_ready_promotion(tmp_path: Path):
    _write_batch_i_safe_unavailable_sources(tmp_path)
    packet_path = tmp_path / "operator_final_daily_packet.csv"
    packet = packet_path.read_text(encoding="utf-8")
    packet_path.write_text(packet.replace("SAFE_UNAVAILABLE_REVIEW_REQUIRED", "PRODUCTION_READY", 1), encoding="utf-8")

    row = generate_batch_i_final_integration_audit_gate(
        base_dir=tmp_path,
        output_csv=tmp_path / "audit.csv",
        output_report=tmp_path / "audit.md",
    )

    assert row["audit_gate_status"] == "BATCH_I_FINAL_INTEGRATION_AUDIT_REVIEW_REQUIRED"
    assert row["batch_i_status_consistent"] == "false"
    assert row["safe_unavailable_preserved"] == "false"
    assert row["production_ready_claim_detected"] == "true"


def test_batch_i_final_integration_main_cli_generates_outputs(tmp_path: Path):
    _write_batch_i_safe_unavailable_sources(tmp_path)
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
            "--batch-i-final-integration-audit-gate",
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
    assert _read_one(tmp_path / "operator_batch_i_final_integration_audit_gate.csv")["audit_gate_status"] == "PASS"
    assert (tmp_path / "reports/operator_batch_i_final_integration_audit_gate_report.md").exists()


def test_batch_i_final_integration_wrapper_generates_csv(tmp_path: Path):
    _write_batch_i_safe_unavailable_sources(tmp_path)
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
