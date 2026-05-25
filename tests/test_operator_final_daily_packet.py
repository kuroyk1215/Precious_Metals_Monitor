from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_final_daily_packet import FINAL_PACKET_FIELDS, generate_final_daily_packet


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_final_daily_packet.sh"


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


def test_final_packet_outputs_safe_unavailable_without_real_quotes(tmp_path: Path):
    _write_safe_unavailable_sources(tmp_path)

    row = generate_final_daily_packet(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_final_daily_packet.csv",
        output_report=tmp_path / "reports/operator_final_daily_packet.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )

    assert row["final_packet_status"] == "FINAL_PACKET_SAFE_UNAVAILABLE"
    assert row["current_readiness"] == "MVP_SAFE_UNAVAILABLE"
    assert row["quote_availability"] == "SAFE_UNAVAILABLE"
    assert row["safety_status"] == "SAFETY_CLEAN"
    assert row["manual_review_status"] == "MANUAL_REVIEW_REQUIRED"
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
    assert set(_read_one(tmp_path / "operator_final_daily_packet.csv")) == set(FINAL_PACKET_FIELDS)
    report = (tmp_path / "reports/operator_final_daily_packet.md").read_text(encoding="utf-8")
    for marker in (
        "current readiness",
        "strategy explanation",
        "quote availability",
        "safety status",
        "manual review status",
        "operator next step",
    ):
        assert marker in report


def test_final_packet_output_has_no_trade_execution_words(tmp_path: Path):
    _write_safe_unavailable_sources(tmp_path)
    generate_final_daily_packet(
        base_dir=tmp_path,
        output_csv=tmp_path / "packet.csv",
        output_report=tmp_path / "packet.md",
    )

    text = (tmp_path / "packet.csv").read_text(encoding="utf-8") + (tmp_path / "packet.md").read_text(encoding="utf-8")
    forbidden = ["B" + "UY", "S" + "ELL", "O" + "RDER", "E" + "XECUTE"]
    assert not any(word in text for word in forbidden)


def test_final_packet_wrapper_generates_csv(tmp_path: Path):
    _write_safe_unavailable_sources(tmp_path)
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
            str(tmp_path / "packet.csv"),
            "--output-report",
            str(tmp_path / "packet.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_one(tmp_path / "packet.csv")["final_packet_status"] == "FINAL_PACKET_SAFE_UNAVAILABLE"
