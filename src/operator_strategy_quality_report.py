from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

STRATEGY_QUALITY_FIELDS = (
    "generated_at",
    "quality_status",
    "data_available",
    "data_unavailable_but_safe",
    "insufficient_history",
    "signal_insufficient",
    "manual_review_only",
    "archive_status_consistency",
    "threshold_statuses",
    "mvp_status",
    "diagnostic_reason",
    "operator_next_step",
    "auto_trade_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "telegram_real_send_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_rows(path: PathLike) -> List[Dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _latest(path: PathLike) -> Dict[str, str]:
    rows = _read_rows(path)
    return rows[-1] if rows else {}


def _is_true(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def build_strategy_quality_row(
    *,
    archive_compare_csv: PathLike = "operator_real_market_archive_compare.csv",
    threshold_explainer_csv: PathLike = "operator_signal_threshold_explainer.csv",
    mvp_status_csv: PathLike = "operator_real_market_mvp_status.csv",
    daily_report_csv: PathLike = "operator_daily_real_market_report.csv",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    archive = _latest(archive_compare_csv)
    threshold_rows = _read_rows(threshold_explainer_csv)
    mvp = _latest(mvp_status_csv)
    daily_rows = _read_rows(daily_report_csv)

    threshold_statuses = sorted({row.get("threshold_status", "SIGNAL_INSUFFICIENT_DATA") for row in threshold_rows})
    mvp_status = mvp.get("mvp_status", "MVP_STATUS_MISSING")
    archive_consistency = archive.get("status_consistency", "ARCHIVE_COMPARE_MISSING")
    data_available = any(row.get("real_quote_state") == "REAL_QUOTE_AVAILABLE" for row in daily_rows) or _is_true(mvp.get("real_quote_available"))
    data_unavailable_but_safe = any(row.get("safe_unavailable") == TRUE_TEXT for row in daily_rows) or _is_true(mvp.get("safe_unavailable"))
    insufficient_history = archive_consistency == "INSUFFICIENT_HISTORY"
    signal_insufficient = not threshold_rows or any(status in {"SIGNAL_INSUFFICIENT_DATA", "HOLD_NO_REAL_QUOTE"} for status in threshold_statuses)
    manual_review_only = True

    if data_available and not signal_insufficient:
        quality_status = "DATA_AVAILABLE_MANUAL_REVIEW_ONLY"
        reason = "data_available_threshold_context_observation_only"
        next_step = "manual_review_strategy_quality_context"
    elif data_unavailable_but_safe:
        quality_status = "DATA_UNAVAILABLE_BUT_SAFE"
        reason = "real_quote_unavailable_but_forbidden_actions_remain_false"
        next_step = "review_connection_permission_continue_collection"
    elif insufficient_history:
        quality_status = "INSUFFICIENT_HISTORY"
        reason = "archive_compare_has_single_run_or_missing_history"
        next_step = "continue_daily_collection"
    elif signal_insufficient:
        quality_status = "SIGNAL_INSUFFICIENT"
        reason = "threshold_explainer_reports_insufficient_signal_context"
        next_step = "regenerate_signal_sources_before_strategy_review"
    else:
        quality_status = "MANUAL_REVIEW_ONLY"
        reason = "strategy_quality_requires_manual_review"
        next_step = "manual_review_only"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "quality_status": quality_status,
        "data_available": TRUE_TEXT if data_available else FALSE_TEXT,
        "data_unavailable_but_safe": TRUE_TEXT if data_unavailable_but_safe else FALSE_TEXT,
        "insufficient_history": TRUE_TEXT if insufficient_history else FALSE_TEXT,
        "signal_insufficient": TRUE_TEXT if signal_insufficient else FALSE_TEXT,
        "manual_review_only": TRUE_TEXT if manual_review_only else FALSE_TEXT,
        "archive_status_consistency": archive_consistency,
        "threshold_statuses": "|".join(threshold_statuses) if threshold_statuses else "SIGNAL_INSUFFICIENT_DATA",
        "mvp_status": mvp_status,
        "diagnostic_reason": reason,
        "operator_next_step": next_step,
        "auto_trade_allowed": FALSE_TEXT,
        "account_read_allowed": FALSE_TEXT,
        "position_read_allowed": FALSE_TEXT,
        "historical_data_request_allowed": FALSE_TEXT,
        "telegram_real_send_allowed": FALSE_TEXT,
        "order_action_allowed": FALSE_TEXT,
        "cancel_action_allowed": FALSE_TEXT,
        "rebalance_action_allowed": FALSE_TEXT,
    }


def write_strategy_quality_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(STRATEGY_QUALITY_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Operator Strategy Quality Report",
            "",
            "## Safety Banner",
            "",
            "- no auto trading",
            "- no account reads",
            "- no position reads",
            "- no historical data requests",
            "- no Telegram real send",
            "- no order/cancel/rebalance",
            "",
            "## Quality Categories",
            "",
            f"- data available={row['data_available']}",
            f"- data unavailable but safe={row['data_unavailable_but_safe']}",
            f"- insufficient history={row['insufficient_history']}",
            f"- signal insufficient={row['signal_insufficient']}",
            f"- manual review only={row['manual_review_only']}",
            "",
            "## Strategy Quality",
            "",
            f"- quality_status={row['quality_status']}",
            f"- archive_status_consistency={row['archive_status_consistency']}",
            f"- threshold_statuses={row['threshold_statuses']}",
            f"- mvp_status={row['mvp_status']}",
            f"- diagnostic_reason={row['diagnostic_reason']}",
            f"- operator_next_step={row['operator_next_step']}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_strategy_quality_report(
    *,
    archive_compare_csv: PathLike = "operator_real_market_archive_compare.csv",
    threshold_explainer_csv: PathLike = "operator_signal_threshold_explainer.csv",
    mvp_status_csv: PathLike = "operator_real_market_mvp_status.csv",
    daily_report_csv: PathLike = "operator_daily_real_market_report.csv",
    output_csv: PathLike = "operator_strategy_quality_report.csv",
    output_report: PathLike = "reports/operator_strategy_quality_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_strategy_quality_row(
        archive_compare_csv=archive_compare_csv,
        threshold_explainer_csv=threshold_explainer_csv,
        mvp_status_csv=mvp_status_csv,
        daily_report_csv=daily_report_csv,
        generated_at=generated_at,
    )
    write_strategy_quality_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 455 strategy quality report.")
    parser.add_argument("--archive-compare-csv", default="operator_real_market_archive_compare.csv")
    parser.add_argument("--threshold-explainer-csv", default="operator_signal_threshold_explainer.csv")
    parser.add_argument("--mvp-status-csv", default="operator_real_market_mvp_status.csv")
    parser.add_argument("--daily-report-csv", default="operator_daily_real_market_report.csv")
    parser.add_argument("--output-csv", default="operator_strategy_quality_report.csv")
    parser.add_argument("--output-report", default="reports/operator_strategy_quality_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_strategy_quality_report(
        archive_compare_csv=args.archive_compare_csv,
        threshold_explainer_csv=args.threshold_explainer_csv,
        mvp_status_csv=args.mvp_status_csv,
        daily_report_csv=args.daily_report_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator strategy quality report generated")
    print(f"quality_status={row['quality_status']}:manual_review_only={row['manual_review_only']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
