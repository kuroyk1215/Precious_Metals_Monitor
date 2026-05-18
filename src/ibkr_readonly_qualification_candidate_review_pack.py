from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv


@dataclass
class IBKRReadOnlyQualificationCandidateReviewPackRow:
    target_id: str
    symbol: str
    currency: str
    exchange: str
    sec_type: str
    mapping_status: str
    candidate_resolver_status: str
    qualification_candidate: str
    safety_overall_status: str
    review_pack_status: str
    operator_review_required: str
    review_priority: str
    review_reason: str
    qualification_allowed: str
    tws_connection_allowed: str
    contract_qualification_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    api_request_allowed: str
    action_allowed: str
    block_reason: str
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
        "phase12b_ibkr_readonly_qualification_candidate_review_pack",
        "candidate_review_pack_only",
        "operator_review_required",
        "overall_blocked_by_default",
        "no_tws_connection",
        "no_contract_qualification",
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


def _row_dict(item: Any) -> dict[str, str]:
    raw = item if isinstance(item, dict) else item.__dict__
    return {str(k): str(v) for k, v in raw.items()}


def _review_decision(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    target_id = row.get("target_id", "unknown")
    qualification_candidate = row.get("qualification_candidate", "false")
    resolver_status = row.get("candidate_resolver_status", "unknown")
    safety_status = row.get("safety_overall_status", "BLOCKED")

    if safety_status != "BLOCKED":
        return (
            "blocked_unexpected_safety_status",
            "true",
            "high",
            "unexpected_safety_summary_status",
            "safety_status_must_remain_blocked",
        )

    if qualification_candidate == "true" and resolver_status == "candidate_resolved_blocked_by_safety_summary":
        return (
            "review_required_candidate",
            "true",
            "high",
            "future_qualification_candidate_requires_operator_review",
            "candidate_review_required_before_any_real_qualification",
        )

    if resolver_status == "excluded_mapping_review_required":
        return (
            "review_required_mapping_exclusion",
            "true",
            "medium",
            "excluded_candidate_mapping_requires_manual_review",
            "mapping_review_required_before_candidate_can_be_reconsidered",
        )

    return (
        "review_required_unclassified",
        "true",
        "medium",
        "candidate_review_required_for_" + target_id,
        "unclassified_candidate_review_required",
    )


def build_ibkr_readonly_qualification_candidate_review_pack_rows(
    candidate_resolver_rows: list[Any],
    tz_cfg: dict[str, str],
) -> list[IBKRReadOnlyQualificationCandidateReviewPackRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[IBKRReadOnlyQualificationCandidateReviewPackRow] = []

    for item in candidate_resolver_rows:
        row = _row_dict(item)
        status, review_required, priority, review_reason, block_reason = _review_decision(row)

        rows.append(
            IBKRReadOnlyQualificationCandidateReviewPackRow(
                target_id=row.get("target_id", "unknown"),
                symbol=row.get("symbol", "unknown"),
                currency=row.get("currency", "unknown"),
                exchange=row.get("exchange", "unknown"),
                sec_type=row.get("sec_type", "unknown"),
                mapping_status=row.get("mapping_status", "unknown"),
                candidate_resolver_status=row.get("candidate_resolver_status", "unknown"),
                qualification_candidate=row.get("qualification_candidate", "false"),
                safety_overall_status=row.get("safety_overall_status", "BLOCKED"),
                review_pack_status=status,
                operator_review_required=review_required,
                review_priority=priority,
                review_reason=review_reason,
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                block_reason=block_reason,
                warning_flags=_flags(status, review_reason, block_reason, row.get("warning_flags", "none")),
                notes="Candidate review pack only; no TWS connection, no IBKR API request, no qualification, no market data, and no trading.",
                timestamp_jst=row.get("timestamp_jst", ts_jst) or ts_jst,
                timestamp_et=row.get("timestamp_et", ts_et) or ts_et,
            )
        )

    return rows


def load_ibkr_readonly_qualification_candidate_review_pack_rows_by_target(path: str) -> dict[str, dict[str, str]]:
    if not Path(path).exists():
        return {}

    with open(path, "r", encoding="utf-8", newline="") as f:
        return {
            str(row.get("target_id", "")): {k: str(v) if v is not None else "" for k, v in row.items()}
            for row in csv.DictReader(f)
            if row.get("target_id")
        }


def write_ibkr_readonly_qualification_candidate_review_pack_csv(
    path: Path,
    rows: list[IBKRReadOnlyQualificationCandidateReviewPackRow],
) -> None:
    fields = list(IBKRReadOnlyQualificationCandidateReviewPackRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_readonly_qualification_candidate_review_pack_report(
    path: Path,
    rows: list[IBKRReadOnlyQualificationCandidateReviewPackRow],
    input_source: str,
) -> None:
    statuses = sorted({row.review_pack_status for row in rows})
    review_required_count = sum(1 for row in rows if row.operator_review_required == "true")
    candidate_review_count = sum(1 for row in rows if row.review_pack_status == "review_required_candidate")
    mapping_review_count = sum(1 for row in rows if row.review_pack_status == "review_required_mapping_exclusion")
    high_priority_count = sum(1 for row in rows if row.review_priority == "high")
    qualification_allowed_count = sum(1 for row in rows if row.qualification_allowed == "true")
    tws_allowed_count = sum(1 for row in rows if row.tws_connection_allowed == "true")
    api_allowed_count = sum(1 for row in rows if row.api_request_allowed == "true")
    action_allowed_count = sum(1 for row in rows if row.action_allowed == "true")

    lines = [
        "# Phase 12B IBKR Read-Only Qualification Candidate Review Pack Report",
        "",
        "- phase: Phase 12B",
        "- scope: IBKR read-only qualification candidate review pack",
        "- input_source: " + input_source,
        "- row_count: " + str(len(rows)),
        "- review_required_count: " + str(review_required_count),
        "- candidate_review_count: " + str(candidate_review_count),
        "- mapping_review_count: " + str(mapping_review_count),
        "- high_priority_count: " + str(high_priority_count),
        "- qualification_allowed_count: " + str(qualification_allowed_count),
        "- tws_connection_allowed_count: " + str(tws_allowed_count),
        "- api_request_allowed_count: " + str(api_allowed_count),
        "- action_allowed_count: " + str(action_allowed_count),
        "- review_pack_statuses: " + (",".join(statuses) if statuses else "none"),
        "",
        "## Candidate Review Pack Rows",
        "",
        "| target_id | symbol | currency | exchange | sec_type | qualification_candidate | review_pack_status | review_priority | qualification_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.target_id} | {row.symbol} | {row.currency} | {row.exchange} | {row.sec_type} | {row.qualification_candidate} | {row.review_pack_status} | {row.review_priority} | {row.qualification_allowed} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Final Decision",
            "",
            "- Candidate review pack completed.",
            "- Every row still requires operator review.",
            "- Future qualification candidates remain blocked until an explicit future phase is designed.",
            "- Overall safety status remains BLOCKED.",
            "- TWS connection remains blocked.",
            "- Market data requests remain blocked.",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- IBKR read-only qualification candidate review pack only",
            "- no configuration file is modified",
            "- no TWS connection",
            "- no IBKR connection",
            "- no real contract qualification",
            "- qualification_allowed=false for every row",
            "- contract_qualification_allowed=false for every row",
            "- market_data_request_allowed=false for every row",
            "- historical_data_request_allowed=false for every row",
            "- api_request_allowed=false for every row",
            "- action_allowed=false for every row",
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
