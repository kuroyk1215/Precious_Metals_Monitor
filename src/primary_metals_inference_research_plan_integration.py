from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Union
from zoneinfo import ZoneInfo

from src.primary_metals_market_inference_layer import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    TRUE_TEXT,
    build_primary_metals_market_inference_rows,
)


FALSE_TEXT = "false"

PHASE = "Phase 22A-22C"

READY = "READY"
INPUT_REQUIRED = "INPUT_REQUIRED"
RESEARCH_PLAN_THEORETICAL_ONLY = "RESEARCH_PLAN_THEORETICAL_ONLY"
RESEARCH_PLAN_PRICE_CONFIRMED = "RESEARCH_PLAN_PRICE_CONFIRMED"
RESEARCH_PLAN_BLOCKED = "RESEARCH_PLAN_BLOCKED"

DEFAULT_WARNING_FLAGS = (
    "PRIMARY_METALS_INFERENCE_RESEARCH_PLAN_INTEGRATION_DEFINED",
    "RESEARCH_ONLY",
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
    "phase22a22c_primary_metals_inference_research_plan_integration",
)


@dataclass(frozen=True)
class PrimaryMetalsInferenceResearchPlanRow:
    row_id: str
    row_name: str
    source_layer: str
    input_source: str
    component: str
    status: str
    metal: str
    etf_symbol: str
    market_direction: str
    theoretical_fair_value: str
    etf_actual_price: str
    etf_data_status: str
    market_signal_available: str
    theoretical_value_available: str
    execution_price_confidence: str
    research_plan_available: str
    direction_summary_allowed: str
    theoretical_range_allowed: str
    high_confidence_buy_sell_point_allowed: str
    execution_price_required_before_trade: str
    execution_allowed: str
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
    "metal",
    "etf_symbol",
    "market_direction",
    "theoretical_fair_value",
    "etf_actual_price",
    "etf_data_status",
    "market_signal_available",
    "theoretical_value_available",
    "execution_price_confidence",
    "research_plan_available",
    "direction_summary_allowed",
    "theoretical_range_allowed",
    "high_confidence_buy_sell_point_allowed",
    "execution_price_required_before_trade",
    "execution_allowed",
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


def _actual_inference_rows(rows):
    return [row for row in rows if row.row_id != "FINAL"]


def _plan_status(row):
    if row.market_signal_available != TRUE_TEXT:
        return RESEARCH_PLAN_BLOCKED

    if row.execution_price_confidence == CONFIDENCE_HIGH:
        return RESEARCH_PLAN_PRICE_CONFIRMED

    if row.execution_price_confidence == CONFIDENCE_LOW:
        return RESEARCH_PLAN_THEORETICAL_ONLY

    return RESEARCH_PLAN_BLOCKED


def _make_plan_row(input_source, inference_row, timestamp_jst, timestamp_et):
    status = _plan_status(inference_row)

    research_plan_available = inference_row.market_signal_available == TRUE_TEXT
    theoretical_range_allowed = (
        inference_row.theoretical_value_available == TRUE_TEXT
        and inference_row.execution_price_confidence in {CONFIDENCE_LOW, CONFIDENCE_HIGH}
    )
    direction_summary_allowed = inference_row.market_signal_available == TRUE_TEXT
    high_confidence_allowed = (
        inference_row.high_confidence_buy_sell_point_allowed == TRUE_TEXT
        and inference_row.execution_price_confidence == CONFIDENCE_HIGH
    )

    execution_price_required = inference_row.execution_price_confidence != CONFIDENCE_HIGH

    evidence = (
        "market_signal_available={};theoretical_value_available={};"
        "execution_price_confidence={};etf_actual_price={};"
        "high_confidence_buy_sell_point_allowed={};execution_price_required_before_trade={}"
    ).format(
        inference_row.market_signal_available,
        inference_row.theoretical_value_available,
        inference_row.execution_price_confidence,
        inference_row.etf_actual_price,
        str(high_confidence_allowed).lower(),
        str(execution_price_required).lower(),
    )

    return PrimaryMetalsInferenceResearchPlanRow(
        row_id="RESEARCH_PLAN_{}".format(inference_row.metal.upper()),
        row_name="{} primary metals inference research plan integration".format(
            inference_row.metal
        ),
        source_layer=PHASE,
        input_source=str(input_source),
        component="Phase 22A-22C",
        status=status,
        metal=inference_row.metal,
        etf_symbol=inference_row.etf_symbol,
        market_direction=inference_row.market_direction,
        theoretical_fair_value=inference_row.theoretical_fair_value,
        etf_actual_price=inference_row.etf_actual_price,
        etf_data_status=inference_row.etf_data_status,
        market_signal_available=inference_row.market_signal_available,
        theoretical_value_available=inference_row.theoretical_value_available,
        execution_price_confidence=inference_row.execution_price_confidence,
        research_plan_available=TRUE_TEXT if research_plan_available else FALSE_TEXT,
        direction_summary_allowed=TRUE_TEXT if direction_summary_allowed else FALSE_TEXT,
        theoretical_range_allowed=TRUE_TEXT if theoretical_range_allowed else FALSE_TEXT,
        high_confidence_buy_sell_point_allowed=(
            TRUE_TEXT if high_confidence_allowed else FALSE_TEXT
        ),
        execution_price_required_before_trade=(
            TRUE_TEXT if execution_price_required else FALSE_TEXT
        ),
        execution_allowed=FALSE_TEXT,
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
                "THEORETICAL_ONLY_RESEARCH_PLAN"
                if status == RESEARCH_PLAN_THEORETICAL_ONLY
                else "ETF_PRICE_CONFIRMED_RESEARCH_PLAN"
                if status == RESEARCH_PLAN_PRICE_CONFIRMED
                else "RESEARCH_PLAN_BLOCKED",
            ]
        ),
        notes=(
            "Research-plan integration only. Direction summary and theoretical range may be "
            "available from primary metals inference. If ETF actual price is unavailable, "
            "execution_price_confidence remains LOW, high-confidence ETF buy/sell points are "
            "blocked, and execution_price_required_before_trade is true. No IBKR connection, "
            "market data request, historical data request, contract request, or trading action "
            "is performed."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_primary_metals_inference_research_plan_rows(
    input_source: Union[str, Path] = "config.yaml",
):
    timestamp_jst, timestamp_et = _now_pair()
    inference_rows = build_primary_metals_market_inference_rows(input_source)

    rows = [
        _make_plan_row(str(input_source), row, timestamp_jst, timestamp_et)
        for row in _actual_inference_rows(inference_rows)
    ]

    research_plan_count = sum(1 for row in rows if row.research_plan_available == TRUE_TEXT)
    theoretical_range_count = sum(
        1 for row in rows if row.theoretical_range_allowed == TRUE_TEXT
    )
    high_confidence_count = sum(
        1 for row in rows if row.high_confidence_buy_sell_point_allowed == TRUE_TEXT
    )
    low_confidence_count = sum(
        1 for row in rows if row.execution_price_confidence == CONFIDENCE_LOW
    )

    final_status = READY if research_plan_count > 0 else INPUT_REQUIRED

    rows.append(
        PrimaryMetalsInferenceResearchPlanRow(
            row_id="FINAL",
            row_name="Final primary metals inference research plan integration decision",
            source_layer=PHASE,
            input_source=str(input_source),
            component="Phase 22A-22C",
            status=final_status,
            metal="portfolio",
            etf_symbol="1540.T;1542.T",
            market_direction="mixed",
            theoretical_fair_value="mixed",
            etf_actual_price="mixed",
            etf_data_status="mixed",
            market_signal_available=TRUE_TEXT if research_plan_count > 0 else FALSE_TEXT,
            theoretical_value_available=TRUE_TEXT if theoretical_range_count > 0 else FALSE_TEXT,
            execution_price_confidence=(
                CONFIDENCE_HIGH
                if high_confidence_count == 2
                else CONFIDENCE_LOW
                if low_confidence_count > 0 or research_plan_count > 0
                else "NONE"
            ),
            research_plan_available=TRUE_TEXT if research_plan_count > 0 else FALSE_TEXT,
            direction_summary_allowed=TRUE_TEXT if research_plan_count > 0 else FALSE_TEXT,
            theoretical_range_allowed=TRUE_TEXT if theoretical_range_count > 0 else FALSE_TEXT,
            high_confidence_buy_sell_point_allowed=FALSE_TEXT,
            execution_price_required_before_trade=TRUE_TEXT,
            execution_allowed=FALSE_TEXT,
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
                "research_plan_count={};theoretical_range_count={};"
                "high_confidence_count={};low_confidence_count={};execution_allowed=false"
            ).format(
                research_plan_count,
                theoretical_range_count,
                high_confidence_count,
                low_confidence_count,
            ),
            warning_flags=_flags(["FINAL_RESEARCH_PLAN_INTEGRATION"]),
            notes=(
                "Final research-plan integration summary. Market direction and theoretical ranges "
                "can be available even when ETF actual execution prices are missing. Execution and "
                "high-confidence ETF buy/sell points remain blocked without actual ETF price confirmation."
            ),
            timestamp_jst=timestamp_jst,
            timestamp_et=timestamp_et,
        )
    )

    return rows


def write_primary_metals_inference_research_plan_csv(
    path: Union[str, Path],
    rows: Iterable[PrimaryMetalsInferenceResearchPlanRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_primary_metals_inference_research_plan_report(
    path: Union[str, Path],
    rows: Iterable[PrimaryMetalsInferenceResearchPlanRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    actual_rows = [row for row in row_list if row.row_id != "FINAL"]

    final_row = row_list[-1] if row_list else None
    final_status = final_row.status if final_row else INPUT_REQUIRED

    research_plan_count = sum(
        1 for row in actual_rows if row.research_plan_available == TRUE_TEXT
    )
    direction_count = sum(
        1 for row in actual_rows if row.direction_summary_allowed == TRUE_TEXT
    )
    theoretical_range_count = sum(
        1 for row in actual_rows if row.theoretical_range_allowed == TRUE_TEXT
    )
    low_confidence_count = sum(
        1 for row in actual_rows if row.execution_price_confidence == CONFIDENCE_LOW
    )
    high_confidence_trade_count = sum(
        1 for row in actual_rows if row.high_confidence_buy_sell_point_allowed == TRUE_TEXT
    )
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)

    lines = [
        "# Phase 22A-22C Primary Metals Inference Research Plan Integration Report",
        "",
        "- phase: Phase 22A-22C",
        "- scope: integrate primary metals inference into research plan",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- final_status: {final_status}",
        f"- research_plan_available_count: {research_plan_count}",
        f"- direction_summary_allowed_count: {direction_count}",
        f"- theoretical_range_allowed_count: {theoretical_range_count}",
        f"- low_execution_price_confidence_count: {low_confidence_count}",
        f"- high_confidence_buy_sell_point_allowed_count: {high_confidence_trade_count}",
        f"- action_allowed_count: {action_allowed_count}",
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
        "| row_id | metal | etf_symbol | status | market_direction | theoretical_fair_value | etf_actual_price | etf_data_status | research_plan_available | theoretical_range_allowed | execution_price_confidence | high_confidence_buy_sell_point_allowed | execution_price_required_before_trade | action_allowed |",
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
                    row.market_direction,
                    row.theoretical_fair_value,
                    row.etf_actual_price,
                    row.etf_data_status,
                    row.research_plan_available,
                    row.theoretical_range_allowed,
                    row.execution_price_confidence,
                    row.high_confidence_buy_sell_point_allowed,
                    row.execution_price_required_before_trade,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Integration Rule",
            "",
            "- Primary metals inference can be promoted into research-plan direction summary.",
            "- Theoretical ranges may be shown when theoretical fair value is available.",
            "- If ETF actual price is missing, execution_price_confidence is LOW and high-confidence ETF buy/sell points remain blocked.",
            "- This phase does not connect to IBKR and does not request market data.",
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
