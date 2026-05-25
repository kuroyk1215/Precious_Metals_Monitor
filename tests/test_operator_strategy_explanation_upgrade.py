from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_strategy_explanation_upgrade import EXPLANATION_FIELDS, generate_strategy_explanation_upgrade


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_strategy_explanation_upgrade.sh"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_no_real_quote_sources(tmp_path: Path) -> None:
    (tmp_path / "operator_gld_slv_spread_framework.csv").write_text(
        "generated_at,gld_quote_status,slv_quote_status,spread_available,spread_observation_status,auto_trade_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,UNAVAILABLE,UNAVAILABLE,false,SAFE_UNAVAILABLE,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_real_market_range_framework.csv").write_text(
        "generated_at,symbol,quote_status,normalized_status,range_status,manual_review_required,auto_trade_allowed,order_action_allowed\n"
        "2026-05-25T00:00:00+00:00,GLD,UNAVAILABLE,SAFE_UNAVAILABLE,RANGE_PENDING_NO_REAL_QUOTE,true,false,false\n"
        "2026-05-25T00:00:00+00:00,SLV,UNAVAILABLE,SAFE_UNAVAILABLE,RANGE_PENDING_NO_REAL_QUOTE,true,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_strategy_quality_report.csv").write_text(
        "generated_at,quality_status,data_unavailable_but_safe,manual_review_only,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,DATA_UNAVAILABLE_BUT_SAFE,true,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )
    (tmp_path / "operator_mvp_readiness_report.csv").write_text(
        "generated_at,readiness_status,safe_unavailable,safety_clean,auto_trade_allowed,account_read_allowed,position_read_allowed,historical_data_request_allowed,telegram_real_send_allowed,order_action_allowed,cancel_action_allowed,rebalance_action_allowed\n"
        "2026-05-25T00:00:00+00:00,MVP_SAFE_UNAVAILABLE,true,true,false,false,false,false,false,false,false,false\n",
        encoding="utf-8",
    )


def test_explanation_outputs_safe_unavailable_reason(tmp_path: Path):
    _write_no_real_quote_sources(tmp_path)

    rows = generate_strategy_explanation_upgrade(
        spread_framework_csv=tmp_path / "operator_gld_slv_spread_framework.csv",
        range_framework_csv=tmp_path / "operator_real_market_range_framework.csv",
        strategy_quality_csv=tmp_path / "operator_strategy_quality_report.csv",
        mvp_readiness_csv=tmp_path / "operator_mvp_readiness_report.csv",
        output_csv=tmp_path / "explanation.csv",
        output_report=tmp_path / "reports/explanation.md",
        generated_at="2026-05-25T00:01:00+00:00",
    )

    assert {row["symbol"] for row in rows} == {"GLD", "SLV"}
    assert {row["explanation_status"] for row in rows} == {"WHY_HOLD_SAFE_UNAVAILABLE"}
    for row in rows:
        assert row["manual_review_required"] == "true"
        assert row["auto_trade_allowed"] == "false"
        assert row["account_read_allowed"] == "false"
        assert row["position_read_allowed"] == "false"
        assert row["historical_data_request_allowed"] == "false"
        assert row["telegram_real_send_allowed"] == "false"
        assert row["order_action_allowed"] == "false"
        assert row["cancel_action_allowed"] == "false"
        assert row["rebalance_action_allowed"] == "false"
    assert set(_read_rows(tmp_path / "explanation.csv")[0]) == set(EXPLANATION_FIELDS)


def test_explanation_output_has_no_trade_execution_words(tmp_path: Path):
    _write_no_real_quote_sources(tmp_path)
    generate_strategy_explanation_upgrade(
        spread_framework_csv=tmp_path / "operator_gld_slv_spread_framework.csv",
        range_framework_csv=tmp_path / "operator_real_market_range_framework.csv",
        strategy_quality_csv=tmp_path / "operator_strategy_quality_report.csv",
        mvp_readiness_csv=tmp_path / "operator_mvp_readiness_report.csv",
        output_csv=tmp_path / "explanation.csv",
        output_report=tmp_path / "reports/explanation.md",
    )

    text = (tmp_path / "explanation.csv").read_text(encoding="utf-8") + (tmp_path / "reports/explanation.md").read_text(encoding="utf-8")
    forbidden = ["B" + "UY", "S" + "ELL", "O" + "RDER", "E" + "XECUTE"]
    assert not any(word in text for word in forbidden)


def test_explanation_wrapper_generates_csv(tmp_path: Path):
    _write_no_real_quote_sources(tmp_path)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))

    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--spread-framework-csv",
            str(tmp_path / "operator_gld_slv_spread_framework.csv"),
            "--range-framework-csv",
            str(tmp_path / "operator_real_market_range_framework.csv"),
            "--strategy-quality-csv",
            str(tmp_path / "operator_strategy_quality_report.csv"),
            "--mvp-readiness-csv",
            str(tmp_path / "operator_mvp_readiness_report.csv"),
            "--output-csv",
            str(tmp_path / "explanation.csv"),
            "--output-report",
            str(tmp_path / "explanation.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_rows(tmp_path / "explanation.csv")[0]["explanation_status"] == "WHY_HOLD_SAFE_UNAVAILABLE"
