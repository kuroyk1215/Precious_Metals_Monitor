from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
from typing import Dict, Iterable, List, Tuple


READY_INTEGRATION_STATUSES = {
    "READY_REFERENCE_ONLY",
    "READY_DELAYED_REFERENCE_ONLY",
    "READY_DELAYED_FROZEN_REFERENCE_ONLY",
}


@dataclass(frozen=True)
class IBKRDailyIntegrationReviewRow:
    display_symbol: str
    review_status: str
    integration_status: str
    data_quality_tier: str
    research_usage: str
    usable_reference_price: str
    usable_reference_price_field: str
    action_allowed: str
    manual_review_required: str
    safety_flags: str
    decision_label: str
    decision_reason: str
    next_step: str
    source_integration_status: str
    source_data_delay_flag: str
    source_snapshot_status: str
    source_reject_reason: str


def _clean(value: object) -> str:
    return str(value or "").strip()


def _norm(value: object) -> str:
    return _clean(value).upper()


def _next_step(data_quality_tier: str, review_status: str, decision_label: str) -> str:
    if review_status == "SAFETY_REJECTED":
        return "manual_safety_review"
    if decision_label == "NO_GO":
        return "wait_for_daily_integration_preflight"
    if decision_label == "NO_PRICE":
        return "refresh_snapshot_or_manual_price_review"
    if decision_label == "UNSUPPORTED":
        return "manual_external_reference_review"
    if data_quality_tier == "tier_2_delayed":
        return "manual_review_delayed_reference"
    if data_quality_tier == "tier_3_delayed_frozen":
        return "manual_review_stale_reference"
    if review_status == "REVIEW_READY":
        return "manual_review_reference"
    return "manual_review_required"


def _decision_for_row(row: Dict[str, str]) -> Tuple[str, str, str]:
    integration_status = _norm(row.get("integration_status"))
    action_allowed = _clean(row.get("action_allowed")).lower()

    if action_allowed != "false":
        return "SAFETY_REJECTED", "NO_ACTION", "source action_allowed was not false"
    if integration_status in READY_INTEGRATION_STATUSES:
        return "REVIEW_READY", "REFERENCE_ONLY", "reference-only input is ready for manual review"
    if integration_status == "EMPTY_PRICE":
        return "REVIEW_BLOCKED", "NO_PRICE", "no usable reference price"
    if integration_status == "UNSUPPORTED":
        return "REVIEW_BLOCKED", "UNSUPPORTED", "instrument or market data is unsupported"
    if integration_status in {"MISSING_INPUT", "NO_GO"}:
        return "REVIEW_BLOCKED", "NO_GO", "daily integration input is unavailable or no-go"
    if integration_status == "SAFETY_REJECTED":
        return "SAFETY_REJECTED", "NO_ACTION", "source daily integration row was safety rejected"
    return "REVIEW_BLOCKED", "NO_GO", "unclassified daily integration status"


def build_review_row(row: Dict[str, str]) -> IBKRDailyIntegrationReviewRow:
    review_status, decision_label, decision_reason = _decision_for_row(row)
    data_quality_tier = _clean(row.get("data_quality_tier")) or "tier_9_unavailable"
    safety_flags = _clean(row.get("safety_flags"))
    if review_status == "SAFETY_REJECTED":
        safety_flags = ",".join(flag for flag in (safety_flags, "review_pack_safety_rejected") if flag)

    return IBKRDailyIntegrationReviewRow(
        display_symbol=_clean(row.get("display_symbol")),
        review_status=review_status,
        integration_status=_clean(row.get("integration_status")) or "NO_GO",
        data_quality_tier=data_quality_tier,
        research_usage=_clean(row.get("research_usage")) or "unavailable",
        usable_reference_price=_clean(row.get("usable_reference_price")),
        usable_reference_price_field=_clean(row.get("usable_reference_price_field")) or "unavailable",
        action_allowed="false",
        manual_review_required="true",
        safety_flags=safety_flags,
        decision_label=decision_label,
        decision_reason=decision_reason,
        next_step=_next_step(data_quality_tier, review_status, decision_label),
        source_integration_status=_clean(row.get("integration_status")) or "NO_GO",
        source_data_delay_flag=_clean(row.get("data_delay_flag")) or "unavailable",
        source_snapshot_status=_clean(row.get("input_snapshot_status")) or _clean(row.get("source_snapshot_status")),
        source_reject_reason=_clean(row.get("reject_reason")) or _clean(row.get("source_reject_reason")),
    )


def build_review_rows(rows: Iterable[Dict[str, str]]) -> List[IBKRDailyIntegrationReviewRow]:
    return [build_review_row(row) for row in rows]


def missing_input_review_row(path: str) -> IBKRDailyIntegrationReviewRow:
    return build_review_row(
        {
            "display_symbol": "",
            "integration_status": "MISSING_INPUT",
            "data_quality_tier": "tier_9_unavailable",
            "research_usage": "unavailable",
            "usable_reference_price": "",
            "usable_reference_price_field": "unavailable",
            "action_allowed": "false",
            "manual_review_required": "true",
            "safety_flags": "missing_input",
            "data_delay_flag": "unavailable",
            "input_snapshot_status": "missing_daily_integration",
            "reject_reason": f"daily_integration_missing:{path}",
        }
    )


def read_daily_integration_rows(path: Path) -> Tuple[str, List[Dict[str, str]]]:
    if not path.exists():
        return "missing", []
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return "empty_file", []
    return "present", rows


def write_review_pack_csv(path: Path, rows: List[IBKRDailyIntegrationReviewRow]) -> None:
    fields = list(IBKRDailyIntegrationReviewRow.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def summarize_data_quality_tiers(rows: Iterable[IBKRDailyIntegrationReviewRow]) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    for row in rows:
        summary[row.data_quality_tier] = summary.get(row.data_quality_tier, 0) + 1
    return summary


def write_review_pack_report(
    path: Path,
    rows: List[IBKRDailyIntegrationReviewRow],
    input_path: str,
    input_status: str,
) -> None:
    tier_summary = summarize_data_quality_tiers(rows)
    review_status_summary: Dict[str, int] = {}
    for row in rows:
        review_status_summary[row.review_status] = review_status_summary.get(row.review_status, 0) + 1

    tier_lines = "\n".join(f"| {tier} | {count} |" for tier, count in sorted(tier_summary.items()))
    status_lines = "\n".join(f"| {status} | {count} |" for status, count in sorted(review_status_summary.items()))
    row_lines = "\n".join(
        f"| {row.display_symbol} | {row.review_status} | {row.decision_label} | {row.integration_status} | {row.data_quality_tier} | {row.research_usage} | {row.usable_reference_price} | {row.next_step} | {row.action_allowed} |"
        for row in rows
    )

    path.write_text(
        "\n".join(
            [
                "# IBKR Daily Integration Review Pack Bridge",
                "",
                "## Review Pack Decision",
                "",
                "| field | value |",
                "|---|---|",
                "| review_pack_status | NO_GO |",
                "| action_allowed | false |",
                "| manual_review_required | true |",
                "",
                "## Input Daily Integration Status",
                "",
                "| field | value |",
                "|---|---|",
                f"| daily_integration_input | {input_path} |",
                f"| daily_integration_input_status | {input_status} |",
                f"| row_count | {len(rows)} |",
                "",
                "## Symbol Review Rows",
                "",
                "| display_symbol | review_status | decision_label | integration_status | data_quality_tier | research_usage | usable_reference_price | next_step | action_allowed |",
                "|---|---|---|---|---|---|---:|---|---|",
                row_lines,
                "",
                "## Data Quality Tier Summary",
                "",
                "| data_quality_tier | count |",
                "|---|---:|",
                tier_lines,
                "",
                "| review_status | count |",
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
                "## Next Phase Handoff",
                "",
                "Phase 289-304 may connect this bridge output to the final research review pack. The handoff must remain research-only and must not create trading advice or broker execution.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
