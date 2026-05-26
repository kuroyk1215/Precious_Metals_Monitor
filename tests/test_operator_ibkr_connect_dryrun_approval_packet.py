from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_ibkr_connect_dryrun_approval_packet import (
    APPROVAL_PACKET_STATUS,
    CSV_FIELDS,
    STATUS_VALUES,
    build_ibkr_connect_dryrun_approval_packet_rows,
    generate_ibkr_connect_dryrun_approval_packet,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_approval_packet_generates_required_schema_and_report(tmp_path: Path) -> None:
    rows = generate_ibkr_connect_dryrun_approval_packet(
        output_csv=tmp_path / "operator_ibkr_connect_dryrun_approval_packet.csv",
        output_report=tmp_path / "reports/operator_ibkr_connect_dryrun_approval_packet_report.md",
        generated_at="2026-05-26T00:00:00+00:00",
    )

    csv_rows = _read_rows(tmp_path / "operator_ibkr_connect_dryrun_approval_packet.csv")
    assert rows == csv_rows
    assert csv_rows
    assert set(csv_rows[0]) == set(CSV_FIELDS)
    assert all(row["manual_only"] == "YES" for row in csv_rows)
    assert all(row["external_effect"] == "NONE" for row in csv_rows)
    assert any(row["category"] == "final_decision" for row in csv_rows)
    assert any(row["category"] == "command_preview" for row in csv_rows)
    assert any(row["blocked_capability"] == "IBKR_CONNECTION" for row in csv_rows)
    assert any(row["blocked_capability"] == "SECRET_OR_ACCOUNT_ID_DISCLOSURE" for row in csv_rows)

    report = (tmp_path / "reports/operator_ibkr_connect_dryrun_approval_packet_report.md").read_text(
        encoding="utf-8"
    )
    assert "# Phase 525-528 IBKR Connect Dry-Run Approval Packet" in report
    assert "## Final Decision" in report
    assert "## Approval Packet" in report
    assert "## No-Go Conditions" in report
    assert "## Guard Checks" in report
    assert "## Next Phase Preconditions" in report
    assert f"approval_packet_status={APPROVAL_PACKET_STATUS}" in report
    for field, value in STATUS_VALUES.items():
        assert f"{field}={value}" in report
    assert "connection_allowed=YES" not in report
    assert "operator_approved=YES" not in report
    assert "connection_decision=GO" not in report
    assert "real_market_data_verified=YES" not in report
    assert "production_ready=YES" not in report
    assert "connect_command_emitted=YES" not in report
    assert "IBKR_CONNECTION_PERMISSION_GATE_READY remains unchanged" in report
    assert "IBKR_CONNECTION_OPERATOR_RUNBOOK_READY remains unchanged" in report


def test_approval_packet_keeps_connection_blocked_and_command_withheld() -> None:
    rows = build_ibkr_connect_dryrun_approval_packet_rows(generated_at="2026-05-26T00:00:00+00:00")

    assert rows[0]["decision"] == "NO_GO"
    assert rows[0]["operator_action_required"] == "YES"
    assert STATUS_VALUES["approval_decision"] == "NO_GO"
    assert STATUS_VALUES["operator_approval_required"] == "YES"
    assert STATUS_VALUES["connect_dry_run_candidate"] == "YES"
    assert STATUS_VALUES["connection_allowed"] == "NO"
    assert STATUS_VALUES["connect_command_emitted"] == "NO"
    assert STATUS_VALUES["external_connections_attempted"] == "NO"
    assert all(row["external_effect"] == "NONE" for row in rows)


def test_approval_packet_main_cli_generates_expected_outputs(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    result = subprocess.run(
        [
            "python3",
            str(REPO_ROOT / "main.py"),
            "--ibkr-connect-dryrun-approval-packet",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "approval_packet_status=IBKR_CONNECT_DRYRUN_APPROVAL_PACKET_READY" in result.stdout
    assert "approval_decision=NO_GO" in result.stdout
    assert "operator_approval_required=YES" in result.stdout
    assert "connect_dry_run_candidate=YES" in result.stdout
    assert "connection_allowed=NO" in result.stdout
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
    assert "connection_allowed=YES" not in result.stdout
    assert "operator_approved=YES" not in result.stdout
    assert "connection_decision=GO" not in result.stdout
    assert "real_market_data_verified=YES" not in result.stdout
    assert "production_ready=YES" not in result.stdout
    assert "connect_command_emitted=YES" not in result.stdout
    assert (tmp_path / "operator_ibkr_connect_dryrun_approval_packet.csv").exists()
    assert (tmp_path / "reports/operator_ibkr_connect_dryrun_approval_packet_report.md").exists()
