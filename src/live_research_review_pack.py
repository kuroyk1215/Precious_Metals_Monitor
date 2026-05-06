from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv


@dataclass
class LiveResearchReviewPackRow:
    target_id: str
    target_type: str
    market: str
    data_role: str
    research_value: str
    currency: str
    data_status: str
    source_quality: str
    quality_status: str
    usable_for_research: str
    research_pack_status: str
    api_request_allowed: str
    action_allowed: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


def _now_pair(tz_cfg: dict[str, str]) -> tuple[str, str]:
    now_utc = datetime.now(timezone.utc)
    return (
        now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat(),
        now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat(),
    )


def _flags(*values: str) -> str:
    flags: set[str] = {
        "phase10e_live_research_review_pack",
        "research_pack_bridge_only",
        "no_api_request",
        "no_ibkr_connection",
        "no_reqMktData",
        "no_reqHistoricalData",
        "no_order",
        "no_auto_trade",
    }
    for value in values:
        if value and value != "none":
            flags.update(flag.strip() for flag in value.split(";") if flag.strip())
    return ";".join(sorted(flags))


def _pack_status(row: dict[str, str]) -> str:
    if row.get("usable_for_research") == "true" and row.get("quality_status") == "pass_mock_quality_gate":
        return "included_for_research"
    if row.get("quality_status", "").startswith("fail"):
        return "excluded_quality_gate_failed"
    return "manual_review_required"


def build_live_research_review_pack_rows(
    quality_rows: list[Any],
    tz_cfg: dict[str, str],
) -> list[LiveResearchReviewPackRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    output: list[LiveResearchReviewPackRow] = []

    for item in quality_rows:
        row = item if isinstance(item, dict) else item.__dict__
        pack_status = _pack_status(row)

        output.append(
            LiveResearchReviewPackRow(
                target_id=str(row.get("target_id", "unknown")),
                target_type=str(row.get("target_type", "unknown")),
                market=str(row.get("market", "UNKNOWN")),
                data_role=str(row.get("data_role", "unknown")),
                research_value=str(row.get("input_value", "unavailable")),
                currency=str(row.get("currency", "unavailable")),
                data_status=str(row.get("data_status", "unavailable")),
                source_quality=str(row.get("source_quality", "unavailable")),
                quality_status=str(row.get("quality_status", "unknown")),
                usable_for_research=str(row.get("usable_for_research", "false")),
                research_pack_status=pack_status,
                api_request_allowed="false",
                action_allowed="false",
                warning_flags=_flags(pack_status, str(row.get("warning_flags", "none"))),
                notes="live/mock research review pack bridge output only; no real API request was made",
                timestamp_jst=str(row.get("timestamp_jst", ts_jst) or ts_jst),
                timestamp_et=str(row.get("timestamp_et", ts_et) or ts_et),
            )
        )

    return output


def write_live_research_review_pack_csv(path: Path, rows: list[LiveResearchReviewPackRow]) -> None:
    fields = list(LiveResearchReviewPackRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_live_research_review_pack_report(
    path: Path,
    rows: list[LiveResearchReviewPackRow],
    input_source: str,
) -> None:
    statuses = sorted({row.research_pack_status for row in rows})
    included_count = sum(1 for row in rows if row.research_pack_status == "included_for_research")
    excluded_count = sum(1 for row in rows if row.research_pack_status.startswith("excluded"))

    lines = [
        "# Phase 10E Live Research Review Pack Report",
        "",
        "- phase: Phase 10E",
        "- scope: live/mock data to research review pack bridge",
        "- input_source: " + input_source,
        "- row_count: " + str(len(rows)),
        "- included_for_research_count: " + str(included_count),
        "- excluded_count: " + str(excluded_count),
        "- research_pack_statuses: " + (",".join(statuses) if statuses else "none"),
        "- api_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Live Research Review Pack Rows",
        "",
        "| target_id | research_value | currency | data_status | source_quality | quality_status | research_pack_status | api_request_allowed | action_allowed |",
        "|---|---:|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.target_id} | {row.research_value} | {row.currency} | {row.data_status} | {row.source_quality} | {row.quality_status} | {row.research_pack_status} | {row.api_request_allowed} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- live/mock research review pack bridge only",
            "- api_request_allowed=false for every row",
            "- action_allowed=false for every row",
            "- no API request",
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

    path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
