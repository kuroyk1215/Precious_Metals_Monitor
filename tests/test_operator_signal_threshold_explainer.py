from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_signal_threshold_explainer import THRESHOLD_EXPLAINER_FIELDS, generate_threshold_explainer


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_signal_threshold_explainer.sh"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_no_real_quote_sources(tmp_path: Path) -> None:
    (tmp_path / "operator_real_quote_signal_bridge.csv").write_text(
        "generated_at,symbol,quote_status,normalized_status,signal_bridge_status,auto_trade_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed,diagnostic_reason\n"
        "2026-05-25T00:00:00+00:00,GLD,UNAVAILABLE,SAFE_UNAVAILABLE,HOLD_NO_REAL_QUOTE,false,false,false,false,real_quote_unavailable\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_quote_normalization.csv").write_text(
        "generated_at,symbol,quote_status,normalized_status,diagnostic_reason\n"
        "2026-05-25T00:00:00+00:00,GLD,UNAVAILABLE,SAFE_UNAVAILABLE,real_quote_unavailable\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_daily_real_market_report.csv").write_text(
        "generated_at,symbol,real_quote_state,quote_status,normalized_status,signal_bridge_status,safe_unavailable\n"
        "2026-05-25T00:00:00+00:00,GLD,SAFE_UNAVAILABLE,UNAVAILABLE,SAFE_UNAVAILABLE,HOLD_NO_REAL_QUOTE,true\n",
        encoding="utf-8",
    )
    (tmp_path / "research_trading_plan.csv").write_text(
        "generated_at,symbol,manual_observation_bias,manual_watch_zone,research_plan_status\n"
        "2026-05-25T00:00:00+00:00,GLD,REFERENCE_ONLY,observe reference range manually,REFERENCE_ONLY_PLAN_READY\n",
        encoding="utf-8",
    )


def test_no_real_quote_outputs_hold_or_insufficient_and_forbidden_flags_false(tmp_path: Path):
    _write_no_real_quote_sources(tmp_path)

    rows = generate_threshold_explainer(
        signal_bridge_csv=tmp_path / "operator_real_quote_signal_bridge.csv",
        normalization_csv=tmp_path / "operator_real_quote_normalization.csv",
        daily_report_csv=tmp_path / "operator_daily_real_market_report.csv",
        research_plan_csv=tmp_path / "research_trading_plan.csv",
        output_csv=tmp_path / "threshold.csv",
        output_report=tmp_path / "reports/threshold.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["threshold_status"] in {"HOLD_NO_REAL_QUOTE", "SIGNAL_INSUFFICIENT_DATA"}
    assert row["auto_trade_allowed"] == "false"
    assert row["order_action_allowed"] == "false"
    assert row["cancel_action_allowed"] == "false"
    assert row["rebalance_action_allowed"] == "false"
    assert row["manual_review_required"] == "true"
    assert set(_read_rows(tmp_path / "threshold.csv")[0]) == set(THRESHOLD_EXPLAINER_FIELDS)


def test_threshold_output_has_no_trade_execution_words(tmp_path: Path):
    _write_no_real_quote_sources(tmp_path)

    generate_threshold_explainer(
        signal_bridge_csv=tmp_path / "operator_real_quote_signal_bridge.csv",
        normalization_csv=tmp_path / "operator_real_quote_normalization.csv",
        daily_report_csv=tmp_path / "operator_daily_real_market_report.csv",
        research_plan_csv=tmp_path / "research_trading_plan.csv",
        output_csv=tmp_path / "threshold.csv",
        output_report=tmp_path / "reports/threshold.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )

    text = (tmp_path / "threshold.csv").read_text(encoding="utf-8") + (tmp_path / "reports/threshold.md").read_text(encoding="utf-8")
    assert "BUY" not in text
    assert "SELL" not in text
    assert "ORDER" not in text


def test_threshold_wrapper_generates_csv(tmp_path: Path):
    _write_no_real_quote_sources(tmp_path)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))

    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--signal-bridge-csv",
            str(tmp_path / "operator_real_quote_signal_bridge.csv"),
            "--normalization-csv",
            str(tmp_path / "operator_real_quote_normalization.csv"),
            "--daily-report-csv",
            str(tmp_path / "operator_daily_real_market_report.csv"),
            "--research-plan-csv",
            str(tmp_path / "research_trading_plan.csv"),
            "--output-csv",
            str(tmp_path / "threshold.csv"),
            "--output-report",
            str(tmp_path / "threshold.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_rows(tmp_path / "threshold.csv")[0]["threshold_status"] == "HOLD_NO_REAL_QUOTE"
