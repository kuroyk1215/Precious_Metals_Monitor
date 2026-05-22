from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class IBKRExecutionCValidationDecision:
    execution_c_status: str
    execution_c_mode: str
    market_data_execution_requested: str
    local_runner_status: str
    pipeline_status: str
    snapshot_status: str
    effective_market_data_type: str
    fallback_stage: str
    data_delay_flag: str
    final_review_status: str
    operator_packet_status: str
    telegram_dry_run_status: str
    telegram_send_gate_status: str
    telegram_send_triggered: str
    validation_decision: str
    validation_reason: str
    manual_review_required: str
    action_allowed: str
    broker_execution_triggered: str
    historical_data_request_triggered: str
    account_read_triggered: str
    position_read_triggered: str
    safety_flags: str
    next_step: str


def _clean(value: object) -> str:
    return str(value or "").strip()


def _lower(value: object) -> str:
    return _clean(value).lower()


def read_csv_rows(path: str | Path) -> Tuple[str, List[Dict[str, str]]]:
    candidate = Path(path)
    if not candidate.exists():
        return "missing", []
    with candidate.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return "empty_file", []
    return "present", rows


def _latest_value(rows: Iterable[Dict[str, str]], field: str, default: str = "unknown") -> str:
    for row in reversed(list(rows)):
        value = _clean(row.get(field))
        if value:
            return value
    return default


def _any_safety_anomaly(rows: Iterable[Dict[str, str]]) -> List[str]:
    flags: List[str] = []
    checks = (
        "action_allowed",
        "broker_execution_triggered",
        "historical_data_request_triggered",
        "account_read_triggered",
        "position_read_triggered",
    )
    for row in rows:
        label = _clean(row.get("display_symbol")) or _clean(row.get("step_name")) or "row"
        for field in checks:
            value = _clean(row.get(field))
            if value and value.lower() != "false":
                flags.append(f"{label}:{field}_not_false")
    return flags


def build_execution_c_validation_decision(
    *,
    execute_market_data: bool = False,
    runner_rows: Iterable[Dict[str, str]] = (),
    pipeline_rows: Iterable[Dict[str, str]] = (),
    snapshot_rows: Iterable[Dict[str, str]] = (),
    operator_rows: Iterable[Dict[str, str]] = (),
    notification_rows: Iterable[Dict[str, str]] = (),
    send_gate_rows: Iterable[Dict[str, str]] = (),
    runner_input_status: str = "missing",
    pipeline_input_status: str = "missing",
    snapshot_input_status: str = "missing",
    operator_input_status: str = "missing",
    notification_input_status: str = "missing",
    send_gate_input_status: str = "missing",
) -> IBKRExecutionCValidationDecision:
    runner_list = list(runner_rows)
    pipeline_list = list(pipeline_rows)
    snapshot_list = list(snapshot_rows)
    operator_list = list(operator_rows)
    notification_list = list(notification_rows)
    send_gate_list = list(send_gate_rows)
    execution_c_mode = "execute_market_data" if execute_market_data else "dry_run"

    local_runner_status = "not_run" if not runner_list else (
        "FAILED_SAFE" if _latest_value(runner_list, "pipeline_exit_code", "1") != "0" else "NO_GO"
    )
    pipeline_status = _latest_value(pipeline_list, "pipeline_status", pipeline_input_status)
    snapshot_status = _latest_value(snapshot_list, "snapshot_status", snapshot_input_status)
    effective_market_data_type = _latest_value(snapshot_list, "effective_market_data_type", "unknown")
    fallback_stage = _latest_value(snapshot_list, "fallback_stage", "unknown")
    data_delay_flag = _latest_value(snapshot_list, "data_delay_flag", "unavailable")
    final_review_status = _latest_value(operator_list, "final_review_status", operator_input_status)
    operator_packet_status = _latest_value(operator_list, "operator_packet_status", operator_input_status)
    telegram_dry_run_status = _latest_value(notification_list, "notification_status", notification_input_status)
    telegram_send_gate_status = _latest_value(send_gate_list, "send_gate_status", send_gate_input_status)
    telegram_send_triggered = _latest_value(send_gate_list, "telegram_send_triggered", "false")

    safety_flags = _any_safety_anomaly(runner_list + pipeline_list + snapshot_list + operator_list + notification_list + send_gate_list)
    if _lower(telegram_send_triggered) not in {"", "false"}:
        safety_flags.append("telegram_send_triggered")

    if not execute_market_data:
        execution_c_status = "EXECUTION_C_DRY_RUN_READY"
        validation_decision = "NO_GO"
        validation_reason = "dry-run framework ready; no IBKR request was made"
        next_step = "manual_operator_may_run_explicit_execution_c_validation"
    elif safety_flags:
        execution_c_status = "EXECUTION_C_FAILED_SAFE"
        validation_decision = "FAILED_SAFE"
        validation_reason = "safety marker anomaly detected"
        next_step = "stop_and_review_safety_flags"
    elif local_runner_status == "FAILED_SAFE" or pipeline_status == "FAILED_SAFE":
        execution_c_status = "EXECUTION_C_FAILED_SAFE"
        validation_decision = "FAILED_SAFE"
        validation_reason = "local runner or pipeline failed safe"
        next_step = "review_runner_and_pipeline_reports"
    elif snapshot_input_status != "present" or _lower(snapshot_status) in {"missing", "snapshot_empty", "delayed_snapshot_empty", "delayed_frozen_snapshot_empty"}:
        execution_c_status = "EXECUTION_C_VALIDATION_BLOCKED"
        validation_decision = "REVIEW_BLOCKED"
        validation_reason = "snapshot missing or no usable price"
        next_step = "review_snapshot_and_market_data_permissions"
    elif _lower(effective_market_data_type) in {"unsupported", "unknown"} or _lower(fallback_stage) in {"unsupported", "connection_error"}:
        execution_c_status = "EXECUTION_C_VALIDATION_BLOCKED"
        validation_decision = "REVIEW_BLOCKED"
        validation_reason = "unsupported, unknown, or connection-error market data state"
        next_step = "review_contract_map_and_ibkr_permissions"
    elif _lower(effective_market_data_type) in {"delayed", "delayed_frozen"} or _lower(data_delay_flag) in {"delayed", "delayed_frozen"}:
        execution_c_status = "EXECUTION_C_VALIDATION_READY"
        validation_decision = "REVIEW_READY_REFERENCE_ONLY"
        validation_reason = "reference-only validation; delayed or delayed_frozen data is not real-time"
        next_step = "manual_operator_review_reference_only_context"
    else:
        execution_c_status = "EXECUTION_C_VALIDATION_READY"
        validation_decision = "REVIEW_READY_REFERENCE_ONLY"
        validation_reason = "reference-only validation completed; no trade authorization"
        next_step = "manual_operator_review_reference_only_context"

    return IBKRExecutionCValidationDecision(
        execution_c_status=execution_c_status,
        execution_c_mode=execution_c_mode,
        market_data_execution_requested=str(execute_market_data).lower(),
        local_runner_status=local_runner_status,
        pipeline_status=pipeline_status,
        snapshot_status=snapshot_status,
        effective_market_data_type=effective_market_data_type,
        fallback_stage=fallback_stage,
        data_delay_flag=data_delay_flag,
        final_review_status=final_review_status,
        operator_packet_status=operator_packet_status,
        telegram_dry_run_status=telegram_dry_run_status,
        telegram_send_gate_status=telegram_send_gate_status,
        telegram_send_triggered="true" if _lower(telegram_send_triggered) == "true" else "false",
        validation_decision=validation_decision,
        validation_reason=validation_reason,
        manual_review_required="true",
        action_allowed="false",
        broker_execution_triggered="false",
        historical_data_request_triggered="false",
        account_read_triggered="false",
        position_read_triggered="false",
        safety_flags=",".join(safety_flags),
        next_step=next_step,
    )


def write_validation_csv(path: str | Path, decision: IBKRExecutionCValidationDecision) -> None:
    fields = list(IBKRExecutionCValidationDecision.__dataclass_fields__.keys())
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerow([getattr(decision, field) for field in fields])


def write_validation_report(path: str | Path, decision: IBKRExecutionCValidationDecision) -> None:
    Path(path).write_text(
        "\n".join(
            [
                "# IBKR Execution C Validation Report",
                "",
                "## Execution C Validation Decision",
                "",
                "| field | value |",
                "|---|---|",
                f"| execution_c_status | {decision.execution_c_status} |",
                f"| validation_decision | {decision.validation_decision} |",
                f"| validation_reason | {decision.validation_reason} |",
                f"| next_step | {decision.next_step} |",
                "| action_allowed | false |",
                "",
                "## Market Data Execution Mode",
                "",
                f"- execution_c_mode={decision.execution_c_mode}",
                f"- market_data_execution_requested={decision.market_data_execution_requested}",
                "- default mode does not connect to IBKR or request market data",
                "",
                "## Snapshot / Delay Classification",
                "",
                f"- snapshot_status={decision.snapshot_status}",
                f"- effective_market_data_type={decision.effective_market_data_type}",
                f"- fallback_stage={decision.fallback_stage}",
                f"- data_delay_flag={decision.data_delay_flag}",
                "- delayed and delayed_frozen data remain reference-only and not real-time",
                "",
                "## Pipeline / Runner / Operator Status",
                "",
                f"- local_runner_status={decision.local_runner_status}",
                f"- pipeline_status={decision.pipeline_status}",
                f"- final_review_status={decision.final_review_status}",
                f"- operator_packet_status={decision.operator_packet_status}",
                "",
                "## Telegram Dry-run / Send Gate Status",
                "",
                f"- telegram_dry_run_status={decision.telegram_dry_run_status}",
                f"- telegram_send_gate_status={decision.telegram_send_gate_status}",
                f"- telegram_send_triggered={decision.telegram_send_triggered}",
                "",
                "## Safety Confirmation",
                "",
                "- action_allowed=false",
                "- broker_execution_triggered=false",
                "- historical_data_request_triggered=false",
                "- account_read_triggered=false",
                "- position_read_triggered=false",
                "- manual_review_required=true",
                "",
                "## Manual Operator Handoff",
                "",
                "Use this packet to review Execution C readiness and delayed/frozen market data classification. It does not authorize trades, account reads, position reads, historical data requests, or broker execution.",
                "",
                "## Next Phase Handoff",
                "",
                "Phase 385-400 may focus on release hardening, a full safety audit, and the operator manual.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
