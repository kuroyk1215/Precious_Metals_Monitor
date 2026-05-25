from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path

from src.operator_dashboard_artifact_reader import DASHBOARD_FIELDS, generate_dashboard_artifact_reader


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_dashboard_sources(tmp_path: Path) -> None:
    (tmp_path / "reports").mkdir(exist_ok=True)
    (tmp_path / "operator_final_daily_packet.csv").write_text(
        "generated_at,final_packet_status,batch_i_env_gate_status,batch_i_safe_unavailable_review_status,batch_j_gate_status,batch_j_threshold_profile_status,batch_j_production_ready_claim_detected,trading_actions_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:00:00+00:00,FINAL_PACKET_SAFE_UNAVAILABLE,SAFE_UNAVAILABLE_REVIEW_REQUIRED,SAFE_UNAVAILABLE_REVIEW_REQUIRED,PASS,BATCH_J_THRESHOLD_PROFILE_REVIEW_ONLY,false,false,false,false,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )
    (tmp_path / "reports/operator_final_daily_packet.md").write_text(
        "# Operator Final Daily Packet\n\n"
        "- batch_i_env_gate_status=SAFE_UNAVAILABLE_REVIEW_REQUIRED\n"
        "- batch_j_gate_status=PASS\n"
        "- batch_j_threshold_profile_status=BATCH_J_THRESHOLD_PROFILE_REVIEW_ONLY\n"
        "- production_ready_claim_detected=false\n"
        "- trading_actions_allowed=false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_batch_i_final_integration_audit_gate.csv").write_text(
        "generated_at,audit_gate_status,batch_i_gate_status,final_packet_batch_i_gate_status,production_ready_claim_detected,trading_actions_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:01:00+00:00,PASS,SAFE_UNAVAILABLE_REVIEW_REQUIRED,SAFE_UNAVAILABLE_REVIEW_REQUIRED,false,false,false,false,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_batch_j_final_integration_audit_gate.csv").write_text(
        "generated_at,audit_gate_status,batch_j_gate_status,final_packet_batch_j_gate_status,batch_j_threshold_profile_status,production_ready_claim_detected,strategy_auto_execution_allowed,trading_actions_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:02:00+00:00,PASS,PASS,PASS,BATCH_J_THRESHOLD_PROFILE_REVIEW_ONLY,false,false,false,false,false,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_batch_j_strategy_threshold_gate.csv").write_text(
        "generated_at,gate_status,threshold_profile_status,batch_i_env_gate_status,batch_i_audit_gate_status,safe_unavailable_preserved,production_ready_claim_detected,strategy_auto_execution_allowed,trading_actions_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:03:00+00:00,PASS,BATCH_J_THRESHOLD_PROFILE_REVIEW_ONLY,SAFE_UNAVAILABLE_REVIEW_REQUIRED,PASS,true,false,false,false,false,false,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_mvp_final_audit_gate.csv").write_text(
        "generated_at,audit_gate_status,trading_actions_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:04:00+00:00,PASS,false,false,false,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_market_mvp_completion_gate.csv").write_text(
        "generated_at,completion_gate_status,trading_actions_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,manual_only,research_only,observation_only\n"
        "2026-05-25T00:05:00+00:00,PASS,false,false,false,false,false,false,false,false,true,true,true\n",
        encoding="utf-8",
    )


def test_dashboard_artifact_reader_outputs_review_only_ready_summary(tmp_path: Path):
    _write_dashboard_sources(tmp_path)

    row = generate_dashboard_artifact_reader(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_dashboard_artifact_reader.csv",
        output_json=tmp_path / "operator_dashboard_artifact_reader.json",
        output_report=tmp_path / "reports/operator_dashboard_artifact_reader.md",
        generated_at="2026-05-25T00:06:00+00:00",
    )

    assert row["dashboard_status"] == "DASHBOARD_ARTIFACT_READER_READY"
    assert row["final_packet_status"] == "FINAL_PACKET_SAFE_UNAVAILABLE"
    assert row["batch_i_env_gate_status"] == "SAFE_UNAVAILABLE_REVIEW_REQUIRED"
    assert row["batch_i_audit_gate_status"] == "PASS"
    assert row["batch_j_gate_status"] == "PASS"
    assert row["batch_j_threshold_profile_status"] == "BATCH_J_THRESHOLD_PROFILE_REVIEW_ONLY"
    assert row["batch_j_audit_gate_status"] == "PASS"
    assert row["safe_unavailable_status"] == "SAFE_UNAVAILABLE_REVIEW_REQUIRED"
    assert row["production_ready_claim_detected"] == "false"
    assert row["real_market_data_verified"] == "false"
    assert row["strategy_execution_ready"] == "false"
    assert row["operator_display_mode"] == "SAFE_UNAVAILABLE_REVIEW_ONLY"
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

    csv_row = _read_one(tmp_path / "operator_dashboard_artifact_reader.csv")
    assert set(csv_row) == set(DASHBOARD_FIELDS)
    json_row = json.loads((tmp_path / "operator_dashboard_artifact_reader.json").read_text(encoding="utf-8"))
    assert json_row["dashboard_status"] == "DASHBOARD_ARTIFACT_READER_READY"
    report = (tmp_path / "reports/operator_dashboard_artifact_reader.md").read_text(encoding="utf-8")
    assert "trading_actions_allowed=false" in report
    assert "account_read_allowed=false" in report
    assert "position_read_allowed=false" in report
    assert "historical_data_request_allowed=false" in report
    assert "telegram_real_send_allowed=false" in report
    assert "web service" in report


def test_dashboard_artifact_reader_requires_review_when_key_artifacts_missing(tmp_path: Path):
    _write_dashboard_sources(tmp_path)
    (tmp_path / "operator_batch_j_final_integration_audit_gate.csv").unlink()

    row = generate_dashboard_artifact_reader(
        base_dir=tmp_path,
        output_csv=tmp_path / "reader.csv",
        output_json=tmp_path / "reader.json",
        output_report=tmp_path / "reader.md",
    )

    assert row["dashboard_status"] == "DASHBOARD_ARTIFACT_READER_REVIEW_REQUIRED"
    assert row["operator_display_mode"] == "DASHBOARD_REVIEW_REQUIRED"
    assert "operator_batch_j_final_integration_audit_gate.csv" in row["diagnostic_reason"]


def test_dashboard_artifact_reader_no_go_on_ready_claim(tmp_path: Path):
    _write_dashboard_sources(tmp_path)
    packet = tmp_path / "operator_final_daily_packet.csv"
    packet.write_text(
        packet.read_text(encoding="utf-8").replace("false,false,false,false,false,false", "LIVE_READY,false,false,false,false,false", 1),
        encoding="utf-8",
    )

    row = generate_dashboard_artifact_reader(
        base_dir=tmp_path,
        output_csv=tmp_path / "reader.csv",
        output_json=tmp_path / "reader.json",
        output_report=tmp_path / "reader.md",
    )

    assert row["dashboard_status"] == "DASHBOARD_ARTIFACT_READER_NO_GO"
    assert row["operator_display_mode"] == "DASHBOARD_NO_GO"
    assert row["production_ready_claim_detected"] == "true"
    assert row["strategy_execution_ready"] == "false"


def test_dashboard_artifact_reader_main_cli_generates_outputs(tmp_path: Path):
    _write_dashboard_sources(tmp_path)
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
            "--dashboard-artifact-reader",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "dashboard_status=DASHBOARD_ARTIFACT_READER_READY" in result.stdout
    assert (tmp_path / "operator_dashboard_artifact_reader.csv").exists()
    assert (tmp_path / "operator_dashboard_artifact_reader.json").exists()
    assert (tmp_path / "reports/operator_dashboard_artifact_reader.md").exists()
