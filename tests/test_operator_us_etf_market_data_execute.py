from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Sequence, Tuple

from src.operator_us_etf_market_data_execute import (
    CSV_FIELDS,
    ERROR_TYPES,
    SYMBOLS,
    any_market_data_field_present,
    build_us_etf_market_data_execute_rows,
    generate_us_etf_market_data_execute,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_config(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "ibkr:",
                "  host: 127.0.0.1",
                "  port: 7497",
                "  client_id: 569572",
                "  readonly: true",
                "  timeout_sec: 1",
                "  market_data_wait_sec: 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _successful_market_data(
    config: Dict[str, Any], symbols: Sequence[str]
) -> Tuple[Dict[str, Dict[str, Any]], None, str]:
    assert config["host"] == "127.0.0.1"
    assert tuple(symbols) == SYMBOLS
    return {
        "GLD": {
            "ticker_received": True,
            "bid_present": True,
            "ask_present": True,
            "last_present": False,
            "close_present": True,
            "delayed_or_realtime": "REALTIME",
        },
        "SLV": {
            "ticker_received": True,
            "bid_present": False,
            "ask_present": False,
            "last_present": True,
            "close_present": True,
            "delayed_or_realtime": "DELAYED",
        },
    }, None, ""


def test_unapproved_path_denies_without_market_data_request(tmp_path: Path) -> None:
    rows = generate_us_etf_market_data_execute(
        operator_approved=False,
        output_csv=tmp_path / "operator_us_etf_market_data_execute.csv",
        output_report=tmp_path / "reports/operator_us_etf_market_data_execute_report.md",
        generated_at="2026-05-28T00:00:00+00:00",
    )
    csv_rows = _read_rows(tmp_path / "operator_us_etf_market_data_execute.csv")
    assert rows == csv_rows
    assert set(csv_rows[0]) == set(CSV_FIELDS)
    assert [row["symbol"] for row in csv_rows] == ["GLD", "SLV"]
    assert all(row["operator_approved"] == "NO" for row in csv_rows)
    assert all(row["market_data_request_attempted"] == "NO" for row in csv_rows)
    assert all(row["error_type"] == "OPERATOR_APPROVAL_REQUIRED" for row in csv_rows)
    assert all(row["account_read_attempted"] == "NO" for row in csv_rows)
    assert all(row["positions_read_attempted"] == "NO" for row in csv_rows)
    assert all(row["historical_data_requested"] == "NO" for row in csv_rows)
    assert all(row["contract_qualification_attempted"] == "NO" for row in csv_rows)
    assert all(row["orders_submitted"] == "NO" for row in csv_rows)
    assert all(row["telegram_real_send_attempted"] == "NO" for row in csv_rows)


def test_authorized_success_archives_gld_and_slv_market_data(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)
    rows = generate_us_etf_market_data_execute(
        operator_approved=True,
        config_path=config_path,
        output_csv=tmp_path / "operator_us_etf_market_data_execute.csv",
        output_report=tmp_path / "reports/operator_us_etf_market_data_execute_report.md",
        generated_at="2026-05-28T00:00:00+00:00",
        market_data_func=_successful_market_data,
    )
    assert [row["symbol"] for row in rows] == ["GLD", "SLV"]
    assert all(row["operator_approved"] == "YES" for row in rows)
    assert all(row["market_data_request_attempted"] == "YES" for row in rows)
    assert rows[0]["market_data_status"] == "REALTIME"
    assert rows[0]["error_type"] == "REALTIME"
    assert rows[1]["market_data_status"] == "DELAYED"
    assert rows[1]["error_type"] == "DELAYED"
    assert any_market_data_field_present(rows)
    assert all(row["account_read_attempted"] == "NO" for row in rows)
    assert all(row["positions_read_attempted"] == "NO" for row in rows)
    assert all(row["historical_data_requested"] == "NO" for row in rows)
    assert all(row["contract_qualification_attempted"] == "NO" for row in rows)
    assert all(row["orders_submitted"] == "NO" for row in rows)
    assert all(row["telegram_real_send_attempted"] == "NO" for row in rows)

    report = (tmp_path / "reports/operator_us_etf_market_data_execute_report.md").read_text(
        encoding="utf-8"
    )
    for section in (
        "# Phase 569-572 GLD / SLV Market Data Execute",
        "## Final Result",
        "## Scope Boundary",
        "## Market Data Summary",
        "## Error Taxonomy",
        "## Explicitly Prohibited Actions",
        "## Artifact Summary",
        "## Residual Risks",
    ):
        assert section in report
    for error_type in ERROR_TYPES:
        assert f"- {error_type}" in report
    assert "trading_enabled=YES" not in report
    assert "production_ready=YES" not in report


def test_no_data_is_symbol_specific(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    def requester(
        config: Dict[str, Any], symbols: Sequence[str]
    ) -> Tuple[Dict[str, Dict[str, Any]], None, str]:
        return {
            "GLD": {
                "ticker_received": True,
                "bid_present": False,
                "ask_present": False,
                "last_present": False,
                "close_present": False,
                "delayed_or_realtime": "UNKNOWN",
            },
            "SLV": {
                "ticker_received": True,
                "bid_present": False,
                "ask_present": False,
                "last_present": False,
                "close_present": True,
                "delayed_or_realtime": "DELAYED_FROZEN",
            },
        }, None, ""

    rows = build_us_etf_market_data_execute_rows(
        operator_approved=True,
        config_path=config_path,
        generated_at="2026-05-28T00:00:00+00:00",
        market_data_func=requester,
    )
    by_symbol = {row["symbol"]: row for row in rows}
    assert by_symbol["GLD"]["market_data_status"] == "NO_DATA"
    assert by_symbol["GLD"]["error_type"] == "NO_DATA"
    assert by_symbol["SLV"]["market_data_status"] == "DELAYED_FROZEN"
    assert by_symbol["SLV"]["error_type"] == "DELAYED_FROZEN"


def test_main_cli_denies_without_operator_approval(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--us-etf-market-data-execute"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 2
    assert "[US_ETF_MARKET_DATA_EXECUTE] denied" in result.stdout
    assert "operator_approved=NO" in result.stdout
    assert "market_data_request_attempted=NO" in result.stdout
    assert "error_type=OPERATOR_APPROVAL_REQUIRED" in result.stdout
    assert "DENIED / OPERATOR_APPROVAL_REQUIRED" in result.stdout
    assert (tmp_path / "operator_us_etf_market_data_execute.csv").exists()
    assert (tmp_path / "reports/operator_us_etf_market_data_execute_report.md").exists()
