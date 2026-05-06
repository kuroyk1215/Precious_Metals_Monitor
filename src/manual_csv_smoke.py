from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv


@dataclass
class ManualCsvSmokeStepRow:
    step_order: int
    step_name: str
    status: str
    output_csv: str
    output_report: str
    row_count: int
    safety_scope: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


def _now_pair(tz_cfg: dict[str, str]) -> tuple[str, str]:
    now_utc = datetime.now(timezone.utc)
    return (
        now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat(),
        now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat(),
    )


def summarize_guard_status(rows: list[Any]) -> str:
    return "ok" if len(rows) == 0 else "generated_outputs_detected"


def summarize_validation_status(rows: list[Any]) -> str:
    if not rows:
        return "fail"
    statuses = {str(getattr(row, "status", "")) for row in rows}
    return "pass" if statuses == {"pass"} else "fail"


def summarize_review_pack_status(rows: list[Any]) -> str:
    if not rows:
        return "check_required"
    actions = {str(getattr(row, "action_allowed", "")) for row in rows}
    return "ok" if actions == {"false"} else "check_required"


def build_manual_csv_smoke_step_row(
    step_order: int,
    step_name: str,
    status: str,
    output_csv: str,
    output_report: str,
    row_count: int,
    tz_cfg: dict[str, str],
    notes: str = "none",
) -> ManualCsvSmokeStepRow:
    ts_jst, ts_et = _now_pair(tz_cfg)
    return ManualCsvSmokeStepRow(
        step_order=step_order,
        step_name=step_name,
        status=status,
        output_csv=output_csv,
        output_report=output_report,
        row_count=row_count,
        safety_scope="manual_csv_smoke_only; report_only; action_allowed=false; no_ibkr_connection; no_reqMktData; no_reqHistoricalData; no_order; no_cancel; no_rebalance; no_auto_trade; no_automatic_execution",
        notes=notes,
        timestamp_jst=ts_jst,
        timestamp_et=ts_et,
    )


def write_manual_csv_smoke_summary_csv(path: Path, rows: list[ManualCsvSmokeStepRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "step_order",
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


def write_manual_csv_smoke_report(path: Path, rows: list[ManualCsvSmokeStepRow], input_csv: str) -> None:
    statuses = {r.status for r in rows}
    required_pass = {"pass", "ok"}
    overall_status = "pass" if rows and "fail" not in statuses and "check_required" not in statuses and statuses.intersection(required_pass) else "check_required"

    lines = [
        "# Final Manual CSV Workflow Smoke Report",
        "",
        "- phase: Phase 6I",
        "- scope: final manual CSV workflow smoke command",
        f"- input_csv: {input_csv}",
        f"- overall_status: {overall_status}",
        "- action_allowed: false",
        "",
        "## Smoke Steps",
        "",
        "| step_order | step_name | status | row_count | output_csv | output_report |",
        "|---:|---|---|---:|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r.step_order} | {r.step_name} | {r.status} | {r.row_count} | {r.output_csv} | {r.output_report} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- report only",
            "- manual CSV only",
            "- action_allowed=false",
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
