from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

RANGE_FIELDS = (
    "generated_at",
    "symbol",
    "quote_status",
    "normalized_status",
    "range_status",
    "lower_observation_band",
    "upper_observation_band",
    "range_basis",
    "confidence_label",
    "manual_review_required",
    "diagnostic_reason",
    "operator_next_step",
    "auto_trade_allowed",
    "order_action_allowed",
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


def _latest_by_symbol(rows: Sequence[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    indexed: Dict[str, Dict[str, str]] = {}
    for row in rows:
        symbol = _symbol(row)
        if symbol:
            indexed[symbol] = row
    return indexed


def _symbols(*groups: Sequence[Dict[str, str]]) -> List[str]:
    seen = {_symbol(row) for rows in groups for row in rows if _symbol(row)}
    if not seen:
        seen = {"GLD", "SLV"}
    return sorted(seen)


def _parse_float(value: object) -> Optional[float]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if number > 0 else None


def _band(center: float, pct: float = 0.02) -> tuple[str, str]:
    return (f"{center * (1 - pct):.4f}", f"{center * (1 + pct):.4f}")


def build_range_framework_rows(
    *,
    normalization_csv: PathLike = "operator_real_quote_normalization.csv",
    spread_framework_csv: PathLike = "operator_gld_slv_spread_framework.csv",
    threshold_explainer_csv: PathLike = "operator_signal_threshold_explainer.csv",
    research_plan_csv: PathLike = "research_trading_plan.csv",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    generated = generated_at or _now_timestamp()
    quote_rows = _read_rows(normalization_csv)
    spread_rows = _read_rows(spread_framework_csv)
    threshold_rows = _read_rows(threshold_explainer_csv)
    plan_rows = _read_rows(research_plan_csv)
    quotes = _latest_by_symbol(quote_rows)
    thresholds = _latest_by_symbol(threshold_rows)
    plans = _latest_by_symbol(plan_rows)
    spread = spread_rows[-1] if spread_rows else {}
    spread_available = spread.get("spread_available") == TRUE_TEXT

    rows: List[Dict[str, str]] = []
    for symbol in _symbols(quote_rows, threshold_rows, plan_rows):
        quote = quotes.get(symbol, {})
        threshold = thresholds.get(symbol, {})
        plan = plans.get(symbol, {})
        quote_status = quote.get("quote_status") or threshold.get("quote_status") or "UNAVAILABLE"
        normalized_status = quote.get("normalized_status") or threshold.get("normalized_status") or "SAFE_UNAVAILABLE"
        last_price = _parse_float(quote.get("last_price"))
        reference_price = _parse_float(plan.get("reference_price"))

        if quote_status != "AVAILABLE" or normalized_status != "NORMALIZED":
            range_status = "RANGE_PENDING_NO_REAL_QUOTE"
            lower = ""
            upper = ""
            basis = "real_quote_unavailable"
            confidence = "NO_REAL_QUOTE"
            reason = quote.get("diagnostic_reason") or threshold.get("diagnostic_reason") or "real_quote_unavailable_for_range_framework"
            next_step = "review_real_marketdata_connection_before_range_observation"
        elif last_price:
            lower, upper = _band(last_price)
            range_status = "RANGE_FRAMEWORK_AVAILABLE" if spread_available else "RANGE_REVIEW_ONLY"
            basis = "last_price_plus_minus_2pct"
            confidence = "REAL_QUOTE_REVIEW_ONLY"
            reason = "real_quote_available_for_manual_range_observation"
            next_step = "manual_review_range_context_only"
        elif reference_price:
            lower, upper = _band(reference_price)
            range_status = "RANGE_REVIEW_ONLY"
            basis = "research_reference_plus_minus_2pct"
            confidence = "REFERENCE_ONLY"
            reason = "reference_price_available_without_normalized_last_price"
            next_step = "manual_review_reference_range_only"
        else:
            range_status = "RANGE_INSUFFICIENT_DATA"
            lower = ""
            upper = ""
            basis = "insufficient_range_inputs"
            confidence = "INSUFFICIENT_DATA"
            reason = "no_real_quote_or_reference_price_for_range_framework"
            next_step = "regenerate_real_market_and_research_sources"

        rows.append(
            {
                "generated_at": generated,
                "symbol": symbol,
                "quote_status": quote_status,
                "normalized_status": normalized_status,
                "range_status": range_status,
                "lower_observation_band": lower,
                "upper_observation_band": upper,
                "range_basis": basis,
                "confidence_label": confidence,
                "manual_review_required": TRUE_TEXT,
                "diagnostic_reason": reason,
                "operator_next_step": next_step,
                "auto_trade_allowed": FALSE_TEXT,
                "order_action_allowed": FALSE_TEXT,
            }
        )
    return rows


def write_range_framework_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(RANGE_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(rows: Sequence[Dict[str, str]]) -> str:
    range_lines = [
        f"- {row['symbol']}: range_status={row['range_status']}; confidence_label={row['confidence_label']}; manual_review_required={row['manual_review_required']}; auto_trade_allowed={row['auto_trade_allowed']}"
        for row in rows
    ]
    return "\n".join(
        [
            "# Operator Real Market Range Framework Report",
            "",
            "## Safety Banner",
            "",
            "- observation-only range framework",
            "- no auto trading",
            "- no account reads",
            "- no position reads",
            "- no historical data requests",
            "- no Telegram real send",
            "- no order/cancel/rebalance",
            "",
            "## Range Framework",
            "",
            *range_lines,
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(rows), encoding="utf-8")


def generate_range_framework(
    *,
    normalization_csv: PathLike = "operator_real_quote_normalization.csv",
    spread_framework_csv: PathLike = "operator_gld_slv_spread_framework.csv",
    threshold_explainer_csv: PathLike = "operator_signal_threshold_explainer.csv",
    research_plan_csv: PathLike = "research_trading_plan.csv",
    output_csv: PathLike = "operator_real_market_range_framework.csv",
    output_report: PathLike = "reports/operator_real_market_range_framework_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_range_framework_rows(
        normalization_csv=normalization_csv,
        spread_framework_csv=spread_framework_csv,
        threshold_explainer_csv=threshold_explainer_csv,
        research_plan_csv=research_plan_csv,
        generated_at=generated_at,
    )
    write_range_framework_csv(output_csv, rows)
    write_markdown_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 460 real-market observation-only range framework.")
    parser.add_argument("--normalization-csv", default="operator_real_quote_normalization.csv")
    parser.add_argument("--spread-framework-csv", default="operator_gld_slv_spread_framework.csv")
    parser.add_argument("--threshold-explainer-csv", default="operator_signal_threshold_explainer.csv")
    parser.add_argument("--research-plan-csv", default="research_trading_plan.csv")
    parser.add_argument("--output-csv", default="operator_real_market_range_framework.csv")
    parser.add_argument("--output-report", default="reports/operator_real_market_range_framework_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_range_framework(
        normalization_csv=args.normalization_csv,
        spread_framework_csv=args.spread_framework_csv,
        threshold_explainer_csv=args.threshold_explainer_csv,
        research_plan_csv=args.research_plan_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator real-market range framework generated")
    for row in rows:
        print(f"{row['symbol']}:range_status={row['range_status']}:manual_review_required={row['manual_review_required']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
