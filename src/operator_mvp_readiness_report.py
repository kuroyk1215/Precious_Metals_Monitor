from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

READINESS_SOURCES = (
    "operator_daily_master_run_summary.csv",
    "operator_continuity_archive_index.csv",
    "operator_real_market_mvp_status.csv",
    "operator_strategy_quality_report.csv",
    "operator_real_market_mvp_regression.csv",
)

READINESS_FIELDS = (
    "generated_at",
    "readiness_status",
    "source_files_present",
    "missing_sources",
    "master_status",
    "continuity_status",
    "mvp_status",
    "strategy_quality_status",
    "regression_status",
    "safety_clean",
    "real_quote_available",
    "safe_unavailable",
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
    )
    for row in rows:
        for field in fields:
            if field in row and not _is_false(row.get(field)):
                return False
    return True


def build_readiness_row(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    base = Path(base_dir)
    present = [name for name in READINESS_SOURCES if (base / name).exists()]
    missing = [name for name in READINESS_SOURCES if name not in present]
    master = _latest(base / "operator_daily_master_run_summary.csv")
    continuity = _latest(base / "operator_continuity_archive_index.csv")
    mvp = _latest(base / "operator_real_market_mvp_status.csv")
    quality = _latest(base / "operator_strategy_quality_report.csv")
    regression = _latest(base / "operator_real_market_mvp_regression.csv")
    rows = [master, continuity, mvp, quality, regression]
    safety_clean = _safety_clean([row for row in rows if row])
    real_quote_available = any(_is_true(row.get("real_quote_available")) for row in rows)
    safe_unavailable = any(
        _is_true(row.get("safe_unavailable"))
        or row.get("master_status") == "MASTER_SAFE_UNAVAILABLE"
        or row.get("mvp_status") == "MVP_SAFE_UNAVAILABLE"
        or row.get("quality_status") == "DATA_UNAVAILABLE_BUT_SAFE"
        for row in rows
    )

    master_status = master.get("master_status", "MISSING")
    continuity_status = continuity.get("continuity_status", "MISSING")
    mvp_status = mvp.get("mvp_status", "MISSING")
    quality_status = quality.get("quality_status", "MISSING")
    regression_status = regression.get("regression_status", "MISSING")

    if missing:
        readiness_status = "MVP_MISSING_SOURCE"
        reason = "missing_sources:" + ",".join(missing)
        next_step = "generate_missing_readiness_sources"
    elif not safety_clean:
        readiness_status = "MVP_BLOCKED"
        reason = "forbidden_action_or_read_field_detected"
        next_step = "stop_and_review_safety_boundary"
    elif safe_unavailable and not real_quote_available:
        readiness_status = "MVP_SAFE_UNAVAILABLE"
        reason = "real_quote_unavailable_but_safety_clean"
        next_step = "continue_daily_collection_review_connection_permission"
    elif regression_status == "FAIL" or master_status == "MASTER_BLOCKED":
        readiness_status = "MVP_BLOCKED"
        reason = "regression_or_master_blocked"
        next_step = "review_regression_and_master_outputs"
    elif real_quote_available and regression_status in {"PASS", "SKIPPED"}:
        readiness_status = "MVP_READY_FOR_DAILY_USE"
        reason = "real_quote_available_safety_clean_manual_review_only"
        next_step = "daily_manual_review_only"
    else:
        readiness_status = "MVP_REVIEW_REQUIRED"
        reason = "sources_present_but_readiness_not_decisive"
        next_step = "manual_review_readiness_sources"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "readiness_status": readiness_status,
        "source_files_present": ",".join(present) if present else "none",
        "missing_sources": ",".join(missing) if missing else "none",
        "master_status": master_status,
        "continuity_status": continuity_status,
        "mvp_status": mvp_status,
        "strategy_quality_status": quality_status,
        "regression_status": regression_status,
        "safety_clean": TRUE_TEXT if safety_clean else FALSE_TEXT,
        "real_quote_available": TRUE_TEXT if real_quote_available else FALSE_TEXT,
        "safe_unavailable": TRUE_TEXT if safe_unavailable else FALSE_TEXT,
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


def write_readiness_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(READINESS_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Operator MVP Readiness Report",
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
            "## Readiness",
            "",
            f"- readiness_status={row['readiness_status']}",
            f"- safety_clean={row['safety_clean']}",
            f"- real_quote_available={row['real_quote_available']}",
            f"- safe_unavailable={row['safe_unavailable']}",
            f"- master_status={row['master_status']}",
            f"- continuity_status={row['continuity_status']}",
            f"- mvp_status={row['mvp_status']}",
            f"- strategy_quality_status={row['strategy_quality_status']}",
            f"- regression_status={row['regression_status']}",
            f"- diagnostic_reason={row['diagnostic_reason']}",
            f"- operator_next_step={row['operator_next_step']}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_mvp_readiness_report(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_mvp_readiness_report.csv",
    output_report: PathLike = "reports/operator_mvp_readiness_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_readiness_row(base_dir=base_dir, generated_at=generated_at)
    write_readiness_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 458 final MVP readiness report.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_mvp_readiness_report.csv")
    parser.add_argument("--output-report", default="reports/operator_mvp_readiness_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_mvp_readiness_report(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator MVP readiness report generated")
    print(f"readiness_status={row['readiness_status']}:safety_clean={row['safety_clean']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
