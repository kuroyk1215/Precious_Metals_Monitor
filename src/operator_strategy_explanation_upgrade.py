from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

EXPLANATION_FIELDS = (
    "generated_at",
    "symbol",
    "explanation_status",
    "spread_observation_status",
    "range_status",
    "strategy_quality_status",
    "readiness_status",
    "manual_review_required",
    "strategy_explanation",
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


def _symbol(row: Dict[str, str]) -> str:
    return str(row.get("symbol") or row.get("display_symbol") or "").strip().upper()


def _symbols(rows: Sequence[Dict[str, str]]) -> List[str]:
    seen = {_symbol(row) for row in rows if _symbol(row)}
    if not seen:
        seen = {"GLD", "SLV"}
    return sorted(seen)


def _is_true(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _build_explanation_status(
    *,
    spread_status: str,
    range_status: str,
    quality_status: str,
    readiness_status: str,
    safe_unavailable: bool,
) -> tuple[str, str, str, str]:
    if readiness_status in {"MVP_BLOCKED", "MVP_MISSING_SOURCE", "MISSING"}:
        return (
            "WHY_MVP_NOT_READY",
            "mvp_readiness_sources_not_ready_for_daily_use",
            "generate_missing_or_blocked_readiness_sources",
            "MVP readiness is not ready, so the strategy remains manual review only.",
        )
    if safe_unavailable or spread_status == "SAFE_UNAVAILABLE" or range_status == "RANGE_PENDING_NO_REAL_QUOTE":
        return (
            "WHY_HOLD_SAFE_UNAVAILABLE",
            "real_quote_or_spread_context_unavailable_but_safety_flags_false",
            "review_real_marketdata_connection_continue_observation_only",
            "Real-market quote context is unavailable, so the safe outcome is to hold for review without execution.",
        )
    if range_status == "RANGE_INSUFFICIENT_DATA" or quality_status == "SIGNAL_INSUFFICIENT":
        return (
            "WHY_INSUFFICIENT_DATA",
            "range_or_strategy_quality_inputs_are_insufficient",
            "regenerate_real_market_range_and_quality_sources",
            "The strategy explanation lacks enough normalized inputs for a useful observation frame.",
        )
    if range_status == "RANGE_REVIEW_ONLY" or quality_status in {"MANUAL_REVIEW_ONLY", "DATA_AVAILABLE_MANUAL_REVIEW_ONLY"}:
        return (
            "WHY_MANUAL_REVIEW_ONLY",
            "inputs_available_but_policy_requires_manual_review_only",
            "manual_review_strategy_context_only",
            "Inputs support a manual review narrative, but all action permissions remain disabled.",
        )
    return (
        "WHY_OBSERVE_ONLY",
        "observation_framework_available_without_execution_permission",
        "continue_observation_only_daily_review",
        "Spread and range context are available for observation only with no execution path.",
    )


def build_strategy_explanation_rows(
    *,
    spread_framework_csv: PathLike = "operator_gld_slv_spread_framework.csv",
    range_framework_csv: PathLike = "operator_real_market_range_framework.csv",
    strategy_quality_csv: PathLike = "operator_strategy_quality_report.csv",
    mvp_readiness_csv: PathLike = "operator_mvp_readiness_report.csv",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    generated = generated_at or _now_timestamp()
    spread = _latest(spread_framework_csv)
    range_rows = _read_rows(range_framework_csv)
    quality = _latest(strategy_quality_csv)
    readiness = _latest(mvp_readiness_csv)
    spread_status = spread.get("spread_observation_status", "SAFE_UNAVAILABLE")
    quality_status = quality.get("quality_status", "MISSING")
    readiness_status = readiness.get("readiness_status", "MISSING")
    safe_unavailable = _is_true(readiness.get("safe_unavailable")) or quality_status == "DATA_UNAVAILABLE_BUT_SAFE"

    rows: List[Dict[str, str]] = []
    range_by_symbol = {_symbol(row): row for row in range_rows if _symbol(row)}
    for symbol in _symbols(range_rows):
        range_row = range_by_symbol.get(symbol, {})
        range_status = range_row.get("range_status", "RANGE_INSUFFICIENT_DATA")
        status, reason, next_step, explanation = _build_explanation_status(
            spread_status=spread_status,
            range_status=range_status,
            quality_status=quality_status,
            readiness_status=readiness_status,
            safe_unavailable=safe_unavailable,
        )
        rows.append(
            {
                "generated_at": generated,
                "symbol": symbol,
                "explanation_status": status,
                "spread_observation_status": spread_status,
                "range_status": range_status,
                "strategy_quality_status": quality_status,
                "readiness_status": readiness_status,
                "manual_review_required": TRUE_TEXT,
                "strategy_explanation": explanation,
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
        )
    return rows


def write_strategy_explanation_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(EXPLANATION_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(rows: Sequence[Dict[str, str]]) -> str:
    explanation_lines = [
        f"- {row['symbol']}: explanation_status={row['explanation_status']}; range_status={row['range_status']}; manual_review_required={row['manual_review_required']}; auto_trade_allowed={row['auto_trade_allowed']}"
        for row in rows
    ]
    return "\n".join(
        [
            "# Operator Strategy Explanation Upgrade Report",
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
            "## Strategy Explanation",
            "",
            *explanation_lines,
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(rows), encoding="utf-8")


def generate_strategy_explanation_upgrade(
    *,
    spread_framework_csv: PathLike = "operator_gld_slv_spread_framework.csv",
    range_framework_csv: PathLike = "operator_real_market_range_framework.csv",
    strategy_quality_csv: PathLike = "operator_strategy_quality_report.csv",
    mvp_readiness_csv: PathLike = "operator_mvp_readiness_report.csv",
    output_csv: PathLike = "operator_strategy_explanation_upgrade.csv",
    output_report: PathLike = "reports/operator_strategy_explanation_upgrade_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_strategy_explanation_rows(
        spread_framework_csv=spread_framework_csv,
        range_framework_csv=range_framework_csv,
        strategy_quality_csv=strategy_quality_csv,
        mvp_readiness_csv=mvp_readiness_csv,
        generated_at=generated_at,
    )
    write_strategy_explanation_csv(output_csv, rows)
    write_markdown_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 461 observation-only strategy explanation upgrade.")
    parser.add_argument("--spread-framework-csv", default="operator_gld_slv_spread_framework.csv")
    parser.add_argument("--range-framework-csv", default="operator_real_market_range_framework.csv")
    parser.add_argument("--strategy-quality-csv", default="operator_strategy_quality_report.csv")
    parser.add_argument("--mvp-readiness-csv", default="operator_mvp_readiness_report.csv")
    parser.add_argument("--output-csv", default="operator_strategy_explanation_upgrade.csv")
    parser.add_argument("--output-report", default="reports/operator_strategy_explanation_upgrade_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_strategy_explanation_upgrade(
        spread_framework_csv=args.spread_framework_csv,
        range_framework_csv=args.range_framework_csv,
        strategy_quality_csv=args.strategy_quality_csv,
        mvp_readiness_csv=args.mvp_readiness_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator strategy explanation upgrade generated")
    for row in rows:
        print(f"{row['symbol']}:explanation_status={row['explanation_status']}:manual_review_required={row['manual_review_required']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
