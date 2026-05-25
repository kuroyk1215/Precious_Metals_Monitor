from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

FINAL_PACKET_SOURCES = (
    "operator_daily_master_run_summary.csv",
    "operator_mvp_readiness_report.csv",
    "operator_strategy_explanation_upgrade.csv",
    "operator_strategy_quality_report.csv",
    "operator_daily_checklist.csv",
    "operator_real_market_mvp_status.csv",
)

FINAL_PACKET_FIELDS = (
    "generated_at",
    "final_packet_status",
    "source_files_present",
    "missing_sources",
    "current_readiness",
    "strategy_explanation",
    "quote_availability",
    "safety_status",
    "manual_review_status",
    "operator_next_step",
    "diagnostic_reason",
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


def _is_false(value: object) -> bool:
    return str(value or "").strip().lower() in {"false", "0", "no", ""}


def _safety_clean(rows: Sequence[Dict[str, str]]) -> bool:
    fields = (
        "auto_trade_allowed",
        "account_read_allowed",
        "position_read_allowed",
        "historical_data_request_allowed",
        "telegram_send_allowed",
        "telegram_real_send_allowed",
        "order_action_allowed",
        "cancel_action_allowed",
        "rebalance_action_allowed",
        "trading_actions_allowed",
        "broker_execution_triggered",
    )
    for row in rows:
        for field in fields:
            if field in row and not _is_false(row.get(field)):
                return False
    return True


def _manual_review_required(rows: Sequence[Dict[str, str]]) -> bool:
    return any(
        _is_true(row.get("manual_review_required"))
        or _is_true(row.get("manual_review_only"))
        or str(row.get("readiness_status", "")).endswith("SAFE_UNAVAILABLE")
        or str(row.get("mvp_status", "")).endswith("SAFE_UNAVAILABLE")
        for row in rows
    )


def _quote_available(rows: Sequence[Dict[str, str]]) -> bool:
    return any(_is_true(row.get("real_quote_available")) or row.get("quote_status") == "AVAILABLE" for row in rows)


def _safe_unavailable(rows: Sequence[Dict[str, str]]) -> bool:
    markers = {
        "MASTER_SAFE_UNAVAILABLE",
        "MVP_SAFE_UNAVAILABLE",
        "DATA_UNAVAILABLE_BUT_SAFE",
        "SAFE_UNAVAILABLE",
        "WHY_HOLD_SAFE_UNAVAILABLE",
    }
    return any(_is_true(row.get("safe_unavailable")) or markers.intersection(str(value).strip() for value in row.values()) for row in rows)


def build_final_daily_packet_row(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    base = Path(base_dir)
    present = [name for name in FINAL_PACKET_SOURCES if (base / name).exists()]
    missing = [name for name in FINAL_PACKET_SOURCES if name not in present]

    master = _latest(base / "operator_daily_master_run_summary.csv")
    readiness = _latest(base / "operator_mvp_readiness_report.csv")
    explanations = _read_rows(base / "operator_strategy_explanation_upgrade.csv")
    quality = _latest(base / "operator_strategy_quality_report.csv")
    checklist_rows = _read_rows(base / "operator_daily_checklist.csv")
    mvp = _latest(base / "operator_real_market_mvp_status.csv")
    rows: List[Dict[str, str]] = [master, readiness, quality, mvp] + explanations + checklist_rows

    safety_clean = _safety_clean([row for row in rows if row])
    real_quote_available = _quote_available(rows)
    safe_unavailable = _safe_unavailable(rows)
    manual_review = _manual_review_required(rows)
    readiness_status = readiness.get("readiness_status", "MISSING")
    quality_status = quality.get("quality_status", "MISSING")
    mvp_status = mvp.get("mvp_status", "MISSING")
    explanation_statuses = sorted({row.get("explanation_status", "MISSING") for row in explanations}) or ["MISSING"]

    if missing:
        status = "FINAL_PACKET_MISSING_SOURCE"
        reason = "missing_sources:" + ",".join(missing)
        next_step = "generate_missing_final_packet_sources"
    elif not safety_clean:
        status = "FINAL_PACKET_BLOCKED"
        reason = "forbidden_action_or_read_field_detected"
        next_step = "stop_and_review_safety_boundary"
    elif safe_unavailable and not real_quote_available:
        status = "FINAL_PACKET_SAFE_UNAVAILABLE"
        reason = "real_quote_unavailable_but_safety_clean"
        next_step = "review_real_marketdata_connection_continue_observation_only"
    elif readiness_status in {"MVP_BLOCKED", "MVP_MISSING_SOURCE"} or mvp_status.startswith("MVP_BLOCKED"):
        status = "FINAL_PACKET_BLOCKED"
        reason = "mvp_readiness_or_status_blocked"
        next_step = "review_mvp_blocking_sources"
    elif manual_review:
        status = "FINAL_PACKET_REVIEW_REQUIRED"
        reason = "manual_review_required_by_strategy_or_checklist"
        next_step = "manual_review_final_packet"
    else:
        status = "FINAL_PACKET_READY"
        reason = "sources_present_safety_clean_observation_only"
        next_step = "daily_observation_only_review"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "final_packet_status": status,
        "source_files_present": ",".join(present) if present else "none",
        "missing_sources": ",".join(missing) if missing else "none",
        "current_readiness": readiness_status,
        "strategy_explanation": "|".join(explanation_statuses),
        "quote_availability": "REAL_QUOTE_AVAILABLE" if real_quote_available else ("SAFE_UNAVAILABLE" if safe_unavailable else "INSUFFICIENT_DATA"),
        "safety_status": "SAFETY_CLEAN" if safety_clean else "SAFETY_BLOCKED",
        "manual_review_status": "MANUAL_REVIEW_REQUIRED" if manual_review else "MANUAL_REVIEW_NOT_REQUIRED",
        "operator_next_step": next_step,
        "diagnostic_reason": f"{reason};quality_status={quality_status};mvp_status={mvp_status}",
        "auto_trade_allowed": FALSE_TEXT,
        "account_read_allowed": FALSE_TEXT,
        "position_read_allowed": FALSE_TEXT,
        "historical_data_request_allowed": FALSE_TEXT,
        "telegram_real_send_allowed": FALSE_TEXT,
        "order_action_allowed": FALSE_TEXT,
        "cancel_action_allowed": FALSE_TEXT,
        "rebalance_action_allowed": FALSE_TEXT,
    }


def write_final_daily_packet_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(FINAL_PACKET_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Operator Final Daily Packet",
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
            "## Final Packet",
            "",
            f"- final_packet_status={row['final_packet_status']}",
            f"- current readiness: {row['current_readiness']}",
            f"- strategy explanation: {row['strategy_explanation']}",
            f"- quote availability: {row['quote_availability']}",
            f"- safety status: {row['safety_status']}",
            f"- manual review status: {row['manual_review_status']}",
            f"- operator next step: {row['operator_next_step']}",
            f"- diagnostic_reason={row['diagnostic_reason']}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_final_daily_packet(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_final_daily_packet.csv",
    output_report: PathLike = "reports/operator_final_daily_packet.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_final_daily_packet_row(base_dir=base_dir, generated_at=generated_at)
    write_final_daily_packet_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 462 final daily operator packet.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_final_daily_packet.csv")
    parser.add_argument("--output-report", default="reports/operator_final_daily_packet.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_final_daily_packet(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator final daily packet generated")
    print(f"final_packet_status={row['final_packet_status']}:safety_status={row['safety_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
