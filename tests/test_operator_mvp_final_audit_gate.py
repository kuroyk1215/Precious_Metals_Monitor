from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_daily_freeze_report import generate_daily_freeze_report
from src.operator_mvp_codebase_map import generate_mvp_codebase_map
from src.operator_mvp_final_audit_gate import AUDIT_FIELDS, generate_mvp_final_audit_gate


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_mvp_final_audit_gate.sh"


def _read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_audit_sources(tmp_path: Path) -> None:
    generate_mvp_codebase_map(
        output_csv=tmp_path / "operator_mvp_codebase_map.csv",
        output_report=tmp_path / "reports/operator_mvp_codebase_map.md",
        generated_at="2026-05-25T00:00:00+00:00",
    )
    (tmp_path / "operator_final_daily_packet.csv").write_text(
        "generated_at,final_packet_status,safety_status,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,FINAL_PACKET_SAFE_UNAVAILABLE,SAFETY_CLEAN,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_latest_strategy_decision.csv").write_text(
        "generated_at,latest_decision_status,manual_action_required,auto_trade_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,LATEST_HOLD_SAFE_UNAVAILABLE,true,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_market_mvp_completion_gate.csv").write_text(
        "generated_at,completion_gate_status,safety_status,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,MVP_COMPLETION_SAFE_UNAVAILABLE,SAFETY_CLEAN,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_daily_checklist.csv").write_text(
        "generated_at,step_order,check_name,manual_review_only,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,1,review packet,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    generate_daily_freeze_report(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_daily_freeze_report.csv",
        output_report=tmp_path / "reports/operator_daily_freeze_report.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )
    (tmp_path / "operator_mvp_readiness_report.csv").write_text(
        "generated_at,readiness_status,safety_clean,real_quote_available,safe_unavailable,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,MVP_SAFE_UNAVAILABLE,true,false,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_market_mvp_regression.csv").write_text(
        "generated_at,regression_status,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,PASS,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )


def test_final_audit_gate_generates_safe_unavailable_status(tmp_path: Path):
    _write_audit_sources(tmp_path)

    row = generate_mvp_final_audit_gate(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_mvp_final_audit_gate.csv",
        output_report=tmp_path / "reports/operator_mvp_final_audit_gate_report.md",
        generated_at="2026-05-25T00:02:00+00:00",
    )

    assert row["final_audit_status"] in {"MVP_SAFE_UNAVAILABLE", "MVP_SKELETON_COMPLETE_WITH_SAFE_UNAVAILABLE"}
    assert row["final_audit_status"] == "MVP_SKELETON_COMPLETE_WITH_SAFE_UNAVAILABLE"
    assert row["safety_status"] == "SAFETY_CLEAN"
    assert row["safe_unavailable"] == "true"
    for field in (
        "auto_trade_allowed",
        "account_read_allowed",
        "position_read_allowed",
        "historical_data_request_allowed",
        "telegram_real_send_allowed",
        "order_action_allowed",
        "cancel_action_allowed",
        "rebalance_action_allowed",
    ):
        assert row[field] == "false"
    assert set(_read_one(tmp_path / "operator_mvp_final_audit_gate.csv")) == set(AUDIT_FIELDS)


def test_final_audit_report_documents_local_only_boundaries(tmp_path: Path):
    _write_audit_sources(tmp_path)
    generate_mvp_final_audit_gate(
        base_dir=tmp_path,
        output_csv=tmp_path / "audit.csv",
        output_report=tmp_path / "audit.md",
    )
    report = (tmp_path / "audit.md").read_text(encoding="utf-8")
    for marker in (
        "no auto trading",
        "no account reads",
        "no position reads",
        "no historical data requests",
        "no Telegram real send",
        "no order/cancel/rebalance",
        "config.yaml remains local-only",
        "ibkr_market_data_api_errors.csv remains local-only",
    ):
        assert marker in report


def test_final_audit_output_has_no_trade_execution_words(tmp_path: Path):
    _write_audit_sources(tmp_path)
    generate_mvp_final_audit_gate(base_dir=tmp_path, output_csv=tmp_path / "audit.csv", output_report=tmp_path / "audit.md")
    text = (tmp_path / "audit.csv").read_text(encoding="utf-8") + (tmp_path / "audit.md").read_text(encoding="utf-8")
    forbidden = ["B" + "UY", "S" + "ELL", "O" + "RDER", "E" + "XECUTE"]
    assert not any(word in text for word in forbidden)


def test_final_audit_wrapper_generates_csv(tmp_path: Path):
    _write_audit_sources(tmp_path)
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
    assert _read_one(tmp_path / "audit.csv")["final_audit_status"] == "MVP_SKELETON_COMPLETE_WITH_SAFE_UNAVAILABLE"
