from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Sequence, Tuple

from src.operator_us_etf_contract_qualification_execute import (
    CSV_FIELDS,
    ERROR_TYPES,
    SYMBOLS,
    build_us_etf_contract_qualification_execute_rows,
    generate_us_etf_contract_qualification_execute,
    qualified_symbols_count,
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
                "  client_id: 553556",
                "  readonly: true",
                "  timeout_sec: 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _successful_qualifier(
    config: Dict[str, Any], symbols: Sequence[str]
) -> Tuple[Dict[str, Dict[str, Any]], None, str]:
    assert config["host"] == "127.0.0.1"
    assert tuple(symbols) == SYMBOLS
    return {
        "GLD": {"contracts": [SimpleNamespace(conId=1001, primaryExchange="ARCA")]},
        "SLV": {"contracts": [SimpleNamespace(conId=1002, primaryExchange="ARCA")]},
    }, None, ""


def test_unapproved_path_denies_without_qualification(tmp_path: Path) -> None:
    rows = generate_us_etf_contract_qualification_execute(
        operator_approved=False,
        output_csv=tmp_path / "operator_us_etf_contract_qualification_execute.csv",
        output_report=tmp_path / "reports/operator_us_etf_contract_qualification_execute_report.md",
        generated_at="2026-05-28T00:00:00+00:00",
    )
    csv_rows = _read_rows(tmp_path / "operator_us_etf_contract_qualification_execute.csv")
    assert rows == csv_rows
    assert set(csv_rows[0]) == set(CSV_FIELDS)
    assert [row["symbol"] for row in csv_rows] == ["GLD", "SLV"]
    assert all(row["operator_approved"] == "NO" for row in csv_rows)
    assert all(row["qualification_attempted"] == "NO" for row in csv_rows)
    assert all(row["error_type"] == "OPERATOR_APPROVAL_REQUIRED" for row in csv_rows)
    assert all(row["market_data_requested"] == "NO" for row in csv_rows)
    assert all(row["account_read_attempted"] == "NO" for row in csv_rows)
    assert all(row["positions_read_attempted"] == "NO" for row in csv_rows)
    assert all(row["historical_data_requested"] == "NO" for row in csv_rows)
    assert all(row["orders_submitted"] == "NO" for row in csv_rows)
    assert all(row["telegram_real_send_attempted"] == "NO" for row in csv_rows)


def test_authorized_success_archives_gld_and_slv(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)
    rows = generate_us_etf_contract_qualification_execute(
        operator_approved=True,
        config_path=config_path,
        output_csv=tmp_path / "operator_us_etf_contract_qualification_execute.csv",
        output_report=tmp_path / "reports/operator_us_etf_contract_qualification_execute_report.md",
        generated_at="2026-05-28T00:00:00+00:00",
        qualify_func=_successful_qualifier,
    )
    assert qualified_symbols_count(rows) == 2
    assert [row["symbol"] for row in rows] == ["GLD", "SLV"]
    assert all(row["operator_approved"] == "YES" for row in rows)
    assert all(row["qualification_attempted"] == "YES" for row in rows)
    assert all(row["qualification_status"] == "QUALIFIED" for row in rows)
    assert all(row["error_type"] == "QUALIFIED" for row in rows)
    assert all(row["qualified"] == "YES" for row in rows)
    assert all(row["contract_count"] == "1" for row in rows)
    assert all(row["primary_exchange_redacted"] == "PRESENT_REDACTED" for row in rows)
    assert all(row["con_id_present"] == "YES" for row in rows)
    assert all(row["market_data_requested"] == "NO" for row in rows)
    assert all(row["account_read_attempted"] == "NO" for row in rows)
    assert all(row["positions_read_attempted"] == "NO" for row in rows)
    assert all(row["historical_data_requested"] == "NO" for row in rows)
    assert all(row["orders_submitted"] == "NO" for row in rows)
    assert all(row["telegram_real_send_attempted"] == "NO" for row in rows)

    report = (tmp_path / "reports/operator_us_etf_contract_qualification_execute_report.md").read_text(
        encoding="utf-8"
    )
    for section in (
        "# Phase 553-556 GLD / SLV Contract Qualification Execute",
        "## Final Result",
        "## Scope Boundary",
        "## Operator Approval",
        "## Qualification Summary",
        "## Qualified Contracts",
        "## Error Taxonomy",
        "## Explicitly Prohibited Actions",
        "## Artifact Summary",
        "## Residual Risks",
        "## Next Phase Preconditions",
    ):
        assert section in report
    for error_type in ERROR_TYPES:
        assert f"- {error_type}" in report
    assert "qualified_symbols_count=2" in report
    assert "market_data_verified=YES" not in report
    assert "production_ready=YES" not in report
    assert "trading_enabled=YES" not in report


def test_partial_failure_is_symbol_specific(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    def qualifier(
        config: Dict[str, Any], symbols: Sequence[str]
    ) -> Tuple[Dict[str, Dict[str, Any]], None, str]:
        return {
            "GLD": {"contracts": [SimpleNamespace(conId=1001, primaryExchange="ARCA")]},
            "SLV": {"contracts": []},
        }, None, ""

    rows = build_us_etf_contract_qualification_execute_rows(
        operator_approved=True,
        config_path=config_path,
        generated_at="2026-05-28T00:00:00+00:00",
        qualify_func=qualifier,
    )
    by_symbol = {row["symbol"]: row for row in rows}
    assert by_symbol["GLD"]["qualification_status"] == "QUALIFIED"
    assert by_symbol["SLV"]["qualification_status"] == "CONTRACT_NOT_FOUND"
    assert qualified_symbols_count(rows) == 1


def test_main_cli_denies_without_operator_approval(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--us-etf-contract-qualification-execute"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 2
    assert "[US_ETF_CONTRACT_QUALIFICATION_EXECUTE] denied" in result.stdout
    assert "operator_approved=NO" in result.stdout
    assert "qualification_attempted=NO" in result.stdout
    assert "error_type=OPERATOR_APPROVAL_REQUIRED" in result.stdout
    assert "DENIED / OPERATOR_APPROVAL_REQUIRED" in result.stdout
    assert (tmp_path / "operator_us_etf_contract_qualification_execute.csv").exists()
    assert (tmp_path / "reports/operator_us_etf_contract_qualification_execute_report.md").exists()
