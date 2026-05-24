from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


TRUE_TEXT = "true"
FALSE_TEXT = "false"
LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE = "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE"
REFERENCE_READY = "OPERATOR_HANDOFF_REFERENCE_READY"
BLOCKED = "OPERATOR_HANDOFF_BLOCKED"
SAFETY_REVIEW_REQUIRED = "OPERATOR_HANDOFF_SAFETY_REVIEW_REQUIRED"
FORBIDDEN_ACTION_WORDS = ("BUY", "SELL", "ORDER", "CANCEL", "REBALANCE", "AUTO_TRADE", "TRADE")


@dataclass(frozen=True)
class DailyOperatorHandoffRow:
    top_level_status: str
    run_id: str
    run_timestamp: str
    display_symbol: str
    symbol: str
    asset_route: str
    data_source_route: str
    snapshot_status: str
    effective_market_data_type: str
    data_delay_flag: str
    latest_price: str
    reference_price: str
    price_status: str
    operator_status: str
    final_research_bucket: str
    api_error_codes: str
    error_10089_detected: str
    error_354_detected: str
    live_subscription_status: str
    reference_only_status: str
    delayed_reference_count: str
    manual_review_required: str
    action_allowed: str
    broker_execution_triggered: str
    historical_data_request_triggered: str
    account_read_triggered: str
    position_read_triggered: str
    telegram_send_triggered: str
    recommended_operator_action: str


def _clean(value: object) -> str:
    return str(value or "").strip()


def _lower(value: object) -> str:
    return _clean(value).lower()


def _truthy(value: object) -> bool:
    return _lower(value) in {"1", "yes", "y", "true", "triggered", "allowed"}


def read_csv_rows(path: str | Path) -> Tuple[str, List[Dict[str, str]]]:
    candidate = Path(path)
    if not candidate.exists():
        return "missing", []
    with candidate.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return "empty_file", []
    return "present", rows


def _row_symbol(row: Dict[str, str]) -> str:
    return _clean(row.get("display_symbol")) or _clean(row.get("symbol")) or _clean(row.get("local_symbol"))


def _latest_value(rows: Iterable[Dict[str, str]], field: str, default: str = "") -> str:
    for row in reversed(list(rows)):
        value = _clean(row.get(field))
        if value:
            return value
    return default


def _first_value(rows: Iterable[Dict[str, str]], fields: Sequence[str], default: str = "") -> str:
    for row in rows:
        for field in fields:
            value = _clean(row.get(field))
            if value:
                return value
    return default


def _indexed_by_symbol(rows: Iterable[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    result: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        symbol = _row_symbol(row)
        if symbol:
            result.setdefault(symbol, []).append(row)
    return result


def _codes(rows: Iterable[Dict[str, str]]) -> List[str]:
    result: List[str] = []
    for row in rows:
        for part in _clean(row.get("error_code")).replace(";", ",").split(","):
            code = part.strip()
            if code and code not in result:
                result.append(code)
    return result


def _contains_error(rows: Iterable[Dict[str, str]], code: str) -> bool:
    needle = str(code)
    fields = (
        "error_code",
        "error_message",
        "raw_error_message",
        "normalized_error_class",
        "live_subscription_status",
        "error_codes_detected",
        "analysis_reason",
        "validation_reason",
        "notes",
    )
    for row in rows:
        for field in fields:
            if needle in _clean(row.get(field)):
                return True
    return False


def _delayed_available(rows: Iterable[Dict[str, str]]) -> bool:
    for row in rows:
        text = " ".join(_clean(row.get(field)) for field in row.keys())
        lowered = text.lower()
        if LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE.lower() in lowered:
            return True
        if "delayed market data available" in lowered or "延迟市场数据可用" in text:
            return True
        if _clean(row.get("error_code")) in {"10089", "354"}:
            return True
    return False


def _live_subscription_status(rows: Iterable[Dict[str, str]], default: str = "") -> str:
    row_list = list(rows)
    for row in row_list:
        if _clean(row.get("live_subscription_status")) == LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE:
            return LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE
        if _clean(row.get("normalized_error_class")) == LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE:
            return LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE
    latest = _latest_value(row_list, "live_subscription_status", default)
    if latest:
        return latest
    if _delayed_available(row_list):
        return LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE
    return default


def _safe_flag(rows: Iterable[Dict[str, str]], field: str) -> str:
    for row in rows:
        if _truthy(row.get(field)):
            return TRUE_TEXT
    return FALSE_TEXT


def _action_allowed(rows: Iterable[Dict[str, str]]) -> str:
    for row in rows:
        value = _clean(row.get("action_allowed"))
        if value and value.lower() != FALSE_TEXT:
            return TRUE_TEXT
    return FALSE_TEXT


def _manual_review_required(rows: Iterable[Dict[str, str]]) -> str:
    for row in rows:
        if _truthy(row.get("manual_review_required")):
            return TRUE_TEXT
    return TRUE_TEXT


def _has_safety_issue(row: DailyOperatorHandoffRow) -> bool:
    if row.action_allowed != FALSE_TEXT:
        return True
    return any(
        getattr(row, field) == TRUE_TEXT
        for field in (
            "broker_execution_triggered",
            "historical_data_request_triggered",
            "account_read_triggered",
            "position_read_triggered",
            "telegram_send_triggered",
        )
    )


def _price_status(snapshot_status: str, price: str) -> str:
    if price:
        return "usable_price"
    if not snapshot_status or _lower(snapshot_status) in {"missing", "empty_file", "unavailable", "unknown"}:
        return "unavailable"
    return "no_price"


def _reference_only_status(market_data_type: str, data_delay_flag: str, final_bucket: str, live_subscription_status: str) -> str:
    lowered = {_lower(market_data_type), _lower(data_delay_flag), _lower(final_bucket)}
    if "delayed_frozen" in lowered or "stale_reference" in lowered:
        return "DELAYED_FROZEN_REFERENCE_ONLY"
    if "delayed" in lowered or "delayed_reference" in lowered:
        return "DELAYED_REFERENCE_ONLY"
    if live_subscription_status == LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE:
        return "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE_REFERENCE_ONLY"
    return "NO_REFERENCE_ONLY_STATUS"


def _recommended_action(
    *,
    action_allowed: str,
    safety_fields: Sequence[str],
    market_data_type: str,
    data_delay_flag: str,
    price_status: str,
    symbol_in_scope: bool,
    error_10089: bool,
    error_354: bool,
    live_subscription_status: str,
) -> str:
    if action_allowed != FALSE_TEXT or any(field == TRUE_TEXT for field in safety_fields):
        return "SAFETY_REVIEW_REQUIRED"
    if not symbol_in_scope:
        return "OUT_OF_SCOPE_REVIEW_BLOCKED"
    if price_status != "usable_price":
        return "NO_PRICE_REVIEW_BLOCKED"
    delayed = _lower(market_data_type) in {"delayed", "delayed_frozen"} or _lower(data_delay_flag) in {"delayed", "delayed_frozen"}
    if delayed:
        return "MANUAL_REFERENCE_REVIEW_ONLY"
    if (error_10089 or error_354) and live_subscription_status == LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE:
        return "MANUAL_REFERENCE_REVIEW_ONLY"
    return "MANUAL_REFERENCE_REVIEW_ONLY"


def _top_level_status(rows: Sequence[DailyOperatorHandoffRow]) -> str:
    if any(_has_safety_issue(row) for row in rows):
        return SAFETY_REVIEW_REQUIRED
    if any(row.recommended_operator_action == "MANUAL_REFERENCE_REVIEW_ONLY" for row in rows):
        return REFERENCE_READY
    return BLOCKED


def _default_run_id(rows: Iterable[Dict[str, str]]) -> str:
    found = _latest_value(rows, "run_id")
    if found:
        return found
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")


def _default_timestamp(rows: Iterable[Dict[str, str]]) -> str:
    for field in ("run_timestamp", "timestamp"):
        found = _latest_value(rows, field)
        if found:
            return found
    return datetime.now(timezone.utc).isoformat()


def _delayed_reference_count(snapshot_rows: Sequence[Dict[str, str]], operator_rows: Sequence[Dict[str, str]], post_rows: Sequence[Dict[str, str]]) -> str:
    from_post = _latest_value(post_rows, "delayed_reference_count")
    if from_post:
        return from_post
    symbols: set[str] = set()
    for row in list(snapshot_rows) + list(operator_rows):
        values = {_lower(row.get("effective_market_data_type")), _lower(row.get("data_delay_flag")), _lower(row.get("final_research_bucket"))}
        if "delayed" in values or "delayed_reference" in values:
            symbol = _row_symbol(row)
            if symbol:
                symbols.add(symbol)
    return str(len(symbols))


def build_daily_operator_handoff_rows(
    *,
    contract_map_rows: Iterable[Dict[str, str]] = (),
    snapshot_rows: Iterable[Dict[str, str]] = (),
    api_error_rows: Iterable[Dict[str, str]] = (),
    execution_c_rows: Iterable[Dict[str, str]] = (),
    operator_rows: Iterable[Dict[str, str]] = (),
    post_analysis_rows: Iterable[Dict[str, str]] = (),
    telegram_rows: Iterable[Dict[str, str]] = (),
) -> List[DailyOperatorHandoffRow]:
    map_list = list(contract_map_rows)
    snapshot_list = list(snapshot_rows)
    api_error_list = list(api_error_rows)
    execution_list = list(execution_c_rows)
    operator_list = list(operator_rows)
    post_list = list(post_analysis_rows)
    telegram_list = list(telegram_rows)
    all_rows = map_list + snapshot_list + api_error_list + execution_list + operator_list + post_list + telegram_list
    global_rows = execution_list + post_list
    delayed_count = _delayed_reference_count(snapshot_list, operator_list, post_list)
    run_id = _default_run_id(all_rows)
    run_timestamp = _default_timestamp(all_rows)

    by_map = _indexed_by_symbol(map_list)
    by_snapshot = _indexed_by_symbol(snapshot_list)
    by_errors = _indexed_by_symbol(api_error_list)
    by_operator = _indexed_by_symbol(operator_list)
    by_telegram = _indexed_by_symbol(telegram_list)

    symbols = sorted(set(by_map) | set(by_snapshot) | set(by_errors) | set(by_operator) | set(by_telegram))
    if not symbols:
        symbols = [""]

    rows: List[DailyOperatorHandoffRow] = []
    global_error_codes = _codes(api_error_list + snapshot_list + post_list)
    global_live_status = _live_subscription_status(post_list)
    global_error_10089 = _contains_error(api_error_list + snapshot_list + post_list, "10089")
    global_error_354 = _contains_error(api_error_list + snapshot_list + post_list, "354")
    if global_live_status != LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE:
        global_live_status = _live_subscription_status(api_error_list + snapshot_list + post_list, global_live_status)

    for symbol_key in symbols:
        symbol_rows = by_map.get(symbol_key, []) + by_snapshot.get(symbol_key, []) + by_errors.get(symbol_key, []) + by_operator.get(symbol_key, []) + by_telegram.get(symbol_key, [])
        map_rows = by_map.get(symbol_key, [])
        snapshot_symbol_rows = by_snapshot.get(symbol_key, [])
        error_symbol_rows = by_errors.get(symbol_key, [])
        operator_symbol_rows = by_operator.get(symbol_key, [])
        relevant_rows = symbol_rows + global_rows

        display_symbol = symbol_key or _first_value(relevant_rows, ("display_symbol", "symbol", "local_symbol"), "UNKNOWN")
        symbol = _first_value(map_rows + snapshot_symbol_rows + error_symbol_rows + operator_symbol_rows, ("symbol", "display_symbol", "local_symbol"), display_symbol)
        asset_route = _first_value(map_rows + snapshot_symbol_rows, ("asset_route", "exchange", "primary_exchange"))
        data_source_route = _first_value(map_rows + snapshot_symbol_rows, ("data_source_route", "fallback_stage", "price_source_priority"))
        snapshot_status = _latest_value(snapshot_symbol_rows, "snapshot_status", _latest_value(post_list, "snapshot_status", "unavailable"))
        market_data_type = _latest_value(snapshot_symbol_rows, "effective_market_data_type", _latest_value(post_list, "effective_market_data_type", "unknown"))
        data_delay_flag = _latest_value(snapshot_symbol_rows, "data_delay_flag", _latest_value(post_list, "data_delay_flag", "unavailable"))
        latest_price = _first_value(reversed(snapshot_symbol_rows), ("market_price", "last", "close", "bid", "ask"))
        reference_price = _first_value(reversed(operator_symbol_rows), ("usable_reference_price", "reference_price", "latest_price"), latest_price)
        price = reference_price or latest_price
        price_status = _price_status(snapshot_status, price)
        operator_status = _latest_value(operator_symbol_rows, "operator_packet_status", _latest_value(post_list, "operator_packet_status", "missing"))
        final_bucket = _latest_value(operator_symbol_rows, "final_research_bucket", "unavailable")
        symbol_error_codes = _codes(error_symbol_rows + snapshot_symbol_rows)
        if not symbol_error_codes:
            symbol_error_codes = global_error_codes
        error_10089 = _contains_error(error_symbol_rows + snapshot_symbol_rows, "10089") or global_error_10089
        error_354 = _contains_error(error_symbol_rows + snapshot_symbol_rows, "354") or global_error_354
        live_status = _live_subscription_status(error_symbol_rows + snapshot_symbol_rows, global_live_status)
        live_status = live_status or "LIVE_SUBSCRIPTION_STATUS_NOT_DETECTED"
        reference_only = _reference_only_status(market_data_type, data_delay_flag, final_bucket, live_status)

        action_allowed = _action_allowed(relevant_rows)
        broker_execution = _safe_flag(relevant_rows, "broker_execution_triggered")
        historical_data = _safe_flag(relevant_rows, "historical_data_request_triggered")
        account_read = _safe_flag(relevant_rows, "account_read_triggered")
        position_read = _safe_flag(relevant_rows, "position_read_triggered")
        telegram_send = _safe_flag(relevant_rows, "telegram_send_triggered")
        recommendation = _recommended_action(
            action_allowed=action_allowed,
            safety_fields=(broker_execution, historical_data, account_read, position_read, telegram_send),
            market_data_type=market_data_type,
            data_delay_flag=data_delay_flag,
            price_status=price_status,
            symbol_in_scope=bool(map_rows),
            error_10089=error_10089,
            error_354=error_354,
            live_subscription_status=live_status,
        )
        if any(word in recommendation.upper() for word in FORBIDDEN_ACTION_WORDS):
            recommendation = "SAFETY_REVIEW_REQUIRED"

        rows.append(
            DailyOperatorHandoffRow(
                top_level_status="",
                run_id=run_id,
                run_timestamp=run_timestamp,
                display_symbol=display_symbol,
                symbol=symbol,
                asset_route=asset_route,
                data_source_route=data_source_route,
                snapshot_status=snapshot_status,
                effective_market_data_type=market_data_type,
                data_delay_flag=data_delay_flag,
                latest_price=latest_price,
                reference_price=reference_price,
                price_status=price_status,
                operator_status=operator_status,
                final_research_bucket=final_bucket,
                api_error_codes=",".join(symbol_error_codes),
                error_10089_detected=TRUE_TEXT if error_10089 else FALSE_TEXT,
                error_354_detected=TRUE_TEXT if error_354 else FALSE_TEXT,
                live_subscription_status=live_status,
                reference_only_status=reference_only,
                delayed_reference_count=delayed_count,
                manual_review_required=_manual_review_required(relevant_rows),
                action_allowed=action_allowed,
                broker_execution_triggered=broker_execution,
                historical_data_request_triggered=historical_data,
                account_read_triggered=account_read,
                position_read_triggered=position_read,
                telegram_send_triggered=telegram_send,
                recommended_operator_action=recommendation,
            )
        )

    return rows


def _with_top_level_status(rows: Sequence[DailyOperatorHandoffRow], status: str) -> List[DailyOperatorHandoffRow]:
    result: List[DailyOperatorHandoffRow] = []
    for row in rows:
        values = row.__dict__.copy()
        values["top_level_status"] = status
        result.append(DailyOperatorHandoffRow(**values))
    return result


def build_daily_operator_handoff_summary(**kwargs) -> Tuple[str, List[DailyOperatorHandoffRow]]:
    rows_without_status = build_daily_operator_handoff_rows(**kwargs)
    status = _top_level_status(rows_without_status)
    return status, _with_top_level_status(rows_without_status, status)


def write_summary_csv(path: str | Path, rows: Sequence[DailyOperatorHandoffRow]) -> None:
    fields = list(DailyOperatorHandoffRow.__dataclass_fields__.keys())
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def build_markdown_report(top_level_status: str, rows: Sequence[DailyOperatorHandoffRow]) -> str:
    safety_true = any(_has_safety_issue(row) for row in rows)
    symbol_lines = "\n".join(
        f"| {row.display_symbol} | {row.snapshot_status} | {row.effective_market_data_type} | {row.price_status} | {row.operator_status} | {row.final_research_bucket} | {row.recommended_operator_action} |"
        for row in rows
    )
    error_lines = "\n".join(
        f"| {row.display_symbol} | {row.api_error_codes or 'none'} | {row.error_10089_detected} | {row.error_354_detected} | {row.live_subscription_status} |"
        for row in rows
    )
    reference_rows = [row.display_symbol for row in rows if row.recommended_operator_action == "MANUAL_REFERENCE_REVIEW_ONLY"]
    blocked_rows = [row.display_symbol for row in rows if row.recommended_operator_action.endswith("_BLOCKED")]
    next_step = (
        "stop_and_review_safety_flags"
        if top_level_status == SAFETY_REVIEW_REQUIRED
        else "manual_operator_review_reference_only_summary"
        if top_level_status == REFERENCE_READY
        else "restore_usable_reference_prices_before_operator_review"
    )
    return "\n".join(
        [
            "# Daily Operator Handoff Summary",
            "",
            "## Top-level Status",
            "",
            f"- top_level_status={top_level_status}",
            f"- delayed_reference_count={rows[0].delayed_reference_count if rows else '0'}",
            "",
            "## Safety Summary",
            "",
            f"- safety_review_required={TRUE_TEXT if safety_true else FALSE_TEXT}",
            "- action_allowed=false" if not any(row.action_allowed != FALSE_TEXT for row in rows) else "- action_allowed=review_required",
            f"- broker_execution_triggered={TRUE_TEXT if any(row.broker_execution_triggered == TRUE_TEXT for row in rows) else FALSE_TEXT}",
            f"- historical_data_request_triggered={TRUE_TEXT if any(row.historical_data_request_triggered == TRUE_TEXT for row in rows) else FALSE_TEXT}",
            f"- account_read_triggered={TRUE_TEXT if any(row.account_read_triggered == TRUE_TEXT for row in rows) else FALSE_TEXT}",
            f"- position_read_triggered={TRUE_TEXT if any(row.position_read_triggered == TRUE_TEXT for row in rows) else FALSE_TEXT}",
            f"- telegram_send_triggered={TRUE_TEXT if any(row.telegram_send_triggered == TRUE_TEXT for row in rows) else FALSE_TEXT}",
            "",
            "## Symbol Table",
            "",
            "| symbol | snapshot_status | market_data_type | price_status | operator_status | final_research_bucket | recommended_operator_action |",
            "|---|---|---|---|---|---|---|",
            symbol_lines,
            "",
            "## API Error Summary",
            "",
            "| symbol | api_error_codes | error_10089_detected | error_354_detected | live_subscription_status |",
            "|---|---|---|---|---|",
            error_lines,
            "",
            "## Reference-only Explanation",
            "",
            f"- reference_only_symbols={','.join(reference_rows) if reference_rows else 'none'}",
            "- Delayed and delayed_frozen prices are manual reference context only.",
            "",
            "## Blocked / No-price Explanation",
            "",
            f"- blocked_symbols={','.join(blocked_rows) if blocked_rows else 'none'}",
            "- No-price or out-of-scope symbols require manual data review before handoff.",
            "",
            "## Next Operator Step",
            "",
            f"- {next_step}",
        ]
    ) + "\n"


def write_markdown_report(path: str | Path, top_level_status: str, rows: Sequence[DailyOperatorHandoffRow]) -> None:
    Path(path).write_text(build_markdown_report(top_level_status, rows), encoding="utf-8")


def build_summary_from_files(
    *,
    contract_map_csv: str | Path,
    snapshot_csv: str | Path,
    api_errors_csv: str | Path,
    execution_c_packet: str | Path,
    operator_packet: str | Path,
    post_analysis_csv: str | Path,
    telegram_notification_packet: str | Path,
) -> Tuple[str, List[DailyOperatorHandoffRow]]:
    _, contract_rows = read_csv_rows(contract_map_csv)
    _, snapshot_rows = read_csv_rows(snapshot_csv)
    _, api_rows = read_csv_rows(api_errors_csv)
    _, execution_rows = read_csv_rows(execution_c_packet)
    _, operator_rows = read_csv_rows(operator_packet)
    _, post_rows = read_csv_rows(post_analysis_csv)
    _, telegram_rows = read_csv_rows(telegram_notification_packet)
    return build_daily_operator_handoff_summary(
        contract_map_rows=contract_rows,
        snapshot_rows=snapshot_rows,
        api_error_rows=api_rows,
        execution_c_rows=execution_rows,
        operator_rows=operator_rows,
        post_analysis_rows=post_rows,
        telegram_rows=telegram_rows,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an offline daily operator handoff summary from local artifacts.")
    parser.add_argument("--contract-map-csv", default="ibkr_verified_contract_map_gld_slv.csv")
    parser.add_argument("--snapshot-csv", default="ibkr_market_data_snapshot.csv")
    parser.add_argument("--api-errors-csv", default="ibkr_market_data_api_errors.csv")
    parser.add_argument("--execution-c-packet", default="ibkr_execution_c_validation_packet.csv")
    parser.add_argument("--operator-packet", default="ibkr_daily_operator_packet.csv")
    parser.add_argument("--post-analysis-csv", default="first_operator_run_post_analysis.csv")
    parser.add_argument("--telegram-notification-packet", default="ibkr_telegram_notification_packet.csv")
    parser.add_argument("--output-csv", default="daily_operator_handoff_summary.csv")
    parser.add_argument("--output-report", default="reports/daily_operator_handoff_summary.md")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    Path(args.output_report).parent.mkdir(parents=True, exist_ok=True)
    top_level_status, rows = build_summary_from_files(
        contract_map_csv=args.contract_map_csv,
        snapshot_csv=args.snapshot_csv,
        api_errors_csv=args.api_errors_csv,
        execution_c_packet=args.execution_c_packet,
        operator_packet=args.operator_packet,
        post_analysis_csv=args.post_analysis_csv,
        telegram_notification_packet=args.telegram_notification_packet,
    )
    write_summary_csv(args.output_csv, rows)
    write_markdown_report(args.output_report, top_level_status, rows)
    print("[PASS] Daily operator handoff summary generated")
    print(f"top_level_status={top_level_status}")
    if rows:
        print(f"delayed_reference_count={rows[0].delayed_reference_count}")
        print(f"live_subscription_status={rows[0].live_subscription_status}")
    print("action_allowed=false" if not any(row.action_allowed != FALSE_TEXT for row in rows) else "action_allowed=review_required")
    print("broker_execution_triggered=false" if not any(row.broker_execution_triggered == TRUE_TEXT for row in rows) else "broker_execution_triggered=true")
    print("historical_data_request_triggered=false" if not any(row.historical_data_request_triggered == TRUE_TEXT for row in rows) else "historical_data_request_triggered=true")
    print("account_read_triggered=false" if not any(row.account_read_triggered == TRUE_TEXT for row in rows) else "account_read_triggered=true")
    print("position_read_triggered=false" if not any(row.position_read_triggered == TRUE_TEXT for row in rows) else "position_read_triggered=true")
    print("telegram_send_triggered=false" if not any(row.telegram_send_triggered == TRUE_TEXT for row in rows) else "telegram_send_triggered=true")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
