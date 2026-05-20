from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Union
from zoneinfo import ZoneInfo

from src.final_research_trading_plan_output import (
    build_final_research_trading_plan_rows,
)


TRUE_TEXT = "true"
FALSE_TEXT = "false"

PHASE = "Phase 25A-27C"

READY = "READY"
INPUT_REQUIRED = "INPUT_REQUIRED"

ORCHESTRATOR_THEORETICAL_ROUTE = "ORCHESTRATOR_THEORETICAL_ROUTE"
ORCHESTRATOR_PRICE_CONFIRMED_ROUTE = "ORCHESTRATOR_PRICE_CONFIRMED_ROUTE"
ORCHESTRATOR_BLOCKED = "ORCHESTRATOR_BLOCKED"

DATA_ROUTE_PRIMARY_METALS_THEORETICAL = "PRIMARY_METALS_THEORETICAL_ROUTE"
DATA_ROUTE_ETF_PRICE_CONFIRMED = "ETF_PRICE_CONFIRMED_ROUTE"
DATA_ROUTE_INPUT_REQUIRED = "INPUT_REQUIRED"

RISK_TRIGGER_MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
RISK_TRIGGER_EXECUTION_PRICE_REQUIRED = "EXECUTION_PRICE_REQUIRED"
RISK_TRIGGER_INPUT_REQUIRED = "INPUT_REQUIRED"

PLAN_DECISION_THEORETICAL_RANGE_ONLY = "THEORETICAL_RANGE_ONLY"
PLAN_DECISION_PRICE_CONFIRMED_RESEARCH_ONLY = "PRICE_CONFIRMED_RESEARCH_ONLY"
PLAN_DECISION_INPUT_REQUIRED = "INPUT_REQUIRED"

DEFAULT_WARNING_FLAGS = (
    "FINAL_RESEARCH_PLAN_ORCHESTRATOR_DEFINED",
    "ONE_COMMAND_FINAL_PLAN",
    "MANUAL_RESEARCH_ONLY",
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
    "phase25a27c_final_research_plan_orchestrator",
)


@dataclass(frozen=True)
class FinalResearchPlanOrchestratorRow:
    row_id: str
    row_name: str
    source_layer: str
    input_source: str
    component: str
    status: str
    plan_decision: str
    data_route: str
    risk_trigger: str
    metal: str
    etf_symbol: str
    market_direction: str
    theoretical_fair_value: str
    etf_actual_price: str
    etf_data_status: str
    data_gap_status: str
    execution_price_confidence: str
    final_research_plan_available: str
    market_direction_summary_allowed: str
    theoretical_range_allowed: str
    manual_review_required: str
    execution_price_required_before_trade: str
    high_confidence_buy_sell_point_allowed: str
    execution_trigger_allowed: str
    final_action_allowed: str
    orchestrator_available: str
    one_command_output_available: str
    allowed_output_summary: str
    blocked_output_summary: str
    risk_warning: str
    user_next_step: str
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
    "data_route",
    "risk_trigger",
    "metal",
    "etf_symbol",
    "market_direction",
    "theoretical_fair_value",
    "etf_actual_price",
    "etf_data_status",
    "data_gap_status",
    "execution_price_confidence",
    "final_research_plan_available",
    "market_direction_summary_allowed",
    "theoretical_range_allowed",
    "manual_review_required",
    "execution_price_required_before_trade",
    "high_confidence_buy_sell_point_allowed",
    "execution_trigger_allowed",
    "final_action_allowed",
    "orchestrator_available",
    "one_command_output_available",
    "allowed_output_summary",
    "blocked_output_summary",
    "risk_warning",
    "user_next_step",
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


def _actual_plan_rows(rows):
    return [row for row in rows if row.row_id != "FINAL"]


def _classify_route(plan_row):
    if plan_row.final_research_plan_available != TRUE_TEXT:
        return ORCHESTRATOR_BLOCKED, PLAN_DECISION_INPUT_REQUIRED, DATA_ROUTE_INPUT_REQUIRED

    if plan_row.data_gap_status == "ETF_ACTUAL_PRICE_CONFIRMED":
        return (
            ORCHESTRATOR_PRICE_CONFIRMED_ROUTE,
            PLAN_DECISION_PRICE_CONFIRMED_RESEARCH_ONLY,
            DATA_ROUTE_ETF_PRICE_CONFIRMED,
        )

    return (
        ORCHESTRATOR_THEORETICAL_ROUTE,
        PLAN_DECISION_THEORETICAL_RANGE_ONLY,
        DATA_ROUTE_PRIMARY_METALS_THEORETICAL,
    )


def _risk_trigger(plan_row, data_route):
    if data_route == DATA_ROUTE_INPUT_REQUIRED:
        return RISK_TRIGGER_INPUT_REQUIRED
    if plan_row.execution_price_required_before_trade == TRUE_TEXT:
        return RISK_TRIGGER_EXECUTION_PRICE_REQUIRED
    return RISK_TRIGGER_MANUAL_REVIEW_REQUIRED


def _user_next_step(row_status, data_route):
    if data_route == DATA_ROUTE_PRIMARY_METALS_THEORETICAL:
        return (
            "Use market direction and theoretical range only; confirm actual ETF price manually "
            "before any trade decision."
        )
    if data_route == DATA_ROUTE_ETF_PRICE_CONFIRMED:
        return (
            "Review confirmed ETF price, liquidity, spread, and manual risk limits before any "
            "trade decision; this layer still emits no action."
        )
    return "Provide primary metals inputs and USDJPY before generating a final research plan."


def _make_orchestrator_row(input_source, plan_row, timestamp_jst, timestamp_et):
    status, plan_decision, data_route = _classify_route(plan_row)
    risk_trigger = _risk_trigger(plan_row, data_route)

    orchestrator_available = plan_row.final_research_plan_available == TRUE_TEXT
    one_command_available = orchestrator_available

    allowed_outputs = []
    if plan_row.market_direction_summary_allowed == TRUE_TEXT:
        allowed_outputs.append("market_direction")
    if plan_row.theoretical_range_allowed == TRUE_TEXT:
        allowed_outputs.append("theoretical_range")
    if orchestrator_available:
        allowed_outputs.extend(["data_gap_status", "risk_warning", "manual_review_required"])
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

    evidence = (
        "final_research_plan_available={};data_route={};risk_trigger={};"
        "execution_price_confidence={};manual_review_required={};final_action_allowed=false"
    ).format(
        plan_row.final_research_plan_available,
        data_route,
        risk_trigger,
        plan_row.execution_price_confidence,
        plan_row.manual_review_required,
    )

    return FinalResearchPlanOrchestratorRow(
        row_id="ORCHESTRATOR_{}".format(plan_row.metal.upper()),
        row_name="{} final research plan orchestrator output".format(plan_row.metal),
        source_layer=PHASE,
        input_source=str(input_source),
        component="Phase 25A-27C",
        status=status,
        plan_decision=plan_decision,
        data_route=data_route,
        risk_trigger=risk_trigger,
        metal=plan_row.metal,
        etf_symbol=plan_row.etf_symbol,
        market_direction=plan_row.market_direction,
        theoretical_fair_value=plan_row.theoretical_fair_value,
        etf_actual_price=plan_row.etf_actual_price,
        etf_data_status=plan_row.etf_data_status,
        data_gap_status=plan_row.data_gap_status,
        execution_price_confidence=plan_row.execution_price_confidence,
        final_research_plan_available=plan_row.final_research_plan_available,
        market_direction_summary_allowed=plan_row.market_direction_summary_allowed,
        theoretical_range_allowed=plan_row.theoretical_range_allowed,
        manual_review_required=TRUE_TEXT,
        execution_price_required_before_trade=TRUE_TEXT,
        high_confidence_buy_sell_point_allowed=FALSE_TEXT,
        execution_trigger_allowed=FALSE_TEXT,
        final_action_allowed=FALSE_TEXT,
        orchestrator_available=TRUE_TEXT if orchestrator_available else FALSE_TEXT,
        one_command_output_available=TRUE_TEXT if one_command_available else FALSE_TEXT,
        allowed_output_summary=";".join(allowed_outputs),
        blocked_output_summary=";".join(blocked_outputs),
        risk_warning=plan_row.risk_warning,
        user_next_step=_user_next_step(status, data_route),
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
                "PRIMARY_METALS_THEORETICAL_ROUTE"
                if data_route == DATA_ROUTE_PRIMARY_METALS_THEORETICAL
                else "ETF_PRICE_CONFIRMED_ROUTE"
                if data_route == DATA_ROUTE_ETF_PRICE_CONFIRMED
                else "INPUT_REQUIRED_ROUTE",
            ]
        ),
        notes=(
            "Final research plan orchestrator only. This row is generated by one command and "
            "summarizes data route, risk trigger, market direction, theoretical range, data gaps, "
            "and manual review requirements. It emits no high-confidence ETF execution point and "
            "no automated trading action."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_final_research_plan_orchestrator_rows(
    input_source: Union[str, Path] = "config.yaml",
):
    timestamp_jst, timestamp_et = _now_pair()
    plan_rows = build_final_research_trading_plan_rows(input_source)

    rows = [
        _make_orchestrator_row(str(input_source), row, timestamp_jst, timestamp_et)
        for row in _actual_plan_rows(plan_rows)
    ]

    orchestrator_count = sum(1 for row in rows if row.orchestrator_available == TRUE_TEXT)
    one_command_count = sum(1 for row in rows if row.one_command_output_available == TRUE_TEXT)
    direction_count = sum(1 for row in rows if row.market_direction_summary_allowed == TRUE_TEXT)
    theoretical_count = sum(1 for row in rows if row.theoretical_range_allowed == TRUE_TEXT)
    low_confidence_count = sum(1 for row in rows if row.execution_price_confidence == "LOW")
    manual_review_count = sum(1 for row in rows if row.manual_review_required == TRUE_TEXT)
    final_action_allowed_count = sum(1 for row in rows if row.final_action_allowed == TRUE_TEXT)

    final_status = READY if orchestrator_count > 0 else INPUT_REQUIRED

    final_data_route = DATA_ROUTE_INPUT_REQUIRED
    final_decision = PLAN_DECISION_INPUT_REQUIRED
    if orchestrator_count > 0 and low_confidence_count > 0:
        final_data_route = DATA_ROUTE_PRIMARY_METALS_THEORETICAL
        final_decision = PLAN_DECISION_THEORETICAL_RANGE_ONLY
    elif orchestrator_count > 0:
        final_data_route = DATA_ROUTE_ETF_PRICE_CONFIRMED
        final_decision = PLAN_DECISION_PRICE_CONFIRMED_RESEARCH_ONLY

    rows.append(
        FinalResearchPlanOrchestratorRow(
            row_id="FINAL",
            row_name="Final research plan orchestrator decision",
            source_layer=PHASE,
            input_source=str(input_source),
            component="Phase 25A-27C",
            status=final_status,
            plan_decision=final_decision,
            data_route=final_data_route,
            risk_trigger=(
                RISK_TRIGGER_EXECUTION_PRICE_REQUIRED
                if final_data_route == DATA_ROUTE_PRIMARY_METALS_THEORETICAL
                else RISK_TRIGGER_MANUAL_REVIEW_REQUIRED
                if final_data_route == DATA_ROUTE_ETF_PRICE_CONFIRMED
                else RISK_TRIGGER_INPUT_REQUIRED
            ),
            metal="portfolio",
            etf_symbol="1540.T;1542.T",
            market_direction="mixed",
            theoretical_fair_value="mixed",
            etf_actual_price="mixed",
            etf_data_status="mixed",
            data_gap_status="mixed" if orchestrator_count > 0 else "INPUT_REQUIRED",
            execution_price_confidence=(
                "LOW" if low_confidence_count > 0 or orchestrator_count > 0 else "NONE"
            ),
            final_research_plan_available=TRUE_TEXT if orchestrator_count > 0 else FALSE_TEXT,
            market_direction_summary_allowed=TRUE_TEXT if direction_count > 0 else FALSE_TEXT,
            theoretical_range_allowed=TRUE_TEXT if theoretical_count > 0 else FALSE_TEXT,
            manual_review_required=TRUE_TEXT,
            execution_price_required_before_trade=TRUE_TEXT,
            high_confidence_buy_sell_point_allowed=FALSE_TEXT,
            execution_trigger_allowed=FALSE_TEXT,
            final_action_allowed=FALSE_TEXT,
            orchestrator_available=TRUE_TEXT if orchestrator_count > 0 else FALSE_TEXT,
            one_command_output_available=TRUE_TEXT if one_command_count > 0 else FALSE_TEXT,
            allowed_output_summary=(
                "market_direction;theoretical_range;data_gap_status;risk_warning;manual_review_required"
                if orchestrator_count > 0
                else "none"
            ),
            blocked_output_summary=(
                "high_confidence_etf_buy_sell_point;execution_trigger;order_action;"
                "cancellation_action;rebalance_action;auto_trade"
            ),
            risk_warning=(
                "Final orchestrator output is research-only. Manual review and ETF execution price "
                "confirmation are required before any trade decision. final_action_allowed=false."
            ),
            user_next_step=(
                "Review the final report. Confirm ETF actual price manually before using any "
                "trade-related interpretation."
                if orchestrator_count > 0
                else "Provide primary metals inputs and USDJPY."
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
                "orchestrator_count={};one_command_count={};direction_count={};"
                "theoretical_count={};low_confidence_count={};manual_review_count={};"
                "final_action_allowed_count={}"
            ).format(
                orchestrator_count,
                one_command_count,
                direction_count,
                theoretical_count,
                low_confidence_count,
                manual_review_count,
                final_action_allowed_count,
            ),
            warning_flags=_flags(["FINAL_ORCHESTRATOR_SUMMARY"]),
            notes=(
                "One-command final research plan orchestrator summary. It composes upstream final "
                "research plan output into a compact operator-facing plan while keeping all actions blocked."
            ),
            timestamp_jst=timestamp_jst,
            timestamp_et=timestamp_et,
        )
    )

    return rows


def write_final_research_plan_orchestrator_csv(
    path: Union[str, Path],
    rows: Iterable[FinalResearchPlanOrchestratorRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_final_research_plan_orchestrator_report(
    path: Union[str, Path],
    rows: Iterable[FinalResearchPlanOrchestratorRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    actual_rows = [row for row in row_list if row.row_id != "FINAL"]

    final_row = row_list[-1] if row_list else None
    final_status = final_row.status if final_row else INPUT_REQUIRED
    plan_decision = final_row.plan_decision if final_row else PLAN_DECISION_INPUT_REQUIRED
    data_route = final_row.data_route if final_row else DATA_ROUTE_INPUT_REQUIRED

    orchestrator_count = sum(1 for row in actual_rows if row.orchestrator_available == TRUE_TEXT)
    one_command_count = sum(1 for row in actual_rows if row.one_command_output_available == TRUE_TEXT)
    direction_count = sum(1 for row in actual_rows if row.market_direction_summary_allowed == TRUE_TEXT)
    theoretical_count = sum(1 for row in actual_rows if row.theoretical_range_allowed == TRUE_TEXT)
    low_confidence_count = sum(1 for row in actual_rows if row.execution_price_confidence == "LOW")
    manual_review_count = sum(1 for row in actual_rows if row.manual_review_required == TRUE_TEXT)
    final_action_allowed_count = sum(
        1 for row in row_list if row.final_action_allowed == TRUE_TEXT
    )

    lines = [
        "# Phase 25A-27C Final Research Plan Orchestrator Report",
        "",
        "- phase: Phase 25A-27C",
        "- scope: one-command final research plan orchestrator",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- final_status: {final_status}",
        f"- plan_decision: {plan_decision}",
        f"- data_route: {data_route}",
        f"- orchestrator_available_count: {orchestrator_count}",
        f"- one_command_output_available_count: {one_command_count}",
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
        "| row_id | metal | etf_symbol | status | plan_decision | data_route | risk_trigger | market_direction | theoretical_fair_value | data_gap_status | execution_price_confidence | manual_review_required | final_action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
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
                    row.data_route,
                    row.risk_trigger,
                    row.market_direction,
                    row.theoretical_fair_value,
                    row.data_gap_status,
                    row.execution_price_confidence,
                    row.manual_review_required,
                    row.final_action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Orchestrator Rule",
            "",
            "- This is the one-command final research plan output.",
            "- Data routing promotes primary metals theoretical inference when ETF actual price is unavailable.",
            "- Risk trigger marks manual review and ETF execution price confirmation as required.",
            "- No high-confidence ETF buy/sell point is emitted.",
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
