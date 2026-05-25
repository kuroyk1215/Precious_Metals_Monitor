from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path

from src.operator_telegram_dry_run_payload import (
    APPROVAL_FIELDS,
    DRY_RUN_FIELDS,
    generate_telegram_approval_gate,
    generate_telegram_dry_run_payload,
)


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


def test_telegram_dry_run_payload_outputs_safe_draft_artifacts(tmp_path: Path):
    _write_dashboard_sources(tmp_path)

    row = generate_telegram_dry_run_payload(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_telegram_dry_run_payload.csv",
        output_json=tmp_path / "operator_telegram_dry_run_payload.json",
        output_report=tmp_path / "reports/operator_telegram_dry_run_payload.md",
        generated_at="2026-05-25T00:07:00+00:00",
    )

    assert row["telegram_payload_status"] == "TELEGRAM_DRY_RUN_READY"
    assert row["dashboard_status"] == "DASHBOARD_ARTIFACT_READER_READY"
    assert row["final_packet_status"] == "FINAL_PACKET_SAFE_UNAVAILABLE"
    assert row["batch_i_env_gate_status"] == "SAFE_UNAVAILABLE_REVIEW_REQUIRED"
    assert row["batch_j_threshold_profile_status"] == "BATCH_J_THRESHOLD_PROFILE_REVIEW_ONLY"
    assert row["safe_unavailable_status"] == "SAFE_UNAVAILABLE_REVIEW_REQUIRED"
    assert row["dry_run_only"] == "true"
    assert row["no_real_send"] == "true"
    assert row["manual_approval_required"] == "true"
    assert row["telegram_real_send_allowed"] == "false"
    for field in (
        "trading_actions_allowed",
        "order_action_allowed",
        "cancel_action_allowed",
        "rebalance_action_allowed",
        "account_read_allowed",
        "position_read_allowed",
        "historical_data_request_allowed",
    ):
        assert row[field] == "false"
    for field in ("manual_only", "research_only", "observation_only"):
        assert row[field] == "true"

    body = row["message_body"]
    assert "SAFE_UNAVAILABLE_REVIEW_REQUIRED" in body
    assert "Manual-only, research-only, observation-only" in body
    assert "No auto trade" in body
    assert "No real Telegram send" in body
    for forbidden in ("TELEGRAM_SEND_READY", "AUTO_SEND_READY", "SENT", "production ready", "live ready", "execution ready"):
        assert forbidden not in body

    csv_row = _read_one(tmp_path / "operator_telegram_dry_run_payload.csv")
    assert set(csv_row) == set(DRY_RUN_FIELDS)
    json_row = json.loads((tmp_path / "operator_telegram_dry_run_payload.json").read_text(encoding="utf-8"))
    assert json_row["telegram_payload_status"] == "TELEGRAM_DRY_RUN_READY"
    report = (tmp_path / "reports/operator_telegram_dry_run_payload.md").read_text(encoding="utf-8")
    assert "telegram_real_send_allowed=false" in report
    assert "manual_approval_required=true" in report
    assert "no_real_send=true" in report


def test_telegram_approval_gate_requires_human_review_for_dry_run_payload(tmp_path: Path):
    _write_dashboard_sources(tmp_path)
    generate_telegram_dry_run_payload(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_telegram_dry_run_payload.csv",
        output_json=tmp_path / "operator_telegram_dry_run_payload.json",
        output_report=tmp_path / "reports/operator_telegram_dry_run_payload.md",
        generated_at="2026-05-25T00:07:00+00:00",
    )

    row = generate_telegram_approval_gate(
        payload_csv=tmp_path / "operator_telegram_dry_run_payload.csv",
        payload_json=tmp_path / "operator_telegram_dry_run_payload.json",
        output_csv=tmp_path / "operator_telegram_approval_gate.csv",
        output_report=tmp_path / "reports/operator_telegram_approval_gate_report.md",
        generated_at="2026-05-25T00:08:00+00:00",
    )

    assert row["approval_gate_status"] == "TELEGRAM_APPROVAL_REVIEW_REQUIRED"
    assert row["telegram_payload_status"] == "TELEGRAM_DRY_RUN_READY"
    assert row["dry_run_payload_present"] == "true"
    assert row["manual_approval_required"] == "true"
    assert row["no_real_send"] == "true"
    assert row["telegram_real_send_allowed"] == "false"
    assert row["production_ready_claim_detected"] == "false"
    assert row["execution_ready_claim_detected"] == "false"
    assert row["trading_actions_allowed"] == "false"
    assert row["account_read_allowed"] == "false"
    assert row["position_read_allowed"] == "false"
    assert row["historical_data_request_allowed"] == "false"
    assert row["manual_only"] == "true"
    assert row["research_only"] == "true"
    assert row["observation_only"] == "true"

    csv_row = _read_one(tmp_path / "operator_telegram_approval_gate.csv")
    assert set(csv_row) == set(APPROVAL_FIELDS)
    report = (tmp_path / "reports/operator_telegram_approval_gate_report.md").read_text(encoding="utf-8")
    assert "TELEGRAM_APPROVAL_REVIEW_REQUIRED" in report
    assert "telegram_real_send_allowed=false" in report


def test_telegram_main_cli_generates_payload_and_gate(tmp_path: Path):
    _write_dashboard_sources(tmp_path)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))

    payload_result = subprocess.run(
        [
            env["PYTHON"],
            str(REPO_ROOT / "main.py"),
            "--config",
            str(REPO_ROOT / "config.yaml"),
            "--watchlist",
            str(REPO_ROOT / "watchlist.yaml"),
            "--telegram-dry-run-payload",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert payload_result.returncode == 0, payload_result.stdout
    assert "telegram_payload_status=TELEGRAM_DRY_RUN_READY" in payload_result.stdout

    gate_result = subprocess.run(
        [
            env["PYTHON"],
            str(REPO_ROOT / "main.py"),
            "--config",
            str(REPO_ROOT / "config.yaml"),
            "--watchlist",
            str(REPO_ROOT / "watchlist.yaml"),
            "--telegram-approval-gate",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert gate_result.returncode == 0, gate_result.stdout
    assert "approval_gate_status=TELEGRAM_APPROVAL_REVIEW_REQUIRED" in gate_result.stdout
    assert (tmp_path / "operator_telegram_dry_run_payload.csv").exists()
    assert (tmp_path / "operator_telegram_dry_run_payload.json").exists()
    assert (tmp_path / "reports/operator_telegram_dry_run_payload.md").exists()
    assert (tmp_path / "operator_telegram_approval_gate.csv").exists()
    assert (tmp_path / "reports/operator_telegram_approval_gate_report.md").exists()
