from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
from typing import Dict, Iterable, List, Optional, Tuple


TRUE_TEXT = "true"
FALSE_TEXT = "false"
LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE = "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE"


@dataclass(frozen=True)
class FirstOperatorRunPostAnalysisDecision:
    post_run_status: str
    post_run_mode: str
    execution_c_input_status: str
    snapshot_input_status: str
    operator_packet_input_status: str
    telegram_notification_input_status: str
    execution_c_status: str
    validation_decision: str
    snapshot_status: str
    effective_market_data_type: str
    data_delay_flag: str
    operator_packet_status: str
    operator_review_ready_count: str
    operator_review_blocked_count: str
    delayed_reference_count: str
    delayed_frozen_reference_count: str
    unsupported_count: str
    no_go_count: str
    error_codes_detected: str
    error_10089_detected: str
    error_354_detected: str
    live_subscription_status: str
    reference_only_status: str
    global_no_trade_status: str
    semantic_status: str
    analysis_decision: str
    analysis_reason: str
    action_allowed: str
    broker_execution_triggered: str
    historical_data_request_triggered: str
    account_read_triggered: str
    position_read_triggered: str
    telegram_send_triggered: str
    manual_review_required: str
    safety_flags: str
    next_step: str


def _clean(value: object) -> str:
    return str(value or "").strip()


def _lower(value: object) -> str:
    return _clean(value).lower()


def _upper(value: object) -> str:
    return _clean(value).upper()


def read_csv_rows(path: str | Path) -> Tuple[str, List[Dict[str, str]]]:
    candidate = Path(path)
    if not candidate.exists():
        return "missing", []
    with candidate.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return "empty_file", []
    return "present", rows


def _default_api_errors_csv() -> Path:
    default_path = Path("ibkr_market_data_api_errors.csv")
    return default_path if default_path.exists() else default_path


def _latest_value(rows: Iterable[Dict[str, str]], field: str, default: str = "unknown") -> str:
    row_list = list(rows)
    for row in reversed(row_list):
        value = _clean(row.get(field))
        if value:
            return value
    return default


def _contains_error(rows: Iterable[Dict[str, str]], code: str) -> bool:
    needle = str(code)
    fields = (
        "error_code",
        "error_message",
        "raw_error_message",
        "normalized_error_class",
        "live_subscription_status",
        "notes",
        "fallback_reason",
        "error_interpretation",
        "analysis_reason",
        "validation_reason",
        "report_text",
    )
    for row in rows:
        for field in fields:
            if needle in _clean(row.get(field)):
                return True
    return False


def _contains_delayed_available_signal(rows: Iterable[Dict[str, str]]) -> bool:
    fields = (
        "error_code",
        "error_message",
        "raw_error_message",
        "normalized_error_class",
        "live_subscription_status",
        "notes",
        "fallback_reason",
        "error_interpretation",
        "analysis_reason",
        "validation_reason",
        "report_text",
    )
    for row in rows:
        for field in fields:
            value = _clean(row.get(field))
            lowered = value.lower()
            if value in {"354", "10089"}:
                return True
            if "delayed market data available" in lowered:
                return True
            if "live_not_subscribed_delayed_available" in lowered:
                return True
            if "延迟市场数据可用" in value:
                return True
    return False


def _error_codes(rows: Iterable[Dict[str, str]]) -> List[str]:
    codes: List[str] = []
    for row in rows:
        for part in _clean(row.get("error_code")).replace(";", ",").split(","):
            code = part.strip()
            if code and code not in codes:
                codes.append(code)
    return codes


def _count_values(rows: Iterable[Dict[str, str]], fields: Iterable[str], values: Iterable[str]) -> int:
    wanted = {value.lower() for value in values}
    count = 0
    for row in rows:
        for field in fields:
            if _lower(row.get(field)) in wanted:
                count += 1
                break
    return count


def _row_symbol(row: Dict[str, str], fallback_prefix: str, index: int) -> str:
    return (
        _clean(row.get("display_symbol"))
        or _clean(row.get("symbol"))
        or _clean(row.get("local_symbol"))
        or f"{fallback_prefix}:{index}"
    )


def _count_unique_symbols(
    rows: Iterable[Dict[str, str]],
    fields: Iterable[str],
    values: Iterable[str],
    *,
    fallback_prefix: str,
) -> int:
    wanted = {value.lower() for value in values}
    symbols: set[str] = set()
    for index, row in enumerate(rows):
        for field in fields:
            if _lower(row.get(field)) in wanted:
                symbols.add(_row_symbol(row, fallback_prefix, index))
                break
    return len(symbols)


def _safety_anomalies(rows: Iterable[Dict[str, str]]) -> List[str]:
    flags: List[str] = []
    safety_fields = (
        "action_allowed",
        "broker_execution_triggered",
        "historical_data_request_triggered",
        "account_read_triggered",
        "position_read_triggered",
        "telegram_send_triggered",
    )
    for row in rows:
        label = _clean(row.get("display_symbol")) or _clean(row.get("workflow")) or _clean(row.get("post_run_mode")) or "row"
        for field in safety_fields:
            value = _clean(row.get(field))
            if value and value.lower() != FALSE_TEXT:
                flags.append(f"{label}:{field}_not_false")
    return flags


def build_first_operator_run_post_analysis_decision(
    *,
    execution_c_rows: Iterable[Dict[str, str]] = (),
    snapshot_rows: Iterable[Dict[str, str]] = (),
    api_error_rows: Iterable[Dict[str, str]] = (),
    operator_rows: Iterable[Dict[str, str]] = (),
    telegram_notification_rows: Iterable[Dict[str, str]] = (),
    execution_c_input_status: str = "missing",
    snapshot_input_status: str = "missing",
    operator_packet_input_status: str = "missing",
    telegram_notification_input_status: str = "missing",
) -> FirstOperatorRunPostAnalysisDecision:
    execution_list = list(execution_c_rows)
    snapshot_list = list(snapshot_rows)
    api_error_list = list(api_error_rows)
    operator_list = list(operator_rows)
    telegram_list = list(telegram_notification_rows)
    all_rows = execution_list + snapshot_list + api_error_list + operator_list + telegram_list
    error_source_rows = snapshot_list + execution_list + api_error_list

    execution_c_status = _latest_value(execution_list, "execution_c_status", execution_c_input_status)
    validation_decision = _latest_value(execution_list, "validation_decision", execution_c_input_status)
    snapshot_status = _latest_value(snapshot_list, "snapshot_status", snapshot_input_status)
    effective_market_data_type = _latest_value(snapshot_list, "effective_market_data_type", "unknown")
    data_delay_flag = _latest_value(snapshot_list, "data_delay_flag", "unavailable")
    operator_packet_status = _latest_value(operator_list, "operator_packet_status", operator_packet_input_status)

    operator_review_ready_count = _count_unique_symbols(
        operator_list,
        ("operator_packet_status",),
        ("OPERATOR_REVIEW_READY",),
        fallback_prefix="operator_ready",
    )
    operator_review_blocked_count = _count_unique_symbols(
        operator_list,
        ("operator_packet_status",),
        ("OPERATOR_REVIEW_BLOCKED",),
        fallback_prefix="operator_blocked",
    )
    delayed_reference_count = _count_unique_symbols(
        snapshot_list + operator_list,
        ("effective_market_data_type", "data_delay_flag", "final_research_bucket"),
        ("delayed", "delayed_reference"),
        fallback_prefix="delayed_reference",
    )
    delayed_frozen_reference_count = _count_unique_symbols(
        snapshot_list + operator_list,
        ("effective_market_data_type", "data_delay_flag", "final_research_bucket"),
        ("delayed_frozen", "stale_reference"),
        fallback_prefix="delayed_frozen_reference",
    )
    unsupported_count = _count_unique_symbols(
        snapshot_list + operator_list,
        ("snapshot_status", "effective_market_data_type", "final_research_bucket", "operator_packet_status"),
        ("unsupported", "UNSUPPORTED"),
        fallback_prefix="unsupported",
    )
    no_go_count = _count_unique_symbols(
        operator_list + execution_list,
        ("final_research_bucket", "operator_packet_status", "validation_decision"),
        ("no_go", "NO_GO"),
        fallback_prefix="no_go",
    )

    errors = _error_codes(error_source_rows)
    error_10089_detected = _contains_error(error_source_rows, "10089")
    error_354_detected = _contains_error(error_source_rows, "354")
    delayed_available_detected = _contains_delayed_available_signal(error_source_rows)
    live_subscription_status = (
        LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE
        if delayed_available_detected
        else "LIVE_SUBSCRIPTION_STATUS_NOT_DETECTED"
    )

    reference_only_status = "NO_REFERENCE_PRICE"
    if _lower(snapshot_status) == "delayed_snapshot_returned" or _lower(effective_market_data_type) == "delayed" or _lower(data_delay_flag) == "delayed":
        reference_only_status = "DELAYED_REFERENCE_ONLY"
    elif _lower(effective_market_data_type) == "delayed_frozen" or _lower(data_delay_flag) == "delayed_frozen":
        reference_only_status = "DELAYED_FROZEN_REFERENCE_ONLY"

    input_statuses = (
        execution_c_input_status,
        snapshot_input_status,
        operator_packet_input_status,
        telegram_notification_input_status,
    )
    missing_or_empty = any(status != "present" for status in input_statuses)
    safety_flags = _safety_anomalies(all_rows)
    ready_reference = (
        execution_c_status == "EXECUTION_C_VALIDATION_READY"
        and validation_decision == "REVIEW_READY_REFERENCE_ONLY"
    )

    if safety_flags:
        post_run_status = "POST_RUN_FAILED_SAFE"
        analysis_decision = "FAILED_SAFE_REVIEW"
        semantic_status = "FAILED_SAFE"
        analysis_reason = "safety marker anomaly detected in local post-run inputs"
        next_step = "stop_and_review_safety_flags"
    elif missing_or_empty:
        post_run_status = "POST_RUN_BLOCKED"
        analysis_decision = "BLOCK_POST_RUN_REVIEW"
        semantic_status = "GLOBAL_NO_GO_AND_BLOCKED"
        analysis_reason = "one or more required local post-run input files are missing or empty"
        next_step = "regenerate_or_restore_operator_run_outputs_before_review"
    elif ready_reference:
        post_run_status = "POST_RUN_REFERENCE_READY"
        analysis_decision = "ACCEPT_REFERENCE_ONLY_RUN"
        semantic_status = "GLOBAL_NO_TRADE_BUT_OPERATOR_REVIEW_READY"
        analysis_reason = "Execution C returned reference-only delayed or delayed_frozen data for manual review"
        next_step = "manual_operator_review_reference_only_summary"
    else:
        post_run_status = "POST_RUN_BLOCKED"
        analysis_decision = "BLOCK_POST_RUN_REVIEW"
        semantic_status = "GLOBAL_NO_GO_AND_BLOCKED"
        analysis_reason = "Execution C inputs do not show REVIEW_READY_REFERENCE_ONLY"
        next_step = "review_execution_c_packet_and_snapshot_report"

    return FirstOperatorRunPostAnalysisDecision(
        post_run_status=post_run_status,
        post_run_mode="local_runtime_outputs_only",
        execution_c_input_status=execution_c_input_status,
        snapshot_input_status=snapshot_input_status,
        operator_packet_input_status=operator_packet_input_status,
        telegram_notification_input_status=telegram_notification_input_status,
        execution_c_status=execution_c_status,
        validation_decision=validation_decision,
        snapshot_status=snapshot_status,
        effective_market_data_type=effective_market_data_type,
        data_delay_flag=data_delay_flag,
        operator_packet_status=operator_packet_status,
        operator_review_ready_count=str(operator_review_ready_count),
        operator_review_blocked_count=str(operator_review_blocked_count),
        delayed_reference_count=str(delayed_reference_count),
        delayed_frozen_reference_count=str(delayed_frozen_reference_count),
        unsupported_count=str(unsupported_count),
        no_go_count=str(no_go_count),
        error_codes_detected=",".join(errors),
        error_10089_detected=TRUE_TEXT if error_10089_detected else FALSE_TEXT,
        error_354_detected=TRUE_TEXT if error_354_detected else FALSE_TEXT,
        live_subscription_status=live_subscription_status,
        reference_only_status=reference_only_status,
        global_no_trade_status="ACTION_ALLOWED_FALSE_CONFIRMED",
        semantic_status=semantic_status,
        analysis_decision=analysis_decision,
        analysis_reason=analysis_reason,
        action_allowed=FALSE_TEXT,
        broker_execution_triggered=FALSE_TEXT,
        historical_data_request_triggered=FALSE_TEXT,
        account_read_triggered=FALSE_TEXT,
        position_read_triggered=FALSE_TEXT,
        telegram_send_triggered=FALSE_TEXT,
        manual_review_required=TRUE_TEXT,
        safety_flags=",".join(safety_flags),
        next_step=next_step,
    )


def write_post_analysis_csv(path: str | Path, decision: FirstOperatorRunPostAnalysisDecision) -> None:
    fields = list(FirstOperatorRunPostAnalysisDecision.__dataclass_fields__.keys())
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerow([getattr(decision, field) for field in fields])


def write_post_analysis_report(path: str | Path, decision: FirstOperatorRunPostAnalysisDecision) -> None:
    Path(path).write_text(_build_report_text(decision), encoding="utf-8")


def write_first_operator_run_summary(path: str | Path, decision: FirstOperatorRunPostAnalysisDecision) -> None:
    Path(path).write_text(_build_summary_text(decision), encoding="utf-8")


def build_decision_from_files(
    *,
    execution_c_packet: str | Path,
    snapshot_csv: str | Path,
    snapshot_report: str | Path,
    api_errors_csv: Optional[str | Path],
    operator_packet: str | Path,
    telegram_notification_packet: str | Path,
) -> FirstOperatorRunPostAnalysisDecision:
    execution_status, execution_rows = read_csv_rows(Path(execution_c_packet))
    snapshot_status, snapshot_rows = read_csv_rows(Path(snapshot_csv))
    api_errors_path = Path(api_errors_csv) if api_errors_csv else _default_api_errors_csv()
    _, api_error_rows = read_csv_rows(api_errors_path)
    operator_status, operator_rows = read_csv_rows(Path(operator_packet))
    telegram_status, telegram_rows = read_csv_rows(Path(telegram_notification_packet))

    report_path = Path(snapshot_report)
    if report_path.exists():
        report_rows = []
        for line in report_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            lowered = stripped.lower()
            cells = [cell.strip() for cell in stripped.strip("|").split("|")] if stripped.startswith("|") else []
            table_code = next((cell for cell in cells if cell in {"10089", "354"}), "")
            if table_code:
                report_rows.append({"error_code": table_code, "error_message": stripped, "action_allowed": "false"})
            elif (
                ("error 10089" in lowered or "error 354" in lowered)
                and ("delayed market data available" in lowered or "延迟市场数据可用" in stripped)
            ):
                report_rows.append({"report_text": stripped, "action_allowed": "false"})
        snapshot_rows = list(snapshot_rows) + report_rows

    return build_first_operator_run_post_analysis_decision(
        execution_c_rows=execution_rows,
        snapshot_rows=snapshot_rows,
        api_error_rows=api_error_rows,
        operator_rows=operator_rows,
        telegram_notification_rows=telegram_rows,
        execution_c_input_status=execution_status,
        snapshot_input_status=snapshot_status,
        operator_packet_input_status=operator_status,
        telegram_notification_input_status=telegram_status,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build first operator-run post analysis from local offline artifacts.")
    parser.add_argument("--execution-c-packet", default="ibkr_execution_c_validation_packet.csv")
    parser.add_argument("--snapshot-csv", default="ibkr_market_data_snapshot.csv")
    parser.add_argument("--snapshot-report", default="reports/ibkr_market_data_snapshot_report.md")
    parser.add_argument("--api-errors-csv", default=None)
    parser.add_argument("--operator-packet", default="ibkr_daily_operator_packet.csv")
    parser.add_argument("--telegram-notification-packet", default="ibkr_telegram_notification_packet.csv")
    parser.add_argument("--output-csv", default="first_operator_run_post_analysis.csv")
    parser.add_argument("--output-report", default="reports/first_operator_run_post_analysis_report.md")
    parser.add_argument("--summary-md", default="reports/first_operator_run_summary.md")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    output_report = Path(args.output_report)
    summary_md = Path(args.summary_md)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    summary_md.parent.mkdir(parents=True, exist_ok=True)

    print("[INFO] First operator-run post analysis started")

    decision = build_decision_from_files(
        execution_c_packet=args.execution_c_packet,
        snapshot_csv=args.snapshot_csv,
        snapshot_report=args.snapshot_report,
        api_errors_csv=args.api_errors_csv,
        operator_packet=args.operator_packet,
        telegram_notification_packet=args.telegram_notification_packet,
    )

    write_post_analysis_csv(Path(args.output_csv), decision)
    write_post_analysis_report(output_report, decision)
    write_first_operator_run_summary(summary_md, decision)

    print("[PASS] First operator-run post analysis generated")
    print(f"post_run_status={decision.post_run_status}")
    print(f"analysis_decision={decision.analysis_decision}")
    print(f"semantic_status={decision.semantic_status}")
    print(f"execution_c_status={decision.execution_c_status}")
    print(f"validation_decision={decision.validation_decision}")
    print(f"snapshot_status={decision.snapshot_status}")
    print(f"effective_market_data_type={decision.effective_market_data_type}")
    print(f"data_delay_flag={decision.data_delay_flag}")
    print(f"operator_review_ready_count={decision.operator_review_ready_count}")
    print(f"delayed_reference_count={decision.delayed_reference_count}")
    print(f"error_codes_detected={decision.error_codes_detected}")
    print(f"error_10089_detected={decision.error_10089_detected}")
    print(f"error_354_detected={decision.error_354_detected}")
    print(f"live_subscription_status={decision.live_subscription_status}")
    print("action_allowed=false")
    print("broker_execution_triggered=false")
    print("historical_data_request_triggered=false")
    print("account_read_triggered=false")
    print("position_read_triggered=false")
    print("telegram_send_triggered=false")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    print(f"summary={args.summary_md}")
    return 0


def _build_report_text(decision: FirstOperatorRunPostAnalysisDecision) -> str:
    return "\n".join(
        [
            "# First Operator Run Post Analysis Report",
            "",
            "## First Operator Run Decision",
            "",
            "| field | value |",
            "|---|---|",
            f"| post_run_status | {decision.post_run_status} |",
            f"| analysis_decision | {decision.analysis_decision} |",
            f"| semantic_status | {decision.semantic_status} |",
            f"| analysis_reason | {decision.analysis_reason} |",
            f"| next_step | {decision.next_step} |",
            "| action_allowed | false |",
            "",
            "## Execution C Result",
            "",
            f"- execution_c_input_status={decision.execution_c_input_status}",
            f"- execution_c_status={decision.execution_c_status}",
            f"- validation_decision={decision.validation_decision}",
            "- REVIEW_READY_REFERENCE_ONLY means manual review can inspect reference context only.",
            "",
            "## Market Data Delay / Subscription Interpretation",
            "",
            f"- snapshot_input_status={decision.snapshot_input_status}",
            f"- snapshot_status={decision.snapshot_status}",
            f"- effective_market_data_type={decision.effective_market_data_type}",
            f"- data_delay_flag={decision.data_delay_flag}",
            f"- reference_only_status={decision.reference_only_status}",
            "- delayed reference-only data cannot trigger trade decisions or broker execution.",
            "",
            "## Error 10089 / 354 Interpretation",
            "",
            f"- error_codes_detected={decision.error_codes_detected}",
            f"- error_10089_detected={decision.error_10089_detected}",
            f"- error_354_detected={decision.error_354_detected}",
            f"- live_subscription_status={decision.live_subscription_status}",
            "- Error 10089 and Error 354 are recognizable live subscription missing / delayed data available scenarios when delayed data is available.",
            "",
            "## Operator Packet Summary",
            "",
            f"- operator_packet_input_status={decision.operator_packet_input_status}",
            f"- operator_packet_status={decision.operator_packet_status}",
            f"- operator_review_ready_count={decision.operator_review_ready_count}",
            f"- operator_review_blocked_count={decision.operator_review_blocked_count}",
            f"- delayed_reference_count={decision.delayed_reference_count}",
            f"- delayed_frozen_reference_count={decision.delayed_frozen_reference_count}",
            f"- unsupported_count={decision.unsupported_count}",
            f"- no_go_count={decision.no_go_count}",
            "- Reference-ready counts are normalized by display_symbol across local input files.",
            "",
            "## NO_GO vs REVIEW_READY Semantics",
            "",
            "- NO_GO is not a pipeline failure in this project.",
            "- Global NO_GO means action_allowed=false / no trade.",
            "- Row-level OPERATOR_REVIEW_READY means the operator can manually review reference-only results.",
            "- Delayed reference data is not a real-time trading signal.",
            "",
            "## Telegram Dry-run Summary",
            "",
            f"- telegram_notification_input_status={decision.telegram_notification_input_status}",
            "- telegram_send_triggered=false",
            "- Telegram credential values are not read by this post-run analysis.",
            "",
            "## Safety Confirmation",
            "",
            "- action_allowed=false",
            "- broker_execution_triggered=false",
            "- historical_data_request_triggered=false",
            "- account_read_triggered=false",
            "- position_read_triggered=false",
            "- telegram_send_triggered=false",
            "- manual_review_required=true",
            f"- safety_flags={decision.safety_flags}",
            "",
            "## Next Step",
            "",
            f"- {decision.next_step}",
        ]
    ) + "\n"


def _build_summary_text(decision: FirstOperatorRunPostAnalysisDecision) -> str:
    return "\n".join(
        [
            "# First Operator Run Summary",
            "",
            f"- post_run_status={decision.post_run_status}",
            f"- analysis_decision={decision.analysis_decision}",
            f"- semantic_status={decision.semantic_status}",
            f"- execution_c_status={decision.execution_c_status}",
            f"- validation_decision={decision.validation_decision}",
            f"- snapshot_status={decision.snapshot_status}",
            f"- effective_market_data_type={decision.effective_market_data_type}",
            f"- data_delay_flag={decision.data_delay_flag}",
            f"- operator_review_ready_count={decision.operator_review_ready_count}",
            f"- live_subscription_status={decision.live_subscription_status}",
            "- NO_GO means no trade; OPERATOR_REVIEW_READY means manual reference-only review.",
            "- delayed reference-only data cannot trigger trade.",
            "- action_allowed=false",
            "- broker_execution_triggered=false",
            "- historical_data_request_triggered=false",
            "- account_read_triggered=false",
            "- position_read_triggered=false",
            "- telegram_send_triggered=false",
            f"- next_step={decision.next_step}",
        ]
    ) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
