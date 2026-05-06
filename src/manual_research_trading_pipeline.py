from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import csv


@dataclass
class ManualResearchTradingPipelineStepRow:
    step_no: int
    phase: str
    step_name: str
    status: str
    output_csv: str
    report: str
    row_count: int
    action_allowed: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


def _now_pair(tz_cfg: dict[str, str]) -> tuple[str, str]:
    now_utc = datetime.now(timezone.utc)
    return (
        now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat(),
        now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat(),
    )


def build_manual_research_trading_pipeline_step_row(
    step_no: int,
    phase: str,
    step_name: str,
    status: str,
    output_csv: str,
    report: str,
    row_count: int,
    tz_cfg: dict[str, str],
    notes: str = "none",
) -> ManualResearchTradingPipelineStepRow:
    ts_jst, ts_et = _now_pair(tz_cfg)
    return ManualResearchTradingPipelineStepRow(
        step_no=step_no,
        phase=phase,
        step_name=step_name,
        status=status or "unknown",
        output_csv=output_csv,
        report=report,
        row_count=row_count,
        action_allowed="false",
        notes=notes or "none",
        timestamp_jst=ts_jst,
        timestamp_et=ts_et,
    )


def summarize_step_status(values: list[str]) -> str:
    cleaned = sorted({v for v in values if v})
    if not cleaned:
        return "none"
    if cleaned == ["ok"]:
        return "ok"
    if cleaned == ["neutral_range_trade_reference"]:
        return "neutral_range_trade_reference"
    if len(cleaned) == 1:
        return cleaned[0]
    return ",".join(cleaned)


def write_manual_research_trading_pipeline_summary_csv(
    path: Path,
    rows: list[ManualResearchTradingPipelineStepRow],
) -> None:
    fields = list(ManualResearchTradingPipelineStepRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_manual_research_trading_pipeline_report(
    path: Path,
    rows: list[ManualResearchTradingPipelineStepRow],
    input_csv: str,
) -> None:
    statuses = sorted({r.status for r in rows})
    lines = [
        "# Phase 8C Manual Research Trading Pipeline Report",
        "",
        "- phase: Phase 8C",
        "- scope: one-command manual research trading pipeline",
        f"- input_csv: {input_csv}",
        f"- step_count: {len(rows)}",
        "- statuses: " + (",".join(statuses) if statuses else "none"),
        "- action_allowed: false",
        "",
        "## Pipeline Steps",
        "",
        "| step_no | phase | step_name | status | row_count | output_csv | report | action_allowed |",
        "|---:|---|---|---|---:|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r.step_no} | {r.phase} | {r.step_name} | {r.status} | {r.row_count} | {r.output_csv} | {r.report} | {r.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- manual research pipeline only",
            "- action_allowed=false for every step",
            "- no IBKR connection",
            "- no reqMktData",
            "- no reqHistoricalData",
            "- no order",
            "- no cancel",
            "- no rebalance",
            "- no auto trade",
            "- no automatic execution",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
