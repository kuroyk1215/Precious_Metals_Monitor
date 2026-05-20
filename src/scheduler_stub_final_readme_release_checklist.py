from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Union
from zoneinfo import ZoneInfo

from src.report_template_daily_log_telegram_ready_output import (
    build_report_template_daily_log_telegram_rows,
)


TRUE_TEXT = "true"
FALSE_TEXT = "false"

PHASE = "Phase 31A-32C"

READY = "READY"
INPUT_REQUIRED = "INPUT_REQUIRED"

SCHEDULER_STUB_READY = "SCHEDULER_STUB_READY"
TELEGRAM_STUB_READY = "TELEGRAM_STUB_READY"
README_READY = "README_READY"
RELEASE_CHECKLIST_READY = "RELEASE_CHECKLIST_READY"
SAFETY_BOUNDARY_READY = "SAFETY_BOUNDARY_READY"

SCHEDULER_STUB_ONLY = "SCHEDULER_STUB_ONLY"
TELEGRAM_TEXT_ONLY = "TELEGRAM_TEXT_ONLY"
MVP_RELEASE_READY = "MVP_RELEASE_READY"
MVP_INPUT_REQUIRED = "MVP_INPUT_REQUIRED"


@dataclass(frozen=True)
class SchedulerStubFinalReadmeReleaseChecklistRow:
    row_id: str
    row_name: str
    source_layer: str
    input_source: str
    component: str
    status: str
    release_decision: str
    scheduler_stub_ready: str
    scheduler_job_started: str
    telegram_stub_ready: str
    telegram_api_called: str
    readme_ready: str
    release_checklist_ready: str
    safety_boundary_ready: str
    upstream_report_available: str
    upstream_daily_log_ready: str
    upstream_telegram_text_ready: str
    final_action_allowed: str
    auto_trade_allowed: str
    manual_review_required: str
    recommended_manual_schedule_jst: str
    operator_command: str
    mvp_release_check: str
    user_next_step: str
    ibkr_connection_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    contract_details_request_allowed: str
    contract_qualification_allowed: str
    order_action_allowed: str
    cancellation_action_allowed: str
    rebalance_action_allowed: str
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
    "release_decision",
    "scheduler_stub_ready",
    "scheduler_job_started",
    "telegram_stub_ready",
    "telegram_api_called",
    "readme_ready",
    "release_checklist_ready",
    "safety_boundary_ready",
    "upstream_report_available",
    "upstream_daily_log_ready",
    "upstream_telegram_text_ready",
    "final_action_allowed",
    "auto_trade_allowed",
    "manual_review_required",
    "recommended_manual_schedule_jst",
    "operator_command",
    "mvp_release_check",
    "user_next_step",
    "ibkr_connection_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "contract_details_request_allowed",
    "contract_qualification_allowed",
    "order_action_allowed",
    "cancellation_action_allowed",
    "rebalance_action_allowed",
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


def _actual_output_rows(rows):
    return [row for row in rows if row.row_id != "FINAL"]


def _make_row(
    input_source,
    row_id,
    row_name,
    component,
    status,
    release_decision,
    upstream_report_available,
    upstream_daily_log_ready,
    upstream_telegram_text_ready,
    mvp_release_check,
    user_next_step,
    timestamp_jst,
    timestamp_et,
):
    evidence = (
        "scheduler_job_started=false;"
        "telegram_api_called=false;"
        f"upstream_report_available={upstream_report_available};"
        f"upstream_daily_log_ready={upstream_daily_log_ready};"
        f"upstream_telegram_text_ready={upstream_telegram_text_ready};"
        "final_action_allowed=false"
    )

    return SchedulerStubFinalReadmeReleaseChecklistRow(
        row_id=row_id,
        row_name=row_name,
        source_layer=PHASE,
        input_source=str(input_source),
        component=component,
        status=status,
        release_decision=release_decision,
        scheduler_stub_ready=TRUE_TEXT,
        scheduler_job_started=FALSE_TEXT,
        telegram_stub_ready=TRUE_TEXT,
        telegram_api_called=FALSE_TEXT,
        readme_ready=TRUE_TEXT,
        release_checklist_ready=TRUE_TEXT,
        safety_boundary_ready=TRUE_TEXT,
        upstream_report_available=upstream_report_available,
        upstream_daily_log_ready=upstream_daily_log_ready,
        upstream_telegram_text_ready=upstream_telegram_text_ready,
        final_action_allowed=FALSE_TEXT,
        auto_trade_allowed=FALSE_TEXT,
        manual_review_required=TRUE_TEXT,
        recommended_manual_schedule_jst="08:30;12:00;16:00",
        operator_command="python main.py --report-template-daily-log-telegram-ready-output <primary_metals_config.yaml>",
        mvp_release_check=mvp_release_check,
        user_next_step=user_next_step,
        ibkr_connection_allowed=FALSE_TEXT,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        contract_details_request_allowed=FALSE_TEXT,
        contract_qualification_allowed=FALSE_TEXT,
        order_action_allowed=FALSE_TEXT,
        cancellation_action_allowed=FALSE_TEXT,
        rebalance_action_allowed=FALSE_TEXT,
        action_allowed=FALSE_TEXT,
        evidence=evidence,
        warning_flags=(
            "SCHEDULER_STUB_FINAL_README_RELEASE_CHECKLIST_DEFINED;"
            "NO_BACKGROUND_JOB_STARTED;"
            "NO_TELEGRAM_API_CALL;"
            "NO_IBKR_CONNECTION;"
            "NO_MARKET_DATA_REQUEST;"
            "NO_HISTORICAL_DATA_REQUEST;"
            "NO_AUTO_TRADE"
        ),
        notes=(
            "Scheduler and Telegram stubs only. No background job is started, "
            "no Telegram API is called, no IBKR connection is made, and no trading action is emitted."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_scheduler_stub_final_readme_release_checklist_rows(
    input_source: Union[str, Path] = "config.yaml",
):
    timestamp_jst, timestamp_et = _now_pair()

    upstream_rows = build_report_template_daily_log_telegram_rows(input_source)
    actual_rows = _actual_output_rows(upstream_rows)

    upstream_report_count = sum(
        1 for row in actual_rows if row.report_section_available == TRUE_TEXT
    )
    upstream_daily_log_count = sum(
        1 for row in actual_rows if row.daily_log_ready == TRUE_TEXT
    )
    upstream_telegram_count = sum(
        1 for row in actual_rows if row.telegram_text_ready == TRUE_TEXT
    )

    upstream_report_available = TRUE_TEXT if upstream_report_count > 0 else FALSE_TEXT
    upstream_daily_log_ready = TRUE_TEXT if upstream_daily_log_count > 0 else FALSE_TEXT
    upstream_telegram_text_ready = TRUE_TEXT if upstream_telegram_count > 0 else FALSE_TEXT

    release_decision = MVP_RELEASE_READY if upstream_report_count > 0 else MVP_INPUT_REQUIRED

    rows = [
        _make_row(
            input_source,
            "SCHEDULER_STUB",
            "Manual scheduler stub",
            "Phase 31A",
            SCHEDULER_STUB_READY,
            SCHEDULER_STUB_ONLY,
            upstream_report_available,
            upstream_daily_log_ready,
            upstream_telegram_text_ready,
            "Manual schedule documented; no background job is started.",
            "Use external scheduler manually only after reviewing generated reports.",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            input_source,
            "TELEGRAM_SEND_STUB",
            "Telegram send stub",
            "Phase 31B",
            TELEGRAM_STUB_READY,
            TELEGRAM_TEXT_ONLY,
            upstream_report_available,
            upstream_daily_log_ready,
            upstream_telegram_text_ready,
            "Telegram-ready text documented; no Telegram API call is made.",
            "Copy Telegram-ready text manually or wire a future sender behind an explicit gate.",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            input_source,
            "FINAL_README",
            "Final MVP README usage guide",
            "Phase 32A",
            README_READY,
            release_decision,
            upstream_report_available,
            upstream_daily_log_ready,
            upstream_telegram_text_ready,
            "README usage guide generated for the final research plan workflow.",
            "Run the one-command output with a reviewed primary_metals input file.",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            input_source,
            "MVP_RELEASE_CHECKLIST",
            "MVP release checklist",
            "Phase 32B",
            RELEASE_CHECKLIST_READY,
            release_decision,
            upstream_report_available,
            upstream_daily_log_ready,
            upstream_telegram_text_ready,
            "Release checklist generated with tests, output files, stubs, and safety checks.",
            "Confirm tests pass and generated outputs remain uncommitted runtime artifacts.",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            input_source,
            "FINAL_SAFETY_BOUNDARY",
            "Final safety boundary statement",
            "Phase 32C",
            SAFETY_BOUNDARY_READY,
            release_decision,
            upstream_report_available,
            upstream_daily_log_ready,
            upstream_telegram_text_ready,
            "Final safety boundary generated: no external execution and no trading action.",
            "Keep this project manual research only unless a future explicit safety gate is added.",
            timestamp_jst,
            timestamp_et,
        ),
    ]

    mvp_ready = release_decision == MVP_RELEASE_READY

    rows.append(
        _make_row(
            input_source,
            "FINAL",
            "Final scheduler stub README release checklist decision",
            "Phase 31A-32C",
            READY if mvp_ready else INPUT_REQUIRED,
            release_decision,
            upstream_report_available,
            upstream_daily_log_ready,
            upstream_telegram_text_ready,
            "MVP release checklist complete." if mvp_ready else "Primary input required.",
            (
                "MVP output path is documented; keep operation manual and research-only."
                if mvp_ready
                else "Provide primary metals inputs and rerun output command."
            ),
            timestamp_jst,
            timestamp_et,
        )
    )

    return rows


def write_scheduler_stub_final_readme_release_checklist_csv(path, rows) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_scheduler_stub_final_readme_release_checklist_report(path, rows, input_source) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    final_row = row_list[-1] if row_list else None
    final_status = final_row.status if final_row else INPUT_REQUIRED
    release_decision = final_row.release_decision if final_row else MVP_INPUT_REQUIRED

    scheduler_started_count = sum(1 for row in row_list if row.scheduler_job_started == TRUE_TEXT)
    telegram_api_called_count = sum(1 for row in row_list if row.telegram_api_called == TRUE_TEXT)
    final_action_allowed_count = sum(1 for row in row_list if row.final_action_allowed == TRUE_TEXT)

    lines = [
        "# Phase 31A-32C Scheduler Stub Final README Release Checklist Report",
        "",
        "- phase: Phase 31A-32C",
        "- scope: scheduler stub, Telegram stub, final README usage, MVP release checklist",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- final_status: {final_status}",
        f"- release_decision: {release_decision}",
        f"- scheduler_job_started_count: {scheduler_started_count}",
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
        "## Operator Usage",
        "",
        "python main.py --report-template-daily-log-telegram-ready-output <primary_metals_config.yaml>",
        "",
        "## MVP Release Checklist",
        "",
        "- Tests pass with python3 -m py_compile main.py src/*.py.",
        "- Tests pass with PYTHONPATH=. python -m pytest -q.",
        "- No Telegram API call is made.",
        "- No background job is started.",
        "- No broker connection is made by this phase.",
        "- No trading action is emitted.",
        "",
        "## Final Safety Boundary",
        "",
        "- manual research only",
        "- no background execution",
        "- no Telegram API call",
        "- no IBKR connection",
        "- no TWS connection",
        "- no market data request",
        "- no historical data request",
        "- no contract details request",
        "- no order action",
        "- no cancellation action",
        "- no rebalance",
        "- no auto trade",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


def write_final_mvp_readme(path, rows) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    final_row = row_list[-1] if row_list else None
    release_decision = final_row.release_decision if final_row else MVP_INPUT_REQUIRED

    text = f"""# 贵金属监控系统 MVP 使用说明

## 当前状态

- release_decision: {release_decision}
- 运行模式：仅人工研究
- 后台任务：禁用
- Telegram API：禁用
- 本阶段券商连接：禁用
- 最终交易动作：禁用

## 一键输出命令

python main.py --report-template-daily-log-telegram-ready-output <primary_metals_config.yaml>

## 输入示例

primary_metals:
  usd_jpy: 155.0
  gold_price: 2400.0
  gold_previous_price: 2380.0
  gold_conversion_factor: 0.01
  gold_etf_data_status: NO_MARKET_DATA_SUBSCRIPTION
  silver_price: 30.0
  silver_previous_price: 31.0
  silver_conversion_factor: 1.0
  silver_etf_data_status: NO_MARKET_DATA_SUBSCRIPTION

## 生成文件

- report_template_daily_log_telegram_ready_output.csv
- final_research_plan_daily_log.csv
- reports/report_template_daily_log_telegram_ready_output_report.md
- reports/telegram_ready_text.txt

## 建议人工运行时间

- JST 08:30：盘前检查
- JST 12:00：午间检查
- JST 16:00：收盘后检查

## 安全边界

本 MVP 只输出市场方向、理论区间、数据缺口、风险提示和人工确认要求。

系统不会输出高置信 ETF 执行买卖点，不会自动下单，不会撤单，不会再平衡，也不会调用 Telegram API 或启动后台任务。
"""
    path.write_text(text, encoding="utf-8")
