from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo


FALSE_TEXT = "false"
TRUE_TEXT = "true"

DEFAULT_WARNING_FLAGS = (
    "PREFLIGHT_GUARD_DESIGN_ONLY",
    "REAL_CONNECTION_BLOCKED",
    "TWS_CONNECTION_BLOCKED",
    "IBKR_API_REQUEST_BLOCKED",
    "CONTRACT_QUALIFICATION_BLOCKED",
    "MARKET_DATA_REQUEST_BLOCKED",
    "HISTORICAL_DATA_REQUEST_BLOCKED",
    "ORDER_BLOCKED",
    "CANCEL_BLOCKED",
    "REBALANCE_BLOCKED",
    "AUTO_TRADE_BLOCKED",
    "phase14a_ibkr_readonly_preflight_guard_design",
)


@dataclass(frozen=True)
class PreflightGuardDesignRow:
    guard_id: str
    guard_name: str
    source_layer: str
    preflight_guard_status: str
    design_only: str
    required_before_real_connection: str
    real_connection_allowed: str
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
    guard_decision: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "guard_id",
    "guard_name",
    "source_layer",
    "preflight_guard_status",
    "design_only",
    "required_before_real_connection",
    "real_connection_allowed",
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
    "guard_decision",
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
    guard_id: str,
    guard_name: str,
    guard_decision: str,
    timestamp_jst: str,
    timestamp_et: str,
) -> PreflightGuardDesignRow:
    return PreflightGuardDesignRow(
        guard_id=guard_id,
        guard_name=guard_name,
        source_layer="Phase 14A",
        preflight_guard_status="DESIGN_ONLY",
        design_only=TRUE_TEXT,
        required_before_real_connection=TRUE_TEXT,
        real_connection_allowed=FALSE_TEXT,
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
        guard_decision=guard_decision,
        warning_flags=_flags([guard_decision]),
        notes=(
            "Phase 14A preflight guard design only. This row documents a future real read-only "
            "connection preflight guard requirement without granting any runtime capability. "
            "No TWS connection, no IBKR connection, no IBKR API request, no real contract qualification, "
            "no market data request, no historical data request, and no trading action is allowed."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_preflight_guard_design_rows(
    input_source: str | Path = "data/market_data_provider_config.yaml",
) -> list[PreflightGuardDesignRow]:
    timestamp_jst, timestamp_et = _now_pair()
    _ = str(input_source)

    return [
        _make_row(
            "CONFIG",
            "Configuration preflight boundary",
            "config_preflight_required_but_real_connection_blocked",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "ENV",
            "Environment preflight boundary",
            "environment_preflight_required_but_real_connection_blocked",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "TWS",
            "TWS session preflight boundary",
            "tws_session_preflight_required_but_tws_connection_blocked",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "ACCOUNT",
            "Account mode preflight boundary",
            "account_mode_preflight_required_but_ibkr_connection_blocked",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "READ_ONLY",
            "Read-only enforcement preflight boundary",
            "read_only_enforcement_required_before_any_future_connection",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "API_SCOPE",
            "IBKR API scope preflight boundary",
            "ibkr_api_scope_preflight_required_but_api_request_blocked",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "CONTRACTS",
            "Contract qualification preflight boundary",
            "contract_qualification_preflight_required_but_real_qualification_blocked",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "MARKET_DATA",
            "Market data request preflight boundary",
            "market_data_preflight_required_but_reqMktData_blocked",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "HISTORICAL_DATA",
            "Historical data request preflight boundary",
            "historical_data_preflight_required_but_reqHistoricalData_blocked",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "ACTIONS",
            "Trading action preflight boundary",
            "order_cancel_rebalance_auto_trade_preflight_required_but_actions_blocked",
            timestamp_jst,
            timestamp_et,
        ),
        _make_row(
            "FINAL",
            "Final preflight guard design",
            "phase14a_preflight_guard_design_complete_but_execution_blocked",
            timestamp_jst,
            timestamp_et,
        ),
    ]


def write_ibkr_readonly_preflight_guard_design_csv(
    path: str | Path,
    rows: Iterable[PreflightGuardDesignRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_preflight_guard_design_report(
    path: str | Path,
    rows: Iterable[PreflightGuardDesignRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    design_only_count = sum(1 for row in row_list if row.preflight_guard_status == "DESIGN_ONLY")
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)
    statuses = sorted({row.preflight_guard_status for row in row_list}) or ["none"]

    lines = [
        "# Phase 14A IBKR Read-Only Preflight Guard Design Report",
        "",
        "- phase: Phase 14A",
        "- scope: IBKR read-only preflight guard design",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- preflight_guard_statuses: {','.join(statuses)}",
        f"- design_only_count: {design_only_count}",
        f"- action_allowed_count: {action_allowed_count}",
        "- preflight_guard_status: DESIGN_ONLY",
        "- design_only: true",
        "- required_before_real_connection: true",
        "- real_connection_allowed: false",
        "- tws_connection_allowed: false",
        "- ibkr_api_request_allowed: false",
        "- contract_qualification_allowed: false",
        "- market_data_request_allowed: false",
        "- historical_data_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Preflight Guard Design Rows",
        "",
        "| guard_id | preflight_guard_status | design_only | required_before_real_connection | real_connection_allowed | tws_connection_allowed | ibkr_api_request_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.guard_id,
                    row.preflight_guard_status,
                    row.design_only,
                    row.required_before_real_connection,
                    row.real_connection_allowed,
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
            "- Preflight guard status: DESIGN_ONLY",
            "- Preflight guard is required before any future real read-only connection.",
            "- Real connection allowed: false",
            "- TWS connection allowed: false",
            "- IBKR API request allowed: false",
            "- Contract qualification allowed: false",
            "- Market data requests remain blocked.",
            "- Historical data requests remain blocked.",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- Phase 14A preflight guard design report only",
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
