from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path

from src.operator_multi_market_adapter_skeleton import (
    ADAPTER_FIELDS,
    ADAPTER_GATE_FIELDS,
    READY_STATUS,
    build_multi_market_adapter_gate_row,
    build_multi_market_adapter_skeleton_rows,
    generate_multi_market_adapter_skeleton,
)
from src.operator_multi_market_symbol_universe import generate_multi_market_symbol_universe


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_multi_market_adapter_skeleton.sh"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _read_one(path: Path) -> dict[str, str]:
    rows = _read_rows(path)
    assert len(rows) == 1
    return rows[0]


def _write_universe(tmp_path: Path) -> None:
    generate_multi_market_symbol_universe(
        output_csv=tmp_path / "operator_multi_market_symbol_universe.csv",
        output_json=tmp_path / "operator_multi_market_symbol_universe.json",
        output_report=tmp_path / "reports/operator_multi_market_symbol_universe.md",
        schema_gate_csv=tmp_path / "operator_multi_market_symbol_schema_gate.csv",
        schema_gate_report=tmp_path / "reports/operator_multi_market_symbol_schema_gate_report.md",
        generated_at="2026-05-25T00:00:00+00:00",
    )


def test_multi_market_adapter_skeleton_rows_are_static_observation_only(tmp_path: Path) -> None:
    _write_universe(tmp_path)
    universe_rows = _read_rows(tmp_path / "operator_multi_market_symbol_universe.csv")
    rows = build_multi_market_adapter_skeleton_rows(universe_rows, generated_at="2026-05-25T00:01:00+00:00")

    assert len(rows) == 18
    assert sum(1 for row in rows if row["market"] == "JP") == 6
    assert sum(1 for row in rows if row["market"] == "CN") == 6
    assert sum(1 for row in rows if row["market"] == "US") == 6
    assert {row["symbol"] for row in rows} >= {"1540.T", "GLD", "518880.SH"}

    for row in rows:
        assert set(row) == set(ADAPTER_FIELDS)
        assert row["adapter_status"] == "ADAPTER_SKELETON_STATIC_READY"
        assert row["observation_status"] == "OBSERVATION_ONLY"
        assert row["enabled_for_observation"] == "true"
        assert row["enabled_for_trading"] == "false"
        assert row["real_market_data_request_allowed"] == "false"
        assert row["contract_qualification_allowed"] == "false"
        assert row["account_read_allowed"] == "false"
        assert row["position_read_allowed"] == "false"
        assert row["historical_data_request_allowed"] == "false"
        assert row["telegram_real_send_allowed"] == "false"
        assert row["manual_only"] == "true"
        assert row["research_only"] == "true"
        assert row["observation_only"] == "true"
        assert "enabled_for_trading=false" in row["diagnostic_reason"]


def test_multi_market_adapter_gate_ready_and_no_go(tmp_path: Path) -> None:
    _write_universe(tmp_path)
    universe_rows = _read_rows(tmp_path / "operator_multi_market_symbol_universe.csv")
    rows = build_multi_market_adapter_skeleton_rows(universe_rows, generated_at="2026-05-25T00:01:00+00:00")
    gate = build_multi_market_adapter_gate_row(rows, universe_rows, generated_at="2026-05-25T00:02:00+00:00")

    assert set(gate) == set(ADAPTER_GATE_FIELDS)
    assert gate["adapter_gate_status"] == READY_STATUS
    assert gate["multi_market_schema_gate_status"] == "MULTI_MARKET_SYMBOL_SCHEMA_READY"
    assert gate["markets_present"] == "CN,JP,US"
    assert gate["jp_symbol_count"] == "6"
    assert gate["cn_symbol_count"] == "6"
    assert gate["us_symbol_count"] == "6"
    assert gate["adapter_rows_count"] == "18"
    assert gate["all_markets_observation_only"] == "true"
    assert gate["all_symbols_trading_disabled"] == "true"
    assert gate["no_real_market_data_request"] == "true"
    assert gate["no_contract_qualification"] == "true"

    unsafe_rows = [dict(row) for row in rows]
    unsafe_rows[0]["real_market_data_request_allowed"] = "true"
    unsafe_gate = build_multi_market_adapter_gate_row(unsafe_rows, universe_rows)
    assert unsafe_gate["adapter_gate_status"] == "MULTI_MARKET_ADAPTER_NO_GO"

    missing_cn = [row for row in rows if row["market"] != "CN"]
    missing_universe = [row for row in universe_rows if row["market"] != "CN"]
    missing_gate = build_multi_market_adapter_gate_row(missing_cn, missing_universe)
    assert missing_gate["adapter_gate_status"] == "MULTI_MARKET_ADAPTER_REVIEW_REQUIRED"


def test_multi_market_adapter_skeleton_outputs_csv_json_and_reports(tmp_path: Path) -> None:
    _write_universe(tmp_path)
    result = generate_multi_market_adapter_skeleton(
        universe_csv=tmp_path / "operator_multi_market_symbol_universe.csv",
        universe_json=tmp_path / "operator_multi_market_symbol_universe.json",
        output_csv=tmp_path / "operator_multi_market_adapter_skeleton.csv",
        output_json=tmp_path / "operator_multi_market_adapter_skeleton.json",
        output_report=tmp_path / "reports/operator_multi_market_adapter_skeleton.md",
        adapter_gate_csv=tmp_path / "operator_multi_market_adapter_gate.csv",
        adapter_gate_report=tmp_path / "reports/operator_multi_market_adapter_gate_report.md",
        generated_at="2026-05-25T00:03:00+00:00",
    )

    assert result["adapter_gate"]["adapter_gate_status"] == READY_STATUS
    csv_rows = _read_rows(tmp_path / "operator_multi_market_adapter_skeleton.csv")
    assert len(csv_rows) == 18
    assert set(csv_rows[0]) == set(ADAPTER_FIELDS)
    gate = _read_one(tmp_path / "operator_multi_market_adapter_gate.csv")
    assert gate["adapter_gate_status"] == READY_STATUS
    assert set(gate) == set(ADAPTER_GATE_FIELDS)

    payload = json.loads((tmp_path / "operator_multi_market_adapter_skeleton.json").read_text(encoding="utf-8"))
    assert payload["adapter_gate_status"] == READY_STATUS
    assert payload["adapter_rows_count"] == 18
    assert any(row["symbol"] == "1540.T" for row in payload["symbols"])
    assert any(row["symbol"] == "GLD" for row in payload["symbols"])
    assert any(row["symbol"] == "518880.SH" for row in payload["symbols"])

    report = (tmp_path / "reports/operator_multi_market_adapter_skeleton.md").read_text(encoding="utf-8")
    assert "MULTI_MARKET_ADAPTER_SKELETON_READY" in report
    assert "1540.T" in report
    assert "GLD" in report
    assert "518880.SH" in report
    assert "enabled_for_trading=false" in report
    assert "real_market_data_request_allowed=false" in report
    assert "contract_qualification_allowed=false" in report
    assert "account_read_allowed=false" in report
    assert "position_read_allowed=false" in report
    assert "historical_data_request_allowed=false" in report
    assert "telegram_real_send_allowed=false" in report


def test_multi_market_adapter_skeleton_main_cli_and_wrapper(tmp_path: Path) -> None:
    _write_universe(tmp_path)
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
            "--multi-market-adapter-skeleton",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cli_result.returncode == 0, cli_result.stdout
    assert "adapter_gate_status=MULTI_MARKET_ADAPTER_SKELETON_READY" in cli_result.stdout
    assert "jp_symbol_count=6" in cli_result.stdout
    assert (tmp_path / "operator_multi_market_adapter_skeleton.csv").exists()
    assert (tmp_path / "operator_multi_market_adapter_skeleton.json").exists()
    assert (tmp_path / "reports/operator_multi_market_adapter_skeleton.md").exists()
    assert (tmp_path / "operator_multi_market_adapter_gate.csv").exists()
    assert (tmp_path / "reports/operator_multi_market_adapter_gate_report.md").exists()

    wrapper_result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--universe-csv",
            str(tmp_path / "operator_multi_market_symbol_universe.csv"),
            "--universe-json",
            str(tmp_path / "operator_multi_market_symbol_universe.json"),
            "--output-csv",
            str(tmp_path / "wrapper_adapter.csv"),
            "--output-json",
            str(tmp_path / "wrapper_adapter.json"),
            "--output-report",
            str(tmp_path / "reports/wrapper_adapter.md"),
            "--adapter-gate-csv",
            str(tmp_path / "wrapper_gate.csv"),
            "--adapter-gate-report",
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
    assert _read_one(tmp_path / "wrapper_gate.csv")["adapter_gate_status"] == READY_STATUS
