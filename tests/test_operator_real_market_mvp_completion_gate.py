from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_real_market_mvp_completion_gate import COMPLETION_GATE_FIELDS, generate_mvp_completion_gate


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_real_market_mvp_completion_gate.sh"


def _read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_gate_sources(tmp_path: Path) -> None:
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
    (tmp_path / "operator_mvp_readiness_report.csv").write_text(
        "generated_at,readiness_status,safety_clean,safe_unavailable,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,MVP_SAFE_UNAVAILABLE,true,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_market_mvp_regression.csv").write_text(
        "generated_at,regression_status,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,PASS,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_continuity_archive_index.csv").write_text(
        "generated_at,source_file,source_exists,continuity_status,operator_next_step\n"
        "2026-05-25T00:00:00+00:00,operator_final_daily_packet.csv,true,CONTINUITY_INDEX_READY,review_multi_run_continuity\n",
        encoding="utf-8",
    )


def test_completion_gate_outputs_safe_unavailable(tmp_path: Path):
    _write_gate_sources(tmp_path)

    row = generate_mvp_completion_gate(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_real_market_mvp_completion_gate.csv",
        output_report=tmp_path / "reports/operator_real_market_mvp_completion_gate_report.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )

    assert row["completion_gate_status"] == "MVP_COMPLETION_SAFE_UNAVAILABLE"
    assert row["safety_status"] == "SAFETY_CLEAN"
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
    assert set(_read_one(tmp_path / "operator_real_market_mvp_completion_gate.csv")) == set(COMPLETION_GATE_FIELDS)
    report = (tmp_path / "reports/operator_real_market_mvp_completion_gate_report.md").read_text(encoding="utf-8")
    for marker in (
        "no auto trading",
        "no account reads",
        "no position reads",
        "no historical data requests",
        "no Telegram real send",
        "no order/cancel/rebalance",
    ):
        assert marker in report


def test_completion_gate_output_has_no_trade_execution_words(tmp_path: Path):
    _write_gate_sources(tmp_path)
    generate_mvp_completion_gate(
        base_dir=tmp_path,
        output_csv=tmp_path / "gate.csv",
        output_report=tmp_path / "gate.md",
    )

    text = (tmp_path / "gate.csv").read_text(encoding="utf-8") + (tmp_path / "gate.md").read_text(encoding="utf-8")
    forbidden = ["B" + "UY", "S" + "ELL", "O" + "RDER", "E" + "XECUTE"]
    assert not any(word in text for word in forbidden)


def test_completion_gate_wrapper_generates_csv(tmp_path: Path):
    _write_gate_sources(tmp_path)
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
            str(tmp_path / "gate.csv"),
            "--output-report",
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
    assert _read_one(tmp_path / "gate.csv")["completion_gate_status"] == "MVP_COMPLETION_SAFE_UNAVAILABLE"
