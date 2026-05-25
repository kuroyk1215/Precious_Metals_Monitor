from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_real_market_range_framework import RANGE_FIELDS, generate_range_framework


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_real_market_range_framework.sh"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_no_real_quote_sources(tmp_path: Path) -> None:
    (tmp_path / "operator_real_quote_normalization.csv").write_text(
        "generated_at,symbol,quote_status,normalized_status,last_price,diagnostic_reason\n"
        "2026-05-25T00:00:00+00:00,GLD,UNAVAILABLE,SAFE_UNAVAILABLE,,real_quote_unavailable\n"
        "2026-05-25T00:00:00+00:00,SLV,UNAVAILABLE,SAFE_UNAVAILABLE,,real_quote_unavailable\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_gld_slv_spread_framework.csv").write_text(
        "generated_at,gld_quote_status,slv_quote_status,spread_available,spread_observation_status,auto_trade_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,UNAVAILABLE,UNAVAILABLE,false,SAFE_UNAVAILABLE,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_signal_threshold_explainer.csv").write_text(
        "generated_at,symbol,quote_status,normalized_status,threshold_status,diagnostic_reason\n"
        "2026-05-25T00:00:00+00:00,GLD,UNAVAILABLE,SAFE_UNAVAILABLE,HOLD_NO_REAL_QUOTE,real_quote_unavailable\n"
        "2026-05-25T00:00:00+00:00,SLV,UNAVAILABLE,SAFE_UNAVAILABLE,HOLD_NO_REAL_QUOTE,real_quote_unavailable\n",
        encoding="utf-8",
    )
    (tmp_path / "research_trading_plan.csv").write_text(
        "generated_at,symbol,reference_price,manual_watch_zone,research_plan_status\n"
        "2026-05-25T00:00:00+00:00,GLD,,N/A,NO_PRICE_PLAN_BLOCKED\n"
        "2026-05-25T00:00:00+00:00,SLV,68.31,reference only,REFERENCE_ONLY_PLAN_READY\n",
        encoding="utf-8",
    )


def test_range_outputs_pending_without_real_quotes(tmp_path: Path):
    _write_no_real_quote_sources(tmp_path)

    rows = generate_range_framework(
        normalization_csv=tmp_path / "operator_real_quote_normalization.csv",
        spread_framework_csv=tmp_path / "operator_gld_slv_spread_framework.csv",
        threshold_explainer_csv=tmp_path / "operator_signal_threshold_explainer.csv",
        research_plan_csv=tmp_path / "research_trading_plan.csv",
        output_csv=tmp_path / "range.csv",
        output_report=tmp_path / "reports/range.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )

    assert {row["symbol"] for row in rows} == {"GLD", "SLV"}
    assert {row["range_status"] for row in rows} == {"RANGE_PENDING_NO_REAL_QUOTE"}
    for row in rows:
        assert row["manual_review_required"] == "true"
        assert row["auto_trade_allowed"] == "false"
        assert row["order_action_allowed"] == "false"
    assert set(_read_rows(tmp_path / "range.csv")[0]) == set(RANGE_FIELDS)


def test_range_output_has_no_trade_execution_words(tmp_path: Path):
    _write_no_real_quote_sources(tmp_path)
    generate_range_framework(
        normalization_csv=tmp_path / "operator_real_quote_normalization.csv",
        spread_framework_csv=tmp_path / "operator_gld_slv_spread_framework.csv",
        threshold_explainer_csv=tmp_path / "operator_signal_threshold_explainer.csv",
        research_plan_csv=tmp_path / "research_trading_plan.csv",
        output_csv=tmp_path / "range.csv",
        output_report=tmp_path / "reports/range.md",
    )

    text = (tmp_path / "range.csv").read_text(encoding="utf-8") + (tmp_path / "reports/range.md").read_text(encoding="utf-8")
    forbidden = ["B" + "UY", "S" + "ELL", "O" + "RDER", "E" + "XECUTE"]
    assert not any(word in text for word in forbidden)


def test_range_wrapper_generates_csv(tmp_path: Path):
    _write_no_real_quote_sources(tmp_path)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))

    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--normalization-csv",
            str(tmp_path / "operator_real_quote_normalization.csv"),
            "--spread-framework-csv",
            str(tmp_path / "operator_gld_slv_spread_framework.csv"),
            "--threshold-explainer-csv",
            str(tmp_path / "operator_signal_threshold_explainer.csv"),
            "--research-plan-csv",
            str(tmp_path / "research_trading_plan.csv"),
            "--output-csv",
            str(tmp_path / "range.csv"),
            "--output-report",
            str(tmp_path / "range.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_rows(tmp_path / "range.csv")[0]["range_status"] == "RANGE_PENDING_NO_REAL_QUOTE"
