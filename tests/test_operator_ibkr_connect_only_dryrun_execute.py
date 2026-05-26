from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path
from typing import Optional

from src.operator_ibkr_connect_only_dryrun_execute import (
    CSV_FIELDS,
    build_ibkr_connect_only_dryrun_execute_rows,
    classify_error,
    generate_ibkr_connect_only_dryrun_execute,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_config(path: Path) -> None:
    path.write_text(
        "ibkr:\n"
        "  host: 127.0.0.1\n"
        "  port: 7496\n"
        "  client_id: 1\n"
        "  timeout_sec: 1\n"
        "  readonly: true\n",
        encoding="utf-8",
    )


def test_unapproved_path_denies_without_connection(tmp_path: Path) -> None:
    rows = generate_ibkr_connect_only_dryrun_execute(
        operator_approved=False,
        output_csv=tmp_path / "operator_ibkr_connect_only_dryrun_execute.csv",
        output_report=tmp_path / "reports/operator_ibkr_connect_only_dryrun_execute_report.md",
        generated_at="2026-05-26T00:00:00+00:00",
    )
    csv_rows = _read_rows(tmp_path / "operator_ibkr_connect_only_dryrun_execute.csv")
    assert rows == csv_rows
    assert set(csv_rows[0]) == set(CSV_FIELDS)
    row = csv_rows[0]
    assert row["status"] == "DENIED"
    assert row["operator_approved"] == "NO"
    assert row["connection_attempted"] == "NO"
    assert row["connected"] == "NO"
    assert row["disconnected"] == "NOT_REQUIRED"
    assert row["error_type"] == "OPERATOR_APPROVAL_REQUIRED"
    assert row["external_effect"] == "NONE"

    report = (tmp_path / "reports/operator_ibkr_connect_only_dryrun_execute_report.md").read_text(
        encoding="utf-8"
    )
    assert "# Phase 537-540 IBKR Connect-Only Dry-Run Execute" in report
    assert "## Final Result" in report
    assert "## Scope Boundary" in report
    assert "## Explicitly Prohibited Actions" in report
    assert "## Operator Approval" in report
    assert "## Connection Attempt Summary" in report
    assert "## Disconnect Summary" in report
    assert "## Error Taxonomy" in report
    assert "## Artifact Summary" in report
    assert "## Residual Risks" in report
    assert "## Next Phase Preconditions" in report
    assert "production_ready=YES" not in report
    assert "market_data_verified=YES" not in report


def test_approved_path_uses_injected_connect_only_function(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)
    calls: list[dict[str, object]] = []

    def fake_connect(config: dict[str, object]) -> tuple[bool, bool, Optional[str], str]:
        calls.append(config)
        return True, True, None, ""

    rows = generate_ibkr_connect_only_dryrun_execute(
        operator_approved=True,
        config_path=config_path,
        output_csv=tmp_path / "operator_ibkr_connect_only_dryrun_execute.csv",
        output_report=tmp_path / "reports/operator_ibkr_connect_only_dryrun_execute_report.md",
        generated_at="2026-05-26T00:00:00+00:00",
        connect_func=fake_connect,
    )
    assert len(calls) == 1
    row = rows[0]
    assert row["status"] == "CONNECTED_THEN_DISCONNECTED"
    assert row["operator_approved"] == "YES"
    assert row["connection_attempted"] == "YES"
    assert row["connected"] == "YES"
    assert row["disconnected"] == "YES"
    assert row["market_data_requested"] == "NO"
    assert row["account_read_attempted"] == "NO"
    assert row["positions_read_attempted"] == "NO"
    assert row["historical_data_requested"] == "NO"
    assert row["contract_qualification_attempted"] == "NO"
    assert row["orders_submitted"] == "NO"
    assert row["telegram_real_send_attempted"] == "NO"
    assert row["host_redacted"] == "PRESENT_REDACTED"
    assert row["port_present"] == "YES"
    assert row["client_id_present"] == "YES"
    assert row["error_type"] == ""


def test_approved_path_classifies_failed_connect(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    def fake_connect(_: dict[str, object]) -> tuple[bool, bool, Optional[str], str]:
        return False, False, "PORT_REFUSED", "connection refused on local socket"

    rows = build_ibkr_connect_only_dryrun_execute_rows(
        operator_approved=True,
        config_path=config_path,
        generated_at="2026-05-26T00:00:00+00:00",
        connect_func=fake_connect,
    )
    row = rows[0]
    assert row["status"] == "FAILED"
    assert row["connection_attempted"] == "YES"
    assert row["connected"] == "NO"
    assert row["disconnected"] == "NOT_REQUIRED"
    assert row["error_type"] == "PORT_REFUSED"


def test_error_taxonomy() -> None:
    assert classify_error("No module named ib_insync") == "IB_INSYNC_MISSING"
    assert classify_error("ConnectionRefusedError connect call failed") == "PORT_REFUSED"
    assert classify_error("API is disabled in TWS") == "API_DISABLED"
    assert classify_error("clientId already in use") == "CLIENT_ID_CONFLICT"
    assert classify_error("operation timed out") == "TIMEOUT"


def test_main_cli_denies_without_operator_approval(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--ibkr-connect-only-dryrun-execute"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 2, result.stdout
    assert "[IBKR_CONNECT_ONLY_DRYRUN_EXECUTE] generated" in result.stdout
    assert "operator_approved=NO" in result.stdout
    assert "connection_attempted=NO" in result.stdout
    assert "DENIED / OPERATOR_APPROVAL_REQUIRED" in result.stdout
    assert "market_data_requested=NO" in result.stdout
    assert "account_read_attempted=NO" in result.stdout
    assert "positions_read_attempted=NO" in result.stdout
    assert "historical_data_requested=NO" in result.stdout
    assert "contract_qualification_attempted=NO" in result.stdout
    assert "orders_submitted=NO" in result.stdout
    assert "telegram_real_send_attempted=NO" in result.stdout
    assert "production_ready=YES" not in result.stdout
    assert "market_data_verified=YES" not in result.stdout
    assert (tmp_path / "operator_ibkr_connect_only_dryrun_execute.csv").exists()
    assert (tmp_path / "reports/operator_ibkr_connect_only_dryrun_execute_report.md").exists()
