from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_ibkr_connect_execution_skeleton_review import (
    CSV_FIELDS,
    EXECUTION_SKELETON_STATUS,
    STATUS_VALUES,
    build_ibkr_connect_execution_skeleton_review_rows,
    generate_ibkr_connect_execution_skeleton_review,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_execution_skeleton_review_generates_schema_and_report(tmp_path: Path) -> None:
    rows = generate_ibkr_connect_execution_skeleton_review(
        output_csv=tmp_path / "operator_ibkr_connect_execution_skeleton_review.csv",
        output_report=tmp_path / "reports/operator_ibkr_connect_execution_skeleton_review_report.md",
        generated_at="2026-05-26T00:00:00+00:00",
    )
    csv_rows = _read_rows(tmp_path / "operator_ibkr_connect_execution_skeleton_review.csv")
    assert rows == csv_rows
    assert set(csv_rows[0]) == set(CSV_FIELDS)
    assert all(row["manual_only"] == "YES" for row in csv_rows)
    assert all(row["external_effect"] == "NONE" for row in csv_rows)
    assert any(row["blocked_capability"] == "IBKR_CONNECTION" for row in csv_rows)
    assert any(row["blocked_capability"] == "REAL_CONNECTION_EXECUTION" for row in csv_rows)

    report = (tmp_path / "reports/operator_ibkr_connect_execution_skeleton_review_report.md").read_text(
        encoding="utf-8"
    )
    assert "# Phase 529-532 IBKR Connect Execution Skeleton Review" in report
    assert f"execution_skeleton_status={EXECUTION_SKELETON_STATUS}" in report
    for field, value in STATUS_VALUES.items():
        assert f"{field}={value}" in report
    assert "connection_allowed=YES" not in report
    assert "execute_cli_present=YES" not in report
    assert "connect_command_emitted=YES" not in report
    assert "operator_approved=YES" not in report
    assert "connection_decision=GO" not in report
    assert "real_market_data_verified=YES" not in report
    assert "production_ready=YES" not in report


def test_execution_skeleton_review_statuses_remain_blocked() -> None:
    rows = build_ibkr_connect_execution_skeleton_review_rows(generated_at="2026-05-26T00:00:00+00:00")
    assert rows[0]["status"] == "NO_GO"
    assert STATUS_VALUES["connection_allowed"] == "NO"
    assert STATUS_VALUES["execute_cli_present"] == "NO"
    assert STATUS_VALUES["connect_command_emitted"] == "NO"
    assert STATUS_VALUES["external_connections_attempted"] == "NO"
    assert STATUS_VALUES["next_phase_execute_candidate"] == "YES"


def test_execution_skeleton_review_main_cli_generates_expected_outputs(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--ibkr-connect-execution-skeleton-review"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "execution_skeleton_status=IBKR_CONNECT_EXECUTION_SKELETON_REVIEW_READY" in result.stdout
    assert "final_decision=NO_GO" in result.stdout
    assert "operator_approval_required=YES" in result.stdout
    assert "connection_allowed=NO" in result.stdout
    assert "execute_cli_present=NO" in result.stdout
    assert "connect_command_emitted=NO" in result.stdout
    assert "external_connections_attempted=NO" in result.stdout
    assert "network_probe_attempted=NO" in result.stdout
    assert "ibkr_connected=NO" in result.stdout
    assert "market_data_requested=NO" in result.stdout
    assert "account_read_attempted=NO" in result.stdout
    assert "positions_read_attempted=NO" in result.stdout
    assert "historical_data_requested=NO" in result.stdout
    assert "contract_qualification_attempted=NO" in result.stdout
    assert "orders_submitted=NO" in result.stdout
    assert "orders_cancelled=NO" in result.stdout
    assert "rebalance_attempted=NO" in result.stdout
    assert "telegram_real_send_attempted=NO" in result.stdout
    assert "next_phase_execute_candidate=YES" in result.stdout
    assert "connection_allowed=YES" not in result.stdout
    assert "execute_cli_present=YES" not in result.stdout
    assert "connect_command_emitted=YES" not in result.stdout
    assert (tmp_path / "operator_ibkr_connect_execution_skeleton_review.csv").exists()
    assert (tmp_path / "reports/operator_ibkr_connect_execution_skeleton_review_report.md").exists()
