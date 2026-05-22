from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class IBKRFinalResearchReviewRow:
    display_symbol: str
    final_review_status: str
    source_review_status: str
    source_decision_label: str
    source_data_quality_tier: str
    source_research_usage: str
    usable_reference_price: str
    usable_reference_price_field: str
    final_decision_label: str
    final_decision_reason: str
    final_research_bucket: str
    operator_action_required: str
    manual_review_required: str
    action_allowed: str
    broker_execution_triggered: str
    historical_data_request_triggered: str
    account_read_triggered: str
    position_read_triggered: str
    safety_flags: str
    next_step: str


def _clean(value: object) -> str:
    return str(value or "").strip()


def _upper(value: object) -> str:
    return _clean(value).upper()


def _bucket_for_row(source_decision_label: str, source_data_quality_tier: str) -> str:
    if source_decision_label == "NO_PRICE":
        return "no_price"
    if source_decision_label == "UNSUPPORTED":
        return "unsupported"
    if source_decision_label == "NO_GO":
        return "no_go"
    if source_data_quality_tier == "tier_2_delayed":
        return "delayed_reference"
    if source_data_quality_tier == "tier_3_delayed_frozen":
        return "stale_reference"
    if source_decision_label == "REFERENCE_ONLY":
        return "reference_only"
    return "no_go"


def _next_step(final_research_bucket: str, final_review_status: str) -> str:
    if final_review_status == "SAFETY_REJECTED":
        return "operator_safety_review"
    if final_research_bucket == "delayed_reference":
        return "operator_manual_review_delayed_reference"
    if final_research_bucket == "stale_reference":
        return "operator_manual_review_stale_reference"
    if final_research_bucket == "no_price":
        return "operator_refresh_snapshot_or_manual_price_review"
    if final_research_bucket == "unsupported":
        return "operator_external_reference_review"
    if final_research_bucket == "no_go":
        return "operator_wait_for_valid_review_pack"
    return "operator_manual_final_research_review"


def _decision_for_row(row: Dict[str, str]) -> Tuple[str, str, str]:
    action_allowed = _clean(row.get("action_allowed")).lower()
    source_review_status = _upper(row.get("review_status"))
    source_decision_label = _upper(row.get("decision_label"))

    if action_allowed != "false":
        return "SAFETY_REJECTED", "NO_ACTION", "source action_allowed was not false"
    if source_review_status == "REVIEW_READY" and source_decision_label == "REFERENCE_ONLY":
        return "FINAL_REVIEW_READY", "REFERENCE_ONLY_REVIEW", "reference-only row is ready for final manual research review"
    if source_review_status == "REVIEW_BLOCKED":
        return "FINAL_REVIEW_BLOCKED", "BLOCKED", "source review pack row is blocked"
    if source_review_status == "SAFETY_REJECTED":
        return "SAFETY_REJECTED", "NO_ACTION", "source review pack row was safety rejected"
    return "FINAL_REVIEW_BLOCKED", "BLOCKED", "unclassified review pack status"


def build_final_review_row(row: Dict[str, str]) -> IBKRFinalResearchReviewRow:
    final_review_status, final_decision_label, final_decision_reason = _decision_for_row(row)
    source_decision_label = _upper(row.get("decision_label")) or "NO_GO"
    source_data_quality_tier = _clean(row.get("data_quality_tier")) or "tier_9_unavailable"
    final_research_bucket = _bucket_for_row(source_decision_label, source_data_quality_tier)
    safety_flags = _clean(row.get("safety_flags"))
    if final_review_status == "SAFETY_REJECTED":
        safety_flags = ",".join(flag for flag in (safety_flags, "final_review_safety_rejected") if flag)

    return IBKRFinalResearchReviewRow(
        display_symbol=_clean(row.get("display_symbol")),
        final_review_status=final_review_status,
        source_review_status=_clean(row.get("review_status")) or "REVIEW_BLOCKED",
        source_decision_label=source_decision_label,
        source_data_quality_tier=source_data_quality_tier,
        source_research_usage=_clean(row.get("research_usage")) or "unavailable",
        usable_reference_price=_clean(row.get("usable_reference_price")),
        usable_reference_price_field=_clean(row.get("usable_reference_price_field")) or "unavailable",
        final_decision_label=final_decision_label,
        final_decision_reason=final_decision_reason,
        final_research_bucket=final_research_bucket,
        operator_action_required="true",
        manual_review_required="true",
        action_allowed="false",
        broker_execution_triggered="false",
        historical_data_request_triggered="false",
        account_read_triggered="false",
        position_read_triggered="false",
        safety_flags=safety_flags,
        next_step=_next_step(final_research_bucket, final_review_status),
    )


def build_final_review_rows(rows: Iterable[Dict[str, str]]) -> List[IBKRFinalResearchReviewRow]:
    return [build_final_review_row(row) for row in rows]


def missing_input_final_review_row(path: str) -> IBKRFinalResearchReviewRow:
    return build_final_review_row(
        {
            "display_symbol": "",
            "review_status": "REVIEW_BLOCKED",
            "decision_label": "NO_GO",
            "data_quality_tier": "tier_9_unavailable",
            "research_usage": "unavailable",
            "usable_reference_price": "",
            "usable_reference_price_field": "unavailable",
            "action_allowed": "false",
            "manual_review_required": "true",
            "safety_flags": f"missing_input,review_pack_missing:{path}",
        }
    )


def read_review_pack_rows(path: Path) -> Tuple[str, List[Dict[str, str]]]:
    if not path.exists():
        return "missing", []
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return "empty_file", []
    return "present", rows


def write_final_review_csv(path: Path, rows: List[IBKRFinalResearchReviewRow]) -> None:
    fields = list(IBKRFinalResearchReviewRow.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def summarize_research_buckets(rows: Iterable[IBKRFinalResearchReviewRow]) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    for row in rows:
        summary[row.final_research_bucket] = summary.get(row.final_research_bucket, 0) + 1
    return summary


def write_final_review_report(
    path: Path,
    rows: List[IBKRFinalResearchReviewRow],
    input_path: str,
    input_status: str,
) -> None:
    bucket_summary = summarize_research_buckets(rows)
    status_summary: Dict[str, int] = {}
    for row in rows:
        status_summary[row.final_review_status] = status_summary.get(row.final_review_status, 0) + 1

    bucket_lines = "\n".join(f"| {bucket} | {count} |" for bucket, count in sorted(bucket_summary.items()))
    status_lines = "\n".join(f"| {status} | {count} |" for status, count in sorted(status_summary.items()))
    row_lines = "\n".join(
        f"| {row.display_symbol} | {row.final_review_status} | {row.final_decision_label} | {row.final_research_bucket} | {row.source_review_status} | {row.source_decision_label} | {row.source_data_quality_tier} | {row.usable_reference_price} | {row.next_step} | {row.action_allowed} |"
        for row in rows
    )

    path.write_text(
        "\n".join(
            [
                "# IBKR Final Research Review Pack Bridge",
                "",
                "## Final Research Review Decision",
                "",
                "| field | value |",
                "|---|---|",
                "| final_research_review_status | NO_GO |",
                "| action_allowed | false |",
                "| manual_review_required | true |",
                "",
                "## Input Review Pack Status",
                "",
                "| field | value |",
                "|---|---|",
                f"| review_pack_input | {input_path} |",
                f"| review_pack_input_status | {input_status} |",
                f"| row_count | {len(rows)} |",
                "",
                "## Symbol Final Review Rows",
                "",
                "| display_symbol | final_review_status | final_decision_label | final_research_bucket | source_review_status | source_decision_label | source_data_quality_tier | usable_reference_price | next_step | action_allowed |",
                "|---|---|---|---|---|---|---|---:|---|---|",
                row_lines,
                "",
                "## Research Bucket Summary",
                "",
                "| final_research_bucket | count |",
                "|---|---:|",
                bucket_lines,
                "",
                "| final_review_status | count |",
                "|---|---:|",
                status_lines,
                "",
                "## Safety Confirmation",
                "",
                "- action_allowed=false",
                "- broker_execution_triggered=false",
                "- historical_data_request_triggered=false",
                "- account_read_triggered=false",
                "- position_read_triggered=false",
                "- manual_review_required=true",
                "",
                "## Operator Handoff",
                "",
                "Operators may use this file for manual research review only. No row authorizes trading, broker execution, historical data requests, account reads, or position reads.",
                "",
                "## Next Phase Handoff",
                "",
                "Phase 305-320 may build a one-command daily run and operator packet around this bridge. That future work must preserve action_allowed=false unless explicitly redesigned and authorized.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
