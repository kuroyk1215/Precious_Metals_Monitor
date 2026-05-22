from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class IBKRTelegramNotificationRow:
    display_symbol: str
    notification_status: str
    notification_severity: str
    source_operator_packet_status: str
    final_decision_label: str
    final_research_bucket: str
    usable_reference_price: str
    operator_instruction: str
    next_step: str
    message_title: str
    message_body: str
    manual_review_required: str
    action_allowed: str
    telegram_send_triggered: str
    broker_execution_triggered: str
    historical_data_request_triggered: str
    account_read_triggered: str
    position_read_triggered: str
    safety_flags: str


def _clean(value: object) -> str:
    return str(value or "").strip()


def _status_and_severity(operator_packet_status: str) -> Tuple[str, str]:
    if operator_packet_status == "OPERATOR_REVIEW_READY":
        return "READY_TO_NOTIFY", "INFO"
    if operator_packet_status == "SAFETY_REJECTED":
        return "SAFETY_REJECTED_NOTIFY", "CRITICAL"
    return "BLOCKED_NOTIFY", "WARNING"


def _bucket_message(final_research_bucket: str) -> str:
    if final_research_bucket == "delayed_reference":
        return "This is delayed/reference-only context for manual review."
    if final_research_bucket == "stale_reference":
        return "This is stale or delayed_frozen/reference-only context for manual review."
    if final_research_bucket in {"no_price", "unsupported", "no_go"}:
        return "No action: no usable notification price or unsupported/no-go research bucket."
    return "Reference-only manual review context. No broker action is authorized."


def build_notification_row(row: Dict[str, str]) -> IBKRTelegramNotificationRow:
    operator_packet_status = _clean(row.get("operator_packet_status")) or "OPERATOR_REVIEW_BLOCKED"
    final_research_bucket = _clean(row.get("final_research_bucket")) or "no_go"
    notification_status, notification_severity = _status_and_severity(operator_packet_status)
    display_symbol = _clean(row.get("display_symbol")) or "UNKNOWN"
    final_decision_label = _clean(row.get("final_decision_label")) or "BLOCKED"
    usable_reference_price = _clean(row.get("usable_reference_price")) or "unavailable"
    operator_instruction = _clean(row.get("operator_instruction")) or "no_action_review_blocked"
    next_step = _clean(row.get("next_step")) or "manual_review_only"
    safety_flags = _clean(row.get("safety_flags"))
    body_parts = [
        f"Symbol: {display_symbol}",
        f"Status: {notification_status} ({notification_severity})",
        f"Decision: {final_decision_label}",
        f"Research bucket: {final_research_bucket}",
        f"Reference price: {usable_reference_price}",
        f"Instruction: {operator_instruction}",
        _bucket_message(final_research_bucket),
        "Manual review required. No action is allowed.",
    ]

    return IBKRTelegramNotificationRow(
        display_symbol=display_symbol,
        notification_status=notification_status,
        notification_severity=notification_severity,
        source_operator_packet_status=operator_packet_status,
        final_decision_label=final_decision_label,
        final_research_bucket=final_research_bucket,
        usable_reference_price=usable_reference_price,
        operator_instruction=operator_instruction,
        next_step=next_step,
        message_title=f"IBKR daily dry-run notification: {display_symbol}",
        message_body=" ".join(body_parts),
        manual_review_required="true",
        action_allowed="false",
        telegram_send_triggered="false",
        broker_execution_triggered="false",
        historical_data_request_triggered="false",
        account_read_triggered="false",
        position_read_triggered="false",
        safety_flags=safety_flags,
    )


def build_notification_rows(rows: Iterable[Dict[str, str]]) -> List[IBKRTelegramNotificationRow]:
    return [build_notification_row(row) for row in rows]


def missing_operator_packet_row(path: str) -> IBKRTelegramNotificationRow:
    return build_notification_row(
        {
            "display_symbol": "NO_GO",
            "operator_packet_status": "OPERATOR_REVIEW_BLOCKED",
            "final_decision_label": "NO_GO",
            "final_research_bucket": "no_go",
            "usable_reference_price": "unavailable",
            "operator_instruction": "no_action_missing_operator_packet",
            "next_step": "generate_operator_packet_before_notification",
            "safety_flags": f"missing_operator_packet:{path}",
        }
    )


def read_csv_rows(path: Path) -> Tuple[str, List[Dict[str, str]]]:
    if not path.exists():
        return "missing", []
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return "empty_file", []
    return "present", rows


def write_notification_csv(path: Path, rows: List[IBKRTelegramNotificationRow]) -> None:
    fields = list(IBKRTelegramNotificationRow.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def build_message_preview(rows: Iterable[IBKRTelegramNotificationRow]) -> str:
    messages: List[str] = []
    for index, row in enumerate(rows, start=1):
        messages.extend(
            [
                f"## Message {index}: {row.display_symbol}",
                "",
                row.message_title,
                "",
                row.message_body,
                "",
                "Safety: action_allowed=false; telegram_send_triggered=false; manual_review_required=true",
                "",
            ]
        )
    return "\n".join(messages).rstrip() + "\n"


def summarize_statuses(rows: Iterable[IBKRTelegramNotificationRow]) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    for row in rows:
        summary[row.notification_status] = summary.get(row.notification_status, 0) + 1
    return summary


def write_message_preview(path: Path, rows: List[IBKRTelegramNotificationRow]) -> None:
    path.write_text(
        "\n".join(
            [
                "# IBKR Telegram Message Preview",
                "",
                "Copyable dry-run text only. No Telegram send is performed.",
                "",
                build_message_preview(rows).rstrip(),
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_notification_report(
    path: Path,
    rows: List[IBKRTelegramNotificationRow],
    operator_packet_path: str,
    operator_packet_status: str,
    pipeline_summary_path: str,
    pipeline_summary_status: str,
    runner_summary_path: str,
    runner_summary_status: str,
    message_preview_path: str,
) -> None:
    status_summary = summarize_statuses(rows)
    status_lines = "\n".join(f"| {status} | {count} |" for status, count in sorted(status_summary.items()))
    row_lines = "\n".join(
        f"| {row.display_symbol} | {row.notification_status} | {row.notification_severity} | {row.source_operator_packet_status} | {row.final_decision_label} | {row.final_research_bucket} | {row.usable_reference_price} | {row.next_step} | {row.action_allowed} | {row.telegram_send_triggered} |"
        for row in rows
    )

    path.write_text(
        "\n".join(
            [
                "# IBKR Telegram Dry-Run Notification Packet",
                "",
                "## Notification Packet Decision",
                "",
                "| field | value |",
                "|---|---|",
                "| notification_packet_status | NO_GO |",
                "| action_allowed | false |",
                "| telegram_send_triggered | false |",
                "| manual_review_required | true |",
                "",
                "## Input Operator Packet Status",
                "",
                "| field | value |",
                "|---|---|",
                f"| operator_packet_input | {operator_packet_path} |",
                f"| operator_packet_input_status | {operator_packet_status} |",
                f"| pipeline_summary_input | {pipeline_summary_path} |",
                f"| pipeline_summary_input_status | {pipeline_summary_status} |",
                f"| runner_summary_input | {runner_summary_path} |",
                f"| runner_summary_input_status | {runner_summary_status} |",
                f"| row_count | {len(rows)} |",
                "",
                "## Symbol Notification Rows",
                "",
                "| display_symbol | notification_status | notification_severity | source_operator_packet_status | final_decision_label | final_research_bucket | usable_reference_price | next_step | action_allowed | telegram_send_triggered |",
                "|---|---|---|---|---|---|---:|---|---|---|",
                row_lines,
                "",
                "## Telegram Message Preview",
                "",
                f"- message_preview={message_preview_path}",
                "- preview_only=true",
                "- telegram_send_triggered=false",
                "",
                "## Safety Confirmation",
                "",
                "- action_allowed=false",
                "- telegram_send_triggered=false",
                "- broker_execution_triggered=false",
                "- historical_data_request_triggered=false",
                "- account_read_triggered=false",
                "- position_read_triggered=false",
                "- manual_review_required=true",
                "",
                "## Next Phase Handoff",
                "",
                "Phase 353-368 may add a Telegram send gate, secret template, and explicit send approval. This phase does not read tokens, send messages, connect to brokers, request historical data, read accounts, or read positions.",
                "",
                "## Notification Status Summary",
                "",
                "| notification_status | count |",
                "|---|---:|",
                status_lines,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
