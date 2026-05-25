from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_latest_strategy_decision import LATEST_DECISION_FIELDS, generate_latest_strategy_decision


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_latest_strategy_decision.sh"


def _read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_decision_sources(tmp_path: Path) -> None:
    (tmp_path / "operator_final_daily_packet.csv").write_text(
        "generated_at,final_packet_status,current_readiness,quote_availability,safety_status,manual_review_status,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,FINAL_PACKET_SAFE_UNAVAILABLE,MVP_SAFE_UNAVAILABLE,SAFE_UNAVAILABLE,SAFETY_CLEAN,MANUAL_REVIEW_REQUIRED,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_strategy_explanation_upgrade.csv").write_text(
        "generated_at,symbol,explanation_status,manual_review_required,auto_trade_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,GLD,WHY_HOLD_SAFE_UNAVAILABLE,true,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_mvp_readiness_report.csv").write_text(
        "generated_at,readiness_status,safe_unavailable,safety_clean,auto_trade_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,MVP_SAFE_UNAVAILABLE,true,true,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_market_range_framework.csv").write_text(
        "generated_at,symbol,range_status,manual_review_required,auto_trade_allowed,order_action_allowed\n"
        "2026-05-25T00:00:00+00:00,GLD,RANGE_PENDING_NO_REAL_QUOTE,true,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_gld_slv_spread_framework.csv").write_text(
        "generated_at,spread_observation_status,spread_available,auto_trade_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,SAFE_UNAVAILABLE,false,false,false,false,false\n",
        encoding="utf-8",
    )


def test_latest_decision_outputs_hold_safe_unavailable(tmp_path: Path):
    _write_decision_sources(tmp_path)

    row = generate_latest_strategy_decision(
        base_dir=tmp_path,
        output_csv=tmp_path / "operator_latest_strategy_decision.csv",
        output_report=tmp_path / "reports/operator_latest_strategy_decision_report.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )

    assert row["latest_decision_status"] == "LATEST_HOLD_SAFE_UNAVAILABLE"
    assert row["manual_action_required"] == "true"
    assert row["auto_trade_allowed"] == "false"
    assert row["order_action_allowed"] == "false"
    assert row["cancel_action_allowed"] == "false"
    assert row["rebalance_action_allowed"] == "false"
    assert set(_read_one(tmp_path / "operator_latest_strategy_decision.csv")) == set(LATEST_DECISION_FIELDS)


def test_latest_decision_missing_sources_is_insufficient_data(tmp_path: Path):
    row = generate_latest_strategy_decision(
        base_dir=tmp_path,
        output_csv=tmp_path / "decision.csv",
        output_report=tmp_path / "decision.md",
    )

    assert row["latest_decision_status"] == "LATEST_INSUFFICIENT_DATA"
    assert row["manual_action_required"] == "true"


def test_latest_decision_output_has_no_trade_execution_words(tmp_path: Path):
    _write_decision_sources(tmp_path)
    generate_latest_strategy_decision(
        base_dir=tmp_path,
        output_csv=tmp_path / "decision.csv",
        output_report=tmp_path / "decision.md",
    )

    text = (tmp_path / "decision.csv").read_text(encoding="utf-8") + (tmp_path / "decision.md").read_text(encoding="utf-8")
    forbidden = ["B" + "UY", "S" + "ELL", "O" + "RDER", "E" + "XECUTE"]
    assert not any(word in text for word in forbidden)


def test_latest_decision_wrapper_generates_csv(tmp_path: Path):
    _write_decision_sources(tmp_path)
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
            str(tmp_path / "decision.csv"),
            "--output-report",
            str(tmp_path / "decision.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_one(tmp_path / "decision.csv")["latest_decision_status"] == "LATEST_HOLD_SAFE_UNAVAILABLE"
