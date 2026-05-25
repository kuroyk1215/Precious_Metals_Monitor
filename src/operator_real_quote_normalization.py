from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union


TRUE_TEXT = "true"
FALSE_TEXT = "false"
SYMBOLS = ("GLD", "SLV")

NORMALIZATION_FIELDS = (
    "generated_at",
    "symbol",
    "asset_class",
    "market",
    "currency",
    "quote_source",
    "quote_status",
    "data_status",
    "connection_succeeded",
    "market_data_request_triggered",
    "snapshot_rows_detected",
    "last_price",
    "bid",
    "ask",
    "close",
    "quote_time",
    "staleness_status",
    "normalized_status",
    "diagnostic_category",
    "diagnostic_reason",
    "operator_next_step",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "allowed", "triggered"}


def _read_rows(path: PathLike) -> List[Dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    try:
        with csv_path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except PermissionError:
        return []


def _latest_row(path: PathLike) -> Optional[Dict[str, str]]:
    rows = _read_rows(path)
    return rows[-1] if rows else None


def _first_present(row: Dict[str, str], fields: Sequence[str]) -> str:
    for field in fields:
        value = str(row.get(field) or "").strip()
        if value:
            return value
    return ""


def _symbol_key(row: Dict[str, str]) -> str:
    return _first_present(row, ("symbol", "display_symbol", "local_symbol")).upper()


def _price_available(row: Dict[str, str]) -> bool:
    return bool(_first_present(row, ("last_price", "last", "market_price", "snapshot_last", "snapshot_market_price", "close", "bid", "ask")))


def _latest_symbol_rows(rows: Sequence[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    by_symbol: Dict[str, Dict[str, str]] = {}
    for row in rows:
        symbol = _symbol_key(row)
        if symbol in SYMBOLS:
            by_symbol[symbol] = row
    return by_symbol


def _safe_int(value: object) -> int:
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return 0


def _diagnostic(
    *,
    snapshot_rows: int,
    connection_succeeded: bool,
    market_data_request_triggered: bool,
    source_row: Optional[Dict[str, str]],
) -> Tuple[str, str]:
    if not connection_succeeded or not market_data_request_triggered:
        return "PERMISSION_OR_CONNECTION_FAILURE", "real_marketdata_connection_or_request_not_confirmed"
    if snapshot_rows <= 0:
        return "NO_REAL_QUOTE_SNAPSHOT", "no_real_marketdata_snapshot_rows_detected"
    if source_row is None or not _price_available(source_row):
        return "NO_REAL_QUOTE_SNAPSHOT", "no_symbol_quote_fields_available_in_phase444_446_outputs"
    return "REAL_QUOTE_AVAILABLE", "real_quote_fields_available_from_operator_chain"


def build_normalized_rows(
    *,
    latest_csv: PathLike = "operator_real_marketdata_latest.csv",
    daily_summary_csv: PathLike = "operator_real_marketdata_daily_run_summary.csv",
    decision_gate_csv: PathLike = "operator_real_marketdata_decision_gate.csv",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    generated = generated_at or _now_timestamp()
    latest_rows = _read_rows(latest_csv)
    latest = latest_rows[-1] if latest_rows else None
    daily = _latest_row(daily_summary_csv)
    decision = _latest_row(decision_gate_csv)
    source = decision or latest or daily or {}
    by_symbol = _latest_symbol_rows(latest_rows)
    connection_succeeded = _truthy(source.get("connection_succeeded"))
    market_data_request_triggered = _truthy(source.get("market_data_request_triggered"))
    snapshot_rows = _safe_int(source.get("snapshot_rows_detected"))

    rows: List[Dict[str, str]] = []
    for symbol in SYMBOLS:
        quote = by_symbol.get(symbol)
        diagnostic_category, diagnostic_reason = _diagnostic(
            snapshot_rows=snapshot_rows,
            connection_succeeded=connection_succeeded,
            market_data_request_triggered=market_data_request_triggered,
            source_row=quote,
        )
        available = diagnostic_category == "REAL_QUOTE_AVAILABLE"
        rows.append(
            {
                "generated_at": generated,
                "symbol": symbol,
                "asset_class": "ETF",
                "market": "US",
                "currency": "USD",
                "quote_source": "phase444_446_operator_chain",
                "quote_status": "AVAILABLE" if available else "UNAVAILABLE",
                "data_status": "REAL_QUOTE_AVAILABLE" if available else "REAL_QUOTE_UNAVAILABLE",
                "connection_succeeded": TRUE_TEXT if connection_succeeded else FALSE_TEXT,
                "market_data_request_triggered": TRUE_TEXT if market_data_request_triggered else FALSE_TEXT,
                "snapshot_rows_detected": str(snapshot_rows),
                "last_price": _first_present(quote or {}, ("last_price", "last", "market_price", "snapshot_last", "snapshot_market_price")),
                "bid": _first_present(quote or {}, ("bid", "snapshot_bid")),
                "ask": _first_present(quote or {}, ("ask", "snapshot_ask")),
                "close": _first_present(quote or {}, ("close", "snapshot_close")),
                "quote_time": _first_present(quote or {}, ("quote_time", "timestamp", "snapshot_time", "generated_at")),
                "staleness_status": "CURRENT_OPERATOR_CHAIN" if available else "UNKNOWN_NO_REAL_QUOTE",
                "normalized_status": "NORMALIZED" if available else "SAFE_UNAVAILABLE",
                "diagnostic_category": diagnostic_category,
                "diagnostic_reason": diagnostic_reason,
                "operator_next_step": "manual_observation_only" if available else "review_real_marketdata_connection",
            }
        )
    return rows


def write_normalized_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(NORMALIZATION_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(rows: Sequence[Dict[str, str]]) -> str:
    lines = [f"- {row['symbol']}: quote_status={row['quote_status']}; normalized_status={row['normalized_status']}; diagnostic_category={row['diagnostic_category']}; operator_next_step={row['operator_next_step']}" for row in rows]
    return "\n".join(
        [
            "# Operator Real Quote Normalization Report",
            "",
            "## Safety Banner",
            "",
            "- read-only / manual-only / observation-only",
            "- no automatic trading",
            "- no account read",
            "- no position read",
            "- no historical data request",
            "- no Telegram real send",
            "",
            "## Normalized Quotes",
            "",
            *lines,
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(rows), encoding="utf-8")


def generate_normalization(
    *,
    latest_csv: PathLike = "operator_real_marketdata_latest.csv",
    daily_summary_csv: PathLike = "operator_real_marketdata_daily_run_summary.csv",
    decision_gate_csv: PathLike = "operator_real_marketdata_decision_gate.csv",
    output_csv: PathLike = "operator_real_quote_normalization.csv",
    output_report: PathLike = "reports/operator_real_quote_normalization_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_normalized_rows(
        latest_csv=latest_csv,
        daily_summary_csv=daily_summary_csv,
        decision_gate_csv=decision_gate_csv,
        generated_at=generated_at,
    )
    write_normalized_csv(output_csv, rows)
    write_markdown_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 447 GLD/SLV real quote normalization.")
    parser.add_argument("--latest-csv", default="operator_real_marketdata_latest.csv")
    parser.add_argument("--daily-summary-csv", default="operator_real_marketdata_daily_run_summary.csv")
    parser.add_argument("--decision-gate-csv", default="operator_real_marketdata_decision_gate.csv")
    parser.add_argument("--output-csv", default="operator_real_quote_normalization.csv")
    parser.add_argument("--output-report", default="reports/operator_real_quote_normalization_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_normalization(
        latest_csv=args.latest_csv,
        daily_summary_csv=args.daily_summary_csv,
        decision_gate_csv=args.decision_gate_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator real quote normalization generated")
    for row in rows:
        print(f"{row['symbol']}:quote_status={row['quote_status']}:normalized_status={row['normalized_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
