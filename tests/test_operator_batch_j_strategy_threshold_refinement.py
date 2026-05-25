from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_batch_j_strategy_threshold_refinement import (
    GATE_FIELDS,
    REFINEMENT_FIELDS,
    generate_batch_j_strategy_threshold_refinement,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_batch_j_strategy_threshold_refinement.sh"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_batch_i_safe_unavailable_outputs(tmp_path: Path) -> None:
    (tmp_path / "reports").mkdir()
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


def test_batch_j_strategy_threshold_refinement_generates_review_only_framework(tmp_path: Path):
    _write_batch_i_safe_unavailable_outputs(tmp_path)

    result = generate_batch_j_strategy_threshold_refinement(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_batch_j_strategy_threshold_refinement.csv",
        output_report=tmp_path / "reports/operator_batch_j_strategy_threshold_refinement_report.md",
        gate_csv=tmp_path / "operator_batch_j_strategy_threshold_gate.csv",
        gate_report=tmp_path / "reports/operator_batch_j_strategy_threshold_gate_report.md",
        generated_at="2026-05-25T00:03:00+00:00",
    )

    rows = result["rows"]
    gate = result["gate"]
    assert [row["symbol"] for row in rows] == ["GLD", "SLV"]
    assert gate["gate_status"] == "PASS"
    assert gate["batch_i_env_gate_status"] == "SAFE_UNAVAILABLE_REVIEW_REQUIRED"
    assert gate["safe_unavailable_preserved"] == "true"
    assert gate["production_ready_claim_detected"] == "false"
    assert gate["strategy_auto_execution_allowed"] == "false"
    for row in rows:
        assert row["spread_status"] == "unavailable"
        assert row["range_status"] == "unavailable"
        assert row["signal_quality"] == "low"
        assert row["risk_label"] == "safe_unavailable"
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

    assert set(_read_rows(tmp_path / "operator_batch_j_strategy_threshold_refinement.csv")[0]) == set(REFINEMENT_FIELDS)
    assert set(_read_rows(tmp_path / "operator_batch_j_strategy_threshold_gate.csv")[0]) == set(GATE_FIELDS)

    refinement_report = (tmp_path / "reports/operator_batch_j_strategy_threshold_refinement_report.md").read_text(
        encoding="utf-8"
    )
    gate_report = (tmp_path / "reports/operator_batch_j_strategy_threshold_gate_report.md").read_text(encoding="utf-8")
    assert "SAFE_UNAVAILABLE_REVIEW_REQUIRED" in refinement_report
    assert "trading_actions_allowed=false" in refinement_report
    assert "PASS does not mean live production ready" in gate_report
    assert "historical_data_request_allowed=false" in gate_report


def test_batch_j_strategy_threshold_refinement_blocks_production_ready_promotion(tmp_path: Path):
    _write_batch_i_safe_unavailable_outputs(tmp_path)
    packet_path = tmp_path / "operator_final_daily_packet.csv"
    packet_path.write_text(
        packet_path.read_text(encoding="utf-8").replace("SAFE_UNAVAILABLE_REVIEW_REQUIRED", "PRODUCTION_READY", 1),
        encoding="utf-8",
    )

    result = generate_batch_j_strategy_threshold_refinement(
        base_dir=tmp_path,
        output_csv=tmp_path / "refinement.csv",
        output_report=tmp_path / "refinement.md",
        gate_csv=tmp_path / "gate.csv",
        gate_report=tmp_path / "gate.md",
    )

    gate = result["gate"]
    assert gate["gate_status"] == "BATCH_J_THRESHOLD_GATE_REVIEW_REQUIRED"
    assert gate["production_ready_claim_detected"] == "true"
    assert gate["trading_actions_allowed"] == "false"


def test_batch_j_strategy_threshold_main_cli_generates_outputs(tmp_path: Path):
    _write_batch_i_safe_unavailable_outputs(tmp_path)
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
            "--batch-j-strategy-threshold-refinement",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "gate_status=PASS" in result.stdout
    assert _read_rows(tmp_path / "operator_batch_j_strategy_threshold_gate.csv")[0]["gate_status"] == "PASS"
    assert (tmp_path / "reports/operator_batch_j_strategy_threshold_gate_report.md").exists()


def test_batch_j_strategy_threshold_wrapper_generates_gate(tmp_path: Path):
    _write_batch_i_safe_unavailable_outputs(tmp_path)
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
            str(tmp_path / "refinement.csv"),
            "--output-report",
            str(tmp_path / "refinement.md"),
            "--gate-csv",
            str(tmp_path / "gate.csv"),
            "--gate-report",
            str(tmp_path / "gate.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_rows(tmp_path / "gate.csv")[0]["gate_status"] == "PASS"
