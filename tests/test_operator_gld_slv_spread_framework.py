from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_gld_slv_spread_framework import SPREAD_FIELDS, generate_spread_framework


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_gld_slv_spread_framework.sh"


def _read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def _write_no_real_quote_sources(tmp_path: Path) -> None:
    (tmp_path / "operator_real_quote_normalization.csv").write_text(
        "generated_at,symbol,quote_status,normalized_status,last_price,diagnostic_reason\n"
        "2026-05-25T00:00:00+00:00,GLD,UNAVAILABLE,SAFE_UNAVAILABLE,,real_quote_unavailable\n"
        "2026-05-25T00:00:00+00:00,SLV,UNAVAILABLE,SAFE_UNAVAILABLE,,real_quote_unavailable\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_quote_signal_bridge.csv").write_text(
        "generated_at,symbol,quote_status,normalized_status,signal_bridge_status,auto_trade_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,GLD,UNAVAILABLE,SAFE_UNAVAILABLE,HOLD_NO_REAL_QUOTE,false,false,false,false\n"
        "2026-05-25T00:00:00+00:00,SLV,UNAVAILABLE,SAFE_UNAVAILABLE,HOLD_NO_REAL_QUOTE,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_daily_real_market_report.csv").write_text(
        "generated_at,symbol,real_quote_state,quote_status,normalized_status,last_price,safe_unavailable\n"
        "2026-05-25T00:00:00+00:00,GLD,SAFE_UNAVAILABLE,UNAVAILABLE,SAFE_UNAVAILABLE,,true\n"
        "2026-05-25T00:00:00+00:00,SLV,SAFE_UNAVAILABLE,UNAVAILABLE,SAFE_UNAVAILABLE,,true\n",
        encoding="utf-8",
    )


def test_spread_outputs_safe_unavailable_without_real_quotes(tmp_path: Path):
    _write_no_real_quote_sources(tmp_path)

    row = generate_spread_framework(
        normalization_csv=tmp_path / "operator_real_quote_normalization.csv",
        signal_bridge_csv=tmp_path / "operator_real_quote_signal_bridge.csv",
        daily_report_csv=tmp_path / "operator_daily_real_market_report.csv",
        output_csv=tmp_path / "spread.csv",
        output_report=tmp_path / "reports/spread.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )

    assert row["spread_observation_status"] == "SAFE_UNAVAILABLE"
    assert row["relative_strength_status"] == "SAFE_UNAVAILABLE"
    assert row["spread_available"] == "false"
    assert row["auto_trade_allowed"] == "false"
    assert row["order_action_allowed"] == "false"
    assert row["cancel_action_allowed"] == "false"
    assert row["rebalance_action_allowed"] == "false"
    assert set(_read_one(tmp_path / "spread.csv")) == set(SPREAD_FIELDS)


def test_spread_output_has_no_trade_execution_words(tmp_path: Path):
    _write_no_real_quote_sources(tmp_path)
    generate_spread_framework(
        normalization_csv=tmp_path / "operator_real_quote_normalization.csv",
        signal_bridge_csv=tmp_path / "operator_real_quote_signal_bridge.csv",
        daily_report_csv=tmp_path / "operator_daily_real_market_report.csv",
        output_csv=tmp_path / "spread.csv",
        output_report=tmp_path / "reports/spread.md",
    )

    text = (tmp_path / "spread.csv").read_text(encoding="utf-8") + (tmp_path / "reports/spread.md").read_text(encoding="utf-8")
    forbidden = ["B" + "UY", "S" + "ELL", "O" + "RDER", "E" + "XECUTE"]
    assert not any(word in text for word in forbidden)


def test_spread_wrapper_generates_csv(tmp_path: Path):
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
            "--signal-bridge-csv",
            str(tmp_path / "operator_real_quote_signal_bridge.csv"),
            "--daily-report-csv",
            str(tmp_path / "operator_daily_real_market_report.csv"),
            "--output-csv",
            str(tmp_path / "spread.csv"),
            "--output-report",
            str(tmp_path / "spread.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_one(tmp_path / "spread.csv")["spread_observation_status"] == "SAFE_UNAVAILABLE"
