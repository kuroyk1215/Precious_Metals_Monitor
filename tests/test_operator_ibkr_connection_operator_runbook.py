from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_ibkr_connection_operator_runbook import (
    CSV_FIELDS,
    RUNBOOK_STATUS,
    STATUS_VALUES,
    build_ibkr_connection_operator_runbook_rows,
    generate_ibkr_connection_operator_runbook,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_operator_runbook_generates_required_schema_and_report(tmp_path: Path) -> None:
    rows = generate_ibkr_connection_operator_runbook(
        output_csv=tmp_path / "operator_ibkr_connection_operator_runbook.csv",
        output_report=tmp_path / "reports/operator_ibkr_connection_operator_runbook_report.md",
        generated_at="2026-05-26T00:00:00+00:00",
    )

    csv_rows = _read_rows(tmp_path / "operator_ibkr_connection_operator_runbook.csv")
    assert rows == csv_rows
    assert csv_rows
    assert set(csv_rows[0]) == set(CSV_FIELDS)
    assert all(row["manual_only"] == "YES" for row in csv_rows)
    assert all(row["external_effect"] == "NONE" for row in csv_rows)
    assert any(row["category"] == "operator_runbook" for row in csv_rows)
    assert any(row["category"] == "local_checklist" for row in csv_rows)
    assert any(row["category"] == "connection_preconditions" for row in csv_rows)
    assert any(row["category"] == "failure_modes" for row in csv_rows)
    assert any(row["category"] == "rollback_actions" for row in csv_rows)
    assert any(row["blocked_capability"] == "IBKR_CONNECTION" for row in csv_rows)
    assert any(row["blocked_capability"] == "SECRET_OR_ACCOUNT_ID_DISCLOSURE" for row in csv_rows)

    report = (tmp_path / "reports/operator_ibkr_connection_operator_runbook_report.md").read_text(encoding="utf-8")
    for heading in (
        "# Phase 521-524 IBKR Connection Operator Runbook",
        "## Final Decision",
        "## Scope Boundary",
        "## Explicitly Prohibited Actions",
        "## Operator Runbook",
        "## Local Checklist",
        "## Connection Preconditions",
        "## Failure Modes",
        "## Rollback Actions",
        "## Artifact Summary",
        "## Residual Risks",
        "## Next Phase Preconditions",
    ):
        assert heading in report
    assert f"runbook_status={RUNBOOK_STATUS}" in report
    for field, value in STATUS_VALUES.items():
        assert f"{field}={value}" in report
    assert "connection_allowed=YES" not in report
    assert "operator_approved=YES" not in report
    assert "connection_decision=GO" not in report
    assert "real_market_data_verified=YES" not in report
    assert "production_ready=YES" not in report
    assert "IBKR_CONNECTION_PERMISSION_GATE_READY remains unchanged" in report


def test_operator_runbook_statuses_remain_connection_blocked() -> None:
    rows = build_ibkr_connection_operator_runbook_rows(generated_at="2026-05-26T00:00:00+00:00")

    assert rows[0]["status"] == "IBKR_CONNECTION_OPERATOR_RUNBOOK_READY"
    assert rows[0]["operator_action_required"] == "YES"
    assert STATUS_VALUES["operator_runbook_ready"] == "YES"
    assert STATUS_VALUES["operator_approval_required"] == "YES"
    assert STATUS_VALUES["connection_allowed"] == "NO"
    assert STATUS_VALUES["next_phase_connect_dry_run_candidate"] == "YES"
    assert all(row["external_effect"] == "NONE" for row in rows)


def test_operator_runbook_main_cli_generates_expected_outputs(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    result = subprocess.run(
        [
            "python3",
            str(REPO_ROOT / "main.py"),
            "--ibkr-connection-operator-runbook",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "runbook_status=IBKR_CONNECTION_OPERATOR_RUNBOOK_READY" in result.stdout
    assert "operator_runbook_ready=YES" in result.stdout
    assert "operator_approval_required=YES" in result.stdout
    assert "connection_allowed=NO" in result.stdout
    assert "external_connections_attempted=NO" in result.stdout
    assert "ibkr_connected=NO" in result.stdout
    assert "market_data_requested=NO" in result.stdout
    assert "account_read_attempted=NO" in result.stdout
    assert "positions_read_attempted=NO" in result.stdout
    assert "historical_data_requested=NO" in result.stdout
    assert "contract_qualification_attempted=NO" in result.stdout
    assert "orders_submitted=NO" in result.stdout
    assert "telegram_real_send_attempted=NO" in result.stdout
    assert "network_probe_attempted=NO" in result.stdout
    assert "next_phase_connect_dry_run_candidate=YES" in result.stdout
    assert "connection_allowed=YES" not in result.stdout
    assert "operator_approved=YES" not in result.stdout
    assert "connection_decision=GO" not in result.stdout
    assert "real_market_data_verified=YES" not in result.stdout
    assert "production_ready=YES" not in result.stdout
    assert (tmp_path / "operator_ibkr_connection_operator_runbook.csv").exists()
    assert (tmp_path / "reports/operator_ibkr_connection_operator_runbook_report.md").exists()
