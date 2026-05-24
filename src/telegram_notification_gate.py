from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union


TRUE_TEXT = "true"
FALSE_TEXT = "false"

TELEGRAM_GATE_PREVIEW_READY = "TELEGRAM_GATE_PREVIEW_READY"
TELEGRAM_GATE_APPROVAL_REQUIRED = "TELEGRAM_GATE_APPROVAL_REQUIRED"
TELEGRAM_GATE_APPROVED_NO_SEND = "TELEGRAM_GATE_APPROVED_NO_SEND"
TELEGRAM_GATE_SAFETY_BLOCKED = "TELEGRAM_GATE_SAFETY_BLOCKED"

PREVIEW_READY = "PREVIEW_READY"
PREVIEW_MISSING = "PREVIEW_MISSING"
PREVIEW_GENERATED = "PREVIEW_GENERATED"

BLOCKED_DRY_RUN_ONLY = "BLOCKED_DRY_RUN_ONLY"
READY_FOR_MANUAL_APPROVAL = "READY_FOR_MANUAL_APPROVAL"
APPROVED_BUT_SEND_NOT_IMPLEMENTED = "APPROVED_BUT_SEND_NOT_IMPLEMENTED"
SAFETY_BLOCKED = "SAFETY_BLOCKED"

REVIEW_PREVIEW_ONLY = "REVIEW_PREVIEW_ONLY"
MANUAL_APPROVAL_REQUIRED = "MANUAL_APPROVAL_REQUIRED"
SAFETY_REVIEW_REQUIRED = "SAFETY_REVIEW_REQUIRED"
NO_NOTIFICATION_READY = "NO_NOTIFICATION_READY"

FORBIDDEN_EXECUTION_WORDS = (
    "BUY",
    "SELL",
    "ORDER",
    "CANCEL",
    "REBALANCE",
    "AUTO_TRADE",
    "EXECUTE",
)

GATE_ACTION_FIELDS = (
    "recommended_notification_action",
    "telegram_send_status",
)

SAFETY_FIELDS = (
    "action_allowed",
    "broker_execution_triggered",
    "historical_data_request_triggered",
    "account_read_triggered",
    "position_read_triggered",
    "telegram_send_triggered",
)


@dataclass(frozen=True)
class SourceArtifact:
    path: str
    status: str
    rows: List[Dict[str, str]]


@dataclass(frozen=True)
class TelegramNotificationGateRow:
    top_level_status: str
    gate_run_id: str
    gate_timestamp: str
    notification_channel: str
    source_operator_status: str
    source_research_plan_status: str
    source_watchlist_status: str
    message_preview_status: str
    approval_required: str
    send_approved: str
    telegram_send_gate_enabled: str
    telegram_send_triggered: str
    telegram_send_status: str
    notification_severity: str
    recommended_notification_action: str
    blocked_reason: str
    action_allowed: str
    broker_execution_triggered: str
    historical_data_request_triggered: str
    account_read_triggered: str
    position_read_triggered: str
    source_telegram_packet_status: str
    source_first_operator_run_status: str
    approval_note: str


PathLike = Union[str, Path]


def _clean(value: object) -> str:
    return str(value or "").strip()


def _lower(value: object) -> str:
    return _clean(value).lower()


def _bool_text(value: bool) -> str:
    return TRUE_TEXT if value else FALSE_TEXT


def _truthy(value: object) -> bool:
    return _lower(value) in {"1", "yes", "y", "true", "triggered", "allowed"}


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_id() -> str:
    return "telegram_gate_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")


def _contains_forbidden(text: str) -> bool:
    upper = text.upper()
    return any(word in upper for word in FORBIDDEN_EXECUTION_WORDS)


def read_csv_artifact(path: PathLike) -> SourceArtifact:
    path_obj = Path(path)
    if not path_obj.exists():
        return SourceArtifact(str(path_obj), "MISSING", [])
    with path_obj.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return SourceArtifact(str(path_obj), "EMPTY", [])
    return SourceArtifact(str(path_obj), "PRESENT", rows)


def _artifact_status(artifact: SourceArtifact, status_fields: Sequence[str]) -> str:
    if artifact.status != "PRESENT":
        return artifact.status
    values: List[str] = []
    for row in artifact.rows:
        for field in status_fields:
            value = _clean(row.get(field))
            if value and value not in values:
                values.append(value)
    return ",".join(values[:4]) if values else "PRESENT"


def _source_safety_issues(artifacts: Sequence[SourceArtifact]) -> List[str]:
    issues: List[str] = []
    for artifact in artifacts:
        if artifact.status != "PRESENT":
            continue
        for index, row in enumerate(artifact.rows, start=1):
            label = _clean(row.get("display_symbol")) or _clean(row.get("symbol")) or f"row_{index}"
            for field in SAFETY_FIELDS:
                if _truthy(row.get(field)):
                    issues.append(f"{Path(artifact.path).name}:{label}:{field}")
    return issues


def _symbol(row: Dict[str, str]) -> str:
    return _clean(row.get("display_symbol")) or _clean(row.get("symbol")) or _clean(row.get("etf_symbol")) or "UNKNOWN"


def _compact_counts(rows: Iterable[Dict[str, str]], field: str) -> str:
    counts: Dict[str, int] = {}
    for row in rows:
        value = _clean(row.get(field)) or "UNKNOWN"
        counts[value] = counts.get(value, 0) + 1
    return ", ".join(f"{key}:{counts[key]}" for key in sorted(counts)) if counts else "none"


def _first_existing_report_status(root: Path) -> str:
    for relative in (
        "reports/ibkr_telegram_message_preview.md",
        "reports/latest_operator_handoff_summary.md",
        "reports/research_trading_plan_report.md",
        "reports/watchlist_universe_report.md",
    ):
        if (root / relative).exists():
            return PREVIEW_READY
    return PREVIEW_GENERATED


def _safe_preview_line(value: str) -> str:
    text = _clean(value).replace("|", "/")
    for word in FORBIDDEN_EXECUTION_WORDS:
        text = text.replace(word, f"{word[0]}-word")
        text = text.replace(word.lower(), f"{word[0].lower()}-word")
    return text


def build_approval_preview(
    *,
    gate_row: TelegramNotificationGateRow,
    operator: SourceArtifact,
    research: SourceArtifact,
    watchlist: SourceArtifact,
    approval_note: str = "",
) -> str:
    lines = [
        "# Telegram Notification Approval Preview",
        "",
        "Telegram-ready preview only. No network call is made.",
        "",
        f"Gate: {gate_row.top_level_status}",
        f"Ops status: {_safe_preview_line(gate_row.source_operator_status)}",
        f"Research plan status: {_safe_preview_line(gate_row.source_research_plan_status)}",
        f"Watchlist status: {_safe_preview_line(gate_row.source_watchlist_status)}",
        "",
        "Key symbol rows:",
    ]

    for row in operator.rows[:6]:
        symbol = _safe_preview_line(_symbol(row))
        price_status = _safe_preview_line(_clean(row.get("price_status")) or "unknown")
        data_delay = _safe_preview_line(_clean(row.get("data_delay_flag")) or "unknown")
        ops_status = _safe_preview_line(_clean(row.get("operator_status")) or "unknown")
        reference_price = _safe_preview_line(_clean(row.get("reference_price")) or _clean(row.get("latest_price")) or "unavailable")
        lines.append(f"- {symbol}: {ops_status}; price_status={price_status}; reference={reference_price}; data={data_delay}")

    if not operator.rows:
        lines.append("- No latest ops rows available.")

    lines.extend(
        [
            "",
            f"No-price / reference-only summary: {_compact_counts(operator.rows, 'price_status')}",
            f"Research rows: {_compact_counts(research.rows, 'research_plan_status')}",
            f"Watchlist universe: {_compact_counts(watchlist.rows, 'universe_status')}",
            "",
            "Safety statement: offline preview only; action_allowed=false; telegram_send_triggered=false; broker_execution_triggered=false; historical_data_request_triggered=false; account_read_triggered=false; position_read_triggered=false.",
        ]
    )
    if approval_note:
        lines.append(f"Approval note: {_safe_preview_line(approval_note)}")
    lines.extend(["", "Next manual step: review this preview and record approval outside the runtime output."])
    return "\n".join(lines) + "\n"


def build_gate(
    *,
    root: PathLike = ".",
    send_approved: bool = False,
    approval_note: str = "",
) -> Tuple[TelegramNotificationGateRow, SourceArtifact, SourceArtifact, SourceArtifact]:
    root_path = Path(root)
    operator = read_csv_artifact(root_path / "latest_daily_operator_handoff_summary.csv")
    research = read_csv_artifact(root_path / "research_trading_plan.csv")
    watchlist = read_csv_artifact(root_path / "watchlist_universe.csv")
    telegram_packet = read_csv_artifact(root_path / "ibkr_telegram_notification_packet.csv")
    first_operator = read_csv_artifact(root_path / "first_operator_run_post_analysis.csv")

    safety_issues = _source_safety_issues([operator, research, watchlist, telegram_packet, first_operator])
    source_operator_status = _artifact_status(operator, ("top_level_status", "operator_status"))
    source_research_status = _artifact_status(research, ("research_plan_status", "plan_status"))
    source_watchlist_status = _artifact_status(watchlist, ("universe_status", "validation_status"))
    preview_status = _first_existing_report_status(root_path)

    has_core_preview_inputs = any(artifact.status == "PRESENT" for artifact in (operator, research, watchlist))
    if not has_core_preview_inputs:
        preview_status = PREVIEW_MISSING

    if safety_issues:
        top_status = TELEGRAM_GATE_SAFETY_BLOCKED
        telegram_send_status = SAFETY_BLOCKED
        notification_severity = "CRITICAL"
        recommended_action = SAFETY_REVIEW_REQUIRED
        blocked_reason = "source_safety_flag_true:" + ",".join(safety_issues[:8])
    elif send_approved:
        top_status = TELEGRAM_GATE_APPROVED_NO_SEND
        telegram_send_status = APPROVED_BUT_SEND_NOT_IMPLEMENTED
        notification_severity = "INFO"
        recommended_action = REVIEW_PREVIEW_ONLY
        blocked_reason = "real_telegram_send_not_implemented_in_phase439"
    elif preview_status == PREVIEW_MISSING:
        top_status = TELEGRAM_GATE_APPROVAL_REQUIRED
        telegram_send_status = BLOCKED_DRY_RUN_ONLY
        notification_severity = "WARNING"
        recommended_action = NO_NOTIFICATION_READY
        blocked_reason = "no_core_preview_inputs_present"
    else:
        top_status = TELEGRAM_GATE_APPROVAL_REQUIRED
        telegram_send_status = READY_FOR_MANUAL_APPROVAL
        notification_severity = "INFO"
        recommended_action = MANUAL_APPROVAL_REQUIRED
        blocked_reason = "manual_approval_required_before_future_send_phase"

    row = TelegramNotificationGateRow(
        top_level_status=top_status,
        gate_run_id=_run_id(),
        gate_timestamp=_now_timestamp(),
        notification_channel="TELEGRAM",
        source_operator_status=source_operator_status,
        source_research_plan_status=source_research_status,
        source_watchlist_status=source_watchlist_status,
        message_preview_status=preview_status,
        approval_required=TRUE_TEXT,
        send_approved=_bool_text(send_approved),
        telegram_send_gate_enabled=FALSE_TEXT,
        telegram_send_triggered=FALSE_TEXT,
        telegram_send_status=telegram_send_status,
        notification_severity=notification_severity,
        recommended_notification_action=recommended_action,
        blocked_reason=blocked_reason,
        action_allowed=FALSE_TEXT,
        broker_execution_triggered=FALSE_TEXT,
        historical_data_request_triggered=FALSE_TEXT,
        account_read_triggered=FALSE_TEXT,
        position_read_triggered=FALSE_TEXT,
        source_telegram_packet_status=telegram_packet.status,
        source_first_operator_run_status=first_operator.status,
        approval_note=approval_note,
    )
    return row, operator, research, watchlist


def write_gate_csv(path: PathLike, row: TelegramNotificationGateRow) -> None:
    fields = list(TelegramNotificationGateRow.__dataclass_fields__.keys())
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(fields)
        writer.writerow([getattr(row, field) for field in fields])


def build_gate_report(
    row: TelegramNotificationGateRow,
    *,
    operator: SourceArtifact,
    research: SourceArtifact,
    watchlist: SourceArtifact,
    output_csv: PathLike,
    preview_report: PathLike,
) -> str:
    return "\n".join(
        [
            "# Telegram Notification Gate Report",
            "",
            "## Top-level Status",
            "",
            f"- top_level_status={row.top_level_status}",
            f"- notification_channel={row.notification_channel}",
            f"- notification_severity={row.notification_severity}",
            "",
            "## Safety Summary",
            "",
            "- offline_only=true",
            "- telegram_api_connection=false",
            "- tws_or_ib_gateway_connection=false",
            f"- action_allowed={row.action_allowed}",
            f"- broker_execution_triggered={row.broker_execution_triggered}",
            f"- historical_data_request_triggered={row.historical_data_request_triggered}",
            f"- account_read_triggered={row.account_read_triggered}",
            f"- position_read_triggered={row.position_read_triggered}",
            f"- telegram_send_triggered={row.telegram_send_triggered}",
            "",
            "## Source Artifact Summary",
            "",
            f"- operator_csv={operator.path}; status={operator.status}; source_status={row.source_operator_status}; rows={len(operator.rows)}",
            f"- research_csv={research.path}; status={research.status}; source_status={row.source_research_plan_status}; rows={len(research.rows)}",
            f"- watchlist_csv={watchlist.path}; status={watchlist.status}; source_status={row.source_watchlist_status}; rows={len(watchlist.rows)}",
            f"- optional_telegram_packet_status={row.source_telegram_packet_status}",
            f"- optional_first_operator_run_status={row.source_first_operator_run_status}",
            "",
            "## Approval Gate Status",
            "",
            f"- approval_required={row.approval_required}",
            f"- send_approved={row.send_approved}",
            f"- telegram_send_gate_enabled={row.telegram_send_gate_enabled}",
            f"- telegram_send_status={row.telegram_send_status}",
            f"- recommended_notification_action={row.recommended_notification_action}",
            "",
            "## Message Preview Status",
            "",
            f"- message_preview_status={row.message_preview_status}",
            f"- preview_report={preview_report}",
            "",
            "## Blocked / Ready Explanation",
            "",
            f"- blocked_reason={row.blocked_reason}",
            f"- output_csv={output_csv}",
            "",
            "## Next Operator Step",
            "",
            "- review the approval preview manually before any later send-enabled phase.",
        ]
    ) + "\n"


def write_gate_report(path: PathLike, report_text: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(report_text, encoding="utf-8")


def write_approval_preview(path: PathLike, preview_text: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(preview_text, encoding="utf-8")


def validate_gate(row: TelegramNotificationGateRow, preview_text: str) -> List[str]:
    errors: List[str] = []
    for field in GATE_ACTION_FIELDS:
        if _contains_forbidden(getattr(row, field)):
            errors.append(f"forbidden_execution_word:{field}")
    if _contains_forbidden(preview_text):
        errors.append("forbidden_execution_word:approval_preview")
    for field in (
        "action_allowed",
        "broker_execution_triggered",
        "historical_data_request_triggered",
        "account_read_triggered",
        "position_read_triggered",
        "telegram_send_triggered",
        "telegram_send_gate_enabled",
    ):
        if getattr(row, field) != FALSE_TEXT:
            errors.append(f"{field}_not_false")
    if row.approval_required != TRUE_TEXT:
        errors.append("approval_required_not_true")
    return errors


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an offline Telegram notification approval gate.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--send-approved", action="store_true")
    parser.add_argument("--approval-note", default="")
    parser.add_argument("--output-csv", default="telegram_notification_gate.csv")
    parser.add_argument("--output-report", default="reports/telegram_notification_gate_report.md")
    parser.add_argument("--preview-report", default="reports/telegram_notification_approval_preview.md")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    row, operator, research, watchlist = build_gate(
        root=args.root,
        send_approved=args.send_approved,
        approval_note=args.approval_note,
    )
    preview_text = build_approval_preview(
        gate_row=row,
        operator=operator,
        research=research,
        watchlist=watchlist,
        approval_note=args.approval_note,
    )
    report_text = build_gate_report(
        row,
        operator=operator,
        research=research,
        watchlist=watchlist,
        output_csv=args.output_csv,
        preview_report=args.preview_report,
    )

    write_gate_csv(args.output_csv, row)
    write_gate_report(args.output_report, report_text)
    write_approval_preview(args.preview_report, preview_text)

    print("[PASS] Telegram notification gate generated")
    print(f"top_level_status={row.top_level_status}")
    print(f"message_preview_status={row.message_preview_status}")
    print(f"approval_required={row.approval_required}")
    print(f"send_approved={row.send_approved}")
    print(f"telegram_send_gate_enabled={row.telegram_send_gate_enabled}")
    print(f"telegram_send_triggered={row.telegram_send_triggered}")
    print(f"telegram_send_status={row.telegram_send_status}")
    print(f"recommended_notification_action={row.recommended_notification_action}")
    print(f"action_allowed={row.action_allowed}")
    print(f"broker_execution_triggered={row.broker_execution_triggered}")
    print(f"historical_data_request_triggered={row.historical_data_request_triggered}")
    print(f"account_read_triggered={row.account_read_triggered}")
    print(f"position_read_triggered={row.position_read_triggered}")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    print(f"preview_report={args.preview_report}")

    errors = validate_gate(row, preview_text)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
