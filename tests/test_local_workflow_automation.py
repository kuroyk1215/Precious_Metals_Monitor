from __future__ import annotations

import json
from pathlib import Path

from src.local_workflow_automation import run_local_workflow


def test_local_workflow_generates_preview_artifacts(tmp_path: Path) -> None:
    workflow = run_local_workflow(
        output_workflow_snapshot=tmp_path / "dashboard/data/local_workflow_automation_snapshot.json",
        output_operator_packet_snapshot=tmp_path / "dashboard/data/operator_daily_packet_snapshot.json",
        output_data_source_snapshot=tmp_path / "dashboard/data/us_gld_slv_data_source_dry_run_snapshot.json",
        output_report_snapshot=tmp_path / "dashboard/data/research_report_framework_snapshot.json",
        output_telegram_snapshot=tmp_path / "dashboard/data/telegram_preview_snapshot.json",
        output_watchlist_snapshot=tmp_path / "dashboard/data/watchlist_policy_snapshot.json",
        output_research_report=tmp_path / "reports/local_research_report_framework_GLD_SLV.md",
        output_operator_packet_report=tmp_path / "reports/operator_daily_packet_preview.md",
        output_telegram_preview_report=tmp_path / "reports/telegram_preview_local_only.md",
        generated_at="2026-06-01T00:00:00+00:00",
    )

    assert workflow["status"] == "LOCAL_WORKFLOW_AUTOMATION_READY"
    assert json.loads((tmp_path / "dashboard/data/operator_daily_packet_snapshot.json").read_text(encoding="utf-8"))[
        "status"
    ] == "OPERATOR_DAILY_PACKET_PREVIEW_READY"
    assert json.loads((tmp_path / "dashboard/data/telegram_preview_snapshot.json").read_text(encoding="utf-8"))[
        "telegram_real_send_enabled"
    ] == "NO"
    assert (tmp_path / "reports/operator_daily_packet_preview.md").exists()
