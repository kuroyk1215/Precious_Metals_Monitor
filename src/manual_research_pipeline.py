from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import csv


@dataclass
class PipelineStepRow:
    step_order: int
    phase: str
    step_name: str
    status: str
    output_csv: str
    output_report: str
    row_count: int
    safety_scope: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


def now_pair(tz_cfg: dict[str, str]) -> tuple[str, str]:
    now_utc = datetime.now(timezone.utc)
    return (
        now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat(),
        now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat(),
    )


def build_pipeline_step_row(
    step_order: int,
    phase: str,
    step_name: str,
    status: str,
    output_csv: str,
    output_report: str,
    row_count: int,
    tz_cfg: dict[str, str],
    notes: str = "none",
) -> PipelineStepRow:
    ts_jst, ts_et = now_pair(tz_cfg)
    return PipelineStepRow(
        step_order=step_order,
        phase=phase,
        step_name=step_name,
        status=status,
        output_csv=output_csv,
        output_report=output_report,
        row_count=row_count,
        safety_scope="manual_research_only; action_allowed=false; no_ibkr_connection; no_market_data_request; no_execution",
        notes=notes,
        timestamp_jst=ts_jst,
        timestamp_et=ts_et,
    )


def write_pipeline_summary_csv(path: Path, rows: list[PipelineStepRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "step_order",
                "phase",
                "step_name",
                "status",
                "output_csv",
                "output_report",
                "row_count",
                "safety_scope",
                "notes",
                "timestamp_jst",
                "timestamp_et",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.step_order,
                    r.phase,
                    r.step_name,
                    r.status,
                    r.output_csv,
                    r.output_report,
                    r.row_count,
                    r.safety_scope,
                    r.notes,
                    r.timestamp_jst,
                    r.timestamp_et,
                ]
            )


def write_pipeline_summary_report(path: Path, rows: list[PipelineStepRow]) -> None:
    overall_status = "ok" if rows and all(r.status in {"ok", "partial", "manual_mock_only"} for r in rows) else "check_required"

    lines = [
        "# End-to-End Manual Research Pipeline Report",
        "",
        f"- overall_status: {overall_status}",
        "- scope: explicit manual research run only",
        "- action_allowed: false",
        "",
        "## Pipeline Steps",
        "",
        "| step_order | phase | step_name | status | row_count | output_csv | output_report |",
        "|---:|---|---|---|---:|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r.step_order} | {r.phase} | {r.step_name} | {r.status} | {r.row_count} | {r.output_csv} | {r.output_report} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- explicit manual trigger only",
            "- action_allowed=false",
            "- no IBKR connection",
            "- no reqMktData",
            "- no reqHistoricalData",
            "- no automatic calibration",
            "- no automatic execution",
            "- generated outputs are research artifacts, not execution instructions",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
