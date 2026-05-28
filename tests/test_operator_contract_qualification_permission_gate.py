from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_contract_qualification_permission_gate import (
    CSV_FIELDS,
    GATE_STATUS,
    STATUS_VALUES,
    build_contract_qualification_permission_gate_rows,
    generate_contract_qualification_permission_gate,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_contract_qualification_gate_generates_schema_and_report(tmp_path: Path) -> None:
    rows = generate_contract_qualification_permission_gate(
        output_csv=tmp_path / "operator_contract_qualification_permission_gate.csv",
        output_report=tmp_path / "reports/operator_contract_qualification_permission_gate_report.md",
        generated_at="2026-05-28T00:00:00+00:00",
    )
    csv_rows = _read_rows(tmp_path / "operator_contract_qualification_permission_gate.csv")
    assert rows == csv_rows
    assert set(csv_rows[0]) == set(CSV_FIELDS)
    assert all(row["fail_closed"] == "YES" for row in csv_rows)
    assert all(row["operator_authorization_required"] == "YES" for row in csv_rows)
    assert all(row["contract_qualification_allowed"] == "NO" for row in csv_rows)
    assert all(row["external_effect"] == "NONE" for row in csv_rows)
    assert any(row["blocked_capability"] == "CONTRACT_QUALIFICATION_EXECUTION" for row in csv_rows)
    assert any(row["blocked_capability"] == "REAL_CONTRACT_QUALIFICATION" for row in csv_rows)

    report = (tmp_path / "reports/operator_contract_qualification_permission_gate_report.md").read_text(
        encoding="utf-8"
    )
    for section in (
        "# Phase 545-548 Contract Qualification Permission Gate",
        "## Final Decision",
        "## Scope Boundary",
        "## Explicitly Prohibited Actions",
        "## Qualification Permission Gates",
        "## Operator Authorization Requirements",
        "## Single-Symbol Preconditions",
        "## Artifact Summary",
        "## Residual Risks",
        "## Next Phase Preconditions",
    ):
        assert section in report
    assert f"qualification_permission_gate_status={GATE_STATUS}" in report
    for field, value in STATUS_VALUES.items():
        assert f"{field}={value}" in report
    assert "contract_qualification_allowed=YES" not in report
    assert "contract_qualification_verified=YES" not in report
    assert "market_data_verified=YES" not in report
    assert "production_ready=YES" not in report
    assert "trading_enabled=YES" not in report


def test_contract_qualification_gate_statuses_remain_denied() -> None:
    rows = build_contract_qualification_permission_gate_rows(
        generated_at="2026-05-28T00:00:00+00:00"
    )
    assert rows[0]["result"] == "DENIED"
    assert STATUS_VALUES["contract_qualification_permission_decision"] == "DENIED"
    assert STATUS_VALUES["operator_authorization_required"] == "YES"
    assert STATUS_VALUES["contract_qualification_allowed"] == "NO"
    assert STATUS_VALUES["external_connections_attempted"] == "NO"
    assert STATUS_VALUES["ibkr_connected"] == "NO"
    assert STATUS_VALUES["contract_qualification_attempted"] == "NO"
    assert STATUS_VALUES["next_phase_single_symbol_qualification_candidate"] == "YES"


def test_contract_qualification_gate_main_cli_generates_expected_outputs(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--contract-qualification-permission-gate"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "[CONTRACT_QUALIFICATION_PERMISSION_GATE] generated" in result.stdout
    assert "contract_qualification_permission_decision=DENIED" in result.stdout
    assert "qualification_permission_gate_status=CONTRACT_QUALIFICATION_PERMISSION_GATE_READY" in result.stdout
    assert "operator_authorization_required=YES" in result.stdout
    assert "contract_qualification_allowed=NO" in result.stdout
    assert "external_connections_attempted=NO" in result.stdout
    assert "ibkr_connected=NO" in result.stdout
    assert "market_data_requested=NO" in result.stdout
    assert "account_read_attempted=NO" in result.stdout
    assert "positions_read_attempted=NO" in result.stdout
    assert "historical_data_requested=NO" in result.stdout
    assert "contract_qualification_attempted=NO" in result.stdout
    assert "orders_submitted=NO" in result.stdout
    assert "telegram_real_send_attempted=NO" in result.stdout
    assert "next_phase_single_symbol_qualification_candidate=YES" in result.stdout
    assert "contract_qualification_allowed=YES" not in result.stdout
    assert "contract_qualification_verified=YES" not in result.stdout
    assert "market_data_verified=YES" not in result.stdout
    assert "production_ready=YES" not in result.stdout
    assert "trading_enabled=YES" not in result.stdout
    assert (tmp_path / "operator_contract_qualification_permission_gate.csv").exists()
    assert (tmp_path / "reports/operator_contract_qualification_permission_gate_report.md").exists()
