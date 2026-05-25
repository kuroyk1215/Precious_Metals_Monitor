from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

ALLOWED_THRESHOLD_STATUSES = {
    "OBSERVE_ONLY",
    "HOLD_NO_REAL_QUOTE",
    "MANUAL_REVIEW_REQUIRED",
    "RANGE_FRAMEWORK_PENDING",
    "SIGNAL_INSUFFICIENT_DATA",
}

THRESHOLD_EXPLAINER_FIELDS = (
    "generated_at",
    "symbol",
    "quote_status",
    "normalized_status",
    "signal_bridge_status",
    "threshold_status",
    "threshold_basis",
    "signal_quality",
    "observation_bias",
    "manual_review_required",
    "auto_trade_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
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


def _symbol(row: Dict[str, str]) -> str:
    return str(row.get("symbol") or row.get("display_symbol") or "").strip().upper()


def _index_latest(rows: Sequence[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    indexed: Dict[str, Dict[str, str]] = {}
    for row in rows:
        symbol = _symbol(row)
        if symbol:
            indexed[symbol] = row
    return indexed


def _symbols(*groups: Sequence[Dict[str, str]]) -> List[str]:
    seen = {_symbol(row) for rows in groups for row in rows if _symbol(row)}
    return sorted(seen)


def _plan_basis(row: Dict[str, str]) -> str:
    return (
        row.get("manual_watch_zone")
        or row.get("manual_observation_bias")
        or row.get("research_plan_status")
        or "research_plan_not_available"
    )


def _has_real_quote(quote: Dict[str, str], daily: Dict[str, str]) -> bool:
    return (
        quote.get("quote_status") == "AVAILABLE"
        and quote.get("normalized_status") == "NORMALIZED"
    ) or daily.get("real_quote_state") == "REAL_QUOTE_AVAILABLE"


def _clean_text(value: object) -> str:
    text = str(value or "").strip()
    blocked = {"BUY", "SELL", "ORDER"}
    return " ".join("TRADE_WORD_REDACTED" if part.upper() in blocked else part for part in text.split())


def build_threshold_explainer_rows(
    *,
    signal_bridge_csv: PathLike = "operator_real_quote_signal_bridge.csv",
    normalization_csv: PathLike = "operator_real_quote_normalization.csv",
    daily_report_csv: PathLike = "operator_daily_real_market_report.csv",
    research_plan_csv: PathLike = "research_trading_plan.csv",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    generated = generated_at or _now_timestamp()
    bridge_rows = _read_rows(signal_bridge_csv)
    quote_rows = _read_rows(normalization_csv)
    daily_rows = _read_rows(daily_report_csv)
    plan_rows = _read_rows(research_plan_csv)
    bridge_by_symbol = _index_latest(bridge_rows)
    quote_by_symbol = _index_latest(quote_rows)
    daily_by_symbol = _index_latest(daily_rows)
    plan_by_symbol = _index_latest(plan_rows)

    rows: List[Dict[str, str]] = []
    for symbol in _symbols(bridge_rows, quote_rows, daily_rows, plan_rows):
        bridge = bridge_by_symbol.get(symbol, {})
        quote = quote_by_symbol.get(symbol, {})
        daily = daily_by_symbol.get(symbol, {})
        plan = plan_by_symbol.get(symbol, {})
        quote_status = quote.get("quote_status") or bridge.get("quote_status") or daily.get("quote_status") or "UNAVAILABLE"
        normalized_status = quote.get("normalized_status") or bridge.get("normalized_status") or daily.get("normalized_status") or "SAFE_UNAVAILABLE"
        bridge_status = bridge.get("signal_bridge_status") or daily.get("signal_bridge_status") or "SIGNAL_INSUFFICIENT_DATA"
        basis = _clean_text(_plan_basis(plan))
        real_quote = _has_real_quote(quote, daily)

        if not quote and not bridge and not daily:
            threshold_status = "SIGNAL_INSUFFICIENT_DATA"
            signal_quality = "SOURCE_DATA_MISSING"
            observation_bias = "SIGNAL_INSUFFICIENT_DATA"
            reason = "no_real_market_signal_sources_for_symbol"
            next_step = "regenerate_real_market_operator_chain"
        elif not real_quote:
            threshold_status = "HOLD_NO_REAL_QUOTE" if quote_status == "UNAVAILABLE" else "SIGNAL_INSUFFICIENT_DATA"
            signal_quality = "REAL_QUOTE_UNAVAILABLE"
            observation_bias = "HOLD_NO_REAL_QUOTE"
            reason = quote.get("diagnostic_reason") or bridge.get("diagnostic_reason") or "real_quote_unavailable"
            next_step = "review_real_marketdata_connection"
        elif not plan:
            threshold_status = "RANGE_FRAMEWORK_PENDING"
            signal_quality = "REAL_QUOTE_WITHOUT_RESEARCH_RANGE"
            observation_bias = "RANGE_FRAMEWORK_PENDING"
            reason = "research_plan_threshold_framework_not_available"
            next_step = "generate_research_plan_before_manual_review"
        else:
            threshold_status = "OBSERVE_ONLY"
            signal_quality = "REAL_QUOTE_AND_RESEARCH_RANGE_AVAILABLE"
            observation_bias = _clean_text(plan.get("manual_observation_bias") or "OBSERVE_ONLY")
            reason = "threshold_context_available_for_manual_observation_only"
            next_step = "manual_review_threshold_context_only"

        if threshold_status not in ALLOWED_THRESHOLD_STATUSES:
            threshold_status = "MANUAL_REVIEW_REQUIRED"

        rows.append(
            {
                "generated_at": generated,
                "symbol": symbol,
                "quote_status": quote_status,
                "normalized_status": normalized_status,
                "signal_bridge_status": bridge_status,
                "threshold_status": threshold_status,
                "threshold_basis": basis,
                "signal_quality": signal_quality,
                "observation_bias": observation_bias,
                "manual_review_required": TRUE_TEXT,
                "auto_trade_allowed": FALSE_TEXT,
                "order_action_allowed": FALSE_TEXT,
                "cancel_action_allowed": FALSE_TEXT,
                "rebalance_action_allowed": FALSE_TEXT,
                "diagnostic_reason": _clean_text(reason),
                "operator_next_step": next_step,
            }
        )
    return rows


def write_threshold_explainer_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(THRESHOLD_EXPLAINER_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(rows: Sequence[Dict[str, str]]) -> str:
    lines = [
        f"- {row['symbol']}: threshold_status={row['threshold_status']}; signal_quality={row['signal_quality']}; manual_review_required={row['manual_review_required']}; auto_trade_allowed={row['auto_trade_allowed']}"
        for row in rows
    ]
    return "\n".join(
        [
            "# Operator Signal Threshold Explainer Report",
            "",
            "## Safety Banner",
            "",
            "- observation-only threshold explanation",
            "- no auto trading",
            "- no account reads",
            "- no position reads",
            "- no historical data requests",
            "- no Telegram real send",
            "- no order/cancel/rebalance",
            "",
            "## Threshold Rows",
            "",
            *lines,
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(rows), encoding="utf-8")


def generate_threshold_explainer(
    *,
    signal_bridge_csv: PathLike = "operator_real_quote_signal_bridge.csv",
    normalization_csv: PathLike = "operator_real_quote_normalization.csv",
    daily_report_csv: PathLike = "operator_daily_real_market_report.csv",
    research_plan_csv: PathLike = "research_trading_plan.csv",
    output_csv: PathLike = "operator_signal_threshold_explainer.csv",
    output_report: PathLike = "reports/operator_signal_threshold_explainer_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_threshold_explainer_rows(
        signal_bridge_csv=signal_bridge_csv,
        normalization_csv=normalization_csv,
        daily_report_csv=daily_report_csv,
        research_plan_csv=research_plan_csv,
        generated_at=generated_at,
    )
    write_threshold_explainer_csv(output_csv, rows)
    write_markdown_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 454 observation-only signal threshold explanation.")
    parser.add_argument("--signal-bridge-csv", default="operator_real_quote_signal_bridge.csv")
    parser.add_argument("--normalization-csv", default="operator_real_quote_normalization.csv")
    parser.add_argument("--daily-report-csv", default="operator_daily_real_market_report.csv")
    parser.add_argument("--research-plan-csv", default="research_trading_plan.csv")
    parser.add_argument("--output-csv", default="operator_signal_threshold_explainer.csv")
    parser.add_argument("--output-report", default="reports/operator_signal_threshold_explainer_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_threshold_explainer(
        signal_bridge_csv=args.signal_bridge_csv,
        normalization_csv=args.normalization_csv,
        daily_report_csv=args.daily_report_csv,
        research_plan_csv=args.research_plan_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator signal threshold explainer generated")
    for row in rows:
        print(f"{row['symbol']}:threshold_status={row['threshold_status']}:manual_review_required={row['manual_review_required']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
