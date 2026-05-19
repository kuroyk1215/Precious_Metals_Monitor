from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping
from zoneinfo import ZoneInfo


TRUE_TEXT = "true"
FALSE_TEXT = "false"

DEFAULT_WARNING_FLAGS = (
    "SANDBOX_RESULT_PACK",
    "SIMULATED_RESULT_ONLY",
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
    "phase13e_ibkr_readonly_qualification_sandbox_result_pack",
)


@dataclass(frozen=True)
class SandboxResultPackRow:
    pack_id: str
    pack_name: str
    source_layer: str
    sandbox_result_pack_status: str
    simulated_result_only: str
    sandbox_qualification_status: str
    simulated_qualification_result: str
    simulated_symbol: str
    simulated_exchange: str
    simulated_currency: str
    simulated_sec_type: str
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
    result_pack_decision: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "pack_id",
    "pack_name",
    "source_layer",
    "sandbox_result_pack_status",
    "simulated_result_only",
    "sandbox_qualification_status",
    "simulated_qualification_result",
    "simulated_symbol",
    "simulated_exchange",
    "simulated_currency",
    "simulated_sec_type",
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
    "result_pack_decision",
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


def _read_simulator_csv(path: Path) -> list[Mapping[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    required = {"simulation_id", "sandbox_qualification_status", "simulated_qualification_result"}
    if not rows or not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        return []

    return rows


def _default_simulator_rows() -> list[Mapping[str, object]]:
    return [
        {
            "simulation_id": "SIM_1540_T",
            "input_label": "Simulated 1540.T qualification candidate",
            "sandbox_qualification_status": "SIMULATED",
            "simulated_symbol": "1540",
            "simulated_exchange": "TSE",
            "simulated_currency": "JPY",
            "simulated_sec_type": "ETF",
            "simulated_qualification_result": "QUALIFIED_SIMULATED",
            "simulated_contract_id": "SIM-1540",
        },
        {
            "simulation_id": "SIM_1542_T",
            "input_label": "Simulated 1542.T qualification candidate",
            "sandbox_qualification_status": "SIMULATED",
            "simulated_symbol": "1542",
            "simulated_exchange": "TSE",
            "simulated_currency": "JPY",
            "simulated_sec_type": "ETF",
            "simulated_qualification_result": "QUALIFIED_SIMULATED",
            "simulated_contract_id": "SIM-1542",
        },
        {
            "simulation_id": "SIM_518880_SH",
            "input_label": "Simulated 518880.SH qualification candidate",
            "sandbox_qualification_status": "SIMULATED",
            "simulated_symbol": "518880",
            "simulated_exchange": "SEHKNTL",
            "simulated_currency": "CNY",
            "simulated_sec_type": "ETF",
            "simulated_qualification_result": "QUALIFIED_SIMULATED",
            "simulated_contract_id": "SIM-518880",
        },
        {
            "simulation_id": "REJECT_REAL_TWS",
            "input_label": "Rejected real TWS input",
            "sandbox_qualification_status": "NOT_SIMULATED",
            "simulated_symbol": "",
            "simulated_exchange": "",
            "simulated_currency": "",
            "simulated_sec_type": "",
            "simulated_qualification_result": "NOT_SIMULATED_INPUT_REJECTED",
            "simulated_contract_id": "",
        },
        {
            "simulation_id": "FINAL",
            "input_label": "Final sandbox result pack summary",
            "sandbox_qualification_status": "NOT_SIMULATED",
            "simulated_symbol": "",
            "simulated_exchange": "",
            "simulated_currency": "",
            "simulated_sec_type": "",
            "simulated_qualification_result": "RESULT_PACK_SUMMARY_ONLY",
            "simulated_contract_id": "",
        },
    ]


def _source_rows(input_source: str | Path) -> list[Mapping[str, object]]:
    path = Path(input_source)
    if path.exists() and path.suffix.lower() == ".csv":
        rows = _read_simulator_csv(path)
        if rows:
            return rows
    return _default_simulator_rows()


def _make_row(source: Mapping[str, object], timestamp_jst: str, timestamp_et: str) -> SandboxResultPackRow:
    pack_id = str(source.get("simulation_id") or source.get("pack_id") or "UNKNOWN")
    pack_name = str(source.get("input_label") or source.get("pack_name") or pack_id)
    qualification_status = str(source.get("sandbox_qualification_status") or "NOT_SIMULATED").strip().upper()
    qualification_result = str(source.get("simulated_qualification_result") or "NOT_SIMULATED_INPUT_REJECTED")

    if qualification_status == "SIMULATED":
        result_pack_decision = "simulated_qualification_result_included_real_qualification_blocked"
    else:
        result_pack_decision = "non_simulated_or_rejected_input_recorded_real_qualification_blocked"

    if pack_id == "FINAL":
        result_pack_decision = "sandbox_result_pack_built_but_real_qualification_blocked"

    return SandboxResultPackRow(
        pack_id=pack_id,
        pack_name=pack_name,
        source_layer="Phase 13E",
        sandbox_result_pack_status="BUILT",
        simulated_result_only=TRUE_TEXT,
        sandbox_qualification_status=qualification_status,
        simulated_qualification_result=qualification_result,
        simulated_symbol=str(source.get("simulated_symbol") or source.get("symbol") or ""),
        simulated_exchange=str(source.get("simulated_exchange") or source.get("exchange") or ""),
        simulated_currency=str(source.get("simulated_currency") or source.get("currency") or ""),
        simulated_sec_type=str(source.get("simulated_sec_type") or source.get("sec_type") or ""),
        simulated_contract_id=str(source.get("simulated_contract_id") or ""),
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
        result_pack_decision=result_pack_decision,
        warning_flags=_flags([result_pack_decision]),
        notes=(
            "Sandbox result pack only. All qualification results are simulated and non-authoritative. "
            "Real TWS connection, IBKR API requests, real contract qualification, market data, historical data, "
            "orders, cancels, rebalancing, and auto-trading remain blocked."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_qualification_sandbox_result_pack_rows(
    input_source: str | Path = "data/market_data_provider_config.yaml",
) -> list[SandboxResultPackRow]:
    timestamp_jst, timestamp_et = _now_pair()
    return [_make_row(row, timestamp_jst, timestamp_et) for row in _source_rows(input_source)]


def write_ibkr_readonly_qualification_sandbox_result_pack_csv(
    path: str | Path,
    rows: Iterable[SandboxResultPackRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_qualification_sandbox_result_pack_report(
    path: str | Path,
    rows: Iterable[SandboxResultPackRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    built_count = sum(1 for row in row_list if row.sandbox_result_pack_status == "BUILT")
    simulated_count = sum(1 for row in row_list if row.sandbox_qualification_status == "SIMULATED")
    not_simulated_count = sum(1 for row in row_list if row.sandbox_qualification_status == "NOT_SIMULATED")
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    statuses = sorted({row.sandbox_result_pack_status for row in row_list}) or ["none"]

    lines = [
        "# Phase 13E IBKR Read-Only Qualification Sandbox Result Pack Report",
        "",
        "- phase: Phase 13E",
        "- scope: IBKR read-only qualification sandbox result pack",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- sandbox_result_pack_statuses: {','.join(statuses)}",
        f"- built_count: {built_count}",
        f"- simulated_count: {simulated_count}",
        f"- not_simulated_count: {not_simulated_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- sandbox_result_pack_status: BUILT",
        "- simulated_result_only: true",
        "- real_qualification_allowed: false",
        "- tws_connection_allowed: false",
        "- ibkr_api_request_allowed: false",
        "- market_data_request_allowed: false",
        "- historical_data_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Sandbox Result Pack Rows",
        "",
        "| pack_id | sandbox_qualification_status | simulated_qualification_result | simulated_symbol | simulated_contract_id | simulated_result_only | real_qualification_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.pack_id,
                    row.sandbox_qualification_status,
                    row.simulated_qualification_result,
                    row.simulated_symbol,
                    row.simulated_contract_id,
                    row.simulated_result_only,
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
            "- Sandbox result pack status: BUILT",
            "- Results are simulated only.",
            "- Simulated qualification results are not real IBKR qualification.",
            "- Real qualification remains blocked.",
            "- TWS connection remains blocked.",
            "- IBKR API request remains blocked.",
            "- Market data requests remain blocked.",
            "- Historical data requests remain blocked.",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- Phase 13E sandbox result pack report only",
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
