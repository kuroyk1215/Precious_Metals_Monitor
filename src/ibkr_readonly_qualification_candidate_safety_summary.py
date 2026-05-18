from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv


@dataclass
class IBKRReadOnlyQualificationCandidateSafetySummaryRow:
    section_id: str
    section_name: str
    source_layer: str
    input_row_count: str
    candidate_count: str
    review_required_count: str
    excluded_count: str
    candidate_final_gate_status: str
    candidate_safety_status: str
    qualification_allowed: str
    tws_connection_allowed: str
    contract_qualification_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    api_request_allowed: str
    action_allowed: str
    blocking_summary: str
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
        "phase12d_ibkr_readonly_qualification_candidate_safety_summary",
        "candidate_safety_summary_only",
        "candidate_safety_blocked_by_default",
        "candidate_final_gate_closed",
        "operator_review_required",
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


def _count(rows: list[Any], key: str, value: str) -> int:
    return sum(1 for item in rows if _row_dict(item).get(key) == value)


def _sum_int(rows: list[Any], key: str) -> int:
    total = 0
    for item in rows:
        value = _row_dict(item).get(key, "0")
        try:
            total += int(value)
        except ValueError:
            total += 0
    return total


def _any_true(rows: list[Any], keys: list[str]) -> bool:
    for item in rows:
        row = _row_dict(item)
        for key in keys:
            if row.get(key) == "true":
                return True
    return False


def _unsafe_prefix(rows: list[Any], summary: str) -> str:
    unsafe = _any_true(
        rows,
        [
            "qualification_allowed",
            "tws_connection_allowed",
            "contract_qualification_allowed",
            "market_data_request_allowed",
            "historical_data_request_allowed",
            "api_request_allowed",
            "action_allowed",
        ],
    )
    if unsafe:
        return "unsafe_true_permission_detected;" + summary
    return summary


def _summary_row(
    section_id: str,
    section_name: str,
    source_layer: str,
    input_rows: list[Any],
    candidate_count: int,
    review_required_count: int,
    excluded_count: int,
    gate_status: str,
    blocking_summary: str,
    ts_jst: str,
    ts_et: str,
) -> IBKRReadOnlyQualificationCandidateSafetySummaryRow:
    summary = _unsafe_prefix(input_rows, blocking_summary)

    return IBKRReadOnlyQualificationCandidateSafetySummaryRow(
        section_id=section_id,
        section_name=section_name,
        source_layer=source_layer,
        input_row_count=str(len(input_rows)),
        candidate_count=str(candidate_count),
        review_required_count=str(review_required_count),
        excluded_count=str(excluded_count),
        candidate_final_gate_status=gate_status,
        candidate_safety_status="BLOCKED",
        qualification_allowed="false",
        tws_connection_allowed="false",
        contract_qualification_allowed="false",
        market_data_request_allowed="false",
        historical_data_request_allowed="false",
        api_request_allowed="false",
        action_allowed="false",
        blocking_summary=summary,
        warning_flags=_flags("BLOCKED", gate_status, summary),
        notes="Candidate safety summary only; no TWS connection, no IBKR API request, no qualification, no market data, and no trading.",
        timestamp_jst=ts_jst,
        timestamp_et=ts_et,
    )


def build_ibkr_readonly_qualification_candidate_safety_summary_rows(
    candidate_resolver_rows: list[Any],
    candidate_review_pack_rows: list[Any],
    candidate_final_gate_rows: list[Any],
    tz_cfg: dict[str, str],
) -> list[IBKRReadOnlyQualificationCandidateSafetySummaryRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)

    resolver_candidate_count = _count(candidate_resolver_rows, "qualification_candidate", "true")
    resolver_excluded_count = _count(candidate_resolver_rows, "qualification_candidate", "false")

    review_candidate_count = _count(candidate_review_pack_rows, "qualification_candidate", "true")
    review_required_count = _count(candidate_review_pack_rows, "operator_review_required", "true")
    review_excluded_count = _count(candidate_review_pack_rows, "qualification_candidate", "false")

    gate_candidate_count = _sum_int(candidate_final_gate_rows, "candidate_count")
    gate_review_required_count = _sum_int(candidate_final_gate_rows, "review_required_count")
    gate_excluded_count = _sum_int(candidate_final_gate_rows, "excluded_count")
    gate_closed_count = _count(candidate_final_gate_rows, "candidate_final_gate_status", "CLOSED")

    rows = [
        _summary_row(
            "12A",
            "Candidate resolver safety summary",
            "Phase 12A",
            candidate_resolver_rows,
            resolver_candidate_count,
            0,
            resolver_excluded_count,
            "CLOSED",
            "candidate_resolver_identified_candidates_but_safety_remains_blocked",
            ts_jst,
            ts_et,
        ),
        _summary_row(
            "12B",
            "Candidate review pack safety summary",
            "Phase 12B",
            candidate_review_pack_rows,
            review_candidate_count,
            review_required_count,
            review_excluded_count,
            "CLOSED",
            "operator_review_required_for_all_candidate_rows",
            ts_jst,
            ts_et,
        ),
        _summary_row(
            "12C",
            "Candidate final gate safety summary",
            "Phase 12C",
            candidate_final_gate_rows,
            gate_candidate_count,
            gate_review_required_count,
            gate_excluded_count,
            "CLOSED",
            "candidate_final_gate_closed_count=" + str(gate_closed_count),
            ts_jst,
            ts_et,
        ),
    ]

    rows.append(
        IBKRReadOnlyQualificationCandidateSafetySummaryRow(
            section_id="FINAL",
            section_name="Final candidate safety summary",
            source_layer="Phase 12A-12C",
            input_row_count=str(
                len(candidate_resolver_rows)
                + len(candidate_review_pack_rows)
                + len(candidate_final_gate_rows)
            ),
            candidate_count=str(resolver_candidate_count),
            review_required_count=str(review_required_count),
            excluded_count=str(resolver_excluded_count),
            candidate_final_gate_status="CLOSED",
            candidate_safety_status="BLOCKED",
            qualification_allowed="false",
            tws_connection_allowed="false",
            contract_qualification_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            api_request_allowed="false",
            action_allowed="false",
            blocking_summary="candidate_safety_status_blocked_until_operator_review_and_explicit_future_phase_design",
            warning_flags=_flags(
                "BLOCKED",
                "CLOSED",
                "candidate_safety_status_blocked_until_operator_review_and_explicit_future_phase_design",
            ),
            notes="Final candidate safety status remains BLOCKED by design.",
            timestamp_jst=ts_jst,
            timestamp_et=ts_et,
        )
    )

    return rows


def write_ibkr_readonly_qualification_candidate_safety_summary_csv(
    path: Path,
    rows: list[IBKRReadOnlyQualificationCandidateSafetySummaryRow],
) -> None:
    fields = list(IBKRReadOnlyQualificationCandidateSafetySummaryRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_readonly_qualification_candidate_safety_summary_report(
    path: Path,
    rows: list[IBKRReadOnlyQualificationCandidateSafetySummaryRow],
    input_source: str,
) -> None:
    statuses = sorted({row.candidate_safety_status for row in rows})
    blocked_count = sum(1 for row in rows if row.candidate_safety_status == "BLOCKED")
    closed_count = sum(1 for row in rows if row.candidate_final_gate_status == "CLOSED")
    qualification_allowed_count = sum(1 for row in rows if row.qualification_allowed == "true")
    tws_allowed_count = sum(1 for row in rows if row.tws_connection_allowed == "true")
    api_allowed_count = sum(1 for row in rows if row.api_request_allowed == "true")
    action_allowed_count = sum(1 for row in rows if row.action_allowed == "true")

    final_row = next((row for row in rows if row.section_id == "FINAL"), rows[-1])

    lines = [
        "# Phase 12D IBKR Read-Only Qualification Candidate Safety Summary Report",
        "",
        "- phase: Phase 12D",
        "- scope: IBKR read-only qualification candidate safety summary",
        "- input_source: " + input_source,
        "- row_count: " + str(len(rows)),
        "- candidate_safety_status: BLOCKED",
        "- candidate_final_gate_status: CLOSED",
        "- blocked_count: " + str(blocked_count),
        "- closed_count: " + str(closed_count),
        "- final_candidate_count: " + final_row.candidate_count,
        "- final_review_required_count: " + final_row.review_required_count,
        "- final_excluded_count: " + final_row.excluded_count,
        "- qualification_allowed_count: " + str(qualification_allowed_count),
        "- tws_connection_allowed_count: " + str(tws_allowed_count),
        "- api_request_allowed_count: " + str(api_allowed_count),
        "- action_allowed_count: " + str(action_allowed_count),
        "- candidate_safety_statuses: " + (",".join(statuses) if statuses else "none"),
        "",
        "## Candidate Safety Summary Rows",
        "",
        "| section_id | source_layer | input_row_count | candidate_count | review_required_count | excluded_count | candidate_final_gate_status | candidate_safety_status | qualification_allowed | action_allowed |",
        "|---|---|---:|---:|---:|---:|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.section_id} | {row.source_layer} | {row.input_row_count} | {row.candidate_count} | {row.review_required_count} | {row.excluded_count} | {row.candidate_final_gate_status} | {row.candidate_safety_status} | {row.qualification_allowed} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Final Decision",
            "",
            "- Candidate safety status: BLOCKED",
            "- Candidate final gate status: CLOSED",
            "- Future qualification candidates remain blocked.",
            "- Operator review remains required.",
            "- Real IBKR qualification remains blocked.",
            "- TWS connection remains blocked.",
            "- Market data requests remain blocked.",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- IBKR read-only qualification candidate safety summary only",
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
