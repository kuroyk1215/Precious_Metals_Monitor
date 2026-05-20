from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Union
from zoneinfo import ZoneInfo

from src.ibkr_readonly_preflight_config_validator import _actual_text, _get_dotted, _load_config


TRUE_TEXT = "true"
FALSE_TEXT = "false"

PHASE = "Phase 21A-21C"

READY = "READY"
INPUT_REQUIRED = "INPUT_REQUIRED"
THEORETICAL_ONLY = "THEORETICAL_ONLY"
ETF_PRICE_CONFIRMED = "ETF_PRICE_CONFIRMED"

DIRECTION_UP = "UP"
DIRECTION_DOWN = "DOWN"
DIRECTION_NEUTRAL = "NEUTRAL"
DIRECTION_UNKNOWN = "UNKNOWN"

CONFIDENCE_HIGH = "HIGH"
CONFIDENCE_MEDIUM = "MEDIUM"
CONFIDENCE_LOW = "LOW"
CONFIDENCE_NONE = "NONE"

DEFAULT_WARNING_FLAGS = (
    "PRIMARY_METALS_MARKET_INFERENCE_DEFINED",
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
    "phase21a21c_primary_metals_market_inference_layer",
)


@dataclass(frozen=True)
class PrimaryMetalsMarketInferenceRow:
    row_id: str
    row_name: str
    source_layer: str
    input_source: str
    component: str
    status: str
    metal: str
    etf_symbol: str
    primary_price: str
    previous_primary_price: str
    usd_jpy: str
    conversion_factor: str
    theoretical_fair_value: str
    etf_actual_price: str
    etf_data_status: str
    market_direction: str
    market_signal_available: str
    theoretical_value_available: str
    execution_price_confidence: str
    execution_allowed: str
    high_confidence_buy_sell_point_allowed: str
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
    "primary_price",
    "previous_primary_price",
    "usd_jpy",
    "conversion_factor",
    "theoretical_fair_value",
    "etf_actual_price",
    "etf_data_status",
    "market_direction",
    "market_signal_available",
    "theoretical_value_available",
    "execution_price_confidence",
    "execution_allowed",
    "high_confidence_buy_sell_point_allowed",
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


def _as_float(value):
    text = _actual_text(value)
    if text in {"missing", "null", "", "unavailable", "not_requested"}:
        return None
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    return number


def _format_number(value):
    if value is None:
        return "unavailable"
    return "{:.6f}".format(value).rstrip("0").rstrip(".")


def _config_number(config, key):
    return _as_float(_get_dotted(config, key))


def _config_text(config, key, fallback):
    value = _actual_text(_get_dotted(config, key))
    if value in {"missing", "null", ""}:
        return fallback
    return value


def _direction(current, previous):
    if current is None or previous is None:
        return DIRECTION_UNKNOWN
    if current > previous:
        return DIRECTION_UP
    if current < previous:
        return DIRECTION_DOWN
    return DIRECTION_NEUTRAL


def _infer_one(
    input_source,
    component,
    metal,
    etf_symbol,
    primary_price,
    previous_primary_price,
    usd_jpy,
    conversion_factor,
    etf_actual_price,
    etf_data_status,
    timestamp_jst,
    timestamp_et,
):
    theoretical_value = None
    if primary_price is not None and usd_jpy is not None and conversion_factor is not None:
        theoretical_value = primary_price * usd_jpy * conversion_factor

    market_direction = _direction(primary_price, previous_primary_price)

    market_signal_available = primary_price is not None and usd_jpy is not None
    theoretical_value_available = theoretical_value is not None

    etf_price_available = etf_actual_price is not None
    if etf_price_available:
        execution_confidence = CONFIDENCE_HIGH
        status = ETF_PRICE_CONFIRMED
    elif theoretical_value_available:
        execution_confidence = CONFIDENCE_LOW
        status = THEORETICAL_ONLY
    elif market_signal_available:
        execution_confidence = CONFIDENCE_LOW
        status = THEORETICAL_ONLY
    else:
        execution_confidence = CONFIDENCE_NONE
        status = INPUT_REQUIRED

    high_confidence_allowed = etf_price_available and theoretical_value_available

    evidence = (
        "primary_price_available={};usd_jpy_available={};theoretical_value_available={};"
        "etf_price_available={};etf_data_status={};market_direction={}"
    ).format(
        str(primary_price is not None).lower(),
        str(usd_jpy is not None).lower(),
        str(theoretical_value_available).lower(),
        str(etf_price_available).lower(),
        etf_data_status,
        market_direction,
    )

    return PrimaryMetalsMarketInferenceRow(
        row_id="{}_{}".format(component.upper(), metal.upper()),
        row_name="{} primary market inference".format(metal),
        source_layer=PHASE,
        input_source=str(input_source),
        component=component,
        status=status,
        metal=metal,
        etf_symbol=etf_symbol,
        primary_price=_format_number(primary_price),
        previous_primary_price=_format_number(previous_primary_price),
        usd_jpy=_format_number(usd_jpy),
        conversion_factor=_format_number(conversion_factor),
        theoretical_fair_value=_format_number(theoretical_value),
        etf_actual_price=_format_number(etf_actual_price),
        etf_data_status=etf_data_status,
        market_direction=market_direction,
        market_signal_available=TRUE_TEXT if market_signal_available else FALSE_TEXT,
        theoretical_value_available=TRUE_TEXT if theoretical_value_available else FALSE_TEXT,
        execution_price_confidence=execution_confidence,
        execution_allowed=FALSE_TEXT,
        high_confidence_buy_sell_point_allowed=TRUE_TEXT if high_confidence_allowed else FALSE_TEXT,
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
                "ETF_PRICE_AVAILABLE" if etf_price_available else "ETF_PRICE_MISSING",
                "THEORETICAL_VALUE_AVAILABLE"
                if theoretical_value_available
                else "THEORETICAL_VALUE_MISSING",
            ]
        ),
        notes=(
            "Primary metals market inference only. This layer may infer market direction and "
            "theoretical ETF fair value from primary metal prices and USDJPY. If ETF actual price "
            "is unavailable, execution_price_confidence is LOW and high-confidence buy/sell points "
            "are not allowed. No IBKR connection, market data request, historical data request, "
            "contract request, or trading action is performed."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_primary_metals_market_inference_rows(
    input_source: Union[str, Path] = "config.yaml",
):
    timestamp_jst, timestamp_et = _now_pair()
    input_source_text = str(input_source)
    config, _load_error = _load_config(input_source)

    usd_jpy = _config_number(config, "primary_metals.usd_jpy")

    rows = []

    metals = [
        {
            "component": "Phase 21A-21C",
            "metal": "gold",
            "etf_symbol": _config_text(config, "primary_metals.gold_etf_symbol", "1540.T"),
            "primary_price": _config_number(config, "primary_metals.gold_price"),
            "previous_primary_price": _config_number(config, "primary_metals.gold_previous_price"),
            "conversion_factor": _config_number(config, "primary_metals.gold_conversion_factor"),
            "etf_actual_price": _config_number(config, "primary_metals.gold_etf_actual_price"),
            "etf_data_status": _config_text(
                config,
                "primary_metals.gold_etf_data_status",
                "NO_MARKET_DATA_SUBSCRIPTION",
            ),
        },
        {
            "component": "Phase 21A-21C",
            "metal": "silver",
            "etf_symbol": _config_text(config, "primary_metals.silver_etf_symbol", "1542.T"),
            "primary_price": _config_number(config, "primary_metals.silver_price"),
            "previous_primary_price": _config_number(config, "primary_metals.silver_previous_price"),
            "conversion_factor": _config_number(config, "primary_metals.silver_conversion_factor"),
            "etf_actual_price": _config_number(config, "primary_metals.silver_etf_actual_price"),
            "etf_data_status": _config_text(
                config,
                "primary_metals.silver_etf_data_status",
                "NO_MARKET_DATA_SUBSCRIPTION",
            ),
        },
    ]

    for item in metals:
        rows.append(
            _infer_one(
                input_source_text,
                item["component"],
                item["metal"],
                item["etf_symbol"],
                item["primary_price"],
                item["previous_primary_price"],
                usd_jpy,
                item["conversion_factor"],
                item["etf_actual_price"],
                item["etf_data_status"],
                timestamp_jst,
                timestamp_et,
            )
        )

    market_signal_count = sum(1 for row in rows if row.market_signal_available == TRUE_TEXT)
    theoretical_count = sum(1 for row in rows if row.theoretical_value_available == TRUE_TEXT)
    low_confidence_count = sum(
        1 for row in rows if row.execution_price_confidence == CONFIDENCE_LOW
    )
    high_confidence_count = sum(
        1 for row in rows if row.execution_price_confidence == CONFIDENCE_HIGH
    )

    final_status = READY if market_signal_count > 0 else INPUT_REQUIRED

    rows.append(
        PrimaryMetalsMarketInferenceRow(
            row_id="FINAL",
            row_name="Final primary metals market inference decision",
            source_layer=PHASE,
            input_source=input_source_text,
            component="Phase 21A-21C",
            status=final_status,
            metal="portfolio",
            etf_symbol="1540.T;1542.T",
            primary_price="mixed",
            previous_primary_price="mixed",
            usd_jpy=_format_number(usd_jpy),
            conversion_factor="mixed",
            theoretical_fair_value="mixed",
            etf_actual_price="mixed",
            etf_data_status="mixed",
            market_direction="mixed",
            market_signal_available=TRUE_TEXT if market_signal_count > 0 else FALSE_TEXT,
            theoretical_value_available=TRUE_TEXT if theoretical_count > 0 else FALSE_TEXT,
            execution_price_confidence=(
                CONFIDENCE_HIGH
                if high_confidence_count == 2
                else CONFIDENCE_LOW
                if low_confidence_count > 0 or market_signal_count > 0
                else CONFIDENCE_NONE
            ),
            execution_allowed=FALSE_TEXT,
            high_confidence_buy_sell_point_allowed=FALSE_TEXT,
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
                "market_signal_count={};theoretical_count={};low_confidence_count={};"
                "high_confidence_count={};execution_allowed=false"
            ).format(
                market_signal_count,
                theoretical_count,
                low_confidence_count,
                high_confidence_count,
            ),
            warning_flags=_flags(["FINAL_PRIMARY_METALS_INFERENCE"]),
            notes=(
                "Final inference summary. Market signal may be available even when ETF execution "
                "prices are missing. Execution remains blocked and high-confidence ETF buy/sell "
                "points are not allowed without actual ETF price confirmation."
            ),
            timestamp_jst=timestamp_jst,
            timestamp_et=timestamp_et,
        )
    )

    return rows


def write_primary_metals_market_inference_csv(
    path: Union[str, Path],
    rows: Iterable[PrimaryMetalsMarketInferenceRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_primary_metals_market_inference_report(
    path: Union[str, Path],
    rows: Iterable[PrimaryMetalsMarketInferenceRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    final_row = row_list[-1] if row_list else None
    final_status = final_row.status if final_row else INPUT_REQUIRED
    actual_rows = [row for row in row_list if row.row_id != "FINAL"]
    market_signal_count = sum(1 for row in actual_rows if row.market_signal_available == TRUE_TEXT)
    theoretical_count = sum(1 for row in actual_rows if row.theoretical_value_available == TRUE_TEXT)
    low_confidence_count = sum(
        1 for row in actual_rows if row.execution_price_confidence == CONFIDENCE_LOW
    )
    high_confidence_trade_count = sum(
        1 for row in actual_rows if row.high_confidence_buy_sell_point_allowed == TRUE_TEXT
    )
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)

    lines = [
        "# Phase 21A-21C Primary Metals Market Inference Layer Report",
        "",
        "- phase: Phase 21A-21C",
        "- scope: primary metals market inference when ETF direct price is unavailable",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- final_status: {final_status}",
        f"- market_signal_available_count: {market_signal_count}",
        f"- theoretical_value_available_count: {theoretical_count}",
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
        "| row_id | metal | etf_symbol | status | primary_price | usd_jpy | theoretical_fair_value | etf_actual_price | etf_data_status | market_direction | market_signal_available | execution_price_confidence | high_confidence_buy_sell_point_allowed | action_allowed |",
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
                    row.primary_price,
                    row.usd_jpy,
                    row.theoretical_fair_value,
                    row.etf_actual_price,
                    row.etf_data_status,
                    row.market_direction,
                    row.market_signal_available,
                    row.execution_price_confidence,
                    row.high_confidence_buy_sell_point_allowed,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Inference Rule",
            "",
            "- Primary metals prices and USDJPY can produce market-direction inference.",
            "- ETF actual price is required for high-confidence ETF execution price and buy/sell point judgment.",
            "- If ETF actual price is missing but primary market inputs are available, market_signal_available can be true while execution_price_confidence remains LOW.",
            "- This layer does not connect to IBKR and does not request market data.",
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
