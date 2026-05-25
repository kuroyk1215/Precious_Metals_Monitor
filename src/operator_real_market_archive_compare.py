from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

SOURCE_FILES = (
    "operator_real_market_mvp_status.csv",
    "operator_daily_real_market_report.csv",
    "operator_real_quote_normalization.csv",
    "operator_real_quote_signal_bridge.csv",
    "operator_real_marketdata_decision_gate.csv",
)

ARCHIVE_COMPARE_FIELDS = (
    "generated_at",
    "comparison_window",
    "source_files_present",
    "run_count_detected",
    "latest_mvp_status",
    "latest_quote_status",
    "latest_signal_bridge_status",
    "status_consistency",
    "quote_availability_trend",
    "safety_consistency",
    "diagnostic_reason",
    "operator_next_step",
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


def _latest(rows: Sequence[Dict[str, str]]) -> Dict[str, str]:
    return rows[-1] if rows else {}


def _is_false(value: object) -> bool:
    return str(value or "").strip().lower() in {"", "false", "0", "no"}


def _is_true(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _status(row: Dict[str, str], fields: Sequence[str], default: str) -> str:
    for field in fields:
        value = str(row.get(field) or "").strip()
        if value:
            return value
    return default


def _symbol_statuses(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> List[str]:
    values: List[str] = []
    for row in rows:
        value = _status(row, fields, "")
        if value:
            values.append(value)
    return values


def _run_count(groups: Dict[str, List[Dict[str, str]]]) -> int:
    generated_values = {
        row.get("generated_at", "").strip()
        for rows in groups.values()
        for row in rows
        if row.get("generated_at", "").strip()
    }
    max_rows = max((len(rows) for rows in groups.values()), default=0)
    return max(len(generated_values), max_rows)


def _safety_clean(rows: Sequence[Dict[str, str]]) -> bool:
    forbidden_fields = (
        "auto_trade_allowed",
        "account_read_allowed",
        "position_read_allowed",
        "historical_data_request_allowed",
        "telegram_real_send_allowed",
        "telegram_send_allowed",
        "order_action_allowed",
        "cancel_action_allowed",
        "rebalance_action_allowed",
        "broker_execution_triggered",
        "account_read_triggered",
        "position_read_triggered",
        "historical_data_request_triggered",
        "telegram_send_triggered",
    )
    for row in rows:
        for field in forbidden_fields:
            if field in row and not _is_false(row.get(field)):
                return False
    return True


def _quote_trend(quote_rows: Sequence[Dict[str, str]], daily_rows: Sequence[Dict[str, str]]) -> str:
    combined = list(quote_rows) + list(daily_rows)
    if not combined:
        return "NO_QUOTE_HISTORY"
    available = [
        row
        for row in combined
        if row.get("quote_status") == "AVAILABLE"
        or row.get("normalized_status") == "NORMALIZED"
        or row.get("real_quote_state") == "REAL_QUOTE_AVAILABLE"
    ]
    if not available:
        return "NO_REAL_QUOTE_AVAILABLE"
    if len(available) == len(combined):
        return "REAL_QUOTE_AVAILABLE_STABLE"
    return "MIXED_REAL_QUOTE_AVAILABILITY"


def build_archive_compare_row(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    base = Path(base_dir)
    groups = {name: _read_rows(base / name) for name in SOURCE_FILES}
    present = [name for name in SOURCE_FILES if (base / name).exists()]
    missing = [name for name in SOURCE_FILES if name not in present]
    run_count = _run_count(groups)

    mvp = _latest(groups["operator_real_market_mvp_status.csv"])
    daily_rows = groups["operator_daily_real_market_report.csv"]
    quote_rows = groups["operator_real_quote_normalization.csv"]
    bridge_rows = groups["operator_real_quote_signal_bridge.csv"]
    decision = _latest(groups["operator_real_marketdata_decision_gate.csv"])
    all_rows = [row for rows in groups.values() for row in rows]

    latest_mvp_status = _status(mvp, ("mvp_status", "latest_status"), "MISSING")
    quote_statuses = _symbol_statuses(daily_rows or quote_rows, ("real_quote_state", "quote_status", "normalized_status"))
    bridge_statuses = _symbol_statuses(bridge_rows, ("signal_bridge_status",))
    latest_quote_status = "|".join(quote_statuses) if quote_statuses else "MISSING"
    latest_bridge_status = "|".join(bridge_statuses) if bridge_statuses else "MISSING"
    safety = "SAFETY_CONSISTENT_FALSE_ACTIONS" if _safety_clean(all_rows) else "SAFETY_REVIEW_REQUIRED"

    if run_count <= 1:
        comparison_window = "SINGLE_RUN"
        status_consistency = "INSUFFICIENT_HISTORY"
        reason = "single_run_detected_multi_day_comparison_pending"
        next_step = "continue_daily_collection"
    elif missing:
        comparison_window = "MULTI_RUN_PARTIAL"
        status_consistency = "SOURCE_GAP_REVIEW_REQUIRED"
        reason = "missing_source_files:" + ",".join(missing)
        next_step = "regenerate_missing_operator_outputs"
    elif safety != "SAFETY_CONSISTENT_FALSE_ACTIONS":
        comparison_window = "MULTI_RUN"
        status_consistency = "SAFETY_REVIEW_REQUIRED"
        reason = "forbidden_action_or_read_flag_detected"
        next_step = "stop_and_review_safety_boundary"
    else:
        comparison_window = "MULTI_RUN"
        stable_values = {latest_mvp_status, latest_quote_status, latest_bridge_status, _status(decision, ("operator_decision",), "MISSING")}
        status_consistency = "CONSISTENT_OBSERVATION_STATE" if "MISSING" not in stable_values else "SOURCE_GAP_REVIEW_REQUIRED"
        reason = "multi_run_sources_compared_observation_only"
        next_step = "review_archive_trend_for_manual_strategy_context"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "comparison_window": comparison_window,
        "source_files_present": ",".join(present) if present else "none",
        "run_count_detected": str(run_count),
        "latest_mvp_status": latest_mvp_status,
        "latest_quote_status": latest_quote_status,
        "latest_signal_bridge_status": latest_bridge_status,
        "status_consistency": status_consistency,
        "quote_availability_trend": _quote_trend(quote_rows, daily_rows),
        "safety_consistency": safety,
        "diagnostic_reason": reason,
        "operator_next_step": next_step,
    }


def write_archive_compare_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(ARCHIVE_COMPARE_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Operator Real Market Archive Compare Report",
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
            "## Comparison",
            "",
            f"- comparison_window={row['comparison_window']}",
            f"- run_count_detected={row['run_count_detected']}",
            f"- latest_mvp_status={row['latest_mvp_status']}",
            f"- latest_quote_status={row['latest_quote_status']}",
            f"- latest_signal_bridge_status={row['latest_signal_bridge_status']}",
            f"- status_consistency={row['status_consistency']}",
            f"- quote_availability_trend={row['quote_availability_trend']}",
            f"- safety_consistency={row['safety_consistency']}",
            f"- diagnostic_reason={row['diagnostic_reason']}",
            f"- operator_next_step={row['operator_next_step']}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_archive_compare(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_real_market_archive_compare.csv",
    output_report: PathLike = "reports/operator_real_market_archive_compare_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_archive_compare_row(base_dir=base_dir, generated_at=generated_at)
    write_archive_compare_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 453 real-market archive comparison.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_real_market_archive_compare.csv")
    parser.add_argument("--output-report", default="reports/operator_real_market_archive_compare_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_archive_compare(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator real-market archive compare generated")
    print(f"comparison_window={row['comparison_window']}:status_consistency={row['status_consistency']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
