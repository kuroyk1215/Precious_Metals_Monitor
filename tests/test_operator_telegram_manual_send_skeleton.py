from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_telegram_manual_send_skeleton import (
    CSV_FIELDS,
    MARKET_DATA_CLASSIFICATION,
    MARKET_DATA_STATUS,
    TELEGRAM_GUARD_STATUS,
    TELEGRAM_PERMISSION_DECISION,
    TELEGRAM_SKELETON_STATUS,
    build_telegram_manual_send_skeleton_row,
    generate_telegram_manual_send_skeleton,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_row_keeps_manual_send_denied_and_archive_ready() -> None:
    row = build_telegram_manual_send_skeleton_row(generated_at="2026-05-31T00:00:00+00:00")
    assert set(row) == set(CSV_FIELDS)
    assert row["phase"] == "Phase 601-616"
    assert row["symbols"] == "GLD,SLV"
    assert row["market_data_status"] == MARKET_DATA_STATUS
    assert row["market_data_classification"] == MARKET_DATA_CLASSIFICATION
    assert row["telegram_permission_decision"] == TELEGRAM_PERMISSION_DECISION
    assert row["telegram_guard_status"] == TELEGRAM_GUARD_STATUS
    assert row["telegram_payload_ready"] == "YES"
    assert row["telegram_real_send_enabled"] == "NO"
    assert row["telegram_real_send_attempted"] == "NO"
    assert row["operator_approval_required"] == "YES"
    assert row["operator_approved"] == "NO"
    assert row["archive_ready"] == "YES"
    assert row["external_effect"] == "NONE_LOCAL_ARTIFACT_GENERATION_ONLY"


def test_generate_writes_csv_report_and_payload_preview(tmp_path: Path) -> None:
    output_csv = tmp_path / "operator_telegram_manual_send_skeleton.csv"
    output_report = tmp_path / "reports/operator_telegram_manual_send_skeleton_report.md"
    output_payload = tmp_path / "telegram/us_etf_telegram_payload_preview.md"
    row = generate_telegram_manual_send_skeleton(
        output_csv=output_csv,
        output_report=output_report,
        output_payload_preview=output_payload,
        generated_at="2026-05-31T00:00:00+00:00",
    )
    assert _read_rows(output_csv) == [row]
    report = output_report.read_text(encoding="utf-8")
    for section in (
        "# Phase 601-616 Telegram Manual Send Skeleton",
        "## Final Telegram Skeleton Status",
        "## Scope Boundary",
        "## Telegram Permission Gate",
        "## Manual Send Guard",
        "## Payload Preview",
        "## Archive Skeleton",
        "## Operator Approval Workflow",
        "## Explicitly Prohibited Actions",
        "## Artifact Summary",
        "## Residual Risks",
        "## Next Phase Preconditions",
    ):
        assert section in report
    payload = output_payload.read_text(encoding="utf-8")
    assert "GLD / SLV" in payload
    assert "Market data blocked by subscription / IBKR 10089" in payload
    assert "JP / CN frozen" in payload
    assert "read-only" in payload
    assert "no trading" in payload
    assert "no account reads" in payload
    assert "no positions reads" in payload
    assert "operator review required" in payload
    assert "SUBSCRIBE_NETWORK_B_OR_CONTINUE_FRAMEWORK_ONLY_MVP" in payload
    forbidden = (
        "telegram_real_send_enabled=YES",
        "telegram_real_send_attempted=YES",
        "telegram_sent=YES",
        "market_data_verified=YES",
        "realtime_market_data_verified=YES",
        "trading_enabled=YES",
        "production_ready=YES",
        "account_read_enabled=YES",
        "positions_read_enabled=YES",
    )
    combined = report + payload + output_csv.read_text(encoding="utf-8")
    for marker in forbidden:
        assert marker not in combined


def test_main_cli_outputs_required_telegram_summary(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--telegram-manual-send-skeleton"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0
    assert "[TELEGRAM_MANUAL_SEND_SKELETON] generated" in result.stdout
    assert f"telegram_skeleton_status={TELEGRAM_SKELETON_STATUS}" in result.stdout
    assert "telegram_permission_decision=DENIED" in result.stdout
    assert "telegram_guard_status=TELEGRAM_MANUAL_SEND_GUARD_READY" in result.stdout
    assert "telegram_payload_ready=YES" in result.stdout
    assert "telegram_archive_ready=YES" in result.stdout
    assert "telegram_real_send_enabled=NO" in result.stdout
    assert "telegram_real_send_attempted=NO" in result.stdout
    assert "operator_approval_required=YES" in result.stdout
    assert "operator_approved=NO" in result.stdout
    assert "symbols=GLD,SLV" in result.stdout
    assert "market_data_status=BLOCKED_BY_SUBSCRIPTION" in result.stdout
    assert "market_data_classification=MARKET_DATA_BLOCKED_BY_SUBSCRIPTION" in result.stdout
    assert "ibkr_error_code=10089" in result.stdout
    assert "dashboard_source=dashboard/us_etf_dashboard_readonly.html" in result.stdout
    assert "next_phase_final_audit_freeze_candidate=YES" in result.stdout
    assert "telegram_real_send_enabled=YES" not in result.stdout
    assert "telegram_real_send_attempted=YES" not in result.stdout
    assert "telegram_sent=YES" not in result.stdout
    assert "market_data_verified=YES" not in result.stdout
    assert "realtime_market_data_verified=YES" not in result.stdout
    assert "trading_enabled=YES" not in result.stdout
    assert "production_ready=YES" not in result.stdout
    assert "account_read_enabled=YES" not in result.stdout
    assert "positions_read_enabled=YES" not in result.stdout
