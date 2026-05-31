from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_us_only_mvp_archive_handoff_pack import (
    ARCHIVE_HANDOFF_STATUS,
    CSV_FIELDS,
    FINAL_MVP_STATUS,
    MARKET_DATA_CLASSIFICATION,
    MARKET_DATA_STATUS,
    NEXT_DEVELOPMENT_OPTIONS,
    NEXT_REVALIDATION_TRIGGER,
    build_us_only_mvp_archive_handoff_pack_row,
    generate_us_only_mvp_archive_handoff_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_row_builds_us_only_archive_handoff_pack() -> None:
    row = build_us_only_mvp_archive_handoff_pack_row(generated_at="2026-05-31T00:00:00+00:00")
    assert set(row) == set(CSV_FIELDS)
    assert row["phase"] == "Phase 625-632"
    assert row["archive_id"] == "US_ONLY_MVP_ARCHIVE_HANDOFF_PACK"
    assert row["status"] == ARCHIVE_HANDOFF_STATUS
    assert row["final_mvp_status"] == FINAL_MVP_STATUS
    assert row["us_only_scope"] == "YES"
    assert row["symbols"] == "GLD,SLV"
    assert row["dashboard_artifact"] == "dashboard/us_etf_dashboard_readonly.html"
    assert row["telegram_payload_preview"] == "telegram/us_etf_telegram_payload_preview.md"
    assert row["final_freeze_summary"] == "Precious_Metals_Monitor_US_Only_MVP_Final_Freeze_Summary.md"
    assert row["market_data_status"] == MARKET_DATA_STATUS
    assert row["market_data_classification"] == MARKET_DATA_CLASSIFICATION
    assert row["next_revalidation_trigger"] == NEXT_REVALIDATION_TRIGGER
    assert row["external_effect"] == "NONE_LOCAL_ARTIFACT_GENERATION_ONLY"
    assert row["recommendation"] == NEXT_DEVELOPMENT_OPTIONS


def test_generate_writes_csv_report_and_handoff_sections(tmp_path: Path) -> None:
    output_csv = tmp_path / "operator_us_only_mvp_archive_handoff_pack.csv"
    output_report = tmp_path / "reports/operator_us_only_mvp_archive_handoff_pack_report.md"
    output_handoff = tmp_path / "Precious_Metals_Monitor_US_Only_MVP_Archive_Handoff_Pack.md"
    row = generate_us_only_mvp_archive_handoff_pack(
        output_csv=output_csv,
        output_report=output_report,
        output_handoff=output_handoff,
        generated_at="2026-05-31T00:00:00+00:00",
    )
    assert _read_rows(output_csv) == [row]
    handoff = output_handoff.read_text(encoding="utf-8")
    for section in (
        "# Precious Metals Monitor US-only MVP Archive Handoff Pack",
        "## Final MVP Status",
        "## Current Scope",
        "## Completed Components",
        "## Current Artifact Map",
        "## Operator Runbook",
        "## Dashboard Open Instructions",
        "## Telegram Preview Instructions",
        "## Market Data Limitation",
        "## Network B Revalidation Path",
        "## JP / CN Frozen Status",
        "## Safety Boundaries",
        "## Forbidden Actions",
        "## Next Development Options",
        "## Codex Resume Context",
        "## Clean Git State Checklist",
    ):
        assert section in handoff
    report = output_report.read_text(encoding="utf-8")
    combined = report + handoff + output_csv.read_text(encoding="utf-8")
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


def test_main_cli_outputs_required_archive_handoff_lines(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--us-only-mvp-archive-handoff-pack"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0
    expected_lines = (
        "[US_ONLY_MVP_ARCHIVE_HANDOFF_PACK] generated",
        f"archive_handoff_status={ARCHIVE_HANDOFF_STATUS}",
        f"final_mvp_status={FINAL_MVP_STATUS}",
        "us_only_scope=YES",
        "symbols=GLD,SLV",
        "dashboard_artifact=dashboard/us_etf_dashboard_readonly.html",
        "telegram_payload_preview=telegram/us_etf_telegram_payload_preview.md",
        "final_freeze_summary=Precious_Metals_Monitor_US_Only_MVP_Final_Freeze_Summary.md",
        "market_data_status=BLOCKED_BY_SUBSCRIPTION",
        "market_data_classification=MARKET_DATA_BLOCKED_BY_SUBSCRIPTION",
        "ibkr_error_code=10089",
        "realtime_market_data_verified=NO",
        "production_ready=NO",
        "trading_enabled=NO",
        "account_read_enabled=NO",
        "positions_read_enabled=NO",
        "telegram_real_send_enabled=NO",
        "jp_status=FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION",
        "cn_status=FROZEN_PENDING_DATA_SOURCE_DECISION",
        f"next_revalidation_trigger={NEXT_REVALIDATION_TRIGGER}",
        f"next_development_options={NEXT_DEVELOPMENT_OPTIONS}",
    )
    for line in expected_lines:
        assert line in result.stdout
    for marker in (
        "market_data_verified=YES",
        "realtime_market_data_verified=YES",
        "trading_enabled=YES",
        "production_ready=YES",
        "auto_trading_enabled=YES",
        "account_read_enabled=YES",
        "positions_read_enabled=YES",
        "telegram_real_send_enabled=YES",
    ):
        assert marker not in result.stdout
