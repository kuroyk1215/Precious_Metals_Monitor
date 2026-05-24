from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

READY = "WATCHLIST_UNIVERSE_READY"
REVIEW_REQUIRED = "WATCHLIST_UNIVERSE_REVIEW_REQUIRED"
INVALID = "WATCHLIST_UNIVERSE_INVALID"

ACTIVE_FIRST_VALIDATION = "ACTIVE_FIRST_VALIDATION"
OPTIONAL_MANUAL_REVIEW = "OPTIONAL_MANUAL_REVIEW"
MANUAL_EXTERNAL_ONLY = "MANUAL_EXTERNAL_ONLY"
IBKR_EXCLUDED = "IBKR_EXCLUDED"
ALLOWED_UNIVERSE_STATUSES = {
    ACTIVE_FIRST_VALIDATION,
    OPTIONAL_MANUAL_REVIEW,
    MANUAL_EXTERNAL_ONLY,
    IBKR_EXCLUDED,
}

VALID = "VALID"
REVIEW_REQUIRED_STATUS = "REVIEW_REQUIRED"
BLOCKED_FROM_IBKR = "BLOCKED_FROM_IBKR"
INVALID_CONFIG = "INVALID_CONFIG"
ALLOWED_VALIDATION_STATUSES = {
    VALID,
    REVIEW_REQUIRED_STATUS,
    BLOCKED_FROM_IBKR,
    INVALID_CONFIG,
}

FORBIDDEN_EXECUTION_WORDS = (
    "BUY",
    "SELL",
    "ORDER",
    "CANCEL",
    "REBALANCE",
    "AUTO_TRADE",
    "EXECUTE",
)

ACTION_STATUS_FIELDS = (
    "universe_status",
    "validation_status",
    "notes",
)

CONFIG_COLUMNS = (
    "market",
    "display_symbol",
    "symbol",
    "exchange",
    "currency",
    "asset_type",
    "data_source_route",
    "ibkr_universe_allowed",
    "first_validation_allowed",
    "optional_symbol",
    "manual_review_required",
    "action_allowed",
    "notes",
)

CONFIG_FILES = (
    "config/watchlist_us.csv",
    "config/watchlist_jp.csv",
    "config/watchlist_cn.csv",
)


@dataclass(frozen=True)
class WatchlistUniverseRow:
    universe_run_id: str
    universe_timestamp: str
    market: str
    display_symbol: str
    symbol: str
    exchange: str
    currency: str
    asset_type: str
    data_source_route: str
    ibkr_universe_allowed: str
    first_validation_allowed: str
    optional_symbol: str
    manual_review_required: str
    action_allowed: str
    universe_status: str
    validation_status: str
    notes: str


PathLike = Union[str, Path]


def _clean(value: object) -> str:
    return str(value or "").strip()


def _lower(value: object) -> str:
    return _clean(value).lower()


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_bool(value: object) -> Optional[bool]:
    text = _lower(value)
    if text == TRUE_TEXT:
        return True
    if text == FALSE_TEXT:
        return False
    return None


def _bool_text(value: Optional[bool]) -> str:
    return TRUE_TEXT if value is True else FALSE_TEXT


def _contains_forbidden(text: str) -> bool:
    upper = text.upper()
    return any(word in upper for word in FORBIDDEN_EXECUTION_WORDS)


def _read_config_rows(root: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for relative in CONFIG_FILES:
        path = root / relative
        if not path.exists():
            rows.append(
                {
                    "market": "MISSING",
                    "display_symbol": relative,
                    "symbol": relative,
                    "exchange": "",
                    "currency": "",
                    "asset_type": "",
                    "data_source_route": "MISSING_CONFIG",
                    "ibkr_universe_allowed": "",
                    "first_validation_allowed": "",
                    "optional_symbol": "",
                    "manual_review_required": "",
                    "action_allowed": "",
                    "notes": f"missing_config_file={relative}",
                }
            )
            continue
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = tuple(reader.fieldnames or ())
            for raw in reader:
                row = {column: _clean(raw.get(column)) for column in CONFIG_COLUMNS}
                row["_missing_columns"] = ",".join(column for column in CONFIG_COLUMNS if column not in fieldnames)
                row["_source_file"] = relative
                rows.append(row)
    return rows


def _derive_status(row: Dict[str, str]) -> Tuple[str, str, str]:
    notes = _clean(row.get("notes"))
    bools = {
        "ibkr_universe_allowed": _parse_bool(row.get("ibkr_universe_allowed")),
        "first_validation_allowed": _parse_bool(row.get("first_validation_allowed")),
        "optional_symbol": _parse_bool(row.get("optional_symbol")),
        "manual_review_required": _parse_bool(row.get("manual_review_required")),
        "action_allowed": _parse_bool(row.get("action_allowed")),
    }
    invalid_reasons = []
    for field, parsed in bools.items():
        if parsed is None:
            invalid_reasons.append(f"invalid_boolean:{field}")
    missing_columns = _clean(row.get("_missing_columns"))
    if missing_columns:
        invalid_reasons.append(f"missing_columns:{missing_columns}")
    for field in ("market", "display_symbol", "symbol", "exchange", "currency", "asset_type", "data_source_route"):
        if not _clean(row.get(field)):
            invalid_reasons.append(f"missing_required:{field}")

    ibkr_allowed = bools["ibkr_universe_allowed"] is True
    first_allowed = bools["first_validation_allowed"] is True
    optional = bools["optional_symbol"] is True
    manual_review = bools["manual_review_required"] is True
    action_allowed = bools["action_allowed"] is True
    route = _clean(row.get("data_source_route"))
    symbol = _clean(row.get("symbol"))
    market = _clean(row.get("market")).upper()

    if action_allowed:
        invalid_reasons.append("action_allowed_must_be_false")
    if not manual_review:
        invalid_reasons.append("manual_review_required_must_be_true")
    if first_allowed and not ibkr_allowed:
        invalid_reasons.append("first_validation_requires_ibkr_universe_allowed")
    if market == "CN" and symbol == "518880" and ibkr_allowed:
        invalid_reasons.append("518880_must_be_ibkr_excluded")
    if route in {"CN_MANUAL_OR_EXTERNAL_ONLY", "JP_OPTIONAL_MANUAL_OR_FUTURE_IBKR"} and ibkr_allowed:
        invalid_reasons.append("manual_route_must_not_be_ibkr_allowed")

    if invalid_reasons:
        return IBKR_EXCLUDED if not ibkr_allowed else ACTIVE_FIRST_VALIDATION, INVALID_CONFIG, _append_notes(notes, invalid_reasons)
    if ibkr_allowed and first_allowed:
        return ACTIVE_FIRST_VALIDATION, VALID, notes
    if market == "CN" or route == "CN_MANUAL_OR_EXTERNAL_ONLY" or "EXCLUDED_FROM_IBKR" in notes.upper():
        return IBKR_EXCLUDED, BLOCKED_FROM_IBKR, notes
    if optional:
        return OPTIONAL_MANUAL_REVIEW, REVIEW_REQUIRED_STATUS, notes
    if not ibkr_allowed:
        return MANUAL_EXTERNAL_ONLY, BLOCKED_FROM_IBKR, notes
    return ACTIVE_FIRST_VALIDATION, VALID, notes


def _append_notes(notes: str, fragments: Sequence[str]) -> str:
    suffix = ";".join(fragments)
    return f"{notes};{suffix}" if notes else suffix


def _build_row(source_row: Dict[str, str], run_id: str, timestamp: str) -> WatchlistUniverseRow:
    universe_status, validation_status, notes = _derive_status(source_row)
    ibkr_allowed = _parse_bool(source_row.get("ibkr_universe_allowed"))
    first_allowed = _parse_bool(source_row.get("first_validation_allowed"))
    optional = _parse_bool(source_row.get("optional_symbol"))
    manual_review = _parse_bool(source_row.get("manual_review_required"))
    action_allowed = _parse_bool(source_row.get("action_allowed"))
    if validation_status == INVALID_CONFIG:
        ibkr_allowed = False if ibkr_allowed is not True else True
        first_allowed = False if ibkr_allowed is not True else first_allowed
        action_allowed = False if action_allowed is not True else True
    return WatchlistUniverseRow(
        universe_run_id=run_id,
        universe_timestamp=timestamp,
        market=_clean(source_row.get("market")) or "MISSING",
        display_symbol=_clean(source_row.get("display_symbol")) or _clean(source_row.get("symbol")) or "MISSING",
        symbol=_clean(source_row.get("symbol")) or _clean(source_row.get("display_symbol")) or "MISSING",
        exchange=_clean(source_row.get("exchange")),
        currency=_clean(source_row.get("currency")),
        asset_type=_clean(source_row.get("asset_type")),
        data_source_route=_clean(source_row.get("data_source_route")),
        ibkr_universe_allowed=_bool_text(ibkr_allowed),
        first_validation_allowed=_bool_text(first_allowed),
        optional_symbol=_bool_text(optional),
        manual_review_required=_bool_text(manual_review),
        action_allowed=_bool_text(action_allowed),
        universe_status=universe_status,
        validation_status=validation_status,
        notes=notes,
    )


def top_level_status(rows: Sequence[WatchlistUniverseRow]) -> str:
    if any(row.validation_status == INVALID_CONFIG for row in rows):
        return INVALID
    if any(
        row.validation_status in {REVIEW_REQUIRED_STATUS, BLOCKED_FROM_IBKR}
        or row.universe_status in {OPTIONAL_MANUAL_REVIEW, MANUAL_EXTERNAL_ONLY, IBKR_EXCLUDED}
        for row in rows
    ):
        return REVIEW_REQUIRED
    return READY


def build_watchlist_universe(root: PathLike = ".") -> Tuple[str, List[WatchlistUniverseRow]]:
    root_path = Path(root)
    run_id = f"watchlist_universe_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_UTC')}"
    timestamp = _now_timestamp()
    rows = [_build_row(row, run_id, timestamp) for row in _read_config_rows(root_path)]
    return top_level_status(rows), rows


def write_universe_csv(path: PathLike, rows: Sequence[WatchlistUniverseRow]) -> None:
    fields = list(WatchlistUniverseRow.__dataclass_fields__.keys())
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def _summary_counts(rows: Sequence[WatchlistUniverseRow], field: str) -> str:
    counts: Dict[str, int] = {}
    for row in rows:
        value = getattr(row, field)
        counts[value] = counts.get(value, 0) + 1
    return "\n".join(f"- {field}.{key}={counts[key]}" for key in sorted(counts))


def _symbol_list(rows: Sequence[WatchlistUniverseRow], predicate) -> str:
    symbols = [row.display_symbol for row in rows if predicate(row)]
    return ",".join(symbols) if symbols else "none"


def build_markdown_report(top_status: str, rows: Sequence[WatchlistUniverseRow]) -> str:
    table = "\n".join(
        f"| {row.market} | {row.display_symbol} | {row.symbol} | {row.exchange} | {row.currency} | {row.data_source_route} | {row.ibkr_universe_allowed} | {row.first_validation_allowed} | {row.optional_symbol} | {row.manual_review_required} | {row.action_allowed} | {row.universe_status} | {row.validation_status} | {row.notes} |"
        for row in rows
    )
    next_step = "operator_review_optional_and_external_symbols" if top_status == REVIEW_REQUIRED else "operator_confirm_static_universe"
    if top_status == INVALID:
        next_step = "fix_watchlist_config_before_any_validation"
    return "\n".join(
        [
            "# Watchlist Universe Report",
            "",
            "## Top-level Status",
            "",
            f"- top_level_status={top_status}",
            f"- total_symbols={len(rows)}",
            "",
            "## Market Summary",
            "",
            _summary_counts(rows, "market"),
            "",
            "## IBKR-allowed Summary",
            "",
            f"- ibkr_allowed_symbols={_symbol_list(rows, lambda row: row.ibkr_universe_allowed == TRUE_TEXT)}",
            f"- first_validation_symbols={_symbol_list(rows, lambda row: row.first_validation_allowed == TRUE_TEXT)}",
            "",
            "## IBKR-excluded Summary",
            "",
            f"- ibkr_excluded_symbols={_symbol_list(rows, lambda row: row.ibkr_universe_allowed == FALSE_TEXT)}",
            "",
            "## Optional Manual Review Summary",
            "",
            f"- optional_manual_review_symbols={_symbol_list(rows, lambda row: row.optional_symbol == TRUE_TEXT or row.manual_review_required == TRUE_TEXT)}",
            "",
            "## Symbol Table",
            "",
            "| market | display_symbol | symbol | exchange | currency | data_source_route | ibkr_universe_allowed | first_validation_allowed | optional_symbol | manual_review_required | action_allowed | universe_status | validation_status | notes |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
            table,
            "",
            "## Safety Statement",
            "",
            "- offline_only=true",
            "- action_allowed=false",
            "- broker_connection_triggered=false",
            "- market_data_request_triggered=false",
            "- historical_data_request_triggered=false",
            "- account_read_triggered=false",
            "- position_read_triggered=false",
            "- telegram_send_triggered=false",
            "- trading_action_triggered=false",
            "",
            "## Next Operator Step",
            "",
            f"- {next_step}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, top_status: str, rows: Sequence[WatchlistUniverseRow]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(build_markdown_report(top_status, rows), encoding="utf-8")


def validate_generated_rows(rows: Sequence[WatchlistUniverseRow]) -> List[str]:
    errors: List[str] = []
    for row in rows:
        if row.universe_status not in ALLOWED_UNIVERSE_STATUSES:
            errors.append(f"{row.display_symbol}:invalid_universe_status")
        if row.validation_status not in ALLOWED_VALIDATION_STATUSES:
            errors.append(f"{row.display_symbol}:invalid_validation_status")
        if row.action_allowed != FALSE_TEXT:
            errors.append(f"{row.display_symbol}:action_allowed_not_false")
        if row.manual_review_required != TRUE_TEXT:
            errors.append(f"{row.display_symbol}:manual_review_required_not_true")
        if row.ibkr_universe_allowed == FALSE_TEXT and row.first_validation_allowed == TRUE_TEXT:
            errors.append(f"{row.display_symbol}:first_validation_allowed_without_ibkr")
        for field in ACTION_STATUS_FIELDS:
            if _contains_forbidden(getattr(row, field)):
                errors.append(f"{row.display_symbol}:forbidden_execution_word:{field}")
    return errors


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an offline static watchlist universe from local config CSV files.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-csv", default="watchlist_universe.csv")
    parser.add_argument("--output-report", default="reports/watchlist_universe_report.md")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    top_status, rows = build_watchlist_universe(args.root)
    write_universe_csv(args.output_csv, rows)
    write_markdown_report(args.output_report, top_status, rows)
    errors = validate_generated_rows(rows)
    print("[PASS] Watchlist universe generated")
    print(f"top_level_status={top_status}")
    print("offline_only=true")
    print(f"ibkr_allowed_symbols={_symbol_list(rows, lambda row: row.ibkr_universe_allowed == TRUE_TEXT)}")
    print(f"ibkr_excluded_symbols={_symbol_list(rows, lambda row: row.ibkr_universe_allowed == FALSE_TEXT)}")
    print("action_allowed=false" if all(row.action_allowed == FALSE_TEXT for row in rows) else "action_allowed=true")
    print("manual_review_required=true" if all(row.manual_review_required == TRUE_TEXT for row in rows) else "manual_review_required=false")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
