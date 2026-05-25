from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_daily_real_market_report import DAILY_REAL_MARKET_REPORT_FIELDS, generate_daily_real_market_report


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_daily_real_market_report.sh"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    normalization = tmp_path / "operator_real_quote_normalization.csv"
    bridge = tmp_path / "operator_real_quote_signal_bridge.csv"
    latest = tmp_path / "operator_real_marketdata_latest.csv"
    daily = tmp_path / "operator_real_marketdata_daily_run_summary.csv"
    normalization.write_text(
        "symbol,quote_status,normalized_status,diagnostic_category,connection_succeeded,market_data_request_triggered,snapshot_rows_detected,last_price,bid,ask,close\n"
        "GLD,UNAVAILABLE,SAFE_UNAVAILABLE,PERMISSION_OR_CONNECTION_FAILURE,false,false,0,,,,\n"
        "SLV,UNAVAILABLE,SAFE_UNAVAILABLE,NO_REAL_QUOTE_SNAPSHOT,true,true,0,,,,\n",
        encoding="utf-8",
    )
    bridge.write_text(
        "symbol,signal_bridge_status,observation_signal\n"
        "GLD,HOLD_NO_REAL_QUOTE,NO_REAL_QUOTE_REVIEW_ONLY\n"
        "SLV,HOLD_NO_REAL_QUOTE,NO_REAL_QUOTE_REVIEW_ONLY\n",
        encoding="utf-8",
    )
    latest.write_text("latest_status\nHOLD_SAFE_FAILURE\n", encoding="utf-8")
    daily.write_text("daily_run_status\nDAILY_OPERATOR_CHAIN_HOLD_SAFE_FAILURE\n", encoding="utf-8")
    return normalization, bridge, latest, daily


def test_daily_report_generates_manual_review_only_rows(tmp_path: Path):
    normalization, bridge, latest, daily = _write_inputs(tmp_path)

    rows = generate_daily_real_market_report(
        normalization_csv=normalization,
        signal_bridge_csv=bridge,
        latest_csv=latest,
        daily_summary_csv=daily,
        output_csv=tmp_path / "operator_daily_real_market_report.csv",
        output_report=tmp_path / "reports/operator_daily_real_market_report.md",
        generated_at="2026-05-25T00:00:02+00:00",
    )

    by_symbol = {row["symbol"]: row for row in rows}
    assert by_symbol["GLD"]["real_quote_state"] == "PERMISSION_OR_CONNECTION_FAILURE"
    assert by_symbol["SLV"]["real_quote_state"] == "SAFE_UNAVAILABLE"
    assert all(row["manual_review_only"] == "true" for row in rows)
    assert all(row["auto_trade_allowed"] == "false" for row in rows)
    assert all(row["account_read_allowed"] == "false" for row in rows)
    assert all(row["position_read_allowed"] == "false" for row in rows)
    assert all(row["historical_data_request_allowed"] == "false" for row in rows)
    assert all(row["telegram_real_send_allowed"] == "false" for row in rows)
    assert all(row["order_action_allowed"] == "false" for row in rows)
    assert all(row["cancel_action_allowed"] == "false" for row in rows)
    assert all(row["rebalance_action_allowed"] == "false" for row in rows)
    assert set(_read_rows(tmp_path / "operator_daily_real_market_report.csv")[0]) == set(DAILY_REAL_MARKET_REPORT_FIELDS)

    report = (tmp_path / "reports/operator_daily_real_market_report.md").read_text(encoding="utf-8")
    assert "no auto trading" in report
    assert "no account reads" in report
    assert "no position reads" in report
    assert "no historical data requests" in report
    assert "no Telegram real send" in report
    assert "no order/cancel/rebalance" in report


def test_daily_report_wrapper_generates_csv(tmp_path: Path):
    normalization, bridge, latest, daily = _write_inputs(tmp_path)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))

    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--normalization-csv",
            str(normalization),
            "--signal-bridge-csv",
            str(bridge),
            "--latest-csv",
            str(latest),
            "--daily-summary-csv",
            str(daily),
            "--output-csv",
            str(tmp_path / "daily.csv"),
            "--output-report",
            str(tmp_path / "daily.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_rows(tmp_path / "daily.csv")[0]["manual_review_only"] == "true"
