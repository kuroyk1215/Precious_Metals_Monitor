from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

from src.local_data_source_dry_run import build_data_source_dry_run_snapshot
from src.local_operator_packet_builder import (
    build_operator_daily_packet_markdown,
    build_operator_daily_packet_snapshot,
    build_telegram_preview_markdown,
    build_telegram_preview_snapshot,
    build_watchlist_policy_snapshot,
)
from src.local_research_report_builder import (
    build_research_report_framework_snapshot,
    build_research_report_markdown,
)


PHASE = "Phase 801-1000"
PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: PathLike, payload: Dict[str, object]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: PathLike, text: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def build_local_workflow_automation_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "LOCAL_WORKFLOW_AUTOMATION_READY",
        "workflow_mode": "CLI_GENERATED_LOCAL_ARTIFACT_PREVIEW",
        "ui_trigger_mode": "VIEW_AND_COPY_COMMAND_ONLY",
        "browser_write_actions_enabled": "NO",
        "external_network_enabled": "NO",
        "market_data_request_enabled": "NO",
        "historical_data_request_enabled": "NO",
        "account_read_enabled": "NO",
        "position_read_enabled": "NO",
        "trading_enabled": "NO",
        "telegram_real_send_enabled": "NO",
        "generated_artifacts": [
            "dashboard/data/operator_daily_packet_snapshot.json",
            "dashboard/data/us_gld_slv_data_source_dry_run_snapshot.json",
            "dashboard/data/research_report_framework_snapshot.json",
            "dashboard/data/telegram_preview_snapshot.json",
            "dashboard/data/watchlist_policy_snapshot.json",
            "reports/local_research_report_framework_GLD_SLV.md",
            "reports/operator_daily_packet_preview.md",
            "reports/telegram_preview_local_only.md",
        ],
        "generated_at_utc": timestamp,
    }


def run_local_workflow(
    output_workflow_snapshot: PathLike = "dashboard/data/local_workflow_automation_snapshot.json",
    output_operator_packet_snapshot: PathLike = "dashboard/data/operator_daily_packet_snapshot.json",
    output_data_source_snapshot: PathLike = "dashboard/data/us_gld_slv_data_source_dry_run_snapshot.json",
    output_report_snapshot: PathLike = "dashboard/data/research_report_framework_snapshot.json",
    output_telegram_snapshot: PathLike = "dashboard/data/telegram_preview_snapshot.json",
    output_watchlist_snapshot: PathLike = "dashboard/data/watchlist_policy_snapshot.json",
    output_research_report: PathLike = "reports/local_research_report_framework_GLD_SLV.md",
    output_operator_packet_report: PathLike = "reports/operator_daily_packet_preview.md",
    output_telegram_preview_report: PathLike = "reports/telegram_preview_local_only.md",
    generated_at: Optional[str] = None,
) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    workflow = build_local_workflow_automation_snapshot(timestamp)
    _write_json(output_workflow_snapshot, workflow)
    _write_json(output_operator_packet_snapshot, build_operator_daily_packet_snapshot(timestamp))
    _write_json(output_data_source_snapshot, build_data_source_dry_run_snapshot(timestamp))
    _write_json(output_report_snapshot, build_research_report_framework_snapshot(timestamp))
    _write_json(output_telegram_snapshot, build_telegram_preview_snapshot(timestamp))
    _write_json(output_watchlist_snapshot, build_watchlist_policy_snapshot(timestamp))
    _write_text(output_research_report, build_research_report_markdown(timestamp))
    _write_text(output_operator_packet_report, build_operator_daily_packet_markdown(timestamp))
    _write_text(output_telegram_preview_report, build_telegram_preview_markdown(timestamp))
    return workflow


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run local read-only workflow preview artifact generation.")
    parser.parse_args(argv)
    snapshot = run_local_workflow()
    print("[LOCAL_WORKFLOW_RUN] generated")
    print(f"phase={snapshot['phase']}")
    print(f"status={snapshot['status']}")
    print("operator_packet=dashboard/data/operator_daily_packet_snapshot.json")
    print("research_report=reports/local_research_report_framework_GLD_SLV.md")
    print("telegram_preview=reports/telegram_preview_local_only.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
