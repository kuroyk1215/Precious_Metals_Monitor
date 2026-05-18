from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv


@dataclass
class IBKRReadOnlyQualificationCandidateResolverRow:
    target_id: str
    symbol: str
    currency: str
    exchange: str
    sec_type: str
    mapping_status: str
    qualification_dry_run_status: str
    future_qualification_candidate: str
    execution_guard_status: str
    safety_overall_status: str
    candidate_resolver_status: str
    qualification_candidate: str
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
        "phase12a_ibkr_readonly_qualification_candidate_resolver",
        "candidate_resolver_only",
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


def _by_target(rows: list[Any]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for item in rows:
        row = _row_dict(item)
        target_id = row.get("target_id")
        if target_id:
            out[target_id] = row
    return out


def _safety_status(safety_summary_rows: list[Any]) -> str:
    for item in safety_summary_rows:
        row = _row_dict(item)
        if row.get("section_id") == "FINAL":
            return row.get("overall_status", "BLOCKED")
    return "BLOCKED"


def _decision(mapping: dict[str, str], dry: dict[str, str], safety_status: str) -> tuple[str, str, str]:
    mapping_status = mapping.get("mapping_status", "unknown")
    future_candidate = dry.get("future_qualification_candidate", "false")
    dry_status = dry.get("qualification_dry_run_status", "unknown")

    if mapping_status != "candidate_mapping_ready":
        return (
            "excluded_mapping_review_required",
            "false",
            "mapping_not_ready_for_future_qualification",
        )

    if future_candidate != "true" or dry_status != "dry_run_ready_for_future_qualification":
        return (
            "excluded_dry_run_not_candidate",
            "false",
            "dry_run_not_future_qualification_candidate",
        )

    if safety_status != "BLOCKED":
        return (
            "blocked_unexpected_safety_status",
            "true",
            "unexpected_safety_summary_status",
        )

    return (
        "candidate_resolved_blocked_by_safety_summary",
        "true",
        "candidate_identified_but_overall_safety_summary_blocked",
    )


def build_ibkr_readonly_qualification_candidate_resolver_rows(
    mapping_rows: list[Any],
    dry_run_rows: list[Any],
    execution_guard_rows: list[Any],
    safety_summary_rows: list[Any],
    tz_cfg: dict[str, str],
) -> list[IBKRReadOnlyQualificationCandidateResolverRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    dry_by_target = _by_target(dry_run_rows)
    guard_by_target = _by_target(execution_guard_rows)
    safety_status = _safety_status(safety_summary_rows)

    rows: list[IBKRReadOnlyQualificationCandidateResolverRow] = []

    for item in mapping_rows:
        mapping = _row_dict(item)
        target_id = mapping.get("target_id", "unknown")
        dry = dry_by_target.get(target_id, {})
        guard = guard_by_target.get(target_id, {})
        resolver_status, qualification_candidate, block_reason = _decision(mapping, dry, safety_status)

        rows.append(
            IBKRReadOnlyQualificationCandidateResolverRow(
                target_id=target_id,
                symbol=mapping.get("symbol", "unknown"),
                currency=mapping.get("currency", "unknown"),
                exchange=mapping.get("exchange", "unknown"),
                sec_type=mapping.get("sec_type", "unknown"),
                mapping_status=mapping.get("mapping_status", "unknown"),
                qualification_dry_run_status=dry.get("qualification_dry_run_status", "unknown"),
                future_qualification_candidate=dry.get("future_qualification_candidate", "false"),
                execution_guard_status=guard.get("execution_guard_status", "unknown"),
                safety_overall_status=safety_status,
                candidate_resolver_status=resolver_status,
                qualification_candidate=qualification_candidate,
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                block_reason=block_reason,
                warning_flags=_flags(
                    resolver_status,
                    block_reason,
                    mapping.get("warning_flags", "none"),
                    dry.get("warning_flags", "none"),
                    guard.get("warning_flags", "none"),
                ),
                notes="Candidate resolver only; no TWS connection, no IBKR API request, no qualification, no market data, and no trading.",
                timestamp_jst=mapping.get("timestamp_jst", ts_jst) or ts_jst,
                timestamp_et=mapping.get("timestamp_et", ts_et) or ts_et,
            )
        )

    return rows


def load_ibkr_readonly_qualification_candidate_resolver_rows_by_target(path: str) -> dict[str, dict[str, str]]:
    if not Path(path).exists():
        return {}

    with open(path, "r", encoding="utf-8", newline="") as f:
        return {
            str(row.get("target_id", "")): {k: str(v) if v is not None else "" for k, v in row.items()}
            for row in csv.DictReader(f)
            if row.get("target_id")
        }


def write_ibkr_readonly_qualification_candidate_resolver_csv(
    path: Path,
    rows: list[IBKRReadOnlyQualificationCandidateResolverRow],
) -> None:
    fields = list(IBKRReadOnlyQualificationCandidateResolverRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_readonly_qualification_candidate_resolver_report(
    path: Path,
    rows: list[IBKRReadOnlyQualificationCandidateResolverRow],
    input_source: str,
) -> None:
    statuses = sorted({row.candidate_resolver_status for row in rows})
    qualification_candidate_count = sum(1 for row in rows if row.qualification_candidate == "true")
    excluded_count = sum(1 for row in rows if row.qualification_candidate == "false")
    qualification_allowed_count = sum(1 for row in rows if row.qualification_allowed == "true")
    tws_allowed_count = sum(1 for row in rows if row.tws_connection_allowed == "true")
    api_allowed_count = sum(1 for row in rows if row.api_request_allowed == "true")
    action_allowed_count = sum(1 for row in rows if row.action_allowed == "true")

    lines = [
        "# Phase 12A IBKR Read-Only Qualification Candidate Resolver Report",
        "",
        "- phase: Phase 12A",
        "- scope: IBKR read-only qualification candidate resolver",
        "- input_source: " + input_source,
        "- row_count: " + str(len(rows)),
        "- qualification_candidate_count: " + str(qualification_candidate_count),
        "- excluded_count: " + str(excluded_count),
        "- qualification_allowed_count: " + str(qualification_allowed_count),
        "- tws_connection_allowed_count: " + str(tws_allowed_count),
        "- api_request_allowed_count: " + str(api_allowed_count),
        "- action_allowed_count: " + str(action_allowed_count),
        "- candidate_resolver_statuses: " + (",".join(statuses) if statuses else "none"),
        "",
        "## Candidate Resolver Rows",
        "",
        "| target_id | symbol | currency | exchange | sec_type | mapping_status | future_qualification_candidate | safety_overall_status | candidate_resolver_status | qualification_candidate | qualification_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.target_id} | {row.symbol} | {row.currency} | {row.exchange} | {row.sec_type} | {row.mapping_status} | {row.future_qualification_candidate} | {row.safety_overall_status} | {row.candidate_resolver_status} | {row.qualification_candidate} | {row.qualification_allowed} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Final Decision",
            "",
            "- Candidate resolver completed.",
            "- Future qualification candidates may be identified, but qualification remains blocked.",
            "- Overall safety status remains BLOCKED.",
            "- TWS connection remains blocked.",
            "- Market data requests remain blocked.",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- IBKR read-only qualification candidate resolver only",
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
