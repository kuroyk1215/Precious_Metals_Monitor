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

DEFAULT_WARNING_FLAGS = (
    "SANDBOX_QUALIFICATION_SIMULATOR",
    "SIMULATION_ONLY",
    "REAL_QUALIFICATION_BLOCKED",
    "TWS_CONNECTION_BLOCKED",
    "IBKR_API_REQUEST_BLOCKED",
    "NO_CONTRACT_QUALIFICATION",
    "NO_REQ_MKT_DATA",
    "NO_REQ_HISTORICAL_DATA",
    "NO_ORDER",
    "NO_CANCEL",
    "NO_REBALANCE",
    "NO_AUTO_TRADE",
    "phase13d_ibkr_readonly_qualification_sandbox_qualification_simulator",
)


@dataclass(frozen=True)
class SandboxQualificationSimulatorRow:
    simulation_id: str
    input_source_type: str
    input_label: str
    source_layer: str
    sandbox_input_validation_status: str
    sandbox_qualification_status: str
    simulated_symbol: str
    simulated_exchange: str
    simulated_currency: str
    simulated_sec_type: str
    simulated_qualification_result: str
    simulated_contract_id: str
    real_qualification_allowed: str
    tws_connection_allowed: str
    ibkr_api_request_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    order_action_allowed: str
    cancel_action_allowed: str
    rebalance_action_allowed: str
    auto_trade_allowed: str
    action_allowed: str
    simulation_decision: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "simulation_id",
    "input_source_type",
    "input_label",
    "source_layer",
    "sandbox_input_validation_status",
    "sandbox_qualification_status",
    "simulated_symbol",
    "simulated_exchange",
    "simulated_currency",
    "simulated_sec_type",
    "simulated_qualification_result",
    "simulated_contract_id",
    "real_qualification_allowed",
    "tws_connection_allowed",
    "ibkr_api_request_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "auto_trade_allowed",
    "action_allowed",
    "simulation_decision",
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


def _read_validator_csv(path: Path) -> list[Mapping[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    required = {"input_source_type", "sandbox_input_validation_status"}
    if not rows or not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        return []

    return rows


def _default_input_rows() -> list[Mapping[str, object]]:
    return [
        {
            "simulation_id": "SIM_1540_T",
            "input_source_type": "manual_csv",
            "input_label": "Simulated 1540.T qualification candidate",
            "sandbox_input_validation_status": "VALIDATED",
            "simulated_symbol": "1540",
            "simulated_exchange": "TSE",
            "simulated_currency": "JPY",
            "simulated_sec_type": "ETF",
        },
        {
            "simulation_id": "SIM_1542_T",
            "input_source_type": "mock_snapshot",
            "input_label": "Simulated 1542.T qualification candidate",
            "sandbox_input_validation_status": "VALIDATED",
            "simulated_symbol": "1542",
            "simulated_exchange": "TSE",
            "simulated_currency": "JPY",
            "simulated_sec_type": "ETF",
        },
        {
            "simulation_id": "SIM_518880_SH",
            "input_source_type": "manual_csv",
            "input_label": "Simulated 518880.SH qualification candidate",
            "sandbox_input_validation_status": "VALIDATED",
            "simulated_symbol": "518880",
            "simulated_exchange": "SEHKNTL",
            "simulated_currency": "CNY",
            "simulated_sec_type": "ETF",
        },
        {
            "simulation_id": "REJECT_REAL_TWS",
            "input_source_type": "real_tws",
            "input_label": "Rejected real TWS input",
            "sandbox_input_validation_status": "REJECTED",
            "simulated_symbol": "",
            "simulated_exchange": "",
            "simulated_currency": "",
            "simulated_sec_type": "",
        },
        {
            "simulation_id": "FINAL",
            "input_source_type": "simulator_summary",
            "input_label": "Final sandbox qualification simulator summary",
            "sandbox_input_validation_status": "REJECTED",
            "simulated_symbol": "",
            "simulated_exchange": "",
            "simulated_currency": "",
            "simulated_sec_type": "",
        },
    ]


def _source_rows(input_source: str | Path) -> list[Mapping[str, object]]:
    path = Path(input_source)
    if path.exists() and path.suffix.lower() == ".csv":
        rows = _read_validator_csv(path)
        if rows:
            return rows
    return _default_input_rows()


def _make_row(source: Mapping[str, object], timestamp_jst: str, timestamp_et: str) -> SandboxQualificationSimulatorRow:
    input_type = str(source.get("input_source_type") or "").strip().lower()
    validation_status = str(source.get("sandbox_input_validation_status") or "REJECTED").strip().upper()
    input_label = str(source.get("input_label") or input_type or "Unknown sandbox input")
    simulation_id = str(source.get("simulation_id") or source.get("validation_id") or input_type.upper() or "UNKNOWN")

    input_is_allowed = input_type in ALLOWED_INPUT_TYPES and validation_status == "VALIDATED"

    symbol = str(source.get("simulated_symbol") or source.get("symbol") or "")
    exchange = str(source.get("simulated_exchange") or source.get("exchange") or "")
    currency = str(source.get("simulated_currency") or source.get("currency") or "")
    sec_type = str(source.get("simulated_sec_type") or source.get("sec_type") or "")

    if input_is_allowed:
        qualification_status = "SIMULATED"
        qualification_result = "QUALIFIED_SIMULATED"
        simulated_contract_id = f"SIM-{symbol or simulation_id}"
        simulation_decision = "sandbox_qualification_simulated_real_qualification_blocked"
    else:
        qualification_status = "NOT_SIMULATED"
        qualification_result = "NOT_SIMULATED_INPUT_REJECTED"
        simulated_contract_id = ""
        simulation_decision = "sandbox_qualification_not_simulated_input_rejected"

    if input_type in {"real_tws", "real_ibkr_runtime", "live_market_data", "historical_request", "order", "cancel", "rebalance", "auto_trade"}:
        simulation_decision = f"{input_type}_input_rejected_before_simulation"

    return SandboxQualificationSimulatorRow(
        simulation_id=simulation_id,
        input_source_type=input_type,
        input_label=input_label,
        source_layer="Phase 13D",
        sandbox_input_validation_status=validation_status,
        sandbox_qualification_status=qualification_status,
        simulated_symbol=symbol,
        simulated_exchange=exchange,
        simulated_currency=currency,
        simulated_sec_type=sec_type,
        simulated_qualification_result=qualification_result,
        simulated_contract_id=simulated_contract_id,
        real_qualification_allowed=FALSE_TEXT,
        tws_connection_allowed=FALSE_TEXT,
        ibkr_api_request_allowed=FALSE_TEXT,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        order_action_allowed=FALSE_TEXT,
        cancel_action_allowed=FALSE_TEXT,
        rebalance_action_allowed=FALSE_TEXT,
        auto_trade_allowed=FALSE_TEXT,
        action_allowed=FALSE_TEXT,
        simulation_decision=simulation_decision,
        warning_flags=_flags([simulation_decision]),
        notes=(
            "Sandbox qualification simulator only. Qualification result is simulated and non-authoritative. "
            "Real TWS connection, IBKR API requests, real contract qualification, market data, historical data, "
            "orders, cancels, rebalancing, and auto-trading remain blocked."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_qualification_sandbox_qualification_simulator_rows(
    input_source: str | Path = "data/market_data_provider_config.yaml",
) -> list[SandboxQualificationSimulatorRow]:
    timestamp_jst, timestamp_et = _now_pair()
    return [_make_row(row, timestamp_jst, timestamp_et) for row in _source_rows(input_source)]


def write_ibkr_readonly_qualification_sandbox_qualification_simulator_csv(
    path: str | Path,
    rows: Iterable[SandboxQualificationSimulatorRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_qualification_sandbox_qualification_simulator_report(
    path: str | Path,
    rows: Iterable[SandboxQualificationSimulatorRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    simulated_count = sum(1 for row in row_list if row.sandbox_qualification_status == "SIMULATED")
    not_simulated_count = sum(1 for row in row_list if row.sandbox_qualification_status == "NOT_SIMULATED")
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    statuses = sorted({row.sandbox_qualification_status for row in row_list}) or ["none"]

    lines = [
        "# Phase 13D IBKR Read-Only Qualification Sandbox Qualification Simulator Report",
        "",
        "- phase: Phase 13D",
        "- scope: IBKR read-only qualification sandbox qualification simulator",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- sandbox_qualification_statuses: {','.join(statuses)}",
        f"- simulated_count: {simulated_count}",
        f"- not_simulated_count: {not_simulated_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- real_qualification_allowed: false",
        "- tws_connection_allowed: false",
        "- ibkr_api_request_allowed: false",
        "- market_data_request_allowed: false",
        "- historical_data_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Sandbox Qualification Simulator Rows",
        "",
        "| simulation_id | input_source_type | sandbox_input_validation_status | sandbox_qualification_status | simulated_symbol | simulated_qualification_result | real_qualification_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.simulation_id,
                    row.input_source_type,
                    row.sandbox_input_validation_status,
                    row.sandbox_qualification_status,
                    row.simulated_symbol,
                    row.simulated_qualification_result,
                    row.real_qualification_allowed,
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
            "- Sandbox qualification simulator is simulation-only.",
            "- Only already-validated manual_csv / mock_snapshot inputs may receive simulated qualification rows.",
            "- Real qualification remains blocked.",
            "- TWS connection remains blocked.",
            "- IBKR API request remains blocked.",
            "- Market data requests remain blocked.",
            "- Historical data requests remain blocked.",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- Phase 13D sandbox qualification simulator report only",
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
