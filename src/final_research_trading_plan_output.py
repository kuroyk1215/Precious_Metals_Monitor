from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Union
from zoneinfo import ZoneInfo

from src.primary_metals_final_review_pack_integration import (
    build_primary_metals_final_review_pack_rows,
)


TRUE_TEXT = "true"
FALSE_TEXT = "false"

PHASE = "Phase 24A-24C"

READY = "READY"
INPUT_REQUIRED = "INPUT_REQUIRED"

FINAL_PLAN_THEORETICAL_ONLY = "FINAL_PLAN_THEORETICAL_ONLY"
FINAL_PLAN_PRICE_CONFIRMED_RESEARCH_ONLY = "FINAL_PLAN_PRICE_CONFIRMED_RESEARCH_ONLY"
FINAL_PLAN_BLOCKED = "FINAL_PLAN_BLOCKED"

PLAN_DECISION_THEORETICAL_RANGE_ONLY = "THEORETICAL_RANGE_ONLY"
PLAN_DECISION_PRICE_CONFIRMED_RESEARCH_ONLY = "PRICE_CONFIRMED_RESEARCH_ONLY"
PLAN_DECISION_INPUT_REQUIRED = "INPUT_REQUIRED"

DATA_GAP_ETF_PRICE_MISSING = "ETF_ACTUAL_PRICE_MISSING"
DATA_GAP_ETF_PRICE_CONFIRMED = "ETF_ACTUAL_PRICE_CONFIRMED"
DATA_GAP_INPUT_REQUIRED = "INPUT_REQUIRED"

DEFAULT_WARNING_FLAGS = (
    "FINAL_RESEARCH_TRADING_PLAN_OUTPUT_DEFINED",
    "MANUAL_RESEARCH_ONLY",
    "NO_HIGH_CONFIDENCE_ETF_BUY_SELL_POINT",
    "NO_IBKR_CONNECTION",
    "NO_TWS_CONNECTION",
    "NO_MARKET_DATA_REQUEST",
    "NO_HISTORICAL_DATA_REQUEST",
    "NO_CONTRACT_DETAILS_REQUEST",
    "NO_CONTRACT_QUALIFICATION",
    "NO_ORDER_ACTION",
    "NO_CANCELLATION_ACTION",
    "NO_REBALANCE",
    "NO_AUTO_TRADE",
    "phase24a24c_final_research_trading_plan_output",
)


@dataclass(frozen=True)
class FinalResearchTradingPlanRow:
    row_id: str
    row_name: str
    source_layer: str
    input_source: str
    component: str
    status: str
    plan_decision: str
    metal: str
    etf_symbol: str
    market_direction: str
    theoretical_fair_value: str
    etf_actual_price: str
    etf_data_status: str
    execution_price_confidence: str
    final_research_plan_available: str
    market_direction_summary_allowed: str
    theoretical_range_allowed: str
    data_gap_status: str
    risk_warning: str
    manual_review_required: str
    execution_price_required_before_trade: str
    high_confidence_buy_sell_point_allowed: str
    execution_trigger_allowed: str
    final_action_allowed: str
    allowed_output_summary: str
    blocked_output_summary: str
    ibkr_connection_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    contract_details_request_allowed: str
    contract_qualification_allowed: str
    order_action_allowed: str
    cancellation_action_allowed: str
    rebalance_action_allowed: str
    auto_trade_allowed: str
    action_allowed: str
    evidence: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "row_id",
    "row_name",
    "source_layer",
    "input_source",
    "component",
    "status",
    "plan_decision",
    "metal",
    "etf_symbol",
    "market_direction",
    "theoretical_fair_value",
    "etf_actual_price",
    "etf_data_status",
    "execution_price_confidence",
    "final_research_plan_available",
    "market_direction_summary_allowed",
    "theoretical_range_allowed",
    "data_gap_status",
    "risk_warning",
    "manual_review_required",
    "execution_price_required_before_trade",
    "high_confidence_buy_sell_point_allowed",
    "execution_trigger_allowed",
    "final_action_allowed",
    "allowed_output_summary",
    "blocked_output_summary",
    "ibkr_connection_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "contract_details_request_allowed",
    "contract_qualification_allowed",
    "order_action_allowed",
    "cancellation_action_allowed",
    "rebalance_action_allowed",
    "auto_trade_allowed",
    "action_allowed",
    "evidence",
    "warning_flags",
    "notes",
    "timestamp_jst",
    "timestamp_et",
]


def _now_pair():
    now_utc = datetime.now(ZoneInfo("UTC"))
    return (
        now_utc.astimezone(ZoneInfo("Asia/Tokyo")).isoformat(),
        now_utc.astimezone(ZoneInfo("America/New_York")).isoformat(),
    )


def _flags(extra=()):
    values = list(DEFAULT_WARNING_FLAGS)
    for item in extra:
        if item and item not in values:
            values.append(item)
    return ";".join(values)


def _actual_review_rows(rows):
    return [row for row in rows if row.row_id != "FINAL"]


def _etf_price_confirmed(row) -> bool:
    return row.etf_actual_price not in {"", "missing", "null", "unavailable", "mixed"}


def _make_risk_warning(row, data_gap_status: str) -> str:
    if data_gap_status == DATA_GAP_ETF_PRICE_MISSING:
        return (
            "ETF actual execution price is missing; only market direction and theoretical range "
            "can be shown. Manual ETF price confirmation is required before any trading decision."
        )
    if data_gap_status == DATA_GAP_ETF_PRICE_CONFIRMED:
        return (
            "ETF actual price is available, but this layer remains research-only. Manual review is "
            "still required and final_action_allowed remains false."
        )
    return "Primary metals inputs are incomplete; final research trading plan is blocked."


def _make_plan_row(input_source, review_row, timestamp_jst, timestamp_et):
    if review_row.final_review_available != TRUE_TEXT:
        status = FINAL_PLAN_BLOCKED
        plan_decision = PLAN_DECISION_INPUT_REQUIRED
        data_gap_status = DATA_GAP_INPUT_REQUIRED
    elif _etf_price_confirmed(review_row):
        status = FINAL_PLAN_PRICE_CONFIRMED_RESEARCH_ONLY
        plan_decision = PLAN_DECISION_PRICE_CONFIRMED_RESEARCH_ONLY
        data_gap_status = DATA_GAP_ETF_PRICE_CONFIRMED
    else:
        status = FINAL_PLAN_THEORETICAL_ONLY
        plan_decision = PLAN_DECISION_THEORETICAL_RANGE_ONLY
        data_gap_status = DATA_GAP_ETF_PRICE_MISSING

    final_plan_available = review_row.final_review_available == TRUE_TEXT
    direction_allowed = review_row.final_direction_summary_allowed == TRUE_TEXT
    theoretical_allowed = review_row.final_theoretical_range_allowed == TRUE_TEXT

    allowed_outputs = []
    if direction_allowed:
        allowed_outputs.append("market_direction")
    if theoretical_allowed:
        allowed_outputs.append("theoretical_range")
    if final_plan_available:
        allowed_outputs.extend(["data_gap", "risk_warning", "manual_review_requirement"])
    if not allowed_outputs:
        allowed_outputs.append("none")

    blocked_outputs = [
        "high_confidence_etf_buy_sell_point",
        "execution_trigger",
        "order_action",
        "cancellation_action",
        "rebalance_action",
        "auto_trade",
    ]

    risk_warning = _make_risk_warning(review_row, data_gap_status)

    evidence = (
        "final_review_available={};direction_allowed={};theoretical_allowed={};"
        "execution_price_confidence={};data_gap_status={};final_action_allowed=false"
    ).format(
        review_row.final_review_available,
        review_row.final_direction_summary_allowed,
        review_row.final_theoretical_range_allowed,
        review_row.execution_price_confidence,
        data_gap_status,
    )

    return FinalResearchTradingPlanRow(
        row_id="FINAL_RESEARCH_PLAN_{}".format(review_row.metal.upper()),
        row_name="{} final research trading plan output".format(review_row.metal),
        source_layer=PHASE,
        input_source=str(input_source),
        component="Phase 24A-24C",
        status=status,
        plan_decision=plan_decision,
        metal=review_row.metal,
        etf_symbol=review_row.etf_symbol,
        market_direction=review_row.market_direction,
        theoretical_fair_value=review_row.theoretical_fair_value,
        etf_actual_price=review_row.etf_actual_price,
        etf_data_status=review_row.etf_data_status,
        execution_price_confidence=review_row.execution_price_confidence,
        final_research_plan_available=TRUE_TEXT if final_plan_available else FALSE_TEXT,
        market_direction_summary_allowed=TRUE_TEXT if direction_allowed else FALSE_TEXT,
        theoretical_range_allowed=TRUE_TEXT if theoretical_allowed else FALSE_TEXT,
        data_gap_status=data_gap_status,
        risk_warning=risk_warning,
        manual_review_required=TRUE_TEXT,
        execution_price_required_before_trade=TRUE_TEXT,
        high_confidence_buy_sell_point_allowed=FALSE_TEXT,
        execution_trigger_allowed=FALSE_TEXT,
        final_action_allowed=FALSE_TEXT,
        allowed_output_summary=";".join(allowed_outputs),
        blocked_output_summary=";".join(blocked_outputs),
        ibkr_connection_allowed=FALSE_TEXT,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        contract_details_request_allowed=FALSE_TEXT,
        contract_qualification_allowed=FALSE_TEXT,
        order_action_allowed=FALSE_TEXT,
        cancellation_action_allowed=FALSE_TEXT,
        rebalance_action_allowed=FALSE_TEXT,
        auto_trade_allowed=FALSE_TEXT,
        action_allowed=FALSE_TEXT,
        evidence=evidence,
        warning_flags=_flags(
            [
                "FINAL_PLAN_THEORETICAL_ONLY"
                if status == FINAL_PLAN_THEORETICAL_ONLY
                else "FINAL_PLAN_PRICE_CONFIRMED_RESEARCH_ONLY"
                if status == FINAL_PLAN_PRICE_CONFIRMED_RESEARCH_ONLY
                else "FINAL_PLAN_BLOCKED",
            ]
        ),
        notes=(
            "Final research trading plan output only. This layer can show market direction, "
            "theoretical range, data gaps, risk warnings, and manual review requirements. It must "
            "not output high-confidence ETF buy/sell points, execution triggers, or any automated "
            "trading instruction."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_final_research_trading_plan_rows(
    input_source: Union[str, Path] = "config.yaml",
):
    timestamp_jst, timestamp_et = _now_pair()
    review_rows = build_primary_metals_final_review_pack_rows(input_source)

    rows = [
        _make_plan_row(str(input_source), row, timestamp_jst, timestamp_et)
        for row in _actual_review_rows(review_rows)
    ]

    final_plan_count = sum(
        1 for row in rows if row.final_research_plan_available == TRUE_TEXT
    )
    direction_count = sum(
        1 for row in rows if row.market_direction_summary_allowed == TRUE_TEXT
    )
    theoretical_count = sum(
        1 for row in rows if row.theoretical_range_allowed == TRUE_TEXT
    )
    low_confidence_count = sum(
        1 for row in rows if row.execution_price_confidence == "LOW"
    )
    manual_review_count = sum(1 for row in rows if row.manual_review_required == TRUE_TEXT)
    final_action_allowed_count = sum(
        1 for row in rows if row.final_action_allowed == TRUE_TEXT
    )

    final_status = READY if final_plan_count > 0 else INPUT_REQUIRED

    plan_decision = PLAN_DECISION_INPUT_REQUIRED
    if final_plan_count > 0 and low_confidence_count > 0:
        plan_decision = PLAN_DECISION_THEORETICAL_RANGE_ONLY
    elif final_plan_count > 0:
        plan_decision = PLAN_DECISION_PRICE_CONFIRMED_RESEARCH_ONLY

    rows.append(
        FinalResearchTradingPlanRow(
            row_id="FINAL",
            row_name="Final research trading plan output decision",
            source_layer=PHASE,
            input_source=str(input_source),
            component="Phase 24A-24C",
            status=final_status,
            plan_decision=plan_decision,
            metal="portfolio",
            etf_symbol="1540.T;1542.T",
            market_direction="mixed",
            theoretical_fair_value="mixed",
            etf_actual_price="mixed",
            etf_data_status="mixed",
            execution_price_confidence=(
                "LOW" if low_confidence_count > 0 or final_plan_count > 0 else "NONE"
            ),
            final_research_plan_available=TRUE_TEXT if final_plan_count > 0 else FALSE_TEXT,
            market_direction_summary_allowed=TRUE_TEXT if direction_count > 0 else FALSE_TEXT,
            theoretical_range_allowed=TRUE_TEXT if theoretical_count > 0 else FALSE_TEXT,
            data_gap_status="mixed" if final_plan_count > 0 else DATA_GAP_INPUT_REQUIRED,
            risk_warning=(
                "Final plan is research-only. Manual review is required before any trade. "
                "No execution trigger or automated trading action is allowed."
            ),
            manual_review_required=TRUE_TEXT,
            execution_price_required_before_trade=TRUE_TEXT,
            high_confidence_buy_sell_point_allowed=FALSE_TEXT,
            execution_trigger_allowed=FALSE_TEXT,
            final_action_allowed=FALSE_TEXT,
            allowed_output_summary=(
                "market_direction;theoretical_range;data_gap;risk_warning;manual_review_requirement"
                if final_plan_count > 0
                else "none"
            ),
            blocked_output_summary=(
                "high_confidence_etf_buy_sell_point;execution_trigger;order_action;"
                "cancellation_action;rebalance_action;auto_trade"
            ),
            ibkr_connection_allowed=FALSE_TEXT,
            market_data_request_allowed=FALSE_TEXT,
            historical_data_request_allowed=FALSE_TEXT,
            contract_details_request_allowed=FALSE_TEXT,
            contract_qualification_allowed=FALSE_TEXT,
            order_action_allowed=FALSE_TEXT,
            cancellation_action_allowed=FALSE_TEXT,
            rebalance_action_allowed=FALSE_TEXT,
            auto_trade_allowed=FALSE_TEXT,
            action_allowed=FALSE_TEXT,
            evidence=(
                "final_plan_count={};direction_count={};theoretical_count={};"
                "low_confidence_count={};manual_review_count={};final_action_allowed_count={}"
            ).format(
                final_plan_count,
                direction_count,
                theoretical_count,
                low_confidence_count,
                manual_review_count,
                final_action_allowed_count,
            ),
            warning_flags=_flags(["FINAL_RESEARCH_TRADING_PLAN_SUMMARY"]),
            notes=(
                "Final output summary. This is a manual research trading plan only. It can show "
                "direction, theoretical ranges, data gaps, and risk warnings, but cannot produce "
                "high-confidence execution points or trading actions."
            ),
            timestamp_jst=timestamp_jst,
            timestamp_et=timestamp_et,
        )
    )

    return rows


def write_final_research_trading_plan_csv(
    path: Union[str, Path],
    rows: Iterable[FinalResearchTradingPlanRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_final_research_trading_plan_report(
    path: Union[str, Path],
    rows: Iterable[FinalResearchTradingPlanRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    actual_rows = [row for row in row_list if row.row_id != "FINAL"]

    final_row = row_list[-1] if row_list else None
    final_status = final_row.status if final_row else INPUT_REQUIRED
    plan_decision = final_row.plan_decision if final_row else PLAN_DECISION_INPUT_REQUIRED

    final_plan_count = sum(
        1 for row in actual_rows if row.final_research_plan_available == TRUE_TEXT
    )
    direction_count = sum(
        1 for row in actual_rows if row.market_direction_summary_allowed == TRUE_TEXT
    )
    theoretical_count = sum(
        1 for row in actual_rows if row.theoretical_range_allowed == TRUE_TEXT
    )
    low_confidence_count = sum(
        1 for row in actual_rows if row.execution_price_confidence == "LOW"
    )
    manual_review_count = sum(1 for row in actual_rows if row.manual_review_required == TRUE_TEXT)
    final_action_allowed_count = sum(
        1 for row in row_list if row.final_action_allowed == TRUE_TEXT
    )

    lines = [
        "# Phase 24A-24C Final Research Trading Plan Output Report",
        "",
        "- phase: Phase 24A-24C",
        "- scope: final manual research trading plan output",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- final_status: {final_status}",
        f"- plan_decision: {plan_decision}",
        f"- final_research_plan_available_count: {final_plan_count}",
        f"- market_direction_summary_allowed_count: {direction_count}",
        f"- theoretical_range_allowed_count: {theoretical_count}",
        f"- low_execution_price_confidence_count: {low_confidence_count}",
        f"- manual_review_required_count: {manual_review_count}",
        f"- final_action_allowed_count: {final_action_allowed_count}",
        "- ibkr_connection_allowed: false",
        "- market_data_request_allowed: false",
        "- historical_data_request_allowed: false",
        "- contract_details_request_allowed: false",
        "- contract_qualification_allowed: false",
        "- order_action_allowed: false",
        "- cancellation_action_allowed: false",
        "- rebalance_action_allowed: false",
        "- auto_trade_allowed: false",
        "- action_allowed: false",
        "",
        "## Rows",
        "",
        "| row_id | metal | etf_symbol | status | plan_decision | market_direction | theoretical_fair_value | etf_actual_price | data_gap_status | execution_price_confidence | final_research_plan_available | theoretical_range_allowed | manual_review_required | high_confidence_buy_sell_point_allowed | final_action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.row_id,
                    row.metal,
                    row.etf_symbol,
                    row.status,
                    row.plan_decision,
                    row.market_direction,
                    row.theoretical_fair_value,
                    row.etf_actual_price,
                    row.data_gap_status,
                    row.execution_price_confidence,
                    row.final_research_plan_available,
                    row.theoretical_range_allowed,
                    row.manual_review_required,
                    row.high_confidence_buy_sell_point_allowed,
                    row.final_action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Final Output Rule",
            "",
            "- Market direction may be shown when primary metals inference is available.",
            "- Theoretical ranges may be shown when theoretical fair value is available.",
            "- ETF actual price gaps must be shown as data gaps.",
            "- manual_review_required is true.",
            "- high-confidence ETF buy/sell points are not emitted in this layer.",
            "- final_action_allowed is always false.",
            "",
            "## Safety Statement",
            "",
            "- no IBKR connection",
            "- no TWS connection",
            "- no market data request",
            "- no historical data request",
            "- no contract details request",
            "- no real contract qualification",
            "- no order action",
            "- no cancellation action",
            "- no rebalance",
            "- no auto trade",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
