from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_ibkr_connection_result_archive import (
    ARCHIVE_STATUS,
    CLASSIFICATION,
    CSV_FIELDS,
    ERROR_TAXONOMY,
    SOURCE_PHASE,
    SOURCE_RESULT,
    build_ibkr_connection_result_archive_rows,
    generate_ibkr_connection_result_archive,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_build_archive_rows_are_connectivity_only() -> None:
    rows = build_ibkr_connection_result_archive_rows(generated_at="2026-05-28T00:00:00+00:00")
    assert len(rows) == 1
    row = rows[0]
    assert set(row) == set(CSV_FIELDS)
    assert row["phase"] == "Phase 541-544"
    assert row["source_phase"] == SOURCE_PHASE
    assert row["connection_status"] == SOURCE_RESULT
    assert row["connected"] == "YES"
    assert row["disconnected"] == "YES"
    assert row["operator_approved"] == "YES"
    assert row["connection_attempted"] == "YES"
    assert row["market_data_requested"] == "NO"
    assert row["account_read_attempted"] == "NO"
    assert row["positions_read_attempted"] == "NO"
    assert row["historical_data_requested"] == "NO"
    assert row["contract_qualification_attempted"] == "NO"
    assert row["orders_submitted"] == "NO"
    assert row["telegram_real_send_attempted"] == "NO"
    assert row["error_type"] == "CONNECTED_THEN_DISCONNECTED"
    assert row["classification"] == CLASSIFICATION


def test_generate_archive_writes_csv_and_required_report_sections(tmp_path: Path) -> None:
    rows = generate_ibkr_connection_result_archive(
        output_csv=tmp_path / "operator_ibkr_connection_result_archive.csv",
        output_report=tmp_path / "reports/operator_ibkr_connection_result_archive_report.md",
        generated_at="2026-05-28T00:00:00+00:00",
    )
    csv_rows = _read_rows(tmp_path / "operator_ibkr_connection_result_archive.csv")
    assert rows == csv_rows
    report = (tmp_path / "reports/operator_ibkr_connection_result_archive_report.md").read_text(
        encoding="utf-8"
    )
    for section in (
        "# Phase 541-544 IBKR Connection Result Archive",
        "## Final Archive Status",
        "## Scope Boundary",
        "## Source Phase Summary",
        "## Result Classification",
        "## Error Taxonomy",
        "## Explicitly Prohibited Actions",
        "## Artifact Summary",
        "## Residual Risks",
        "## Next Phase Preconditions",
    ):
        assert section in report
    for error_type in ERROR_TAXONOMY:
        assert error_type in report
    assert f"archive_status={ARCHIVE_STATUS}" in report
    assert "market_data_verified=NO" in report
    assert "production_ready=YES" not in report
    assert "market_data_verified=YES" not in report


def test_main_cli_outputs_required_archive_status(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--ibkr-connection-result-archive"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "[IBKR_CONNECTION_RESULT_ARCHIVE] generated" in result.stdout
    assert "archive_status=IBKR_CONNECTION_RESULT_ARCHIVE_READY" in result.stdout
    assert "source_phase=Phase 537-540" in result.stdout
    assert "source_result=CONNECTED_THEN_DISCONNECTED" in result.stdout
    assert "classification=CONNECTIVITY_VERIFIED_ONLY" in result.stdout
    assert "ibkr_connectivity_verified=YES" in result.stdout
    assert "market_data_verified=NO" in result.stdout
    assert "account_read_verified=NO" in result.stdout
    assert "positions_read_verified=NO" in result.stdout
    assert "historical_data_verified=NO" in result.stdout
    assert "contract_qualification_verified=NO" in result.stdout
    assert "trading_verified=NO" in result.stdout
    assert "telegram_real_send_verified=NO" in result.stdout
    assert "next_phase_contract_qualification_gate_candidate=YES" in result.stdout
    assert "production_ready=YES" not in result.stdout
    assert "market_data_verified=YES" not in result.stdout
    assert (tmp_path / "operator_ibkr_connection_result_archive.csv").exists()
    assert (tmp_path / "reports/operator_ibkr_connection_result_archive_report.md").exists()
