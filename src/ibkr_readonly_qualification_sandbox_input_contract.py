from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo


TRUE_TEXT = "true"
FALSE_TEXT = "false"

DEFAULT_WARNING_FLAGS = (
    "INPUT_CONTRACT_DEFINED",
    "EXPLICIT_SANDBOX_INPUT_REQUIRED",
    "REAL_TWS_INPUT_REJECTED",
    "REAL_IBKR_RUNTIME_INPUT_REJECTED",
    "SANDBOX_EXECUTION_BLOCKED",
    "IBKR_API_REQUEST_BLOCKED",
    "NO_CONTRACT_QUALIFICATION",
    "NO_REQ_MKT_DATA",
    "NO_REQ_HISTORICAL_DATA",
    "NO_ORDER",
    "NO_CANCEL",
    "NO_REBALANCE",
    "NO_AUTO_TRADE",
    "phase13b_ibkr_readonly_qualification_sandbox_input_contract",
)


@dataclass(frozen=True)
class SandboxInputContractRow:
    contract_id: str
    contract_name: str
    source_layer: str
    sandbox_input_contract_status: str
    required_input_type: str
    requires_explicit_sandbox_input: str
    accepts_manual_csv_input: str
    accepts_mock_snapshot_input: str
    accepts_real_tws_input: str
    accepts_real_ibkr_runtime_input: str
    sandbox_execution_allowed: str
    ibkr_api_request_allowed: str
    contract_qualification_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    order_action_allowed: str
    cancel_action_allowed: str
    rebalance_action_allowed: str
    auto_trade_allowed: str
    action_allowed: str
    contract_decision: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "contract_id",
    "contract_name",
    "source_layer",
    "sandbox_input_contract_status",
    "required_input_type",
    "requires_explicit_sandbox_input",
    "accepts_manual_csv_input",
    "accepts_mock_snapshot_input",
    "accepts_real_tws_input",
    "accepts_real_ibkr_runtime_input",
    "sandbox_execution_allowed",
    "ibkr_api_request_allowed",
    "contract_qualification_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "auto_trade_allowed",
    "action_allowed",
    "contract_decision",
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


def _make_row(
    contract_id: str,
    contract_name: str,
    required_input_type: str,
    contract_decision: str,
    timestamp_jst: str,
    timestamp_et: str,
) -> SandboxInputContractRow:
    return SandboxInputContractRow(
        contract_id=contract_id,
        contract_name=contract_name,
        source_layer="Phase 13B",
        sandbox_input_contract_status="DEFINED",
        required_input_type=required_input_type,
        requires_explicit_sandbox_input=TRUE_TEXT,
        accepts_manual_csv_input=TRUE_TEXT,
        accepts_mock_snapshot_input=TRUE_TEXT,
        accepts_real_tws_input=FALSE_TEXT,
        accepts_real_ibkr_runtime_input=FALSE_TEXT,
        sandbox_execution_allowed=FALSE_TEXT,
        ibkr_api_request_allowed=FALSE_TEXT,
        contract_qualification_allowed=FALSE_TEXT,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        order_action_allowed=FALSE_TEXT,
        cancel_action_allowed=FALSE_TEXT,
        rebalance_action_allowed=FALSE_TEXT,
        auto_trade_allowed=FALSE_TEXT,
        action_allowed=FALSE_TEXT,
        contract_decision=contract_decision,
        warning_flags=_flags([contract_decision]),
        notes=(
            "Sandbox input contract only. Explicit sandbox/manual/mock inputs are allowed for schema design, "
            "but real TWS input, real IBKR runtime input, IBKR API requests, contract qualification, market data, "
            "historical data, order, cancel, rebalance, and auto-trade remain blocked."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_qualification_sandbox_input_contract_rows(
    input_source: str | Path = "data/market_data_provider_config.yaml",
) -> list[SandboxInputContractRow]:
    timestamp_jst, timestamp_et = _now_pair()
    _ = str(input_source)

    return [
        _make_row(
            "SCHEMA",
            "Sandbox input schema boundary",
            "manual_csv_or_mock_snapshot",
            "explicit_schema_required_before_any_sandbox_runtime",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "SOURCE",
            "Allowed input source boundary",
            "manual_csv_or_mock_snapshot",
            "manual_or_mock_sources_allowed_real_runtime_rejected",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "TWS",
            "TWS input rejection boundary",
            "no_real_tws_input",
            "real_tws_input_rejected_by_contract",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "IBKR",
            "IBKR runtime input rejection boundary",
            "no_real_ibkr_runtime_input",
            "real_ibkr_runtime_input_rejected_by_contract",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "DATA",
            "Data request input boundary",
            "no_live_or_historical_request_input",
            "market_and_historical_data_requests_blocked_by_contract",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "ACTIONS",
            "Action input boundary",
            "no_order_cancel_rebalance_auto_trade_input",
            "trade_action_inputs_blocked_by_contract",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "FINAL",
            "Final sandbox input contract",
            "manual_csv_or_mock_snapshot_only",
            "phase13b_input_contract_defined_but_execution_blocked",
            timestamp_jst,
            timestamp_et,
        ),
    ]


def write_ibkr_readonly_qualification_sandbox_input_contract_csv(
    path: str | Path,
    rows: Iterable[SandboxInputContractRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_qualification_sandbox_input_contract_report(
    path: str | Path,
    rows: Iterable[SandboxInputContractRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    defined_count = sum(1 for row in row_list if row.sandbox_input_contract_status == "DEFINED")
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    statuses = sorted({row.sandbox_input_contract_status for row in row_list}) or ["none"]

    lines = [
        "# Phase 13B IBKR Read-Only Qualification Sandbox Input Contract Report",
        "",
        "- phase: Phase 13B",
        "- scope: IBKR read-only qualification sandbox input contract",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- sandbox_input_contract_statuses: {','.join(statuses)}",
        f"- defined_count: {defined_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- sandbox_input_contract_status: DEFINED",
        "- requires_explicit_sandbox_input: true",
        "- accepts_manual_csv_input: true",
        "- accepts_mock_snapshot_input: true",
        "- accepts_real_tws_input: false",
        "- accepts_real_ibkr_runtime_input: false",
        "- sandbox_execution_allowed: false",
        "- ibkr_api_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Sandbox Input Contract Rows",
        "",
        "| contract_id | required_input_type | sandbox_input_contract_status | accepts_manual_csv_input | accepts_mock_snapshot_input | accepts_real_tws_input | accepts_real_ibkr_runtime_input | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.contract_id,
                    row.required_input_type,
                    row.sandbox_input_contract_status,
                    row.accepts_manual_csv_input,
                    row.accepts_mock_snapshot_input,
                    row.accepts_real_tws_input,
                    row.accepts_real_ibkr_runtime_input,
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
            "- Sandbox input contract status: DEFINED",
            "- Explicit sandbox input is required.",
            "- Manual CSV input is allowed only as sandbox input.",
            "- Mock snapshot input is allowed only as sandbox input.",
            "- Real TWS input is rejected.",
            "- Real IBKR runtime input is rejected.",
            "- Sandbox execution allowed: false",
            "- IBKR API request allowed: false",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- Phase 13B sandbox input contract report only",
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
