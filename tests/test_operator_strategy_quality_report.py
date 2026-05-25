from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_strategy_quality_report import STRATEGY_QUALITY_FIELDS, generate_strategy_quality_report


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_strategy_quality_report.sh"


def _read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_quality_sources(tmp_path: Path) -> None:
    (tmp_path / "operator_real_market_archive_compare.csv").write_text(
        "generated_at,comparison_window,status_consistency,quote_availability_trend,safety_consistency\n"
        "2026-05-25T00:00:00+00:00,SINGLE_RUN,INSUFFICIENT_HISTORY,NO_REAL_QUOTE_AVAILABLE,SAFETY_CONSISTENT_FALSE_ACTIONS\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_signal_threshold_explainer.csv").write_text(
        "generated_at,symbol,threshold_status,manual_review_required,auto_trade_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,GLD,HOLD_NO_REAL_QUOTE,true,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_market_mvp_status.csv").write_text(
        "generated_at,mvp_status,real_quote_available,safe_unavailable,manual_review_only,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,MVP_SAFE_UNAVAILABLE,false,true,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_daily_real_market_report.csv").write_text(
        "generated_at,symbol,real_quote_state,safe_unavailable,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,GLD,SAFE_UNAVAILABLE,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )


def test_strategy_quality_report_generates_safe_manual_only_summary(tmp_path: Path):
    _write_quality_sources(tmp_path)

    row = generate_strategy_quality_report(
        archive_compare_csv=tmp_path / "operator_real_market_archive_compare.csv",
        threshold_explainer_csv=tmp_path / "operator_signal_threshold_explainer.csv",
        mvp_status_csv=tmp_path / "operator_real_market_mvp_status.csv",
        daily_report_csv=tmp_path / "operator_daily_real_market_report.csv",
        output_csv=tmp_path / "quality.csv",
        output_report=tmp_path / "reports/quality.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )

    assert row["quality_status"] == "DATA_UNAVAILABLE_BUT_SAFE"
    assert row["data_unavailable_but_safe"] == "true"
    assert row["insufficient_history"] == "true"
    assert row["signal_insufficient"] == "true"
    assert row["manual_review_only"] == "true"
    assert row["auto_trade_allowed"] == "false"
    assert row["account_read_allowed"] == "false"
    assert row["position_read_allowed"] == "false"
    assert row["historical_data_request_allowed"] == "false"
    assert row["telegram_real_send_allowed"] == "false"
    assert row["order_action_allowed"] == "false"
    assert row["cancel_action_allowed"] == "false"
    assert row["rebalance_action_allowed"] == "false"
    assert set(_read_one(tmp_path / "quality.csv")) == set(STRATEGY_QUALITY_FIELDS)

    report = (tmp_path / "reports/quality.md").read_text(encoding="utf-8")
    assert "data available=false" in report
    assert "data unavailable but safe=true" in report
    assert "insufficient history=true" in report
    assert "signal insufficient=true" in report
    assert "manual review only=true" in report
    assert "no historical data requests" in report


def test_strategy_quality_output_has_no_trade_execution_words(tmp_path: Path):
    _write_quality_sources(tmp_path)

    generate_strategy_quality_report(
        archive_compare_csv=tmp_path / "operator_real_market_archive_compare.csv",
        threshold_explainer_csv=tmp_path / "operator_signal_threshold_explainer.csv",
        mvp_status_csv=tmp_path / "operator_real_market_mvp_status.csv",
        daily_report_csv=tmp_path / "operator_daily_real_market_report.csv",
        output_csv=tmp_path / "quality.csv",
        output_report=tmp_path / "reports/quality.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )

    text = (tmp_path / "quality.csv").read_text(encoding="utf-8") + (tmp_path / "reports/quality.md").read_text(encoding="utf-8")
    assert "BUY" not in text
    assert "SELL" not in text
    assert "ORDER" not in text


def test_strategy_quality_wrapper_generates_csv(tmp_path: Path):
    _write_quality_sources(tmp_path)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))

    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--archive-compare-csv",
            str(tmp_path / "operator_real_market_archive_compare.csv"),
            "--threshold-explainer-csv",
            str(tmp_path / "operator_signal_threshold_explainer.csv"),
            "--mvp-status-csv",
            str(tmp_path / "operator_real_market_mvp_status.csv"),
            "--daily-report-csv",
            str(tmp_path / "operator_daily_real_market_report.csv"),
            "--output-csv",
            str(tmp_path / "quality.csv"),
            "--output-report",
            str(tmp_path / "quality.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_one(tmp_path / "quality.csv")["quality_status"] == "DATA_UNAVAILABLE_BUT_SAFE"
