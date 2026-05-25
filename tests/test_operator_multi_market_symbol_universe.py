from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path

from src.operator_multi_market_symbol_universe import (
    READY_STATUS,
    SCHEMA_GATE_FIELDS,
    UNIVERSE_FIELDS,
    build_multi_market_symbol_schema_gate_row,
    build_multi_market_symbol_universe_rows,
    generate_multi_market_symbol_universe,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_multi_market_symbol_universe.sh"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _read_one(path: Path) -> dict[str, str]:
    rows = _read_rows(path)
    assert len(rows) == 1
    return rows[0]


def test_multi_market_symbol_universe_rows_are_static_observation_only() -> None:
    rows = build_multi_market_symbol_universe_rows(generated_at="2026-05-25T00:00:00+00:00")

    assert len(rows) == 18
    assert sum(1 for row in rows if row["market"] == "JP") == 6
    assert sum(1 for row in rows if row["market"] == "CN") == 6
    assert sum(1 for row in rows if row["market"] == "US") == 6
    assert {row["symbol"] for row in rows} >= {"1540.T", "GLD", "518880.SH"}

    row_518880 = next(row for row in rows if row["symbol"] == "518880.SH")
    assert row_518880["ibkr_contract_expected"] == "unknown"
    assert row_518880["local_market_symbol"] == "true"
    assert "ibkr_availability_not_assumed" in row_518880["diagnostic_reason"]

    for row in rows:
        assert set(row) == set(UNIVERSE_FIELDS)
        assert row["enabled_for_observation"] == "true"
        assert row["enabled_for_trading"] == "false"
        assert row["manual_only"] == "true"
        assert row["research_only"] == "true"
        assert row["observation_only"] == "true"
        for field in (
            "trading_actions_allowed",
            "order_action_allowed",
            "cancel_action_allowed",
            "rebalance_action_allowed",
            "account_read_allowed",
            "position_read_allowed",
            "historical_data_request_allowed",
            "telegram_real_send_allowed",
        ):
            assert row[field] == "false"


def test_multi_market_schema_gate_ready_and_counts() -> None:
    rows = build_multi_market_symbol_universe_rows(generated_at="2026-05-25T00:00:00+00:00")
    gate = build_multi_market_symbol_schema_gate_row(rows, generated_at="2026-05-25T00:00:00+00:00")

    assert set(gate) == set(SCHEMA_GATE_FIELDS)
    assert gate["schema_gate_status"] == READY_STATUS
    assert gate["markets_present"] == "CN,JP,US"
    assert gate["jp_symbol_count"] == "6"
    assert gate["cn_symbol_count"] == "6"
    assert gate["us_symbol_count"] == "6"
    assert gate["trading_unit_rules_present"] == "true"
    assert gate["settlement_rules_present"] == "true"
    assert gate["timezone_rules_present"] == "true"
    assert gate["all_trading_disabled"] == "true"
    assert gate["all_observation_enabled"] == "true"
    assert gate["no_account_or_position_read"] == "true"
    assert gate["no_historical_data_request"] == "true"
    assert gate["no_real_telegram_send"] == "true"


def test_multi_market_schema_gate_detects_missing_market_and_trading_enabled() -> None:
    rows = build_multi_market_symbol_universe_rows()
    missing_cn = [row for row in rows if row["market"] != "CN"]
    missing_gate = build_multi_market_symbol_schema_gate_row(missing_cn)
    assert missing_gate["schema_gate_status"] == "MULTI_MARKET_SYMBOL_SCHEMA_REVIEW_REQUIRED"
    assert missing_gate["diagnostic_reason"] == "missing_markets:CN"

    unsafe_rows = [dict(row) for row in rows]
    unsafe_rows[0]["enabled_for_trading"] = "true"
    unsafe_gate = build_multi_market_symbol_schema_gate_row(unsafe_rows)
    assert unsafe_gate["schema_gate_status"] == "MULTI_MARKET_SYMBOL_SCHEMA_NO_GO"
    assert unsafe_gate["all_trading_disabled"] == "false"


def test_multi_market_symbol_universe_outputs_csv_json_and_reports(tmp_path: Path) -> None:
    result = generate_multi_market_symbol_universe(
        output_csv=tmp_path / "operator_multi_market_symbol_universe.csv",
        output_json=tmp_path / "operator_multi_market_symbol_universe.json",
        output_report=tmp_path / "reports/operator_multi_market_symbol_universe.md",
        schema_gate_csv=tmp_path / "operator_multi_market_symbol_schema_gate.csv",
        schema_gate_report=tmp_path / "reports/operator_multi_market_symbol_schema_gate_report.md",
        generated_at="2026-05-25T00:00:00+00:00",
    )

    assert result["schema_gate"]["schema_gate_status"] == READY_STATUS
    csv_rows = _read_rows(tmp_path / "operator_multi_market_symbol_universe.csv")
    assert len(csv_rows) == 18
    assert set(csv_rows[0]) == set(UNIVERSE_FIELDS)
    gate = _read_one(tmp_path / "operator_multi_market_symbol_schema_gate.csv")
    assert gate["schema_gate_status"] == READY_STATUS
    assert set(gate) == set(SCHEMA_GATE_FIELDS)

    payload = json.loads((tmp_path / "operator_multi_market_symbol_universe.json").read_text(encoding="utf-8"))
    assert payload["schema_gate_status"] == READY_STATUS
    assert payload["symbol_count"] == 18
    assert any(row["symbol"] == "1540.T" for row in payload["symbols"])
    assert any(row["symbol"] == "GLD" for row in payload["symbols"])
    assert any(row["symbol"] == "518880.SH" for row in payload["symbols"])

    report = (tmp_path / "reports/operator_multi_market_symbol_universe.md").read_text(encoding="utf-8")
    assert "MULTI_MARKET_SYMBOL_SCHEMA_READY" in report
    assert "1540.T" in report
    assert "GLD" in report
    assert "518880.SH" in report
    assert "enabled_for_trading=false" in report
    assert "trading_actions_allowed=false" in report
    assert "account_read_allowed=false" in report
    assert "position_read_allowed=false" in report
    assert "historical_data_request_allowed=false" in report
    assert "telegram_real_send_allowed=false" in report


def test_multi_market_symbol_universe_main_cli_and_wrapper(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))

    cli_result = subprocess.run(
        [
            env["PYTHON"],
            str(REPO_ROOT / "main.py"),
            "--config",
            str(REPO_ROOT / "config.yaml"),
            "--watchlist",
            str(REPO_ROOT / "watchlist.yaml"),
            "--multi-market-symbol-universe",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cli_result.returncode == 0, cli_result.stdout
    assert "schema_gate_status=MULTI_MARKET_SYMBOL_SCHEMA_READY" in cli_result.stdout
    assert "jp_symbol_count=6" in cli_result.stdout
    assert (tmp_path / "operator_multi_market_symbol_universe.csv").exists()
    assert (tmp_path / "operator_multi_market_symbol_universe.json").exists()
    assert (tmp_path / "reports/operator_multi_market_symbol_universe.md").exists()
    assert (tmp_path / "operator_multi_market_symbol_schema_gate.csv").exists()
    assert (tmp_path / "reports/operator_multi_market_symbol_schema_gate_report.md").exists()

    wrapper_result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--output-csv",
            str(tmp_path / "wrapper_universe.csv"),
            "--output-json",
            str(tmp_path / "wrapper_universe.json"),
            "--output-report",
            str(tmp_path / "reports/wrapper_universe.md"),
            "--schema-gate-csv",
            str(tmp_path / "wrapper_gate.csv"),
            "--schema-gate-report",
            str(tmp_path / "reports/wrapper_gate.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert wrapper_result.returncode == 0, wrapper_result.stdout
    assert _read_one(tmp_path / "wrapper_gate.csv")["schema_gate_status"] == READY_STATUS
