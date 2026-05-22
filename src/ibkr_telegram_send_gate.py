from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import json
import urllib.parse
import urllib.request
from typing import Callable, Optional, Tuple


@dataclass(frozen=True)
class IBKRTelegramSendGateDecision:
    send_gate_status: str
    send_gate_reason: str
    send_mode: str
    approval_file_status: str
    token_status: str
    chat_id_status: str
    notification_packet_status: str
    message_preview_status: str
    telegram_send_triggered: str
    telegram_send_status: str
    telegram_response_status: str
    telegram_response_summary: str
    action_allowed: str
    broker_execution_triggered: str
    historical_data_request_triggered: str
    account_read_triggered: str
    position_read_triggered: str
    manual_review_required: str
    safety_flags: str


TelegramSender = Callable[[str, str, str], Tuple[str, str]]


def _file_status(path: str | Path) -> str:
    return "present" if Path(path).exists() else "missing"


def _present_status(value: Optional[str], required: bool) -> str:
    if not required:
        return "not_required"
    return "present" if value else "missing"


def _decision(
    send_gate_status: str,
    send_gate_reason: str,
    send_mode: str,
    approval_file_status: str,
    token_status: str,
    chat_id_status: str,
    notification_packet_status: str,
    message_preview_status: str,
    telegram_send_triggered: str,
    telegram_send_status: str,
    telegram_response_status: str = "not_available",
    telegram_response_summary: str = "not_available",
    safety_flags: str = "",
) -> IBKRTelegramSendGateDecision:
    return IBKRTelegramSendGateDecision(
        send_gate_status=send_gate_status,
        send_gate_reason=send_gate_reason,
        send_mode=send_mode,
        approval_file_status=approval_file_status,
        token_status=token_status,
        chat_id_status=chat_id_status,
        notification_packet_status=notification_packet_status,
        message_preview_status=message_preview_status,
        telegram_send_triggered=telegram_send_triggered,
        telegram_send_status=telegram_send_status,
        telegram_response_status=telegram_response_status,
        telegram_response_summary=telegram_response_summary,
        action_allowed="false",
        broker_execution_triggered="false",
        historical_data_request_triggered="false",
        account_read_triggered="false",
        position_read_triggered="false",
        manual_review_required="true",
        safety_flags=safety_flags,
    )


def evaluate_send_gate(
    *,
    send_telegram: bool,
    approval_file: str | Path,
    notification_packet: str | Path,
    message_preview: str | Path,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
    sender: Optional[TelegramSender] = None,
) -> IBKRTelegramSendGateDecision:
    send_mode = "explicit_send" if send_telegram else "dry_run"
    approval_status = _file_status(approval_file) if send_telegram else "not_required"
    token_status = _present_status(bot_token, send_telegram)
    chat_status = _present_status(chat_id, send_telegram)
    notification_status = _file_status(notification_packet)
    preview_status = _file_status(message_preview)

    if not send_telegram:
        return _decision(
            "DRY_RUN_ONLY",
            "send_telegram_flag_not_set",
            send_mode,
            approval_status,
            token_status,
            chat_status,
            notification_status,
            preview_status,
            "false",
            "not_attempted",
        )

    blockers = []
    if approval_status == "missing":
        blockers.append("approval_file_missing")
    if token_status == "missing":
        blockers.append("telegram_bot_token_missing")
    if chat_status == "missing":
        blockers.append("telegram_chat_id_missing")
    if notification_status == "missing":
        blockers.append("notification_packet_missing")
    if preview_status == "missing":
        blockers.append("message_preview_missing")

    if blockers:
        return _decision(
            "SEND_BLOCKED",
            ",".join(blockers),
            send_mode,
            approval_status,
            token_status,
            chat_status,
            notification_status,
            preview_status,
            "false",
            "blocked",
            safety_flags="telegram_send_blocked_by_gate",
        )

    message_text = Path(message_preview).read_text(encoding="utf-8")
    active_sender = sender or send_telegram_message
    try:
        response_status, response_summary = active_sender(str(bot_token), str(chat_id), message_text)
    except Exception as exc:  # pragma: no cover - exercised with a test sender
        return _decision(
            "SEND_FAILED_SAFE",
            "telegram_send_exception",
            send_mode,
            approval_status,
            token_status,
            chat_status,
            notification_status,
            preview_status,
            "true",
            "failed",
            telegram_response_status="exception",
            telegram_response_summary=type(exc).__name__,
            safety_flags="telegram_send_failed_safe",
        )

    return _decision(
        "SEND_ALLOWED",
        "all_send_gate_requirements_satisfied",
        send_mode,
        approval_status,
        token_status,
        chat_status,
        notification_status,
        preview_status,
        "true",
        "sent" if response_status == "ok" else "failed",
        telegram_response_status=response_status,
        telegram_response_summary=response_summary,
        safety_flags="telegram_send_attempted",
    )


def send_telegram_message(bot_token: str, chat_id: str, message_text: str) -> Tuple[str, str]:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": message_text[:3900],
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(request, timeout=15) as response:
        status = getattr(response, "status", 0)
        body = response.read(4096).decode("utf-8", errors="replace")
    summary = f"http_status={status}"
    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict) and "ok" in parsed:
            summary = f"http_status={status};ok={str(parsed.get('ok')).lower()}"
    except json.JSONDecodeError:
        pass
    return "ok" if 200 <= int(status) < 300 else "http_error", summary


def write_send_gate_csv(path: str | Path, decision: IBKRTelegramSendGateDecision) -> None:
    fields = list(IBKRTelegramSendGateDecision.__dataclass_fields__.keys())
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerow([getattr(decision, field) for field in fields])


def write_send_gate_report(
    path: str | Path,
    decision: IBKRTelegramSendGateDecision,
    notification_packet: str,
    message_preview: str,
    approval_file: str,
) -> None:
    Path(path).write_text(
        "\n".join(
            [
                "# IBKR Telegram Send Gate Report",
                "",
                "## Send Gate Decision",
                "",
                "| field | value |",
                "|---|---|",
                f"| send_gate_status | {decision.send_gate_status} |",
                f"| send_gate_reason | {decision.send_gate_reason} |",
                f"| send_mode | {decision.send_mode} |",
                f"| telegram_send_triggered | {decision.telegram_send_triggered} |",
                f"| telegram_send_status | {decision.telegram_send_status} |",
                "| action_allowed | false |",
                "",
                "## Gate Inputs",
                "",
                "| field | value |",
                "|---|---|",
                f"| approval_file | {approval_file} |",
                f"| approval_file_status | {decision.approval_file_status} |",
                f"| token_status | {decision.token_status} |",
                f"| chat_id_status | {decision.chat_id_status} |",
                f"| notification_packet | {notification_packet} |",
                f"| notification_packet_status | {decision.notification_packet_status} |",
                f"| message_preview | {message_preview} |",
                f"| message_preview_status | {decision.message_preview_status} |",
                "",
                "## Telegram Response",
                "",
                f"- telegram_response_status={decision.telegram_response_status}",
                f"- telegram_response_summary={decision.telegram_response_summary}",
                "- token_value_redacted=true",
                "- chat_id_value_redacted=true",
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
                "## Operator Boundary",
                "",
                "Telegram sending is notification delivery only. It does not authorize trades, broker execution, account reads, position reads, or historical data requests.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
