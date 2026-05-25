from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_real_quote_signal_bridge import SIGNAL_BRIDGE_FIELDS, generate_signal_bridge


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_real_quote_signal_bridge.sh"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    normalization = tmp_path / "operator_real_quote_normalization.csv"
    research = tmp_path / "research_trading_plan.csv"
    decision = tmp_path / "operator_real_marketdata_decision_gate.csv"
    normalization.write_text(
        "symbol,quote_status,normalized_status,diagnostic_reason\n"
        "GLD,UNAVAILABLE,SAFE_UNAVAILABLE,real_marketdata_connection_or_request_not_confirmed\n"
        "SLV,UNAVAILABLE,SAFE_UNAVAILABLE,real_marketdata_connection_or_request_not_confirmed\n",
        encoding="utf-8",
    )
    research.write_text(
        "symbol,research_plan_status,action_allowed\n"
        "GLD,NO_PRICE_PLAN_BLOCKED,false\n"
        "SLV,REFERENCE_ONLY_PLAN_READY,false\n",
        encoding="utf-8",
    )
    decision.write_text("operator_decision\nHOLD_SAFE_FAILURE\n", encoding="utf-8")
    return normalization, research, decision


def test_signal_bridge_holds_when_no_real_quote(tmp_path: Path):
    normalization, research, decision = _write_inputs(tmp_path)

    rows = generate_signal_bridge(
        normalization_csv=normalization,
        research_plan_csv=research,
        decision_gate_csv=decision,
        output_csv=tmp_path / "operator_real_quote_signal_bridge.csv",
        output_report=tmp_path / "reports/operator_real_quote_signal_bridge_report.md",
        generated_at="2026-05-25T00:00:01+00:00",
    )

    assert {row["symbol"] for row in rows} == {"GLD", "SLV"}
    assert all(row["signal_bridge_status"] == "HOLD_NO_REAL_QUOTE" for row in rows)
    assert all(row["observation_signal"] == "NO_REAL_QUOTE_REVIEW_ONLY" for row in rows)
    assert all(row["manual_action_allowed"] == "false" for row in rows)
    assert all(row["auto_trade_allowed"] == "false" for row in rows)
    assert all(row["order_action_allowed"] == "false" for row in rows)
    assert all(row["cancel_action_allowed"] == "false" for row in rows)
    assert all(row["rebalance_action_allowed"] == "false" for row in rows)
    assert set(_read_rows(tmp_path / "operator_real_quote_signal_bridge.csv")[0]) == set(SIGNAL_BRIDGE_FIELDS)


def test_signal_bridge_wrapper_generates_review_only_rows(tmp_path: Path):
    normalization, research, decision = _write_inputs(tmp_path)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))

    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--normalization-csv",
            str(normalization),
            "--research-plan-csv",
            str(research),
            "--decision-gate-csv",
            str(decision),
            "--output-csv",
            str(tmp_path / "bridge.csv"),
            "--output-report",
            str(tmp_path / "bridge.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_rows(tmp_path / "bridge.csv")[0]["signal_bridge_status"] == "HOLD_NO_REAL_QUOTE"
