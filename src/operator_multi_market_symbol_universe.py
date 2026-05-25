from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

READY_STATUS = "MULTI_MARKET_SYMBOL_SCHEMA_READY"
REVIEW_STATUS = "MULTI_MARKET_SYMBOL_SCHEMA_REVIEW_REQUIRED"
NO_GO_STATUS = "MULTI_MARKET_SYMBOL_SCHEMA_NO_GO"

UNIVERSE_FIELDS = (
    "generated_at",
    "market",
    "symbol",
    "display_name",
    "asset_type",
    "currency",
    "timezone",
    "trading_unit",
    "settlement_rule",
    "exchange_hint",
    "data_source_expected",
    "ibkr_contract_expected",
    "local_market_symbol",
    "enabled_for_observation",
    "enabled_for_trading",
    "manual_only",
    "research_only",
    "observation_only",
    "trading_actions_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "telegram_real_send_allowed",
    "diagnostic_reason",
)

SCHEMA_GATE_FIELDS = (
    "generated_at",
    "schema_gate_status",
    "markets_present",
    "jp_symbol_count",
    "cn_symbol_count",
    "us_symbol_count",
    "trading_unit_rules_present",
    "settlement_rules_present",
    "timezone_rules_present",
    "all_trading_disabled",
    "all_observation_enabled",
    "no_account_or_position_read",
    "no_historical_data_request",
    "no_real_telegram_send",
    "diagnostic_reason",
)

MARKET_RULES = {
    "JP": {
        "currency": "JPY",
        "timezone": "JST",
        "trading_unit": "100_share_round_lot",
        "settlement_rule": "TSE_close_15:30_JST;closing_auction_15:25-15:30_JST",
        "exchange_hint": "TSE",
        "diagnostic_reason": "JP rule: JST;100_share_round_lot;TSE_close_15:30;closing_auction_15:25-15:30",
    },
    "CN": {
        "currency": "CNY",
        "timezone": "CST",
        "trading_unit": "ordinary_stock_100_share_integer_multiple",
        "settlement_rule": "A_share_common_stock_and_stock_etf_T+1",
        "exchange_hint": "SSE/SZSE",
        "diagnostic_reason": "CN rule: CST;ordinary_stock_100_share_integer_multiple;A_share_common_stock_and_stock_etf_T+1",
    },
    "US": {
        "currency": "USD",
        "timezone": "ET/JST",
        "trading_unit": "default_whole_share",
        "settlement_rule": "IBKR_cash_account;settled_cash;T+1",
        "exchange_hint": "NYSE/NASDAQ/ARCA",
        "diagnostic_reason": "US rule: ET/JST;IBKR_cash_account;settled_cash;default_whole_share;T+1",
    },
}

SYMBOL_UNIVERSE = (
    ("JP", "1540.T", "1540.T", "gold_etf", "true"),
    ("JP", "1542.T", "1542.T", "silver_etf", "true"),
    ("JP", "7203.T", "Toyota", "large_cap", "true"),
    ("JP", "6758.T", "Sony", "large_cap", "true"),
    ("JP", "9432.T", "NTT", "large_cap", "true"),
    ("JP", "8035.T", "Tokyo Electron", "semiconductor", "true"),
    ("US", "GLD", "GLD", "gold_etf", "true"),
    ("US", "SLV", "SLV", "silver_etf", "true"),
    ("US", "AAPL", "AAPL", "large_cap", "true"),
    ("US", "MSFT", "MSFT", "large_cap", "true"),
    ("US", "NVDA", "NVDA", "semiconductor", "true"),
    ("US", "SPY", "SPY", "broad_market_etf", "true"),
    ("CN", "518880.SH", "518880.SH", "gold_etf", "unknown"),
    ("CN", "600519.SH", "600519.SH", "large_cap", "unknown"),
    ("CN", "600276.SH", "600276.SH", "pharma", "unknown"),
    ("CN", "601138.SH", "601138.SH", "manufacturing", "unknown"),
    ("CN", "002130.SZ", "002130.SZ", "manufacturing", "unknown"),
    ("CN", "510300.SH", "510300.SH", "broad_market_etf", "unknown"),
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _is_true(value: object) -> bool:
    return str(value or "").strip().lower() == TRUE_TEXT


def _is_false(value: object) -> bool:
    return str(value or "").strip().lower() == FALSE_TEXT


def build_multi_market_symbol_universe_rows(*, generated_at: Optional[str] = None) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    rows: List[Dict[str, str]] = []
    for market, symbol, display_name, asset_type, ibkr_expected in SYMBOL_UNIVERSE:
        rules = MARKET_RULES[market]
        diagnostic = [
            "static_multi_market_symbol_universe_only",
            "no_ibkr_contract_qualification",
            "no_real_market_data",
            "no_account_or_position_read",
            "no_historical_data_request",
            "no_telegram_real_send",
            rules["diagnostic_reason"],
        ]
        if symbol == "518880.SH":
            diagnostic.append("518880.SH_ibkr_availability_not_assumed_local_market_symbol_only")
        rows.append(
            {
                "generated_at": timestamp,
                "market": market,
                "symbol": symbol,
                "display_name": display_name,
                "asset_type": asset_type,
                "currency": rules["currency"],
                "timezone": rules["timezone"],
                "trading_unit": rules["trading_unit"],
                "settlement_rule": rules["settlement_rule"],
                "exchange_hint": rules["exchange_hint"],
                "data_source_expected": "static_symbol_universe_only",
                "ibkr_contract_expected": ibkr_expected,
                "local_market_symbol": TRUE_TEXT,
                "enabled_for_observation": TRUE_TEXT,
                "enabled_for_trading": FALSE_TEXT,
                "manual_only": TRUE_TEXT,
                "research_only": TRUE_TEXT,
                "observation_only": TRUE_TEXT,
                "trading_actions_allowed": FALSE_TEXT,
                "order_action_allowed": FALSE_TEXT,
                "cancel_action_allowed": FALSE_TEXT,
                "rebalance_action_allowed": FALSE_TEXT,
                "account_read_allowed": FALSE_TEXT,
                "position_read_allowed": FALSE_TEXT,
                "historical_data_request_allowed": FALSE_TEXT,
                "telegram_real_send_allowed": FALSE_TEXT,
                "diagnostic_reason": ";".join(diagnostic),
            }
        )
    return rows


def build_multi_market_symbol_schema_gate_row(
    rows: Sequence[Dict[str, str]],
    *,
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    timestamp = generated_at or (rows[0]["generated_at"] if rows else _now_timestamp())
    markets = {row.get("market", "") for row in rows}
    required_markets = {"JP", "CN", "US"}
    missing_markets = sorted(required_markets - markets)
    jp_count = sum(1 for row in rows if row.get("market") == "JP")
    cn_count = sum(1 for row in rows if row.get("market") == "CN")
    us_count = sum(1 for row in rows if row.get("market") == "US")

    all_trading_disabled = bool(rows) and all(_is_false(row.get("enabled_for_trading")) for row in rows)
    all_observation_enabled = bool(rows) and all(_is_true(row.get("enabled_for_observation")) for row in rows)
    trading_unit_rules_present = bool(rows) and all(bool(row.get("trading_unit")) for row in rows)
    settlement_rules_present = bool(rows) and all(bool(row.get("settlement_rule")) for row in rows)
    timezone_rules_present = bool(rows) and all(bool(row.get("timezone")) for row in rows)
    no_account_or_position_read = bool(rows) and all(
        _is_false(row.get("account_read_allowed")) and _is_false(row.get("position_read_allowed")) for row in rows
    )
    no_historical_data_request = bool(rows) and all(_is_false(row.get("historical_data_request_allowed")) for row in rows)
    no_real_telegram_send = bool(rows) and all(_is_false(row.get("telegram_real_send_allowed")) for row in rows)

    if any(_is_true(row.get("enabled_for_trading")) for row in rows):
        status = NO_GO_STATUS
        reason = "one_or_more_symbols_enabled_for_trading"
    elif missing_markets:
        status = REVIEW_STATUS
        reason = "missing_markets:" + ",".join(missing_markets)
    elif not all_trading_disabled:
        status = REVIEW_STATUS
        reason = "symbol_trading_disabled_marker_missing"
    else:
        status = READY_STATUS
        reason = "JP_CN_US_present_all_symbols_trading_disabled_static_schema_ready"

    return {
        "generated_at": timestamp,
        "schema_gate_status": status,
        "markets_present": ",".join(sorted(markets)),
        "jp_symbol_count": str(jp_count),
        "cn_symbol_count": str(cn_count),
        "us_symbol_count": str(us_count),
        "trading_unit_rules_present": TRUE_TEXT if trading_unit_rules_present else FALSE_TEXT,
        "settlement_rules_present": TRUE_TEXT if settlement_rules_present else FALSE_TEXT,
        "timezone_rules_present": TRUE_TEXT if timezone_rules_present else FALSE_TEXT,
        "all_trading_disabled": TRUE_TEXT if all_trading_disabled else FALSE_TEXT,
        "all_observation_enabled": TRUE_TEXT if all_observation_enabled else FALSE_TEXT,
        "no_account_or_position_read": TRUE_TEXT if no_account_or_position_read else FALSE_TEXT,
        "no_historical_data_request": TRUE_TEXT if no_historical_data_request else FALSE_TEXT,
        "no_real_telegram_send": TRUE_TEXT if no_real_telegram_send else FALSE_TEXT,
        "diagnostic_reason": reason,
    }


def _write_rows_csv(path: PathLike, rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: PathLike, rows: Sequence[Dict[str, str]], schema_gate: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": schema_gate["generated_at"],
        "schema_gate_status": schema_gate["schema_gate_status"],
        "markets_present": schema_gate["markets_present"],
        "symbol_count": len(rows),
        "schema_gate": schema_gate,
        "symbols": list(rows),
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_universe_markdown(rows: Sequence[Dict[str, str]], schema_gate: Dict[str, str]) -> str:
    lines = [
        "# Operator Multi-Market Symbol Universe",
        "",
        "## Scope",
        "",
        "- static JP / CN / US symbol universe and unified schema only",
        "- manual-only / research-only / observation-only",
        "- no IBKR, TWS, Gateway, real market data, account read, position read, historical data request, Telegram real send, trading, order, cancel, or rebalance",
        "- no buy/sell points and no automatic trading advice",
        "",
        "## Schema Gate",
        "",
    ]
    lines.extend(f"- {field}={schema_gate[field]}" for field in SCHEMA_GATE_FIELDS)
    lines.extend(
        [
            "",
            "## Market Rules",
            "",
            "- JP: JST; 100_share_round_lot; TSE closes at 15:30; closing auction 15:25-15:30",
            "- CN: CST; ordinary_stock_100_share_integer_multiple; A_share_common_stock_and_stock_etf_T+1",
            "- US: ET/JST; IBKR cash account; settled cash; default_whole_share; T+1",
            "",
            "## Symbols",
            "",
            "| market | symbol | display_name | asset_type | currency | timezone | trading_unit | settlement_rule | enabled_for_observation | enabled_for_trading |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| {market} | {symbol} | {display_name} | {asset_type} | {currency} | {timezone} | {trading_unit} | {settlement_rule} | {enabled_for_observation} | {enabled_for_trading} |".format(
                **row
            )
        )
    lines.extend(["", "## Safety Assertions", ""])
    for row in rows:
        lines.append(
            "- {symbol}: enabled_for_trading={enabled_for_trading}; trading_actions_allowed={trading_actions_allowed}; "
            "account_read_allowed={account_read_allowed}; position_read_allowed={position_read_allowed}; "
            "historical_data_request_allowed={historical_data_request_allowed}; telegram_real_send_allowed={telegram_real_send_allowed}; "
            "manual_only={manual_only}; research_only={research_only}; observation_only={observation_only}; diagnostic_reason={diagnostic_reason}".format(
                **row
            )
        )
    return "\n".join(lines) + "\n"


def build_schema_gate_markdown(row: Dict[str, str]) -> str:
    lines = [
        "# Operator Multi-Market Symbol Schema Gate",
        "",
        "## Scope",
        "",
        "- validates only the static JP / CN / US symbol universe schema",
        "- confirms trading disabled and observation enabled markers",
        "- no external service, market data, account, position, historical data, Telegram, or trading action",
        "",
        "## Gate",
        "",
    ]
    lines.extend(f"- {field}={row[field]}" for field in SCHEMA_GATE_FIELDS)
    return "\n".join(lines) + "\n"


def _write_text(path: PathLike, text: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def generate_multi_market_symbol_universe(
    *,
    output_csv: PathLike = "operator_multi_market_symbol_universe.csv",
    output_json: PathLike = "operator_multi_market_symbol_universe.json",
    output_report: PathLike = "reports/operator_multi_market_symbol_universe.md",
    schema_gate_csv: PathLike = "operator_multi_market_symbol_schema_gate.csv",
    schema_gate_report: PathLike = "reports/operator_multi_market_symbol_schema_gate_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, object]:
    rows = build_multi_market_symbol_universe_rows(generated_at=generated_at)
    gate = build_multi_market_symbol_schema_gate_row(rows, generated_at=generated_at)
    _write_rows_csv(output_csv, rows, UNIVERSE_FIELDS)
    _write_json(output_json, rows, gate)
    _write_text(output_report, build_universe_markdown(rows, gate))
    _write_rows_csv(schema_gate_csv, [gate], SCHEMA_GATE_FIELDS)
    _write_text(schema_gate_report, build_schema_gate_markdown(gate))
    return {"rows": rows, "schema_gate": gate}


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 498-502 multi-market symbol universe schema.")
    parser.add_argument("--output-csv", default="operator_multi_market_symbol_universe.csv")
    parser.add_argument("--output-json", default="operator_multi_market_symbol_universe.json")
    parser.add_argument("--output-report", default="reports/operator_multi_market_symbol_universe.md")
    parser.add_argument("--schema-gate-csv", default="operator_multi_market_symbol_schema_gate.csv")
    parser.add_argument("--schema-gate-report", default="reports/operator_multi_market_symbol_schema_gate_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    result = generate_multi_market_symbol_universe(
        output_csv=args.output_csv,
        output_json=args.output_json,
        output_report=args.output_report,
        schema_gate_csv=args.schema_gate_csv,
        schema_gate_report=args.schema_gate_report,
        generated_at=args.generated_at,
    )
    gate = result["schema_gate"]
    print("[MULTI_MARKET_SYMBOL_UNIVERSE] generated")
    print(
        "schema_gate_status={}:jp_symbol_count={}:cn_symbol_count={}:us_symbol_count={}".format(
            gate["schema_gate_status"],
            gate["jp_symbol_count"],
            gate["cn_symbol_count"],
            gate["us_symbol_count"],
        )
    )
    print("NOTICE: Static symbol universe only. No IBKR, market data, account, position, historical data, Telegram, or trading action.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
