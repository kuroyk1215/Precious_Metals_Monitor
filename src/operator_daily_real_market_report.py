from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"

DAILY_REAL_MARKET_REPORT_FIELDS = (
    "generated_at",
    "symbol",
    "real_quote_state",
    "quote_status",
    "normalized_status",
    "signal_bridge_status",
    "observation_allowed",
    "manual_review_only",
    "permission_or_connection_failure",
    "safe_unavailable",
    "connection_succeeded",
    "market_data_request_triggered",
    "snapshot_rows_detected",
    "last_price",
    "bid",
    "ask",
    "close",
    "observation_summary",
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


def _symbol(row: Dict[str, str]) -> str:
    return str(row.get("symbol") or row.get("display_symbol") or "").strip().upper()


def _index(rows: Sequence[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    indexed: Dict[str, Dict[str, str]] = {}
    for row in rows:
        symbol = _symbol(row)
        if symbol:
            indexed[symbol] = row
    return indexed


def build_daily_real_market_rows(
    *,
    normalization_csv: PathLike = "operator_real_quote_normalization.csv",
    signal_bridge_csv: PathLike = "operator_real_quote_signal_bridge.csv",
    latest_csv: PathLike = "operator_real_marketdata_latest.csv",
    daily_summary_csv: PathLike = "operator_real_marketdata_daily_run_summary.csv",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    generated = generated_at or _now_timestamp()
    quote_rows = _read_rows(normalization_csv)
    bridge_by_symbol = _index(_read_rows(signal_bridge_csv))
    _read_rows(latest_csv)
    _read_rows(daily_summary_csv)

    rows: List[Dict[str, str]] = []
    for quote in quote_rows:
        symbol = _symbol(quote)
        bridge = bridge_by_symbol.get(symbol, {})
        available = quote.get("quote_status") == "AVAILABLE" and quote.get("normalized_status") == "NORMALIZED"
        permission_failure = quote.get("diagnostic_category") == "PERMISSION_OR_CONNECTION_FAILURE"
        safe_unavailable = quote.get("normalized_status") == "SAFE_UNAVAILABLE"
        if available:
            state = "REAL_QUOTE_AVAILABLE"
            summary = "real quote available for observation-only review"
            next_step = "manual_observation_review_only"
        elif permission_failure:
            state = "PERMISSION_OR_CONNECTION_FAILURE"
            summary = "permission or connection failure; manual review only"
            next_step = "review_real_marketdata_connection"
        else:
            state = "SAFE_UNAVAILABLE"
            summary = "safe unavailable; no real quote for observation"
            next_step = "review_real_marketdata_connection"
        rows.append(
            {
                "generated_at": generated,
                "symbol": symbol,
                "real_quote_state": state,
                "quote_status": quote.get("quote_status", "UNAVAILABLE"),
                "normalized_status": quote.get("normalized_status", "SAFE_UNAVAILABLE"),
                "signal_bridge_status": bridge.get("signal_bridge_status", "HOLD_NO_REAL_QUOTE"),
                "observation_allowed": "true" if available else FALSE_TEXT,
                "manual_review_only": "true",
                "permission_or_connection_failure": "true" if permission_failure else FALSE_TEXT,
                "safe_unavailable": "true" if safe_unavailable else FALSE_TEXT,
                "connection_succeeded": quote.get("connection_succeeded", FALSE_TEXT),
                "market_data_request_triggered": quote.get("market_data_request_triggered", FALSE_TEXT),
                "snapshot_rows_detected": quote.get("snapshot_rows_detected", "0"),
                "last_price": quote.get("last_price", ""),
                "bid": quote.get("bid", ""),
                "ask": quote.get("ask", ""),
                "close": quote.get("close", ""),
                "observation_summary": summary,
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


def write_daily_real_market_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(DAILY_REAL_MARKET_REPORT_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(rows: Sequence[Dict[str, str]]) -> str:
    lines = [f"- {row['symbol']}: real_quote_state={row['real_quote_state']}; observation_allowed={row['observation_allowed']}; manual_review_only={row['manual_review_only']}; operator_next_step={row['operator_next_step']}" for row in rows]
    return "\n".join(
        [
            "# Operator Daily Real Market Report",
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
            "## Real Market States",
            "",
            "- real quote available is reported as REAL_QUOTE_AVAILABLE",
            "- safe unavailable is reported as SAFE_UNAVAILABLE",
            "- permission / connection failure is reported as PERMISSION_OR_CONNECTION_FAILURE",
            "- observation allowed remains observation-only",
            "- manual review only remains true for every row",
            "",
            "## Symbol Rows",
            "",
            *lines,
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(rows), encoding="utf-8")


def generate_daily_real_market_report(
    *,
    normalization_csv: PathLike = "operator_real_quote_normalization.csv",
    signal_bridge_csv: PathLike = "operator_real_quote_signal_bridge.csv",
    latest_csv: PathLike = "operator_real_marketdata_latest.csv",
    daily_summary_csv: PathLike = "operator_real_marketdata_daily_run_summary.csv",
    output_csv: PathLike = "operator_daily_real_market_report.csv",
    output_report: PathLike = "reports/operator_daily_real_market_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_daily_real_market_rows(
        normalization_csv=normalization_csv,
        signal_bridge_csv=signal_bridge_csv,
        latest_csv=latest_csv,
        daily_summary_csv=daily_summary_csv,
        generated_at=generated_at,
    )
    write_daily_real_market_csv(output_csv, rows)
    write_markdown_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 449 daily real-market observation report.")
    parser.add_argument("--normalization-csv", default="operator_real_quote_normalization.csv")
    parser.add_argument("--signal-bridge-csv", default="operator_real_quote_signal_bridge.csv")
    parser.add_argument("--latest-csv", default="operator_real_marketdata_latest.csv")
    parser.add_argument("--daily-summary-csv", default="operator_real_marketdata_daily_run_summary.csv")
    parser.add_argument("--output-csv", default="operator_daily_real_market_report.csv")
    parser.add_argument("--output-report", default="reports/operator_daily_real_market_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_daily_real_market_report(
        normalization_csv=args.normalization_csv,
        signal_bridge_csv=args.signal_bridge_csv,
        latest_csv=args.latest_csv,
        daily_summary_csv=args.daily_summary_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator daily real market report generated")
    for row in rows:
        print(f"{row['symbol']}:real_quote_state={row['real_quote_state']}:manual_review_only={row['manual_review_only']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
