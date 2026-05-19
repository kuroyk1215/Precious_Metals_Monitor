from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping
from zoneinfo import ZoneInfo


TRUE_TEXT = "true"
FALSE_TEXT = "false"

ALLOWED_INPUT_TYPES = {"manual_csv", "mock_snapshot"}
REJECTED_INPUT_TYPES = {
    "real_tws",
    "real_ibkr_runtime",
    "live_market_data",
    "historical_request",
    "order",
    "cancel",
    "rebalance",
    "auto_trade",
}

DEFAULT_WARNING_FLAGS = (
    "SANDBOX_INPUT_VALIDATOR",
    "EXPLICIT_SANDBOX_INPUT_REQUIRED",
    "REAL_TWS_INPUT_REJECTED",
    "REAL_IBKR_RUNTIME_INPUT_REJECTED",
    "LIVE_MARKET_DATA_REJECTED",
    "HISTORICAL_REQUEST_REJECTED",
    "ORDER_REJECTED",
    "CANCEL_REJECTED",
    "REBALANCE_REJECTED",
    "AUTO_TRADE_REJECTED",
    "SANDBOX_EXECUTION_BLOCKED",
    "IBKR_API_REQUEST_BLOCKED",
    "NO_CONTRACT_QUALIFICATION",
    "NO_REQ_MKT_DATA",
    "NO_REQ_HISTORICAL_DATA",
    "NO_ORDER",
    "NO_CANCEL",
    "NO_REBALANCE",
    "NO_AUTO_TRADE",
    "phase13c_ibkr_readonly_qualification_sandbox_input_validator",
)


@dataclass(frozen=True)
class SandboxInputValidatorRow:
    validation_id: str
    input_source_type: str
    input_label: str
    source_layer: str
    sandbox_input_validation_status: str
    input_allowed: str
    validation_passed: str
    rejection_required: str
    requires_explicit_sandbox_input: str
    accepts_real_tws_input: str
    accepts_real_ibkr_runtime_input: str
    sandbox_execution_allowed: str
    tws_connection_allowed: str
    ibkr_api_request_allowed: str
    contract_qualification_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    order_action_allowed: str
    cancel_action_allowed: str
    rebalance_action_allowed: str
    auto_trade_allowed: str
    action_allowed: str
    validation_decision: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "validation_id",
    "input_source_type",
    "input_label",
    "source_layer",
    "sandbox_input_validation_status",
    "input_allowed",
    "validation_passed",
    "rejection_required",
    "requires_explicit_sandbox_input",
    "accepts_real_tws_input",
    "accepts_real_ibkr_runtime_input",
    "sandbox_execution_allowed",
    "tws_connection_allowed",
    "ibkr_api_request_allowed",
    "contract_qualification_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "auto_trade_allowed",
    "action_allowed",
    "validation_decision",
    "warning_flags",
    "notes",
    "timestamp_jst",
    "timestamp_et",
]


def _now_pair() -> tuple[str, str]:
    now_utc = datetime.now(ZoneInfo("UTC"))
    return (
        now_utc.astimezone(ZoneInfo("Asia/Tokyo")).isoformat(),
        now_utc.astimezone(ZoneInfo("America/New_York")).isoformat(),
    )


def _flags(extra: Iterable[str] = ()) -> str:
    values = list(DEFAULT_WARNING_FLAGS)
    for item in extra:
        if item and item not in values:
            values.append(item)
    return ";".join(values)


def _normalize_input_type(value: object) -> str:
    return str(value or "").strip().lower()


def _read_input_csv(path: Path) -> list[Mapping[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows or not reader.fieldnames or "input_source_type" not in set(reader.fieldnames):
        return []

    return rows


def _default_input_rows() -> list[Mapping[str, object]]:
    return [
        {"validation_id": "MANUAL_CSV", "input_source_type": "manual_csv", "input_label": "Manual CSV sandbox input"},
        {"validation_id": "MOCK_SNAPSHOT", "input_source_type": "mock_snapshot", "input_label": "Mock snapshot sandbox input"},
        {"validation_id": "REAL_TWS", "input_source_type": "real_tws", "input_label": "Real TWS input"},
        {"validation_id": "REAL_IBKR_RUNTIME", "input_source_type": "real_ibkr_runtime", "input_label": "Real IBKR runtime input"},
        {"validation_id": "LIVE_MARKET_DATA", "input_source_type": "live_market_data", "input_label": "Live market data request input"},
        {"validation_id": "HISTORICAL_REQUEST", "input_source_type": "historical_request", "input_label": "Historical data request input"},
        {"validation_id": "ORDER", "input_source_type": "order", "input_label": "Order action input"},
        {"validation_id": "CANCEL", "input_source_type": "cancel", "input_label": "Cancel action input"},
        {"validation_id": "REBALANCE", "input_source_type": "rebalance", "input_label": "Rebalance action input"},
        {"validation_id": "AUTO_TRADE", "input_source_type": "auto_trade", "input_label": "Auto-trade action input"},
        {"validation_id": "FINAL", "input_source_type": "validator_summary", "input_label": "Final sandbox input validator summary"},
    ]


def _source_rows(input_source: str | Path) -> list[Mapping[str, object]]:
    path = Path(input_source)
    if path.exists() and path.suffix.lower() == ".csv":
        rows = _read_input_csv(path)
        if rows:
            return rows
    return _default_input_rows()


def _make_row(source: Mapping[str, object], timestamp_jst: str, timestamp_et: str) -> SandboxInputValidatorRow:
    input_type = _normalize_input_type(source.get("input_source_type"))
    validation_id = str(source.get("validation_id") or input_type.upper() or "UNKNOWN")
    input_label = str(source.get("input_label") or input_type or "Unknown input")
    allowed = input_type in ALLOWED_INPUT_TYPES

    if allowed:
        status = "VALIDATED"
        validation_decision = "sandbox_input_type_allowed_but_execution_remains_blocked"
        input_allowed = TRUE_TEXT
        validation_passed = TRUE_TEXT
        rejection_required = FALSE_TEXT
    else:
        status = "REJECTED"
        validation_decision = "sandbox_input_type_rejected_or_summary_only"
        input_allowed = FALSE_TEXT
        validation_passed = FALSE_TEXT
        rejection_required = TRUE_TEXT

    if input_type == "real_tws":
        validation_decision = "real_tws_input_rejected_by_validator"
    elif input_type == "real_ibkr_runtime":
        validation_decision = "real_ibkr_runtime_input_rejected_by_validator"
    elif input_type == "live_market_data":
        validation_decision = "live_market_data_input_rejected_by_validator"
    elif input_type == "historical_request":
        validation_decision = "historical_request_input_rejected_by_validator"
    elif input_type == "order":
        validation_decision = "order_input_rejected_by_validator"
    elif input_type == "cancel":
        validation_decision = "cancel_input_rejected_by_validator"
    elif input_type == "rebalance":
        validation_decision = "rebalance_input_rejected_by_validator"
    elif input_type == "auto_trade":
        validation_decision = "auto_trade_input_rejected_by_validator"
    elif input_type == "validator_summary":
        validation_decision = "validator_summary_only_execution_blocked"

    return SandboxInputValidatorRow(
        validation_id=validation_id,
        input_source_type=input_type,
        input_label=input_label,
        source_layer="Phase 13C",
        sandbox_input_validation_status=status,
        input_allowed=input_allowed,
        validation_passed=validation_passed,
        rejection_required=rejection_required,
        requires_explicit_sandbox_input=TRUE_TEXT,
        accepts_real_tws_input=FALSE_TEXT,
        accepts_real_ibkr_runtime_input=FALSE_TEXT,
        sandbox_execution_allowed=FALSE_TEXT,
        tws_connection_allowed=FALSE_TEXT,
        ibkr_api_request_allowed=FALSE_TEXT,
        contract_qualification_allowed=FALSE_TEXT,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        order_action_allowed=FALSE_TEXT,
        cancel_action_allowed=FALSE_TEXT,
        rebalance_action_allowed=FALSE_TEXT,
        auto_trade_allowed=FALSE_TEXT,
        action_allowed=FALSE_TEXT,
        validation_decision=validation_decision,
        warning_flags=_flags([validation_decision]),
        notes=(
            "Sandbox input validator only. Allowed inputs are limited to manual_csv and mock_snapshot "
            "as sandbox input shapes. Execution, TWS connection, IBKR runtime input, IBKR API requests, "
            "contract qualification, market data, historical data, orders, cancels, rebalancing, and auto-trading remain blocked."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_qualification_sandbox_input_validator_rows(
    input_source: str | Path = "data/market_data_provider_config.yaml",
) -> list[SandboxInputValidatorRow]:
    timestamp_jst, timestamp_et = _now_pair()
    return [_make_row(row, timestamp_jst, timestamp_et) for row in _source_rows(input_source)]


def write_ibkr_readonly_qualification_sandbox_input_validator_csv(
    path: str | Path,
    rows: Iterable[SandboxInputValidatorRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_qualification_sandbox_input_validator_report(
    path: str | Path,
    rows: Iterable[SandboxInputValidatorRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    validated_count = sum(1 for row in row_list if row.sandbox_input_validation_status == "VALIDATED")
    rejected_count = sum(1 for row in row_list if row.sandbox_input_validation_status == "REJECTED")
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    statuses = sorted({row.sandbox_input_validation_status for row in row_list}) or ["none"]

    lines = [
        "# Phase 13C IBKR Read-Only Qualification Sandbox Input Validator Report",
        "",
        "- phase: Phase 13C",
        "- scope: IBKR read-only qualification sandbox input validator",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- sandbox_input_validation_statuses: {','.join(statuses)}",
        f"- validated_count: {validated_count}",
        f"- rejected_count: {rejected_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- allowed_input_types: manual_csv,mock_snapshot",
        "- accepts_real_tws_input: false",
        "- accepts_real_ibkr_runtime_input: false",
        "- sandbox_execution_allowed: false",
        "- ibkr_api_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Sandbox Input Validator Rows",
        "",
        "| validation_id | input_source_type | sandbox_input_validation_status | input_allowed | validation_passed | rejection_required | sandbox_execution_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.validation_id,
                    row.input_source_type,
                    row.sandbox_input_validation_status,
                    row.input_allowed,
                    row.validation_passed,
                    row.rejection_required,
                    row.sandbox_execution_allowed,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Final Decision",
            "",
            "- Sandbox input validator is active for input-shape checks only.",
            "- manual_csv and mock_snapshot are accepted only as sandbox input shapes.",
            "- real_tws and real_ibkr_runtime inputs are rejected.",
            "- live market data and historical request inputs are rejected.",
            "- order, cancel, rebalance, and auto-trade inputs are rejected.",
            "- Sandbox execution allowed: false",
            "- IBKR API request allowed: false",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- Phase 13C sandbox input validator report only",
            "- no configuration file is modified",
            "- no TWS connection",
            "- no IBKR connection",
            "- no real contract qualification",
            "- no reqMktData",
            "- no reqHistoricalData",
            "- no order",
            "- no cancel",
            "- no rebalance",
            "- no auto trade",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
