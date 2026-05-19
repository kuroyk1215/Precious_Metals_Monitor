from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo


FALSE_TEXT = "false"

DEFAULT_WARNING_FLAGS = (
    "DESIGN_ONLY",
    "SANDBOX_EXECUTION_BLOCKED",
    "REAL_IBKR_CONNECTION_BLOCKED",
    "TWS_CONNECTION_BLOCKED",
    "IBKR_API_REQUEST_BLOCKED",
    "NO_CONTRACT_QUALIFICATION",
    "NO_REQ_MKT_DATA",
    "NO_REQ_HISTORICAL_DATA",
    "NO_ORDER",
    "NO_CANCEL",
    "NO_REBALANCE",
    "NO_AUTO_TRADE",
    "phase13a_ibkr_readonly_qualification_sandbox_design",
)


@dataclass(frozen=True)
class SandboxDesignRow:
    component_id: str
    component_name: str
    source_layer: str
    sandbox_design_status: str
    sandbox_execution_allowed: str
    real_ibkr_connection_allowed: str
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
    design_decision: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "component_id",
    "component_name",
    "source_layer",
    "sandbox_design_status",
    "sandbox_execution_allowed",
    "real_ibkr_connection_allowed",
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
    "design_decision",
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
    component_id: str,
    component_name: str,
    source_layer: str,
    design_decision: str,
    timestamp_jst: str,
    timestamp_et: str,
) -> SandboxDesignRow:
    return SandboxDesignRow(
        component_id=component_id,
        component_name=component_name,
        source_layer=source_layer,
        sandbox_design_status="DESIGN_ONLY",
        sandbox_execution_allowed=FALSE_TEXT,
        real_ibkr_connection_allowed=FALSE_TEXT,
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
        design_decision=design_decision,
        warning_flags=_flags([design_decision]),
        notes=(
            "Sandbox design packet only. This phase documents the future read-only qualification "
            "sandbox structure without opening any TWS, IBKR API, qualification, market data, "
            "historical data, order, cancel, rebalance, or auto-trade capability."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_qualification_sandbox_design_rows(
    input_source: str | Path = "data/market_data_provider_config.yaml",
) -> list[SandboxDesignRow]:
    timestamp_jst, timestamp_et = _now_pair()
    _ = str(input_source)

    return [
        _make_row("ENV", "Sandbox environment boundary", "Phase 13A", "sandbox_environment_design_only_no_runtime_execution", timestamp_jst, timestamp_et),
        _make_row("NETWORK", "Network and TWS boundary", "Phase 13A", "network_and_tws_connection_blocked_by_design", timestamp_jst, timestamp_et),
        _make_row("CONTRACTS", "Contract qualification boundary", "Phase 13A", "contract_qualification_blocked_until_future_explicit_gate", timestamp_jst, timestamp_et),
        _make_row("DATA", "Market and historical data request boundary", "Phase 13A", "market_and_historical_data_requests_blocked_by_design", timestamp_jst, timestamp_et),
        _make_row("ACTIONS", "Trading action boundary", "Phase 13A", "orders_cancels_rebalance_and_auto_trade_blocked_by_design", timestamp_jst, timestamp_et),
        _make_row("FINAL", "Final sandbox design packet", "Phase 13A", "phase13a_sandbox_design_complete_but_execution_blocked", timestamp_jst, timestamp_et),
    ]


def write_ibkr_readonly_qualification_sandbox_design_csv(
    path: str | Path,
    rows: Iterable[SandboxDesignRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_qualification_sandbox_design_report(
    path: str | Path,
    rows: Iterable[SandboxDesignRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    design_only_count = sum(1 for row in row_list if row.sandbox_design_status == "DESIGN_ONLY")
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == "true")
    statuses = sorted({row.sandbox_design_status for row in row_list}) or ["none"]

    lines = [
        "# Phase 13A IBKR Read-Only Qualification Sandbox Design Report",
        "",
        "- phase: Phase 13A",
        "- scope: IBKR read-only qualification sandbox design",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- sandbox_design_statuses: {','.join(statuses)}",
        f"- design_only_count: {design_only_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- sandbox_design_status: DESIGN_ONLY",
        "- sandbox_execution_allowed: false",
        "- real_ibkr_connection_allowed: false",
        "- tws_connection_allowed: false",
        "- ibkr_api_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Sandbox Design Rows",
        "",
        "| component_id | component_name | sandbox_design_status | sandbox_execution_allowed | real_ibkr_connection_allowed | tws_connection_allowed | ibkr_api_request_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.component_id,
                    row.component_name,
                    row.sandbox_design_status,
                    row.sandbox_execution_allowed,
                    row.real_ibkr_connection_allowed,
                    row.tws_connection_allowed,
                    row.ibkr_api_request_allowed,
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
            "- Sandbox design status: DESIGN_ONLY",
            "- Sandbox execution allowed: false",
            "- Real IBKR connection allowed: false",
            "- TWS connection allowed: false",
            "- IBKR API request allowed: false",
            "- Contract qualification allowed: false",
            "- Market data requests remain blocked.",
            "- Historical data requests remain blocked.",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- Phase 13A sandbox design report only",
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
