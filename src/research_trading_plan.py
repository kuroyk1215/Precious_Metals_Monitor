from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

from src.daily_operator_handoff_summary import build_summary_from_files


FALSE_TEXT = "false"
TRUE_TEXT = "true"
REFERENCE_READY = "RESEARCH_PLAN_REFERENCE_READY"
BLOCKED = "RESEARCH_PLAN_BLOCKED"
SAFETY_REVIEW_REQUIRED = "RESEARCH_PLAN_SAFETY_REVIEW_REQUIRED"
READY_STATUS = "REFERENCE_ONLY_PLAN_READY"
NO_PRICE_STATUS = "NO_PRICE_PLAN_BLOCKED"
RISK_STATUS = "RISK_REVIEW_ONLY"
OUT_OF_SCOPE_STATUS = "OUT_OF_SCOPE_BLOCKED"
FORBIDDEN_ACTION_WORDS = (
    "BUY",
    "SELL",
    "ORDER",
    "CANCEL",
    "REBALANCE",
    "AUTO_TRADE",
    "EXECUTE",
    "ENTRY_ORDER",
    "EXIT_ORDER",
)
ACTION_FIELDS = (
    "research_plan_status",
    "manual_observation_bias",
    "manual_watch_zone",
    "manual_invalid_trigger",
    "manual_exit_review_trigger",
    "risk_note",
)
SAFETY_FIELDS = (
    "action_allowed",
    "broker_execution_triggered",
    "historical_data_request_triggered",
    "account_read_triggered",
    "position_read_triggered",
    "telegram_send_triggered",
)


@dataclass(frozen=True)
class ResearchTradingPlanRow:
    plan_run_id: str
    plan_timestamp: str
    display_symbol: str
    symbol: str
    reference_price: str
    price_status: str
    data_delay_flag: str
    effective_market_data_type: str
    live_subscription_status: str
    api_error_codes: str
    operator_status: str
    recommended_operator_action: str
    research_plan_status: str
    data_quality_label: str
    market_context_label: str
    manual_observation_bias: str
    manual_watch_zone: str
    manual_invalid_trigger: str
    manual_exit_review_trigger: str
    risk_note: str
    time_horizon: str
    action_allowed: str
    broker_execution_triggered: str
    historical_data_request_triggered: str
    account_read_triggered: str
    position_read_triggered: str
    telegram_send_triggered: str


def _clean(value: object) -> str:
    return str(value or "").strip()


def _lower(value: object) -> str:
    return _clean(value).lower()


def _is_false(value: object) -> bool:
    return _lower(value) == FALSE_TEXT


def _truthy(value: object) -> bool:
    return _lower(value) in {"1", "yes", "y", "true", "triggered", "allowed"}


def _read_csv(path: Path) -> Tuple[str, List[Dict[str, str]]]:
    if not path.exists():
        return "missing", []
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return ("present" if rows else "empty", rows)


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _has_safety_issue(row: Dict[str, str]) -> bool:
    if not _is_false(row.get("action_allowed")):
        return True
    for field in SAFETY_FIELDS[1:]:
        if _truthy(row.get(field)):
            return True
    return False


def _usable_reference_price(row: Dict[str, str]) -> bool:
    return bool(_clean(row.get("reference_price"))) and _lower(row.get("price_status")) not in {"no_price", "missing", "unavailable"}


def _delayed(row: Dict[str, str]) -> bool:
    return _lower(row.get("data_delay_flag")) in {"delayed", "delayed_frozen"} or _lower(row.get("effective_market_data_type")) in {
        "delayed",
        "delayed_frozen",
    }


def _format_price(value: str) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    return f"{number:.2f}"


def _observation_band(reference_price: str) -> str:
    return f"observe around reference price +/-2% ({_format_price(reference_price)}); manual review only"


def _contains_forbidden(text: str) -> bool:
    upper = text.upper()
    return any(word in upper for word in FORBIDDEN_ACTION_WORDS)


def _sanitize_action_text(text: str) -> str:
    if not _contains_forbidden(text):
        return text
    return "manual review only"


def _row_status(row: Dict[str, str], in_scope: bool) -> Tuple[str, str, str, str, str, str, str]:
    if _has_safety_issue(row):
        return (
            RISK_STATUS,
            "RISK_REVIEW_ONLY",
            "SAFETY_REVIEW_REQUIRED",
            "SAFETY_REVIEW_REQUIRED",
            "manual review only",
            "manual review only",
            "Safety flag review required before this reference artifact can be used.",
        )
    if not in_scope:
        return (
            OUT_OF_SCOPE_STATUS,
            "RISK_REVIEW_ONLY",
            "OUT_OF_SCOPE",
            "OUT_OF_SCOPE",
            "N/A",
            "N/A",
            "Symbol is outside this GLD SLV research scope.",
        )
    if _lower(row.get("price_status")) == "no_price" or not _usable_reference_price(row):
        return (
            NO_PRICE_STATUS,
            "NO_PRICE_BLOCKED",
            "NO_PRICE",
            "NO_PRICE_BLOCKED",
            "N/A",
            "N/A",
            "Manual data review required before any research plan.",
        )
    if _delayed(row):
        return (
            READY_STATUS,
            "REFERENCE_ONLY",
            "DELAYED_USABLE_REFERENCE",
            "DELAYED_REFERENCE_ONLY",
            "manual review only if local reference differs by more than 3%",
            "manual review only if reference context changes materially",
            "Reference-only research artifact from delayed data; manual review required; no broker or account calls.",
        )
    return (
        READY_STATUS,
        "MANUAL_WATCH_ONLY",
        "USABLE_REFERENCE",
        "REFERENCE_ONLY",
        "manual review only if local reference differs by more than 3%",
        "manual review only if reference context changes materially",
        "Reference-only research artifact; manual review required; no broker or account calls.",
    )


def _build_row(source_row: Dict[str, str], plan_run_id: str, plan_timestamp: str) -> ResearchTradingPlanRow:
    display_symbol = _clean(source_row.get("display_symbol")) or _clean(source_row.get("symbol")) or "UNKNOWN"
    in_scope = display_symbol in {"GLD", "SLV"} or _clean(source_row.get("symbol")) in {"GLD", "SLV"}
    status, bias, quality, context, invalid_trigger, exit_trigger, risk_note = _row_status(source_row, in_scope)
    reference_price = _clean(source_row.get("reference_price"))
    watch_zone = _observation_band(reference_price) if status == READY_STATUS else "N/A"
    action = _clean(source_row.get("recommended_operator_action")) or "MANUAL_REFERENCE_REVIEW_ONLY"

    values = {
        "plan_run_id": plan_run_id,
        "plan_timestamp": plan_timestamp,
        "display_symbol": display_symbol,
        "symbol": _clean(source_row.get("symbol")) or display_symbol,
        "reference_price": reference_price,
        "price_status": _clean(source_row.get("price_status")) or "missing",
        "data_delay_flag": _clean(source_row.get("data_delay_flag")) or "missing",
        "effective_market_data_type": _clean(source_row.get("effective_market_data_type")) or "missing",
        "live_subscription_status": _clean(source_row.get("live_subscription_status")) or "missing",
        "api_error_codes": _clean(source_row.get("api_error_codes")) or "none",
        "operator_status": _clean(source_row.get("operator_status")) or "missing",
        "recommended_operator_action": action,
        "research_plan_status": status,
        "data_quality_label": quality,
        "market_context_label": context,
        "manual_observation_bias": bias,
        "manual_watch_zone": watch_zone,
        "manual_invalid_trigger": invalid_trigger,
        "manual_exit_review_trigger": exit_trigger,
        "risk_note": risk_note,
        "time_horizon": "manual review session",
        "action_allowed": FALSE_TEXT if _is_false(source_row.get("action_allowed")) else TRUE_TEXT,
        "broker_execution_triggered": TRUE_TEXT if _truthy(source_row.get("broker_execution_triggered")) else FALSE_TEXT,
        "historical_data_request_triggered": TRUE_TEXT if _truthy(source_row.get("historical_data_request_triggered")) else FALSE_TEXT,
        "account_read_triggered": TRUE_TEXT if _truthy(source_row.get("account_read_triggered")) else FALSE_TEXT,
        "position_read_triggered": TRUE_TEXT if _truthy(source_row.get("position_read_triggered")) else FALSE_TEXT,
        "telegram_send_triggered": TRUE_TEXT if _truthy(source_row.get("telegram_send_triggered")) else FALSE_TEXT,
    }
    for field in ACTION_FIELDS:
        values[field] = _sanitize_action_text(values[field])
    return ResearchTradingPlanRow(**values)


def _default_blocked_rows() -> List[Dict[str, str]]:
    return [
        {
            "display_symbol": symbol,
            "symbol": symbol,
            "reference_price": "",
            "price_status": "no_price",
            "data_delay_flag": "missing",
            "effective_market_data_type": "missing",
            "live_subscription_status": "missing",
            "api_error_codes": "none",
            "operator_status": "missing",
            "recommended_operator_action": "NO_PRICE_REVIEW_BLOCKED",
            "action_allowed": FALSE_TEXT,
            "broker_execution_triggered": FALSE_TEXT,
            "historical_data_request_triggered": FALSE_TEXT,
            "account_read_triggered": FALSE_TEXT,
            "position_read_triggered": FALSE_TEXT,
            "telegram_send_triggered": FALSE_TEXT,
        }
        for symbol in ("GLD", "SLV")
    ]


def _handoff_rows_from_fallback(root: Path) -> Tuple[str, List[Dict[str, str]]]:
    status, handoff_rows = build_summary_from_files(
        contract_map_csv=root / "ibkr_verified_contract_map_gld_slv.csv",
        snapshot_csv=root / "ibkr_market_data_snapshot.csv",
        api_errors_csv=root / "ibkr_market_data_api_errors.csv",
        execution_c_packet=root / "ibkr_execution_c_validation_packet.csv",
        operator_packet=root / "ibkr_daily_operator_packet.csv",
        post_analysis_csv=root / "first_operator_run_post_analysis.csv",
        telegram_notification_packet=root / "ibkr_telegram_notification_packet.csv",
    )
    rows = [row.__dict__.copy() for row in handoff_rows]
    return status, rows


PathLike = Union[str, Path]


def load_source_handoff_rows(root: PathLike = ".") -> Tuple[str, List[Dict[str, str]], str]:
    root_path = Path(root)
    for artifact_path, source_name in (
        (root_path / "latest_daily_operator_handoff_summary.csv", "latest_daily_operator_handoff_summary.csv"),
        (root_path / "daily_operator_handoff_summary.csv", "daily_operator_handoff_summary.csv"),
    ):
        status, rows = _read_csv(artifact_path)
        if rows:
            return status, rows, source_name

    fallback_inputs = [
        root_path / "first_operator_run_post_analysis.csv",
        root_path / "ibkr_execution_c_validation_packet.csv",
        root_path / "ibkr_daily_operator_packet.csv",
        root_path / "ibkr_market_data_snapshot.csv",
        root_path / "ibkr_market_data_api_errors.csv",
    ]
    if any(path.exists() for path in fallback_inputs):
        _, rows = _handoff_rows_from_fallback(root_path)
        if rows:
            return "fallback_built", rows, "fallback_operator_artifacts"

    return "missing", _default_blocked_rows(), "missing_operator_artifacts"


def top_level_status(rows: Sequence[ResearchTradingPlanRow]) -> str:
    if any(
        row.action_allowed != FALSE_TEXT
        or row.broker_execution_triggered == TRUE_TEXT
        or row.historical_data_request_triggered == TRUE_TEXT
        or row.account_read_triggered == TRUE_TEXT
        or row.position_read_triggered == TRUE_TEXT
        or row.telegram_send_triggered == TRUE_TEXT
        for row in rows
    ):
        return SAFETY_REVIEW_REQUIRED
    if any(row.research_plan_status == READY_STATUS for row in rows):
        return REFERENCE_READY
    return BLOCKED


def build_research_trading_plan(root: PathLike = ".") -> Tuple[str, List[ResearchTradingPlanRow], str]:
    source_status, source_rows, source_name = load_source_handoff_rows(root)
    plan_run_id = f"research_plan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_UTC')}"
    plan_timestamp = _now_timestamp()
    rows = [_build_row(row, plan_run_id, plan_timestamp) for row in source_rows]
    return top_level_status(rows), rows, f"{source_name}:{source_status}"


def write_plan_csv(path: PathLike, rows: Sequence[ResearchTradingPlanRow]) -> None:
    fields = list(ResearchTradingPlanRow.__dataclass_fields__.keys())
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def _safety_line(rows: Sequence[ResearchTradingPlanRow], field: str) -> str:
    value = TRUE_TEXT if any(getattr(row, field) == TRUE_TEXT for row in rows) else FALSE_TEXT
    if field == "action_allowed":
        value = FALSE_TEXT if all(row.action_allowed == FALSE_TEXT for row in rows) else TRUE_TEXT
    return f"- {field}={value}"


def build_markdown_report(top_status: str, rows: Sequence[ResearchTradingPlanRow], source_name: str) -> str:
    table = "\n".join(
        f"| {row.display_symbol} | {row.reference_price or 'N/A'} | {row.price_status} | {row.data_delay_flag} | {row.research_plan_status} | {row.manual_observation_bias} | {row.manual_watch_zone} |"
        for row in rows
    )
    quality = "\n".join(f"- {row.display_symbol}: {row.data_quality_label} / {row.market_context_label}" for row in rows)
    risk_notes = "\n".join(f"- {row.display_symbol}: {row.risk_note}" for row in rows)
    no_price = ",".join(row.display_symbol for row in rows if row.research_plan_status == NO_PRICE_STATUS) or "none"
    reference = ",".join(row.display_symbol for row in rows if row.research_plan_status == READY_STATUS) or "none"
    next_step = (
        "manual_safety_review"
        if top_status == SAFETY_REVIEW_REQUIRED
        else "manual_reference_review"
        if top_status == REFERENCE_READY
        else "manual_data_review"
    )
    return "\n".join(
        [
            "# Research Trading Plan Report",
            "",
            "## Top-level Status",
            "",
            f"- top_level_status={top_status}",
            f"- source_artifact={source_name}",
            "",
            "## Safety Summary",
            "",
            *[_safety_line(rows, field) for field in SAFETY_FIELDS],
            "",
            "## Data Quality Summary",
            "",
            quality,
            "",
            "## Symbol Research Table",
            "",
            "| symbol | reference_price | price_status | data_delay_flag | research_plan_status | manual_observation_bias | manual_watch_zone |",
            "|---|---|---|---|---|---|---|",
            table,
            "",
            "## Reference-only Explanation",
            "",
            f"- reference_only_symbols={reference}",
            "- Delayed usable prices are manual reference context only.",
            "",
            "## No-price Blocked Explanation",
            "",
            f"- no_price_symbols={no_price}",
            "- No-price symbols require manual data review before any research plan.",
            "",
            "## Risk Notes",
            "",
            risk_notes,
            "",
            "## Next Operator Step",
            "",
            f"- {next_step}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, top_status: str, rows: Sequence[ResearchTradingPlanRow], source_name: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(build_markdown_report(top_status, rows, source_name), encoding="utf-8")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an offline GLD SLV manual reference research plan from local handoff artifacts.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-csv", default="research_trading_plan.csv")
    parser.add_argument("--output-report", default="reports/research_trading_plan_report.md")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    top_status, rows, source_name = build_research_trading_plan(args.root)
    write_plan_csv(args.output_csv, rows)
    write_markdown_report(args.output_report, top_status, rows, source_name)
    print("[PASS] Research trading plan generated")
    print(f"top_level_status={top_status}")
    for field in SAFETY_FIELDS:
        print(_safety_line(rows, field)[2:])
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
