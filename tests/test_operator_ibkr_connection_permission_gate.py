from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_ibkr_connection_permission_gate import (
    CONNECTION_PERMISSION_DECISION,
    CSV_FIELDS,
    PERMISSION_GATE_STATUS,
    STATUS_VALUES,
    build_ibkr_connection_permission_gate_rows,
    generate_ibkr_connection_permission_gate,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_permission_gate_generates_fail_closed_schema_and_report(tmp_path: Path) -> None:
    rows = generate_ibkr_connection_permission_gate(
        output_csv=tmp_path / "operator_ibkr_connection_permission_gate.csv",
        output_report=tmp_path / "reports/operator_ibkr_connection_permission_gate_report.md",
        generated_at="2026-05-26T00:00:00+00:00",
    )

    csv_rows = _read_rows(tmp_path / "operator_ibkr_connection_permission_gate.csv")
    assert rows == csv_rows
    assert csv_rows
    assert set(csv_rows[0]) == set(CSV_FIELDS)
    assert all(row["external_effect"] == "NONE" for row in csv_rows)
    assert all(row["fail_closed"] == "YES" for row in csv_rows)
    assert any(row["blocks"] == "IBKR_CONNECTION" for row in csv_rows)
    assert any(row["blocks"] == "MARKET_DATA_REQUEST" for row in csv_rows)
    assert any(row["blocks"] == "TELEGRAM_REAL_SEND" for row in csv_rows)

    report = (tmp_path / "reports/operator_ibkr_connection_permission_gate_report.md").read_text(encoding="utf-8")
    assert f"connection_permission_decision={CONNECTION_PERMISSION_DECISION}" in report
    assert f"permission_gate_status={PERMISSION_GATE_STATUS}" in report
    for field, value in STATUS_VALUES.items():
        assert f"{field}={value}" in report
    assert "connection_decision=GO" not in report
    assert "real_market_data_verified=YES" not in report
    assert "production_ready=YES" not in report
    assert "POST_MVP_MULTI_MARKET_FREEZE_READY remains unchanged" in report
    assert "REAL_MARKET_ENV_READINESS_PREFLIGHT_READY remains unchanged" in report


def test_permission_gate_denied_is_safe_default_not_failure() -> None:
    rows = build_ibkr_connection_permission_gate_rows(generated_at="2026-05-26T00:00:00+00:00")

    final_rows = [row for row in rows if row["category"] == "final_decision"]
    assert len(final_rows) == 1
    assert final_rows[0]["result"] == "DENIED"
    assert final_rows[0]["approval_required"] == "YES"
    assert final_rows[0]["operator_action_required"] == "YES"
    assert STATUS_VALUES["connection_allowed"] == "NO"
    assert STATUS_VALUES["next_phase_connection_candidate"] == "YES"


def test_permission_gate_main_cli_generates_expected_outputs(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    result = subprocess.run(
        [
            "python3",
            str(REPO_ROOT / "main.py"),
            "--ibkr-connection-permission-gate",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "connection_permission_decision=DENIED" in result.stdout
    assert "permission_gate_status=IBKR_CONNECTION_PERMISSION_GATE_READY" in result.stdout
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
    assert "next_phase_connection_candidate=YES" in result.stdout
    assert "connection_decision=GO" not in result.stdout
    assert "real_market_data_verified=YES" not in result.stdout
    assert "production_ready=YES" not in result.stdout
    assert (tmp_path / "operator_ibkr_connection_permission_gate.csv").exists()
    assert (tmp_path / "reports/operator_ibkr_connection_permission_gate_report.md").exists()
