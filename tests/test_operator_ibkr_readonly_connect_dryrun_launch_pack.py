from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_ibkr_readonly_connect_dryrun_launch_pack import (
    CSV_FIELDS,
    FINAL_DECISION,
    LAUNCH_PACK_STATUS,
    STATUS_VALUES,
    build_ibkr_readonly_connect_dryrun_launch_pack_rows,
    generate_ibkr_readonly_connect_dryrun_launch_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_launch_pack_generates_artifact_only_fail_closed_outputs(tmp_path: Path) -> None:
    rows = generate_ibkr_readonly_connect_dryrun_launch_pack(
        output_csv=tmp_path / "operator_ibkr_readonly_connect_dryrun_launch_pack.csv",
        output_report=tmp_path / "reports/operator_ibkr_readonly_connect_dryrun_launch_pack_report.md",
        generated_at="2026-05-26T00:00:00+00:00",
    )

    csv_rows = _read_rows(tmp_path / "operator_ibkr_readonly_connect_dryrun_launch_pack.csv")
    assert rows == csv_rows
    assert csv_rows
    assert set(csv_rows[0]) == set(CSV_FIELDS)
    assert all(row["external_effect"] == "NONE" for row in csv_rows)
    assert all(row["fail_closed"] == "YES" for row in csv_rows)
    assert any(row["blocks"] == "IBKR_CONNECTION" for row in csv_rows)
    assert any(row["blocks"] == "MARKET_DATA_REQUEST" for row in csv_rows)
    assert any(row["blocks"] == "SECRET_OR_ACCOUNT_ID_DISCLOSURE" for row in csv_rows)

    report = (tmp_path / "reports/operator_ibkr_readonly_connect_dryrun_launch_pack_report.md").read_text(
        encoding="utf-8"
    )
    assert f"final_decision={FINAL_DECISION}" in report
    assert f"launch_pack_status={LAUNCH_PACK_STATUS}" in report
    for field, value in STATUS_VALUES.items():
        assert f"{field}={value}" in report
    assert "connection_allowed=YES" not in report
    assert "execution_command_included=YES" not in report
    assert "real_market_data_verified=YES" not in report
    assert "production_ready=YES" not in report
    assert "IBKR_CONNECTION_PERMISSION_GATE_READY remains unchanged" in report


def test_launch_pack_no_go_is_safe_default_without_execute_path() -> None:
    rows = build_ibkr_readonly_connect_dryrun_launch_pack_rows(generated_at="2026-05-26T00:00:00+00:00")

    final_rows = [row for row in rows if row["category"] == "final_decision"]
    assert len(final_rows) == 1
    assert final_rows[0]["result"] == "NO_GO"
    assert final_rows[0]["operator_approval_required"] == "YES"
    assert STATUS_VALUES["connection_allowed"] == "NO"
    assert STATUS_VALUES["execution_command_included"] == "NO"
    assert STATUS_VALUES["external_connections_attempted"] == "NO"


def test_launch_pack_main_cli_generates_expected_outputs(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    result = subprocess.run(
        [
            "python3",
            str(REPO_ROOT / "main.py"),
            "--ibkr-readonly-connect-dryrun-launch-pack",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "final_decision=NO_GO" in result.stdout
    assert "launch_pack_status=IBKR_READONLY_CONNECT_DRYRUN_LAUNCH_PACK_READY" in result.stdout
    assert "artifact_only=YES" in result.stdout
    assert "operator_approval_required=YES" in result.stdout
    assert "connection_allowed=NO" in result.stdout
    assert "execution_command_included=NO" in result.stdout
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
    assert "execution_command_included=YES" not in result.stdout
    assert "real_market_data_verified=YES" not in result.stdout
    assert "production_ready=YES" not in result.stdout
    assert (tmp_path / "operator_ibkr_readonly_connect_dryrun_launch_pack.csv").exists()
    assert (tmp_path / "reports/operator_ibkr_readonly_connect_dryrun_launch_pack_report.md").exists()
