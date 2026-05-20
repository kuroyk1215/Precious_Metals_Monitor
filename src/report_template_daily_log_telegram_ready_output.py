from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Union
from zoneinfo import ZoneInfo

from src.final_research_plan_orchestrator import build_final_research_plan_orchestrator_rows


TRUE_TEXT = "true"
FALSE_TEXT = "false"

PHASE = "Phase 28A-30C"

READY = "READY"
INPUT_REQUIRED = "INPUT_REQUIRED"

OUTPUT_READY = "OUTPUT_READY"
OUTPUT_BLOCKED = "OUTPUT_BLOCKED"

TELEGRAM_READY = "TELEGRAM_READY"
TELEGRAM_BLOCKED = "TELEGRAM_BLOCKED"

DEFAULT_WARNING_FLAGS = (
    "REPORT_TEMPLATE_DAILY_LOG_TELEGRAM_READY_OUTPUT_DEFINED",
    "TELEGRAM_TEXT_ONLY",
    "NO_TELEGRAM_API_CALL",
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
    "phase28a30c_report_template_daily_log_telegram_ready_output",
)


@dataclass(frozen=True)
class ReportTemplateDailyLogTelegramRow:
    row_id: str
    row_name: str
    source_layer: str
    input_source: str
    component: str
    status: str
    telegram_status: str
    metal: str
    etf_symbol: str
    market_direction: str
    theoretical_fair_value: str
    etf_actual_price: str
    etf_data_status: str
    data_route: str
    data_gap_status: str
    risk_trigger: str
    risk_warning: str
    execution_price_confidence: str
    final_research_plan_available: str
    market_direction_summary_allowed: str
    theoretical_range_allowed: str
    manual_review_required: str
    execution_price_required_before_trade: str
    high_confidence_buy_sell_point_allowed: str
    final_action_allowed: str
    report_section_available: str
    daily_log_ready: str
    telegram_text_ready: str
    telegram_api_called: str
    markdown_summary: str
    telegram_message: str
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
    "telegram_status",
    "metal",
    "etf_symbol",
    "market_direction",
    "theoretical_fair_value",
    "etf_actual_price",
    "etf_data_status",
    "data_route",
    "data_gap_status",
    "risk_trigger",
    "risk_warning",
    "execution_price_confidence",
    "final_research_plan_available",
    "market_direction_summary_allowed",
    "theoretical_range_allowed",
    "manual_review_required",
    "execution_price_required_before_trade",
    "high_confidence_buy_sell_point_allowed",
    "final_action_allowed",
    "report_section_available",
    "daily_log_ready",
    "telegram_text_ready",
    "telegram_api_called",
    "markdown_summary",
    "telegram_message",
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


def _actual_orchestrator_rows(rows):
    return [row for row in rows if row.row_id != "FINAL"]


def _short_value(value: str) -> str:
    if value in {"", "missing", "null", "unavailable", "mixed"}:
        return "N/A"
    return str(value)


def _make_markdown_summary(row) -> str:
    return (
        f"### {row.metal.upper()} / {row.etf_symbol}\\n"
        f"- market_direction: {row.market_direction}\\n"
        f"- theoretical_fair_value: {_short_value(row.theoretical_fair_value)}\\n"
        f"- etf_actual_price: {_short_value(row.etf_actual_price)}\\n"
        f"- data_route: {row.data_route}\\n"
        f"- data_gap_status: {row.data_gap_status}\\n"
        f"- execution_price_confidence: {row.execution_price_confidence}\\n"
        f"- manual_review_required: true\\n"
        f"- final_action_allowed: false"
    )


def _make_telegram_message(row) -> str:
    return (
        f"[{row.metal.upper()} {row.etf_symbol}] "
        f"direction={row.market_direction}; "
        f"theoretical={_short_value(row.theoretical_fair_value)}; "
        f"data_gap={row.data_gap_status}; "
        f"confidence={row.execution_price_confidence}; "
        "manual_review=true; action_allowed=false"
    )


def _make_output_row(input_source, orchestrator_row, timestamp_jst, timestamp_et):
    available = orchestrator_row.orchestrator_available == TRUE_TEXT
    status = OUTPUT_READY if available else OUTPUT_BLOCKED
    telegram_status = TELEGRAM_READY if available else TELEGRAM_BLOCKED

    markdown_summary = _make_markdown_summary(orchestrator_row) if available else "INPUT_REQUIRED"
    telegram_message = _make_telegram_message(orchestrator_row) if available else "INPUT_REQUIRED"

    evidence = (
        "orchestrator_available={};data_route={};risk_trigger={};"
        "manual_review_required={};final_action_allowed=false;telegram_api_called=false"
    ).format(
        orchestrator_row.orchestrator_available,
        orchestrator_row.data_route,
        orchestrator_row.risk_trigger,
        orchestrator_row.manual_review_required,
    )

    return ReportTemplateDailyLogTelegramRow(
        row_id="OUTPUT_{}".format(orchestrator_row.metal.upper()),
        row_name="{} report template daily log telegram-ready output".format(
            orchestrator_row.metal
        ),
        source_layer=PHASE,
        input_source=str(input_source),
        component="Phase 28A-30C",
        status=status,
        telegram_status=telegram_status,
        metal=orchestrator_row.metal,
        etf_symbol=orchestrator_row.etf_symbol,
        market_direction=orchestrator_row.market_direction,
        theoretical_fair_value=orchestrator_row.theoretical_fair_value,
        etf_actual_price=orchestrator_row.etf_actual_price,
        etf_data_status=orchestrator_row.etf_data_status,
        data_route=orchestrator_row.data_route,
        data_gap_status=orchestrator_row.data_gap_status,
        risk_trigger=orchestrator_row.risk_trigger,
        risk_warning=orchestrator_row.risk_warning,
        execution_price_confidence=orchestrator_row.execution_price_confidence,
        final_research_plan_available=orchestrator_row.final_research_plan_available,
        market_direction_summary_allowed=orchestrator_row.market_direction_summary_allowed,
        theoretical_range_allowed=orchestrator_row.theoretical_range_allowed,
        manual_review_required=TRUE_TEXT,
        execution_price_required_before_trade=TRUE_TEXT,
        high_confidence_buy_sell_point_allowed=FALSE_TEXT,
        final_action_allowed=FALSE_TEXT,
        report_section_available=TRUE_TEXT if available else FALSE_TEXT,
        daily_log_ready=TRUE_TEXT if available else FALSE_TEXT,
        telegram_text_ready=TRUE_TEXT if available else FALSE_TEXT,
        telegram_api_called=FALSE_TEXT,
        markdown_summary=markdown_summary,
        telegram_message=telegram_message,
        user_next_step=orchestrator_row.user_next_step,
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
        warning_flags=_flags(["TELEGRAM_READY_TEXT_ONLY" if available else "OUTPUT_INPUT_REQUIRED"]),
        notes=(
            "Report template, daily log, and Telegram-ready text only. This layer formats final "
            "research plan output for human review and optional external delivery by the operator. "
            "It does not call Telegram API, does not connect to IBKR, and does not perform any "
            "trading action."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_report_template_daily_log_telegram_rows(
    input_source: Union[str, Path] = "config.yaml",
):
    timestamp_jst, timestamp_et = _now_pair()
    orchestrator_rows = build_final_research_plan_orchestrator_rows(input_source)

    rows = [
        _make_output_row(str(input_source), row, timestamp_jst, timestamp_et)
        for row in _actual_orchestrator_rows(orchestrator_rows)
    ]

    output_ready_count = sum(1 for row in rows if row.report_section_available == TRUE_TEXT)
    telegram_ready_count = sum(1 for row in rows if row.telegram_text_ready == TRUE_TEXT)
    daily_log_ready_count = sum(1 for row in rows if row.daily_log_ready == TRUE_TEXT)
    final_action_allowed_count = sum(1 for row in rows if row.final_action_allowed == TRUE_TEXT)

    final_status = READY if output_ready_count > 0 else INPUT_REQUIRED

    rows.append(
        ReportTemplateDailyLogTelegramRow(
            row_id="FINAL",
            row_name="Final report template daily log telegram-ready output decision",
            source_layer=PHASE,
            input_source=str(input_source),
            component="Phase 28A-30C",
            status=final_status,
            telegram_status=TELEGRAM_READY if telegram_ready_count > 0 else TELEGRAM_BLOCKED,
            metal="portfolio",
            etf_symbol="1540.T;1542.T",
            market_direction="mixed",
            theoretical_fair_value="mixed",
            etf_actual_price="mixed",
            etf_data_status="mixed",
            data_route="mixed" if output_ready_count > 0 else "INPUT_REQUIRED",
            data_gap_status="mixed" if output_ready_count > 0 else "INPUT_REQUIRED",
            risk_trigger="MANUAL_REVIEW_REQUIRED" if output_ready_count > 0 else "INPUT_REQUIRED",
            risk_warning=(
                "Final report is research-only. Manual review is required; Telegram text is generated but not sent."
                if output_ready_count > 0
                else "Primary metals inputs are incomplete; report output is blocked."
            ),
            execution_price_confidence="LOW" if output_ready_count > 0 else "NONE",
            final_research_plan_available=TRUE_TEXT if output_ready_count > 0 else FALSE_TEXT,
            market_direction_summary_allowed=TRUE_TEXT if output_ready_count > 0 else FALSE_TEXT,
            theoretical_range_allowed=TRUE_TEXT if output_ready_count > 0 else FALSE_TEXT,
            manual_review_required=TRUE_TEXT,
            execution_price_required_before_trade=TRUE_TEXT,
            high_confidence_buy_sell_point_allowed=FALSE_TEXT,
            final_action_allowed=FALSE_TEXT,
            report_section_available=TRUE_TEXT if output_ready_count > 0 else FALSE_TEXT,
            daily_log_ready=TRUE_TEXT if daily_log_ready_count > 0 else FALSE_TEXT,
            telegram_text_ready=TRUE_TEXT if telegram_ready_count > 0 else FALSE_TEXT,
            telegram_api_called=FALSE_TEXT,
            markdown_summary=(
                "Final report sections generated."
                if output_ready_count > 0
                else "INPUT_REQUIRED"
            ),
            telegram_message=(
                "Telegram-ready text generated but not sent."
                if telegram_ready_count > 0
                else "INPUT_REQUIRED"
            ),
            user_next_step=(
                "Review markdown report and daily log; copy Telegram-ready text manually if needed."
                if output_ready_count > 0
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
                "output_ready_count={};telegram_ready_count={};daily_log_ready_count={};"
                "final_action_allowed_count={};telegram_api_called=false"
            ).format(
                output_ready_count,
                telegram_ready_count,
                daily_log_ready_count,
                final_action_allowed_count,
            ),
            warning_flags=_flags(["FINAL_REPORT_TEMPLATE_DAILY_LOG_TELEGRAM_READY_OUTPUT"]),
            notes=(
                "Final output summary. Markdown report, persistent CSV log, and Telegram-ready "
                "text can be generated. No Telegram API call and no trading action are performed."
            ),
            timestamp_jst=timestamp_jst,
            timestamp_et=timestamp_et,
        )
    )

    return rows


def write_report_template_daily_log_telegram_csv(
    path: Union[str, Path],
    rows: Iterable[ReportTemplateDailyLogTelegramRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def append_report_template_daily_log(
    path: Union[str, Path],
    rows: Iterable[ReportTemplateDailyLogTelegramRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    write_header = not path.exists() or path.stat().st_size == 0

    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_telegram_ready_text(
    path: Union[str, Path],
    rows: Iterable[ReportTemplateDailyLogTelegramRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = [row for row in rows if row.row_id != "FINAL"]

    lines = [
        "Precious Metals Monitor - Final Research Plan",
        "manual_review_required=true",
        "final_action_allowed=false",
        "telegram_api_called=false",
        "",
    ]

    if not row_list:
        lines.append("INPUT_REQUIRED")
    else:
        for row in row_list:
            lines.append(row.telegram_message)

    path.write_text("\n".join(lines), encoding="utf-8")


def write_report_template_daily_log_telegram_report(
    path: Union[str, Path],
    rows: Iterable[ReportTemplateDailyLogTelegramRow],
    input_source: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    actual_rows = [row for row in row_list if row.row_id != "FINAL"]

    final_row = row_list[-1] if row_list else None
    final_status = final_row.status if final_row else INPUT_REQUIRED

    output_ready_count = sum(1 for row in actual_rows if row.report_section_available == TRUE_TEXT)
    daily_log_ready_count = sum(1 for row in actual_rows if row.daily_log_ready == TRUE_TEXT)
    telegram_ready_count = sum(1 for row in actual_rows if row.telegram_text_ready == TRUE_TEXT)
    telegram_api_called_count = sum(1 for row in row_list if row.telegram_api_called == TRUE_TEXT)
    final_action_allowed_count = sum(1 for row in row_list if row.final_action_allowed == TRUE_TEXT)

    lines = [
        "# Phase 28A-30C Report Template Daily Log Telegram-Ready Output Report",
        "",
        "- phase: Phase 28A-30C",
        "- scope: report template, persistent daily log, telegram-ready text",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- final_status: {final_status}",
        f"- report_section_available_count: {output_ready_count}",
        f"- daily_log_ready_count: {daily_log_ready_count}",
        f"- telegram_text_ready_count: {telegram_ready_count}",
        f"- telegram_api_called_count: {telegram_api_called_count}",
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
        "## Human-Readable Plan",
        "",
    ]

    for row in actual_rows:
        lines.append(row.markdown_summary)
        lines.append("")
        lines.append(f"- risk_warning: {row.risk_warning}")
        lines.append(f"- user_next_step: {row.user_next_step}")
        lines.append("")

    lines.extend(
        [
            "## Telegram-Ready Text",
            "",
            "```text",
            "Precious Metals Monitor - Final Research Plan",
            "manual_review_required=true",
            "final_action_allowed=false",
            "telegram_api_called=false",
            "",
        ]
    )

    if actual_rows:
        for row in actual_rows:
            lines.append(row.telegram_message)
    else:
        lines.append("INPUT_REQUIRED")

    lines.extend(
        [
            "```",
            "",
            "## Output Rule",
            "",
            "- Markdown report can be generated for human review.",
            "- Daily CSV log can be persisted locally.",
            "- Telegram-ready text can be generated for manual copy or later integration.",
            "- Telegram API is not called in this phase.",
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
            "- no Telegram API call",
            "- no order action",
            "- no cancellation action",
            "- no rebalance",
            "- no auto trade",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
