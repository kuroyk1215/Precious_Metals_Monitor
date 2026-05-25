from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

READY_STATUS = "MULTI_MARKET_ADAPTER_SKELETON_READY"
REVIEW_STATUS = "MULTI_MARKET_ADAPTER_REVIEW_REQUIRED"
NO_GO_STATUS = "MULTI_MARKET_ADAPTER_NO_GO"

SCHEMA_READY_STATUS = "MULTI_MARKET_SYMBOL_SCHEMA_READY"
SCHEMA_REVIEW_STATUS = "MULTI_MARKET_SYMBOL_SCHEMA_REVIEW_REQUIRED"
SCHEMA_NO_GO_STATUS = "MULTI_MARKET_SYMBOL_SCHEMA_NO_GO"

ADAPTER_FIELDS = (
    "generated_at",
    "market",
    "symbol",
    "adapter_status",
    "observation_status",
    "market_rule_status",
    "timezone",
    "trading_unit",
    "settlement_rule",
    "exchange_hint",
    "data_source_expected",
    "ibkr_contract_expected",
    "local_market_symbol",
    "enabled_for_observation",
    "enabled_for_trading",
    "real_market_data_request_allowed",
    "contract_qualification_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "trading_actions_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "telegram_real_send_allowed",
    "manual_only",
    "research_only",
    "observation_only",
    "diagnostic_reason",
)

ADAPTER_GATE_FIELDS = (
    "generated_at",
    "adapter_gate_status",
    "multi_market_schema_gate_status",
    "markets_present",
    "jp_symbol_count",
    "cn_symbol_count",
    "us_symbol_count",
    "adapter_rows_count",
    "all_markets_observation_only",
    "all_symbols_trading_disabled",
    "no_real_market_data_request",
    "no_contract_qualification",
    "no_account_or_position_read",
    "no_historical_data_request",
    "no_real_telegram_send",
    "no_trading_actions",
    "diagnostic_reason",
)

REQUIRED_MARKETS = {"JP", "CN", "US"}
PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _is_true(value: object) -> bool:
    return str(value or "").strip().lower() == TRUE_TEXT


def _is_false(value: object) -> bool:
    return str(value or "").strip().lower() == FALSE_TEXT


def _read_csv_rows(path: PathLike) -> List[Dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _read_json_symbols(path: PathLike) -> List[Dict[str, str]]:
    json_path = Path(path)
    if not json_path.exists():
        return []
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    symbols = payload.get("symbols", [])
    if isinstance(symbols, list):
        return [row for row in symbols if isinstance(row, dict)]
    return []


def load_symbol_universe_rows(
    *,
    universe_csv: PathLike = "operator_multi_market_symbol_universe.csv",
    universe_json: PathLike = "operator_multi_market_symbol_universe.json",
) -> List[Dict[str, str]]:
    csv_rows = _read_csv_rows(universe_csv)
    json_rows = _read_json_symbols(universe_json)
    if not csv_rows:
        return []
    if json_rows and len(json_rows) != len(csv_rows):
        rows = [dict(row) for row in csv_rows]
        for row in rows:
            row["diagnostic_reason"] = "{};json_symbol_count_mismatch".format(row.get("diagnostic_reason", ""))
        return rows
    return csv_rows


def build_multi_market_adapter_skeleton_rows(
    universe_rows: Sequence[Dict[str, str]],
    *,
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    rows: List[Dict[str, str]] = []
    for source in universe_rows:
        diagnostic = [
            "multi_market_adapter_skeleton_static_only",
            "enabled_for_trading=false",
            "real_market_data_request_allowed=false",
            "contract_qualification_allowed=false",
            "account_read_allowed=false",
            "position_read_allowed=false",
            "historical_data_request_allowed=false",
            "telegram_real_send_allowed=false",
            "no_buy_sell_points",
            "observation_only=true",
        ]
        source_reason = source.get("diagnostic_reason", "")
        if source_reason:
            diagnostic.append(source_reason)
        rows.append(
            {
                "generated_at": timestamp,
                "market": source.get("market", ""),
                "symbol": source.get("symbol", ""),
                "adapter_status": "ADAPTER_SKELETON_STATIC_READY",
                "observation_status": "OBSERVATION_ONLY",
                "market_rule_status": "STATIC_RULE_SUMMARY_READY",
                "timezone": source.get("timezone", ""),
                "trading_unit": source.get("trading_unit", ""),
                "settlement_rule": source.get("settlement_rule", ""),
                "exchange_hint": source.get("exchange_hint", ""),
                "data_source_expected": "static_universe_adapter_skeleton_only",
                "ibkr_contract_expected": source.get("ibkr_contract_expected", ""),
                "local_market_symbol": source.get("local_market_symbol", TRUE_TEXT),
                "enabled_for_observation": source.get("enabled_for_observation", TRUE_TEXT),
                "enabled_for_trading": FALSE_TEXT,
                "real_market_data_request_allowed": FALSE_TEXT,
                "contract_qualification_allowed": FALSE_TEXT,
                "account_read_allowed": FALSE_TEXT,
                "position_read_allowed": FALSE_TEXT,
                "historical_data_request_allowed": FALSE_TEXT,
                "trading_actions_allowed": FALSE_TEXT,
                "order_action_allowed": FALSE_TEXT,
                "cancel_action_allowed": FALSE_TEXT,
                "rebalance_action_allowed": FALSE_TEXT,
                "telegram_real_send_allowed": FALSE_TEXT,
                "manual_only": TRUE_TEXT,
                "research_only": TRUE_TEXT,
                "observation_only": TRUE_TEXT,
                "diagnostic_reason": ";".join(diagnostic),
            }
        )
    return rows


def _schema_gate_status_from_universe(universe_rows: Sequence[Dict[str, str]]) -> str:
    if not universe_rows:
        return SCHEMA_REVIEW_STATUS
    markets = {row.get("market", "") for row in universe_rows}
    if any(_is_true(row.get("enabled_for_trading")) for row in universe_rows):
        return SCHEMA_NO_GO_STATUS
    if REQUIRED_MARKETS - markets:
        return SCHEMA_REVIEW_STATUS
    if not all(_is_false(row.get("enabled_for_trading")) for row in universe_rows):
        return SCHEMA_REVIEW_STATUS
    return SCHEMA_READY_STATUS


def build_multi_market_adapter_gate_row(
    rows: Sequence[Dict[str, str]],
    universe_rows: Sequence[Dict[str, str]],
    *,
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    timestamp = generated_at or (rows[0]["generated_at"] if rows else _now_timestamp())
    markets = {row.get("market", "") for row in rows}
    missing_markets = sorted(REQUIRED_MARKETS - markets)
    jp_count = sum(1 for row in rows if row.get("market") == "JP")
    cn_count = sum(1 for row in rows if row.get("market") == "CN")
    us_count = sum(1 for row in rows if row.get("market") == "US")

    all_markets_observation_only = bool(rows) and all(_is_true(row.get("observation_only")) for row in rows)
    all_symbols_trading_disabled = bool(rows) and all(_is_false(row.get("enabled_for_trading")) for row in rows)
    no_real_market_data_request = bool(rows) and all(_is_false(row.get("real_market_data_request_allowed")) for row in rows)
    no_contract_qualification = bool(rows) and all(_is_false(row.get("contract_qualification_allowed")) for row in rows)
    no_account_or_position_read = bool(rows) and all(
        _is_false(row.get("account_read_allowed")) and _is_false(row.get("position_read_allowed")) for row in rows
    )
    no_historical_data_request = bool(rows) and all(_is_false(row.get("historical_data_request_allowed")) for row in rows)
    no_real_telegram_send = bool(rows) and all(_is_false(row.get("telegram_real_send_allowed")) for row in rows)
    no_trading_actions = bool(rows) and all(
        _is_false(row.get("trading_actions_allowed"))
        and _is_false(row.get("order_action_allowed"))
        and _is_false(row.get("cancel_action_allowed"))
        and _is_false(row.get("rebalance_action_allowed"))
        for row in rows
    )
    unsafe_request = any(
        _is_true(row.get("enabled_for_trading"))
        or _is_true(row.get("real_market_data_request_allowed"))
        or _is_true(row.get("contract_qualification_allowed"))
        for row in rows
    )
    multi_market_schema_gate_status = _schema_gate_status_from_universe(universe_rows)

    if unsafe_request:
        status = NO_GO_STATUS
        reason = "enabled_trading_real_market_data_or_contract_qualification_detected"
    elif not universe_rows or missing_markets:
        status = REVIEW_STATUS
        reason = "missing_symbol_universe_or_markets:" + (",".join(missing_markets) if missing_markets else "symbol_universe")
    elif len(rows) != len(universe_rows):
        status = REVIEW_STATUS
        reason = "adapter_rows_incomplete"
    elif not all_symbols_trading_disabled:
        status = REVIEW_STATUS
        reason = "symbol_trading_disabled_marker_missing"
    else:
        status = READY_STATUS
        reason = "JP_CN_US_adapter_skeleton_complete_all_symbols_trading_disabled_observation_only"

    return {
        "generated_at": timestamp,
        "adapter_gate_status": status,
        "multi_market_schema_gate_status": multi_market_schema_gate_status,
        "markets_present": ",".join(sorted(markets)),
        "jp_symbol_count": str(jp_count),
        "cn_symbol_count": str(cn_count),
        "us_symbol_count": str(us_count),
        "adapter_rows_count": str(len(rows)),
        "all_markets_observation_only": TRUE_TEXT if all_markets_observation_only else FALSE_TEXT,
        "all_symbols_trading_disabled": TRUE_TEXT if all_symbols_trading_disabled else FALSE_TEXT,
        "no_real_market_data_request": TRUE_TEXT if no_real_market_data_request else FALSE_TEXT,
        "no_contract_qualification": TRUE_TEXT if no_contract_qualification else FALSE_TEXT,
        "no_account_or_position_read": TRUE_TEXT if no_account_or_position_read else FALSE_TEXT,
        "no_historical_data_request": TRUE_TEXT if no_historical_data_request else FALSE_TEXT,
        "no_real_telegram_send": TRUE_TEXT if no_real_telegram_send else FALSE_TEXT,
        "no_trading_actions": TRUE_TEXT if no_trading_actions else FALSE_TEXT,
        "diagnostic_reason": reason,
    }


def _write_rows_csv(path: PathLike, rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: PathLike, rows: Sequence[Dict[str, str]], gate: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": gate["generated_at"],
        "adapter_gate_status": gate["adapter_gate_status"],
        "multi_market_schema_gate_status": gate["multi_market_schema_gate_status"],
        "adapter_rows_count": len(rows),
        "adapter_gate": gate,
        "symbols": list(rows),
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_adapter_markdown(rows: Sequence[Dict[str, str]], gate: Dict[str, str]) -> str:
    lines = [
        "# Operator Multi-Market Adapter Skeleton",
        "",
        "## Scope",
        "",
        "- static JP / CN / US adapter skeleton only",
        "- manual-only / research-only / observation-only",
        "- no IBKR, TWS, Gateway, real market data request, contract qualification, account read, position read, historical data request, Telegram real send, trading, order, cancel, or rebalance",
        "- no buy/sell points and no automatic trading advice",
        "",
        "## Adapter Gate",
        "",
    ]
    lines.extend(f"- {field}={gate[field]}" for field in ADAPTER_GATE_FIELDS)
    lines.extend(
        [
            "",
            "## Symbols",
            "",
            "| market | symbol | adapter_status | observation_status | timezone | trading_unit | settlement_rule | enabled_for_trading | real_market_data_request_allowed | contract_qualification_allowed |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| {market} | {symbol} | {adapter_status} | {observation_status} | {timezone} | {trading_unit} | {settlement_rule} | {enabled_for_trading} | {real_market_data_request_allowed} | {contract_qualification_allowed} |".format(
                **row
            )
        )
    lines.extend(["", "## Safety Assertions", ""])
    for row in rows:
        lines.append(
            "- {symbol}: enabled_for_trading={enabled_for_trading}; real_market_data_request_allowed={real_market_data_request_allowed}; "
            "contract_qualification_allowed={contract_qualification_allowed}; account_read_allowed={account_read_allowed}; "
            "position_read_allowed={position_read_allowed}; historical_data_request_allowed={historical_data_request_allowed}; "
            "telegram_real_send_allowed={telegram_real_send_allowed}; trading_actions_allowed={trading_actions_allowed}; "
            "manual_only={manual_only}; research_only={research_only}; observation_only={observation_only}; diagnostic_reason={diagnostic_reason}".format(
                **row
            )
        )
    return "\n".join(lines) + "\n"


def build_adapter_gate_markdown(row: Dict[str, str]) -> str:
    lines = [
        "# Operator Multi-Market Adapter Gate",
        "",
        "## Scope",
        "",
        "- validates only the static JP / CN / US adapter skeleton",
        "- confirms observation-only and trading disabled markers",
        "- no external service, market data request, contract qualification, account, position, historical data, Telegram, or trading action",
        "",
        "## Gate",
        "",
    ]
    lines.extend(f"- {field}={row[field]}" for field in ADAPTER_GATE_FIELDS)
    return "\n".join(lines) + "\n"


def _write_text(path: PathLike, text: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def generate_multi_market_adapter_skeleton(
    *,
    universe_csv: PathLike = "operator_multi_market_symbol_universe.csv",
    universe_json: PathLike = "operator_multi_market_symbol_universe.json",
    output_csv: PathLike = "operator_multi_market_adapter_skeleton.csv",
    output_json: PathLike = "operator_multi_market_adapter_skeleton.json",
    output_report: PathLike = "reports/operator_multi_market_adapter_skeleton.md",
    adapter_gate_csv: PathLike = "operator_multi_market_adapter_gate.csv",
    adapter_gate_report: PathLike = "reports/operator_multi_market_adapter_gate_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, object]:
    universe_rows = load_symbol_universe_rows(universe_csv=universe_csv, universe_json=universe_json)
    rows = build_multi_market_adapter_skeleton_rows(universe_rows, generated_at=generated_at)
    gate = build_multi_market_adapter_gate_row(rows, universe_rows, generated_at=generated_at)
    _write_rows_csv(output_csv, rows, ADAPTER_FIELDS)
    _write_json(output_json, rows, gate)
    _write_text(output_report, build_adapter_markdown(rows, gate))
    _write_rows_csv(adapter_gate_csv, [gate], ADAPTER_GATE_FIELDS)
    _write_text(adapter_gate_report, build_adapter_gate_markdown(gate))
    return {"rows": rows, "adapter_gate": gate}


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 503-508 multi-market adapter skeleton.")
    parser.add_argument("--universe-csv", default="operator_multi_market_symbol_universe.csv")
    parser.add_argument("--universe-json", default="operator_multi_market_symbol_universe.json")
    parser.add_argument("--output-csv", default="operator_multi_market_adapter_skeleton.csv")
    parser.add_argument("--output-json", default="operator_multi_market_adapter_skeleton.json")
    parser.add_argument("--output-report", default="reports/operator_multi_market_adapter_skeleton.md")
    parser.add_argument("--adapter-gate-csv", default="operator_multi_market_adapter_gate.csv")
    parser.add_argument("--adapter-gate-report", default="reports/operator_multi_market_adapter_gate_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    result = generate_multi_market_adapter_skeleton(
        universe_csv=args.universe_csv,
        universe_json=args.universe_json,
        output_csv=args.output_csv,
        output_json=args.output_json,
        output_report=args.output_report,
        adapter_gate_csv=args.adapter_gate_csv,
        adapter_gate_report=args.adapter_gate_report,
        generated_at=args.generated_at,
    )
    gate = result["adapter_gate"]
    print("[MULTI_MARKET_ADAPTER_SKELETON] generated")
    print(
        "adapter_gate_status={}:multi_market_schema_gate_status={}:jp_symbol_count={}:cn_symbol_count={}:us_symbol_count={}".format(
            gate["adapter_gate_status"],
            gate["multi_market_schema_gate_status"],
            gate["jp_symbol_count"],
            gate["cn_symbol_count"],
            gate["us_symbol_count"],
        )
    )
    print("NOTICE: Static adapter skeleton only. No IBKR, market data request, contract qualification, account, position, historical data, Telegram, or trading action.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
