from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class IBKRDailyOperatorPacketRow:
    display_symbol: str
    operator_packet_status: str
    final_review_status: str
    final_decision_label: str
    final_research_bucket: str
    usable_reference_price: str
    usable_reference_price_field: str
    operator_action_required: str
    operator_instruction: str
    manual_review_required: str
    action_allowed: str
    broker_execution_triggered: str
    historical_data_request_triggered: str
    account_read_triggered: str
    position_read_triggered: str
    safety_flags: str
    execution_c_mode: str
    pipeline_stage: str
    next_step: str


def _clean(value: object) -> str:
    return str(value or "").strip()


def _upper(value: object) -> str:
    return _clean(value).upper()


def _status_and_instruction(final_review_status: str) -> Tuple[str, str]:
    if final_review_status == "FINAL_REVIEW_READY":
        return "OPERATOR_REVIEW_READY", "manual_review_reference_only"
    if final_review_status == "SAFETY_REJECTED":
        return "SAFETY_REJECTED", "no_action_safety_rejected"
    return "OPERATOR_REVIEW_BLOCKED", "no_action_review_blocked"


def _next_step(final_research_bucket: str) -> str:
    if final_research_bucket == "delayed_reference":
        return "operator_compare_with_manual_market_context"
    if final_research_bucket == "stale_reference":
        return "operator_verify_market_open_or_latest_quote"
    if final_research_bucket in {"no_price", "unsupported", "no_go"}:
        return "no_operator_action"
    return "operator_manual_research_review"


def build_operator_packet_row(row: Dict[str, str], execution_c_mode: str = "dry_run") -> IBKRDailyOperatorPacketRow:
    final_review_status = _upper(row.get("final_review_status")) or "FINAL_REVIEW_BLOCKED"
    final_research_bucket = _clean(row.get("final_research_bucket")) or "no_go"
    packet_status, instruction = _status_and_instruction(final_review_status)
    safety_flags = _clean(row.get("safety_flags"))
    if _clean(row.get("action_allowed")).lower() != "false":
        packet_status = "SAFETY_REJECTED"
        instruction = "no_action_safety_rejected"
        safety_flags = ",".join(flag for flag in (safety_flags, "operator_packet_action_allowed_not_false") if flag)

    return IBKRDailyOperatorPacketRow(
        display_symbol=_clean(row.get("display_symbol")),
        operator_packet_status=packet_status,
        final_review_status=final_review_status,
        final_decision_label=_clean(row.get("final_decision_label")) or "BLOCKED",
        final_research_bucket=final_research_bucket,
        usable_reference_price=_clean(row.get("usable_reference_price")),
        usable_reference_price_field=_clean(row.get("usable_reference_price_field")) or "unavailable",
        operator_action_required=_clean(row.get("operator_action_required")) or "true",
        operator_instruction=instruction,
        manual_review_required="true",
        action_allowed="false",
        broker_execution_triggered="false",
        historical_data_request_triggered="false",
        account_read_triggered="false",
        position_read_triggered="false",
        safety_flags=safety_flags,
        execution_c_mode=execution_c_mode,
        pipeline_stage="operator_packet",
        next_step=_next_step(final_research_bucket),
    )


def build_operator_packet_rows(
    rows: Iterable[Dict[str, str]],
    execution_c_mode: str = "dry_run",
) -> List[IBKRDailyOperatorPacketRow]:
    return [build_operator_packet_row(row, execution_c_mode) for row in rows]


def missing_input_operator_packet_row(path: str, execution_c_mode: str = "dry_run") -> IBKRDailyOperatorPacketRow:
    return build_operator_packet_row(
        {
            "display_symbol": "",
            "final_review_status": "FINAL_REVIEW_BLOCKED",
            "final_decision_label": "BLOCKED",
            "final_research_bucket": "no_go",
            "usable_reference_price": "",
            "usable_reference_price_field": "unavailable",
            "operator_action_required": "true",
            "action_allowed": "false",
            "safety_flags": f"missing_input,final_pack_missing:{path}",
        },
        execution_c_mode,
    )


def read_final_pack_rows(path: Path) -> Tuple[str, List[Dict[str, str]]]:
    if not path.exists():
        return "missing", []
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return "empty_file", []
    return "present", rows


def write_operator_packet_csv(path: Path, rows: List[IBKRDailyOperatorPacketRow]) -> None:
    fields = list(IBKRDailyOperatorPacketRow.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def summarize_operator_statuses(rows: Iterable[IBKRDailyOperatorPacketRow]) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    for row in rows:
        summary[row.operator_packet_status] = summary.get(row.operator_packet_status, 0) + 1
    return summary


def write_operator_packet_report(
    path: Path,
    rows: List[IBKRDailyOperatorPacketRow],
    input_path: str,
    input_status: str,
    execution_c_mode: str,
) -> None:
    status_summary = summarize_operator_statuses(rows)
    bucket_summary: Dict[str, int] = {}
    for row in rows:
        bucket_summary[row.final_research_bucket] = bucket_summary.get(row.final_research_bucket, 0) + 1

    status_lines = "\n".join(f"| {status} | {count} |" for status, count in sorted(status_summary.items()))
    bucket_lines = "\n".join(f"| {bucket} | {count} |" for bucket, count in sorted(bucket_summary.items()))
    row_lines = "\n".join(
        f"| {row.display_symbol} | {row.operator_packet_status} | {row.final_review_status} | {row.final_decision_label} | {row.final_research_bucket} | {row.usable_reference_price} | {row.operator_instruction} | {row.next_step} | {row.action_allowed} |"
        for row in rows
    )

    path.write_text(
        "\n".join(
            [
                "# IBKR Daily Operator Packet",
                "",
                "## Operator Packet Decision",
                "",
                "| field | value |",
                "|---|---|",
                "| operator_packet_status | NO_GO |",
                "| action_allowed | false |",
                "| manual_review_required | true |",
                "",
                "## Pipeline Input Status",
                "",
                "| field | value |",
                "|---|---|",
                f"| final_pack_input | {input_path} |",
                f"| final_pack_input_status | {input_status} |",
                f"| row_count | {len(rows)} |",
                "",
                "## Symbol Operator Rows",
                "",
                "| display_symbol | operator_packet_status | final_review_status | final_decision_label | final_research_bucket | usable_reference_price | operator_instruction | next_step | action_allowed |",
                "|---|---|---|---|---|---:|---|---|---|",
                row_lines,
                "",
                "## Execution C Mode",
                "",
                f"- execution_c_mode={execution_c_mode}",
                "- default mode does not connect to IBKR",
                "- execute_market_data mode only runs the gated market data snapshot step",
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
                "## Manual Operator Handoff",
                "",
                "Use this packet for manual research review only. It does not authorize trades, broker execution, account reads, position reads, or historical data requests.",
                "",
                "## Next Phase Handoff",
                "",
                "Phase 321-336 may add scheduler, local daily run, and log rotation around this dry-run-first pipeline.",
                "",
                "## Operator Status Summary",
                "",
                "| operator_packet_status | count |",
                "|---|---:|",
                status_lines,
                "",
                "| final_research_bucket | count |",
                "|---|---:|",
                bucket_lines,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
