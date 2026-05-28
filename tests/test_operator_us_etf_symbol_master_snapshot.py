from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_us_etf_symbol_master_snapshot import (
    CN_STATUS,
    CSV_FIELDS,
    JP_STATUS,
    build_us_etf_symbol_master_snapshot_rows,
    generate_us_etf_symbol_master_snapshot,
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
        "con_id_present",
        "primary_exchange_redacted",
        "evidence",
        "timestamp_utc",
    ]
    rows = [
        {
            "phase": "Phase 553-556",
            "symbol": "GLD",
            "asset_class": "ETF",
            "exchange": "SMART",
            "currency": "USD",
            "qualification_status": "QUALIFIED",
            "qualified": "YES",
            "con_id_present": "YES",
            "primary_exchange_redacted": "PRESENT_REDACTED",
            "evidence": "GLD_qualified_once_contract_count_1",
            "timestamp_utc": "2026-05-28T00:00:00+00:00",
        },
        {
            "phase": "Phase 553-556",
            "symbol": "SLV",
            "asset_class": "ETF",
            "exchange": "SMART",
            "currency": "USD",
            "qualification_status": "QUALIFIED",
            "qualified": "YES",
            "con_id_present": "YES",
            "primary_exchange_redacted": "PRESENT_REDACTED",
            "evidence": "SLV_qualified_once_contract_count_1",
            "timestamp_utc": "2026-05-28T00:00:00+00:00",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_build_snapshot_rows_from_qualified_source(tmp_path: Path) -> None:
    source = tmp_path / "operator_us_etf_contract_qualification_execute.csv"
    _write_source(source)
    rows = build_us_etf_symbol_master_snapshot_rows(
        source_csv=source,
        generated_at="2026-05-28T01:02:03+00:00",
    )
    assert [row["symbol"] for row in rows] == ["GLD", "SLV"]
    assert all(set(row) == set(CSV_FIELDS) for row in rows)
    assert all(row["phase"] == "Phase 557-560" for row in rows)
    assert all(row["source_phase"] == "Phase 553-556" for row in rows)
    assert all(row["qualification_status"] == "QUALIFIED" for row in rows)
    assert all(row["qualified"] == "YES" for row in rows)
    assert all(row["contract_metadata_available"] == "YES" for row in rows)
    assert all(row["con_id_present"] == "YES" for row in rows)
    assert all(row["primary_exchange_redacted"] == "PRESENT_REDACTED" for row in rows)
    assert all(row["market_data_verified"] == "NO" for row in rows)
    assert all(row["historical_data_verified"] == "NO" for row in rows)
    assert all(row["account_read_verified"] == "NO" for row in rows)
    assert all(row["positions_read_verified"] == "NO" for row in rows)
    assert all(row["trading_enabled"] == "NO" for row in rows)
    assert all(row["jp_status"] == JP_STATUS for row in rows)
    assert all(row["cn_status"] == CN_STATUS for row in rows)
    assert all(row["external_effect"] == "NONE" for row in rows)


def test_generate_snapshot_artifacts_and_report_sections(tmp_path: Path) -> None:
    source = tmp_path / "operator_us_etf_contract_qualification_execute.csv"
    output_csv = tmp_path / "operator_us_etf_symbol_master_snapshot.csv"
    output_report = tmp_path / "reports/operator_us_etf_symbol_master_snapshot_report.md"
    _write_source(source)
    rows = generate_us_etf_symbol_master_snapshot(
        source_csv=source,
        output_csv=output_csv,
        output_report=output_report,
        generated_at="2026-05-28T01:02:03+00:00",
    )
    assert rows == _read_rows(output_csv)
    report = output_report.read_text(encoding="utf-8")
    for section in (
        "# Phase 557-560 GLD / SLV Symbol Master Snapshot",
        "## Final Snapshot Status",
        "## Scope Boundary",
        "## Source Qualification Summary",
        "## Symbol Master Snapshot",
        "## JP / CN Frozen Status",
        "## Explicitly Prohibited Actions",
        "## Artifact Summary",
        "## Residual Risks",
        "## Next Phase Preconditions",
    ):
        assert section in report
    assert "symbol_master_status=US_ETF_SYMBOL_MASTER_SNAPSHOT_READY" in report
    assert "qualified_symbols_count=2" in report
    assert "market_data_verified=YES" not in report
    assert "historical_data_verified=YES" not in report
    assert "account_read_verified=YES" not in report
    assert "positions_read_verified=YES" not in report
    assert "trading_enabled=YES" not in report
    assert "production_ready=YES" not in report


def test_main_cli_generates_required_output(tmp_path: Path) -> None:
    _write_source(tmp_path / "operator_us_etf_contract_qualification_execute.csv")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--us-etf-symbol-master-snapshot"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0
    required_lines = [
        "[US_ETF_SYMBOL_MASTER_SNAPSHOT] generated",
        "symbol_master_status=US_ETF_SYMBOL_MASTER_SNAPSHOT_READY",
        "source_phase=Phase 553-556",
        "symbols=GLD,SLV",
        "GLD_qualification_status=QUALIFIED",
        "SLV_qualification_status=QUALIFIED",
        "qualified_symbols_count=2",
        "market_data_verified=NO",
        "historical_data_verified=NO",
        "account_read_verified=NO",
        "positions_read_verified=NO",
        "trading_enabled=NO",
        "jp_status=FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION",
        "cn_status=FROZEN_PENDING_DATA_SOURCE_DECISION",
        "next_phase_market_data_permission_gate_candidate=YES",
    ]
    for line in required_lines:
        assert line in result.stdout
    forbidden_lines = [
        "market_data_verified=YES",
        "historical_data_verified=YES",
        "account_read_verified=YES",
        "positions_read_verified=YES",
        "trading_enabled=YES",
        "production_ready=YES",
    ]
    for line in forbidden_lines:
        assert line not in result.stdout
    assert (tmp_path / "operator_us_etf_symbol_master_snapshot.csv").exists()
    assert (tmp_path / "reports/operator_us_etf_symbol_master_snapshot_report.md").exists()
