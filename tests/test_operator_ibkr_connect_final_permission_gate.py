from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_ibkr_connect_final_permission_gate import (
    CSV_FIELDS,
    FINAL_PERMISSION_GATE_STATUS,
    STATUS_VALUES,
    build_ibkr_connect_final_permission_gate_rows,
    generate_ibkr_connect_final_permission_gate,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_final_permission_gate_generates_schema_and_report(tmp_path: Path) -> None:
    rows = generate_ibkr_connect_final_permission_gate(
        output_csv=tmp_path / "operator_ibkr_connect_final_permission_gate.csv",
        output_report=tmp_path / "reports/operator_ibkr_connect_final_permission_gate_report.md",
        generated_at="2026-05-26T00:00:00+00:00",
    )
    csv_rows = _read_rows(tmp_path / "operator_ibkr_connect_final_permission_gate.csv")
    assert rows == csv_rows
    assert set(csv_rows[0]) == set(CSV_FIELDS)
    assert all(row["fail_closed"] == "YES" for row in csv_rows)
    assert all(row["operator_authorization_required"] == "YES" for row in csv_rows)
    assert all(row["connect_execution_allowed"] == "NO" for row in csv_rows)
    assert all(row["external_effect"] == "NONE" for row in csv_rows)
    assert any(row["blocked_capability"] == "IBKR_CONNECTION_EXECUTION" for row in csv_rows)
    assert any(row["blocked_capability"] == "NETWORK_OR_IBKR_SIDE_EFFECT" for row in csv_rows)

    report = (tmp_path / "reports/operator_ibkr_connect_final_permission_gate_report.md").read_text(
        encoding="utf-8"
    )
    assert "# Phase 533-536 IBKR Connect Final Permission Gate" in report
    assert f"final_permission_gate_status={FINAL_PERMISSION_GATE_STATUS}" in report
    for field, value in STATUS_VALUES.items():
        assert f"{field}={value}" in report
    assert "connection_allowed=YES" not in report
    assert "connect_execution_allowed=YES" not in report
    assert "operator_authorized=YES" not in report
    assert "connection_decision=GO" not in report
    assert "production_ready=YES" not in report
    assert "real_market_data_verified=YES" not in report


def test_final_permission_gate_statuses_remain_denied() -> None:
    rows = build_ibkr_connect_final_permission_gate_rows(generated_at="2026-05-26T00:00:00+00:00")
    assert rows[0]["result"] == "DENIED"
    assert STATUS_VALUES["connect_execution_permission_decision"] == "DENIED"
    assert STATUS_VALUES["operator_authorization_required"] == "YES"
    assert STATUS_VALUES["connect_execution_allowed"] == "NO"
    assert STATUS_VALUES["connection_allowed"] == "NO"
    assert STATUS_VALUES["external_connections_attempted"] == "NO"
    assert STATUS_VALUES["network_probe_attempted"] == "NO"
    assert STATUS_VALUES["next_phase_connect_only_execute_candidate"] == "YES"


def test_final_permission_gate_main_cli_generates_expected_outputs(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--ibkr-connect-final-permission-gate"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "[IBKR_CONNECT_FINAL_PERMISSION_GATE] generated" in result.stdout
    assert "connect_execution_permission_decision=DENIED" in result.stdout
    assert "final_permission_gate_status=IBKR_CONNECT_FINAL_PERMISSION_GATE_READY" in result.stdout
    assert "operator_authorization_required=YES" in result.stdout
    assert "connect_execution_allowed=NO" in result.stdout
    assert "connection_allowed=NO" in result.stdout
    assert "external_connections_attempted=NO" in result.stdout
    assert "ibkr_connected=NO" in result.stdout
    assert "network_probe_attempted=NO" in result.stdout
    assert "market_data_requested=NO" in result.stdout
    assert "account_read_attempted=NO" in result.stdout
    assert "positions_read_attempted=NO" in result.stdout
    assert "historical_data_requested=NO" in result.stdout
    assert "contract_qualification_attempted=NO" in result.stdout
    assert "orders_submitted=NO" in result.stdout
    assert "telegram_real_send_attempted=NO" in result.stdout
    assert "next_phase_connect_only_execute_candidate=YES" in result.stdout
    assert "connection_allowed=YES" not in result.stdout
    assert "connect_execution_allowed=YES" not in result.stdout
    assert "operator_authorized=YES" not in result.stdout
    assert "connection_decision=GO" not in result.stdout
    assert "production_ready=YES" not in result.stdout
    assert "real_market_data_verified=YES" not in result.stdout
    assert (tmp_path / "operator_ibkr_connect_final_permission_gate.csv").exists()
    assert (tmp_path / "reports/operator_ibkr_connect_final_permission_gate_report.md").exists()
