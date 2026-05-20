from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Union
from zoneinfo import ZoneInfo

from src.primary_metals_inference_research_plan_integration import (
    RESEARCH_PLAN_PRICE_CONFIRMED,
    RESEARCH_PLAN_THEORETICAL_ONLY,
    build_primary_metals_inference_research_plan_rows,
)


TRUE_TEXT = "true"
FALSE_TEXT = "false"

PHASE = "Phase 23A-23C"

READY = "READY"
INPUT_REQUIRED = "INPUT_REQUIRED"

FINAL_REVIEW_THEORETICAL_ONLY = "FINAL_REVIEW_THEORETICAL_ONLY"
FINAL_REVIEW_PRICE_CONFIRMED = "FINAL_REVIEW_PRICE_CONFIRMED"
FINAL_REVIEW_BLOCKED = "FINAL_REVIEW_BLOCKED"

FINAL_DECISION_RESEARCH_ONLY_THEORETICAL_RANGE = "RESEARCH_ONLY_THEORETICAL_RANGE"
FINAL_DECISION_RESEARCH_ONLY_PRICE_CONFIRMED = "RESEARCH_ONLY_PRICE_CONFIRMED"
FINAL_DECISION_INPUT_REQUIRED = "INPUT_REQUIRED"

DEFAULT_WARNING_FLAGS = (
    "PRIMARY_METALS_FINAL_REVIEW_PACK_INTEGRATION_DEFINED",
    "FINAL_REVIEW_RESEARCH_ONLY",
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
    "phase23a23c_primary_metals_final_review_pack_integration",
)


@dataclass(frozen=True)
class PrimaryMetalsFinalReviewPackRow:
    row_id: str
    row_name: str
    source_layer: str
    input_source: str
    component: str
    status: str
    final_decision: str
    metal: str
    etf_symbol: str
    market_direction: str
    theoretical_fair_value: str
    etf_actual_price: str
    etf_data_status: str
    market_signal_available: str
    theoretical_range_allowed: str
    execution_price_confidence: str
    research_plan_available: str
    direction_summary_allowed: str
    high_confidence_buy_sell_point_allowed: str
    execution_price_required_before_trade: str
    final_review_available: str
    final_direction_summary_allowed: str
    final_theoretical_range_allowed: str
    final_high_confidence_execution_allowed: str
    final_action_allowed: str
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
    "final_decision",
    "metal",
    "etf_symbol",
    "market_direction",
    "theoretical_fair_value",
    "etf_actual_price",
    "etf_data_status",
    "market_signal_available",
    "theoretical_range_allowed",
    "execution_price_confidence",
    "research_plan_available",
    "direction_summary_allowed",
    "high_confidence_buy_sell_point_allowed",
    "execution_price_required_before_trade",
    "final_review_available",
    "final_direction_summary_allowed",
    "final_theoretical_range_allowed",
    "final_high_confidence_execution_allowed",
    "final_action_allowed",
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


def _status_and_decision(plan_row):
    if plan_row.research_plan_available != TRUE_TEXT:
        return FINAL_REVIEW_BLOCKED, FINAL_DECISION_INPUT_REQUIRED

    if plan_row.status == RESEARCH_PLAN_PRICE_CONFIRMED:
        return FINAL_REVIEW_PRICE_CONFIRMED, FINAL_DECISION_RESEARCH_ONLY_PRICE_CONFIRMED

    if plan_row.status == RESEARCH_PLAN_THEORETICAL_ONLY:
        return (
            FINAL_REVIEW_THEORETICAL_ONLY,
            FINAL_DECISION_RESEARCH_ONLY_THEORETICAL_RANGE,
        )

    return FINAL_REVIEW_BLOCKED, FINAL_DECISION_INPUT_REQUIRED


def _make_final_review_row(input_source, plan_row, timestamp_jst, timestamp_et):
    status, final_decision = _status_and_decision(plan_row)

    final_review_available = plan_row.research_plan_available == TRUE_TEXT
    final_direction_allowed = plan_row.direction_summary_allowed == TRUE_TEXT
    final_theoretical_allowed = plan_row.theoretical_range_allowed == TRUE_TEXT

    # Phase 23 remains research-only: even with ETF price confirmed, final action remains blocked.
    final_high_confidence_execution_allowed = (
        plan_row.high_confidence_buy_sell_point_allowed == TRUE_TEXT
        and plan_row.execution_price_confidence == "HIGH"
    )

    evidence = (
        "research_plan_available={};direction_summary_allowed={};"
        "theoretical_range_allowed={};execution_price_confidence={};"
        "high_confidence_buy_sell_point_allowed={};final_action_allowed=false"
    ).format(
        plan_row.research_plan_available,
        plan_row.direction_summary_allowed,
        plan_row.theoretical_range_allowed,
        plan_row.execution_price_confidence,
        plan_row.high_confidence_buy_sell_point_allowed,
    )

    return PrimaryMetalsFinalReviewPackRow(
        row_id="FINAL_REVIEW_{}".format(plan_row.metal.upper()),
        row_name="{} primary metals final review pack integration".format(plan_row.metal),
        source_layer=PHASE,
        input_source=str(input_source),
        component="Phase 23A-23C",
        status=status,
        final_decision=final_decision,
        metal=plan_row.metal,
        etf_symbol=plan_row.etf_symbol,
        market_direction=plan_row.market_direction,
        theoretical_fair_value=plan_row.theoretical_fair_value,
        etf_actual_price=plan_row.etf_actual_price,
        etf_data_status=plan_row.etf_data_status,
        market_signal_available=plan_row.market_signal_available,
        theoretical_range_allowed=plan_row.theoretical_range_allowed,
        execution_price_confidence=plan_row.execution_price_confidence,
        research_plan_available=plan_row.research_plan_available,
        direction_summary_allowed=plan_row.direction_summary_allowed,
        high_confidence_buy_sell_point_allowed=plan_row.high_confidence_buy_sell_point_allowed,
        execution_price_required_before_trade=plan_row.execution_price_required_before_trade,
        final_review_available=TRUE_TEXT if final_review_available else FALSE_TEXT,
        final_direction_summary_allowed=TRUE_TEXT if final_direction_allowed else FALSE_TEXT,
        final_theoretical_range_allowed=TRUE_TEXT if final_theoretical_allowed else FALSE_TEXT,
        final_high_confidence_execution_allowed=(
            TRUE_TEXT if final_high_confidence_execution_allowed else FALSE_TEXT
        ),
        final_action_allowed=FALSE_TEXT,
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
                "FINAL_REVIEW_THEORETICAL_ONLY"
                if status == FINAL_REVIEW_THEORETICAL_ONLY
                else "FINAL_REVIEW_PRICE_CONFIRMED"
                if status == FINAL_REVIEW_PRICE_CONFIRMED
                else "FINAL_REVIEW_BLOCKED",
            ]
        ),
        notes=(
            "Final review pack integration only. This layer distinguishes market direction, "
            "theoretical range, and high-confidence ETF execution readiness. If ETF actual price "
            "is missing, final review may allow direction and theoretical range but blocks "
            "high-confidence ETF execution points. No IBKR connection, market data request, "
            "historical data request, contract request, or trading action is performed."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_primary_metals_final_review_pack_rows(
    input_source: Union[str, Path] = "config.yaml",
):
    timestamp_jst, timestamp_et = _now_pair()
    plan_rows = build_primary_metals_inference_research_plan_rows(input_source)

    rows = [
        _make_final_review_row(str(input_source), row, timestamp_jst, timestamp_et)
        for row in _actual_plan_rows(plan_rows)
    ]

    final_review_count = sum(1 for row in rows if row.final_review_available == TRUE_TEXT)
    direction_count = sum(1 for row in rows if row.final_direction_summary_allowed == TRUE_TEXT)
    theoretical_count = sum(1 for row in rows if row.final_theoretical_range_allowed == TRUE_TEXT)
    low_confidence_count = sum(
        1 for row in rows if row.execution_price_confidence == "LOW"
    )
    high_confidence_count = sum(
        1 for row in rows if row.final_high_confidence_execution_allowed == TRUE_TEXT
    )

    final_status = READY if final_review_count > 0 else INPUT_REQUIRED

    final_decision = FINAL_DECISION_INPUT_REQUIRED
    if final_review_count > 0 and low_confidence_count > 0:
        final_decision = FINAL_DECISION_RESEARCH_ONLY_THEORETICAL_RANGE
    elif final_review_count > 0 and high_confidence_count > 0:
        final_decision = FINAL_DECISION_RESEARCH_ONLY_PRICE_CONFIRMED

    rows.append(
        PrimaryMetalsFinalReviewPackRow(
            row_id="FINAL",
            row_name="Final primary metals final review pack decision",
            source_layer=PHASE,
            input_source=str(input_source),
            component="Phase 23A-23C",
            status=final_status,
            final_decision=final_decision,
            metal="portfolio",
            etf_symbol="1540.T;1542.T",
            market_direction="mixed",
            theoretical_fair_value="mixed",
            etf_actual_price="mixed",
            etf_data_status="mixed",
            market_signal_available=TRUE_TEXT if direction_count > 0 else FALSE_TEXT,
            theoretical_range_allowed=TRUE_TEXT if theoretical_count > 0 else FALSE_TEXT,
            execution_price_confidence=(
                "LOW"
                if low_confidence_count > 0 or final_review_count > 0
                else "NONE"
            ),
            research_plan_available=TRUE_TEXT if final_review_count > 0 else FALSE_TEXT,
            direction_summary_allowed=TRUE_TEXT if direction_count > 0 else FALSE_TEXT,
            high_confidence_buy_sell_point_allowed=FALSE_TEXT,
            execution_price_required_before_trade=TRUE_TEXT,
            final_review_available=TRUE_TEXT if final_review_count > 0 else FALSE_TEXT,
            final_direction_summary_allowed=TRUE_TEXT if direction_count > 0 else FALSE_TEXT,
            final_theoretical_range_allowed=TRUE_TEXT if theoretical_count > 0 else FALSE_TEXT,
            final_high_confidence_execution_allowed=FALSE_TEXT,
            final_action_allowed=FALSE_TEXT,
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
                "final_review_count={};direction_count={};theoretical_count={};"
                "low_confidence_count={};high_confidence_count={};final_action_allowed=false"
            ).format(
                final_review_count,
                direction_count,
                theoretical_count,
                low_confidence_count,
                high_confidence_count,
            ),
            warning_flags=_flags(["FINAL_PRIMARY_METALS_REVIEW_PACK"]),
            notes=(
                "Final review summary. Direction and theoretical range may be available, but final "
                "action remains blocked. High-confidence ETF execution requires confirmed ETF actual "
                "price and remains non-trading in this layer."
            ),
            timestamp_jst=timestamp_jst,
            timestamp_et=timestamp_et,
        )
    )

    return rows


def write_primary_metals_final_review_pack_csv(
    path: Union[str, Path],
    rows: Iterable[PrimaryMetalsFinalReviewPackRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_primary_metals_final_review_pack_report(
    path: Union[str, Path],
    rows: Iterable[PrimaryMetalsFinalReviewPackRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    actual_rows = [row for row in row_list if row.row_id != "FINAL"]

    final_row = row_list[-1] if row_list else None
    final_status = final_row.status if final_row else INPUT_REQUIRED
    final_decision = final_row.final_decision if final_row else FINAL_DECISION_INPUT_REQUIRED

    final_review_count = sum(1 for row in actual_rows if row.final_review_available == TRUE_TEXT)
    direction_count = sum(
        1 for row in actual_rows if row.final_direction_summary_allowed == TRUE_TEXT
    )
    theoretical_count = sum(
        1 for row in actual_rows if row.final_theoretical_range_allowed == TRUE_TEXT
    )
    low_confidence_count = sum(
        1 for row in actual_rows if row.execution_price_confidence == "LOW"
    )
    high_confidence_exec_count = sum(
        1 for row in actual_rows if row.final_high_confidence_execution_allowed == TRUE_TEXT
    )
    final_action_allowed_count = sum(
        1 for row in row_list if row.final_action_allowed == TRUE_TEXT
    )

    lines = [
        "# Phase 23A-23C Primary Metals Final Review Pack Integration Report",
        "",
        "- phase: Phase 23A-23C",
        "- scope: integrate primary metals research plan into final review pack",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- final_status: {final_status}",
        f"- final_decision: {final_decision}",
        f"- final_review_available_count: {final_review_count}",
        f"- final_direction_summary_allowed_count: {direction_count}",
        f"- final_theoretical_range_allowed_count: {theoretical_count}",
        f"- low_execution_price_confidence_count: {low_confidence_count}",
        f"- final_high_confidence_execution_allowed_count: {high_confidence_exec_count}",
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
        "| row_id | metal | etf_symbol | status | final_decision | market_direction | theoretical_fair_value | etf_actual_price | etf_data_status | execution_price_confidence | final_direction_summary_allowed | final_theoretical_range_allowed | final_high_confidence_execution_allowed | final_action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
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
                    row.final_decision,
                    row.market_direction,
                    row.theoretical_fair_value,
                    row.etf_actual_price,
                    row.etf_data_status,
                    row.execution_price_confidence,
                    row.final_direction_summary_allowed,
                    row.final_theoretical_range_allowed,
                    row.final_high_confidence_execution_allowed,
                    row.final_action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Final Review Rule",
            "",
            "- Market direction can be included in the final review pack when primary metals inference is available.",
            "- Theoretical ranges can be included when theoretical fair value is available.",
            "- If ETF actual price is missing, execution_price_confidence remains LOW and high-confidence ETF execution points are blocked.",
            "- final_action_allowed is always false in this research-only layer.",
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
