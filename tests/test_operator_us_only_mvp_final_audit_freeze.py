from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_us_only_mvp_final_audit_freeze import (
    CSV_FIELDS,
    FINAL_MVP_STATUS,
    MARKET_DATA_CLASSIFICATION,
    MARKET_DATA_STATUS,
    NEXT_REVALIDATION_TRIGGER,
    build_us_only_mvp_final_audit_freeze_row,
    generate_us_only_mvp_final_audit_freeze,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_row_freezes_us_only_readonly_mvp_state() -> None:
    row = build_us_only_mvp_final_audit_freeze_row(generated_at="2026-05-31T00:00:00+00:00")
    assert set(row) == set(CSV_FIELDS)
    assert row["phase"] == "Phase 617-624"
    assert row["status"] == FINAL_MVP_STATUS
    assert row["us_only_scope"] == "YES"
    assert row["symbols"] == "GLD,SLV"
    assert row["connectivity_verified"] == "YES"
    assert row["contract_qualification_verified"] == "YES"
    assert row["market_data_request_tested"] == "YES"
    assert row["market_data_status"] == MARKET_DATA_STATUS
    assert row["market_data_classification"] == MARKET_DATA_CLASSIFICATION
    assert row["realtime_market_data_verified"] == "NO"
    assert row["dashboard_ready"] == "YES"
    assert row["telegram_skeleton_ready"] == "YES"
    assert row["telegram_real_send_enabled"] == "NO"
    assert row["jp_status"] == "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION"
    assert row["cn_status"] == "FROZEN_PENDING_DATA_SOURCE_DECISION"
    assert row["trading_enabled"] == "NO"
    assert row["account_read_enabled"] == "NO"
    assert row["positions_read_enabled"] == "NO"
    assert row["production_ready"] == "NO"
    assert row["external_effect"] == "NONE_LOCAL_ARTIFACT_GENERATION_ONLY"
    assert row["recommendation"] == NEXT_REVALIDATION_TRIGGER


def test_generate_writes_required_artifacts_and_sections(tmp_path: Path) -> None:
    output_csv = tmp_path / "operator_us_only_mvp_final_audit_freeze.csv"
    output_report = tmp_path / "reports/operator_us_only_mvp_final_audit_freeze_report.md"
    output_summary = tmp_path / "Precious_Metals_Monitor_US_Only_MVP_Final_Freeze_Summary.md"
    row = generate_us_only_mvp_final_audit_freeze(
        output_csv=output_csv,
        output_report=output_report,
        output_summary=output_summary,
        generated_at="2026-05-31T00:00:00+00:00",
    )
    assert _read_rows(output_csv) == [row]
    report = output_report.read_text(encoding="utf-8")
    for section in (
        "# Phase 617-624 US-only MVP Final Audit Freeze",
        "## Final Decision",
        "## Scope Boundary",
        "## US-only MVP Components",
        "## GLD / SLV Status",
        "## Market Data Limitation",
        "## Dashboard Status",
        "## Telegram Skeleton Status",
        "## JP / CN Frozen Status",
        "## Explicitly Prohibited Actions",
        "## Residual Risks",
        "## Operator Handoff",
        "## Future Revalidation Path",
    ):
        assert section in report
    summary = output_summary.read_text(encoding="utf-8")
    for section in (
        "# Precious Metals Monitor US-only MVP Final Freeze Summary",
        "## Final Status",
        "## What Is Completed",
        "## What Is Not Completed",
        "## Current Market Data Limitation",
        "## Safety Boundaries",
        "## Operator Workflow",
        "## Future Upgrade Path",
        "## Next Revalidation Trigger",
    ):
        assert section in summary
    combined = report + summary + output_csv.read_text(encoding="utf-8")
    forbidden = (
        "market_data_verified=YES",
        "realtime_market_data_verified=YES",
        "trading_enabled=YES",
        "production_ready=YES",
        "auto_trading_enabled=YES",
        "account_read_enabled=YES",
        "positions_read_enabled=YES",
        "telegram_real_send_enabled=YES",
    )
    for marker in forbidden:
        assert marker not in combined


def test_main_cli_outputs_required_final_freeze_summary(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--us-only-mvp-final-audit-freeze"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0
    expected_lines = (
        "[US_ONLY_MVP_FINAL_AUDIT_FREEZE] generated",
        f"final_mvp_status={FINAL_MVP_STATUS}",
        "us_only_scope=YES",
        "symbols=GLD,SLV",
        "connectivity_verified=YES",
        "contract_qualification_verified=YES",
        "market_data_request_tested=YES",
        "market_data_status=BLOCKED_BY_SUBSCRIPTION",
        "market_data_classification=MARKET_DATA_BLOCKED_BY_SUBSCRIPTION",
        "ibkr_error_code=10089",
        "subscription_required=YES",
        "delayed_available=YES",
        "realtime_market_data_verified=NO",
        "dashboard_ready=YES",
        "telegram_skeleton_ready=YES",
        "telegram_real_send_enabled=NO",
        "jp_status=FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION",
        "cn_status=FROZEN_PENDING_DATA_SOURCE_DECISION",
        "trading_enabled=NO",
        "account_read_enabled=NO",
        "positions_read_enabled=NO",
        "production_ready=NO",
        "external_connections_attempted=NO",
        f"next_revalidation_trigger={NEXT_REVALIDATION_TRIGGER}",
    )
    for line in expected_lines:
        assert line in result.stdout
    forbidden = (
        "market_data_verified=YES",
        "realtime_market_data_verified=YES",
        "trading_enabled=YES",
        "production_ready=YES",
        "auto_trading_enabled=YES",
        "account_read_enabled=YES",
        "positions_read_enabled=YES",
        "telegram_real_send_enabled=YES",
    )
    for marker in forbidden:
        assert marker not in result.stdout
