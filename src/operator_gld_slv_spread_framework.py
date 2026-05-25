from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"

SPREAD_FIELDS = (
    "generated_at",
    "gld_quote_status",
    "slv_quote_status",
    "gld_last_price",
    "slv_last_price",
    "spread_available",
    "gld_slv_ratio",
    "relative_strength_status",
    "spread_observation_status",
    "diagnostic_reason",
    "operator_next_step",
    "auto_trade_allowed",
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


def _symbol(row: Dict[str, str]) -> str:
    return str(row.get("symbol") or row.get("display_symbol") or "").strip().upper()


def _latest_by_symbol(rows: Sequence[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    indexed: Dict[str, Dict[str, str]] = {}
    for row in rows:
        symbol = _symbol(row)
        if symbol:
            indexed[symbol] = row
    return indexed


def _parse_float(value: object) -> Optional[float]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if number > 0 else None


def _quote_status(symbol: str, quotes: Dict[str, Dict[str, str]], bridge: Dict[str, Dict[str, str]], daily: Dict[str, Dict[str, str]]) -> str:
    return (
        quotes.get(symbol, {}).get("quote_status")
        or bridge.get(symbol, {}).get("quote_status")
        or daily.get(symbol, {}).get("quote_status")
        or "UNAVAILABLE"
    )


def _last_price(symbol: str, quotes: Dict[str, Dict[str, str]], daily: Dict[str, Dict[str, str]]) -> Optional[float]:
    return _parse_float(quotes.get(symbol, {}).get("last_price")) or _parse_float(daily.get(symbol, {}).get("last_price"))


def build_spread_framework_row(
    *,
    normalization_csv: PathLike = "operator_real_quote_normalization.csv",
    signal_bridge_csv: PathLike = "operator_real_quote_signal_bridge.csv",
    daily_report_csv: PathLike = "operator_daily_real_market_report.csv",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    quote_rows = _read_rows(normalization_csv)
    bridge_rows = _read_rows(signal_bridge_csv)
    daily_rows = _read_rows(daily_report_csv)
    quotes = _latest_by_symbol(quote_rows)
    bridge = _latest_by_symbol(bridge_rows)
    daily = _latest_by_symbol(daily_rows)

    gld_status = _quote_status("GLD", quotes, bridge, daily)
    slv_status = _quote_status("SLV", quotes, bridge, daily)
    gld_price = _last_price("GLD", quotes, daily)
    slv_price = _last_price("SLV", quotes, daily)

    if gld_status == "AVAILABLE" and slv_status == "AVAILABLE" and gld_price and slv_price:
        ratio = gld_price / slv_price
        spread_available = "true"
        ratio_text = f"{ratio:.6f}"
        relative_strength = "RELATIVE_STRENGTH_REVIEW_ONLY"
        spread_status = "SPREAD_FRAMEWORK_AVAILABLE"
        reason = "gld_slv_real_quote_prices_available_for_manual_ratio_observation"
        next_step = "manual_review_spread_context_only"
    else:
        spread_available = FALSE_TEXT
        ratio_text = ""
        relative_strength = "SAFE_UNAVAILABLE"
        spread_status = "SAFE_UNAVAILABLE"
        reason = "gld_or_slv_real_quote_unavailable_for_spread_framework"
        next_step = "review_real_marketdata_connection_before_spread_observation"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "gld_quote_status": gld_status,
        "slv_quote_status": slv_status,
        "gld_last_price": "" if gld_price is None else f"{gld_price:.4f}",
        "slv_last_price": "" if slv_price is None else f"{slv_price:.4f}",
        "spread_available": spread_available,
        "gld_slv_ratio": ratio_text,
        "relative_strength_status": relative_strength,
        "spread_observation_status": spread_status,
        "diagnostic_reason": reason,
        "operator_next_step": next_step,
        "auto_trade_allowed": FALSE_TEXT,
        "order_action_allowed": FALSE_TEXT,
        "cancel_action_allowed": FALSE_TEXT,
        "rebalance_action_allowed": FALSE_TEXT,
    }


def write_spread_framework_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SPREAD_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Operator GLD/SLV Spread Framework Report",
            "",
            "## Safety Banner",
            "",
            "- observation-only spread framework",
            "- no auto trading",
            "- no account reads",
            "- no position reads",
            "- no historical data requests",
            "- no Telegram real send",
            "- no order/cancel/rebalance",
            "",
            "## Spread Framework",
            "",
            f"- gld_quote_status={row['gld_quote_status']}",
            f"- slv_quote_status={row['slv_quote_status']}",
            f"- spread_available={row['spread_available']}",
            f"- gld_slv_ratio={row['gld_slv_ratio']}",
            f"- relative_strength_status={row['relative_strength_status']}",
            f"- spread_observation_status={row['spread_observation_status']}",
            f"- diagnostic_reason={row['diagnostic_reason']}",
            f"- operator_next_step={row['operator_next_step']}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_spread_framework(
    *,
    normalization_csv: PathLike = "operator_real_quote_normalization.csv",
    signal_bridge_csv: PathLike = "operator_real_quote_signal_bridge.csv",
    daily_report_csv: PathLike = "operator_daily_real_market_report.csv",
    output_csv: PathLike = "operator_gld_slv_spread_framework.csv",
    output_report: PathLike = "reports/operator_gld_slv_spread_framework_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_spread_framework_row(
        normalization_csv=normalization_csv,
        signal_bridge_csv=signal_bridge_csv,
        daily_report_csv=daily_report_csv,
        generated_at=generated_at,
    )
    write_spread_framework_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 459 GLD/SLV observation-only spread framework.")
    parser.add_argument("--normalization-csv", default="operator_real_quote_normalization.csv")
    parser.add_argument("--signal-bridge-csv", default="operator_real_quote_signal_bridge.csv")
    parser.add_argument("--daily-report-csv", default="operator_daily_real_market_report.csv")
    parser.add_argument("--output-csv", default="operator_gld_slv_spread_framework.csv")
    parser.add_argument("--output-report", default="reports/operator_gld_slv_spread_framework_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_spread_framework(
        normalization_csv=args.normalization_csv,
        signal_bridge_csv=args.signal_bridge_csv,
        daily_report_csv=args.daily_report_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator GLD/SLV spread framework generated")
    print(f"spread_observation_status={row['spread_observation_status']}:spread_available={row['spread_available']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
