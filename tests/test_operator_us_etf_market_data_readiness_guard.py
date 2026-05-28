from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_us_etf_market_data_readiness_guard import (
    CN_STATUS,
    CSV_FIELDS,
    JP_STATUS,
    build_us_etf_market_data_readiness_guard_rows,
    generate_us_etf_market_data_readiness_guard,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_source(path: Path) -> None:
    fields = [
        "phase",
        "symbol",
        "asset_class",
        "exchange",
        "currency",
        "qualification_status",
        "qualified",
        "market_data_verified",
        "timestamp_utc",
    ]
    rows = [
        {
            "phase": "Phase 557-560",
            "symbol": "GLD",
            "asset_class": "ETF",
            "exchange": "SMART",
            "currency": "USD",
            "qualification_status": "QUALIFIED",
            "qualified": "YES",
            "market_data_verified": "NO",
            "timestamp_utc": "2026-05-28T00:00:00+00:00",
        },
        {
            "phase": "Phase 557-560",
            "symbol": "SLV",
            "asset_class": "ETF",
            "exchange": "SMART",
            "currency": "USD",
            "qualification_status": "QUALIFIED",
            "qualified": "YES",
            "market_data_verified": "NO",
            "timestamp_utc": "2026-05-28T00:00:00+00:00",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_build_guard_rows_from_symbol_master_source(tmp_path: Path) -> None:
    source = tmp_path / "operator_us_etf_symbol_master_snapshot.csv"
    _write_source(source)
    rows = build_us_etf_market_data_readiness_guard_rows(
        source_csv=source,
        generated_at="2026-05-28T01:02:03+00:00",
    )
    assert len(rows) == 4
    assert all(set(row) == set(CSV_FIELDS) for row in rows)
    assert {row["symbol"] for row in rows} == {"GLD", "SLV"}
    assert {row["category"] for row in rows} == {"market_data_permission_gate", "market_data_execute_guard"}
    assert all(row["phase"] == "Phase 561-568" for row in rows)
    assert all(row["operator_authorization_required"] == "YES" for row in rows)
    assert all(row["market_data_request_allowed"] == "NO" for row in rows)
    assert all(row["market_data_execute_guard_ready"] == "YES" for row in rows)
    assert all(row["market_data_requested"] == "NO" for row in rows)
    assert all(row["external_connections_attempted"] == "NO" for row in rows)
    assert all(row["account_read_attempted"] == "NO" for row in rows)
    assert all(row["positions_read_attempted"] == "NO" for row in rows)
    assert all(row["historical_data_requested"] == "NO" for row in rows)
    assert all(row["contract_qualification_attempted"] == "NO" for row in rows)
    assert all(row["orders_submitted"] == "NO" for row in rows)
    assert all(row["telegram_real_send_attempted"] == "NO" for row in rows)
    assert all(row["jp_status"] == JP_STATUS for row in rows)
    assert all(row["cn_status"] == CN_STATUS for row in rows)
    assert all(row["external_effect"] == "NONE" for row in rows)


def test_generate_guard_artifacts_and_report_sections(tmp_path: Path) -> None:
    source = tmp_path / "operator_us_etf_symbol_master_snapshot.csv"
    output_csv = tmp_path / "operator_us_etf_market_data_readiness_guard.csv"
    output_report = tmp_path / "reports/operator_us_etf_market_data_readiness_guard_report.md"
    _write_source(source)
    rows = generate_us_etf_market_data_readiness_guard(
        source_csv=source,
        output_csv=output_csv,
        output_report=output_report,
        generated_at="2026-05-28T01:02:03+00:00",
    )
    assert rows == _read_rows(output_csv)
    report = output_report.read_text(encoding="utf-8")
    for section in (
        "# Phase 561-568 US ETF Market Data Readiness Guard",
        "## Final Decision",
        "## Scope Boundary",
        "## Source Symbol Master Summary",
        "## Market Data Permission Gate",
        "## GLD / SLV Execute Guard",
        "## JP / CN Frozen Status",
        "## Explicitly Prohibited Actions",
        "## Artifact Summary",
        "## Residual Risks",
        "## Next Phase Preconditions",
    ):
        assert section in report
    assert "market_data_permission_decision=DENIED" in report
    assert "market_data_readiness_guard_status=US_ETF_MARKET_DATA_READINESS_GUARD_READY" in report
    assert "market_data_request_allowed=YES" not in report
    assert "market_data_requested=YES" not in report
    assert "market_data_verified=YES" not in report
    assert "historical_data_verified=YES" not in report
    assert "account_read_verified=YES" not in report
    assert "positions_read_verified=YES" not in report
    assert "trading_enabled=YES" not in report
    assert "production_ready=YES" not in report


def test_main_cli_generates_required_output(tmp_path: Path) -> None:
    _write_source(tmp_path / "operator_us_etf_symbol_master_snapshot.csv")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--us-etf-market-data-readiness-guard"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0
    required_lines = [
        "[US_ETF_MARKET_DATA_READINESS_GUARD] generated",
        "market_data_permission_decision=DENIED",
        "market_data_readiness_guard_status=US_ETF_MARKET_DATA_READINESS_GUARD_READY",
        "operator_authorization_required=YES",
        "symbols=GLD,SLV",
        "GLD_qualification_status=QUALIFIED",
        "SLV_qualification_status=QUALIFIED",
        "market_data_request_allowed=NO",
        "market_data_execute_guard_ready=YES",
        "market_data_requested=NO",
        "external_connections_attempted=NO",
        "account_read_attempted=NO",
        "positions_read_attempted=NO",
        "historical_data_requested=NO",
        "contract_qualification_attempted=NO",
        "orders_submitted=NO",
        "telegram_real_send_attempted=NO",
        "jp_status=FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION",
        "cn_status=FROZEN_PENDING_DATA_SOURCE_DECISION",
        "next_phase_market_data_execute_candidate=YES",
    ]
    for line in required_lines:
        assert line in result.stdout
    forbidden_lines = [
        "market_data_request_allowed=YES",
        "market_data_requested=YES",
        "market_data_verified=YES",
        "historical_data_verified=YES",
        "account_read_verified=YES",
        "positions_read_verified=YES",
        "trading_enabled=YES",
        "production_ready=YES",
    ]
    for line in forbidden_lines:
        assert line not in result.stdout
    assert (tmp_path / "operator_us_etf_market_data_readiness_guard.csv").exists()
    assert (tmp_path / "reports/operator_us_etf_market_data_readiness_guard_report.md").exists()
