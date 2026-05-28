from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


PHASE = "Phase 549-552"
GUARD_STATUS = "SINGLE_SYMBOL_CONTRACT_QUALIFICATION_GUARD_READY"
YES_TEXT = "YES"
NO_TEXT = "NO"
DEFAULT_SYMBOL = "GLD"
DEFAULT_ASSET_CLASS = "ETF"
DEFAULT_EXCHANGE = "SMART"
DEFAULT_CURRENCY = "USD"

CSV_FIELDS = (
    "phase",
    "guard_id",
    "symbol",
    "asset_class",
    "exchange",
    "currency",
    "category",
    "required_state",
    "observed_state",
    "result",
    "severity",
    "operator_approved",
    "qualification_allowed",
    "qualification_attempted",
    "external_connections_attempted",
    "market_data_requested",
    "account_read_attempted",
    "positions_read_attempted",
    "historical_data_requested",
    "orders_submitted",
    "telegram_real_send_attempted",
    "external_effect",
    "blocked_capability",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

STATUS_FIELDS = (
    "single_symbol_qualification_guard_status",
    "operator_authorization_required",
    "qualification_allowed",
    "qualification_attempted",
    "external_connections_attempted",
    "ibkr_connected",
    "market_data_requested",
    "account_read_attempted",
    "positions_read_attempted",
    "historical_data_requested",
    "orders_submitted",
    "telegram_real_send_attempted",
    "next_phase_single_symbol_qualification_execute_candidate",
)

STATUS_VALUES = {
    "single_symbol_qualification_guard_status": GUARD_STATUS,
    "operator_authorization_required": YES_TEXT,
    "qualification_allowed": NO_TEXT,
    "qualification_attempted": NO_TEXT,
    "external_connections_attempted": NO_TEXT,
    "ibkr_connected": NO_TEXT,
    "market_data_requested": NO_TEXT,
    "account_read_attempted": NO_TEXT,
    "positions_read_attempted": NO_TEXT,
    "historical_data_requested": NO_TEXT,
    "orders_submitted": NO_TEXT,
    "telegram_real_send_attempted": NO_TEXT,
    "next_phase_single_symbol_qualification_execute_candidate": YES_TEXT,
}

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _row(
    *,
    guard_id: str,
    symbol: str,
    asset_class: str,
    exchange: str,
    currency: str,
    category: str,
    required_state: str,
    observed_state: str,
    result: str,
    severity: str,
    blocked_capability: str,
    evidence: str,
    recommendation: str,
    timestamp_utc: str,
) -> Dict[str, str]:
    return {
        "phase": PHASE,
        "guard_id": guard_id,
        "symbol": symbol,
        "asset_class": asset_class,
        "exchange": exchange,
        "currency": currency,
        "category": category,
        "required_state": required_state,
        "observed_state": observed_state,
        "result": result,
        "severity": severity,
        "operator_approved": NO_TEXT,
        "qualification_allowed": NO_TEXT,
        "qualification_attempted": NO_TEXT,
        "external_connections_attempted": NO_TEXT,
        "market_data_requested": NO_TEXT,
        "account_read_attempted": NO_TEXT,
        "positions_read_attempted": NO_TEXT,
        "historical_data_requested": NO_TEXT,
        "orders_submitted": NO_TEXT,
        "telegram_real_send_attempted": NO_TEXT,
        "external_effect": "NONE",
        "blocked_capability": blocked_capability,
        "evidence": evidence,
        "recommendation": recommendation,
        "timestamp_utc": timestamp_utc,
    }


def build_single_symbol_contract_qualification_guard_rows(
    *,
    symbol: str = DEFAULT_SYMBOL,
    asset_class: str = DEFAULT_ASSET_CLASS,
    exchange: str = DEFAULT_EXCHANGE,
    currency: str = DEFAULT_CURRENCY,
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    common = {
        "symbol": symbol,
        "asset_class": asset_class,
        "exchange": exchange,
        "currency": currency,
        "timestamp_utc": timestamp,
    }
    return [
        _row(
            guard_id="SINGLE-SYMBOL-QUALIFICATION-GUARD-000",
            category="final_decision",
            required_state="operator_approval_required_before_real_single_symbol_contract_qualification",
            observed_state="operator_approved_NO_qualification_allowed_NO",
            result="BLOCKED",
            severity="CRITICAL",
            blocked_capability="REAL_CONTRACT_QUALIFICATION",
            evidence="guard_artifact_generated_without_qualification_execution_path",
            recommendation="collect_explicit_operator_authorization_before_any_qualification_attempt",
            **common,
        ),
        _row(
            guard_id="SINGLE-SYMBOL-QUALIFICATION-GUARD-001",
            category="single_symbol_scope",
            required_state="exactly_one_future_candidate_symbol_recorded_without_execution",
            observed_state=f"candidate_symbol_{symbol}_asset_class_{asset_class}_exchange_{exchange}_currency_{currency}",
            result="PASS",
            severity="HIGH",
            blocked_capability="MULTI_SYMBOL_OR_CHAINED_QUALIFICATION",
            evidence="single_candidate_metadata_recorded_for_next_phase_only",
            recommendation="keep_next_phase_limited_to_one_operator_approved_symbol",
            **common,
        ),
        _row(
            guard_id="SINGLE-SYMBOL-QUALIFICATION-GUARD-002",
            category="external_connection_guard",
            required_state="no_ibkr_tws_gateway_connection_and_no_network_probe",
            observed_state="external_connections_attempted_NO_ibkr_connected_NO",
            result="PASS",
            severity="CRITICAL",
            blocked_capability="EXTERNAL_CONNECTION_OR_NETWORK_PROBE",
            evidence="artifact_only_generator_has_no_connector_or_probe_path",
            recommendation="do_not_connect_until_separate_execution_phase_authorization",
            **common,
        ),
        _row(
            guard_id="SINGLE-SYMBOL-QUALIFICATION-GUARD-003",
            category="data_access_guard",
            required_state="no_market_data_account_positions_or_historical_data_requests",
            observed_state="market_data_account_positions_historical_flags_NO",
            result="PASS",
            severity="CRITICAL",
            blocked_capability="IBKR_DATA_ACCESS",
            evidence="guard_outputs_static_no_request_attempt_flags",
            recommendation="do_not_pair_contract_qualification_guard_with_any_data_request",
            **common,
        ),
        _row(
            guard_id="SINGLE-SYMBOL-QUALIFICATION-GUARD-004",
            category="action_guard",
            required_state="no_orders_cancels_rebalance_or_telegram_real_send",
            observed_state="orders_submitted_NO_telegram_real_send_attempted_NO",
            result="PASS",
            severity="CRITICAL",
            blocked_capability="TRADING_OR_REAL_NOTIFICATION",
            evidence="guard_has_no_order_cancel_rebalance_or_real_send_path",
            recommendation="keep_trading_and_notification_execution_out_of_qualification_phases",
            **common,
        ),
        _row(
            guard_id="SINGLE-SYMBOL-QUALIFICATION-GUARD-005",
            category="status_label_guard",
            required_state="do_not_reclassify_connectivity_permission_or_guard_artifacts_as_qualification_verified",
            observed_state="qualification_attempted_NO_qualification_allowed_NO",
            result="PASS",
            severity="HIGH",
            blocked_capability="MISLEADING_VERIFICATION_OR_PRODUCTION_STATUS",
            evidence="ready_status_describes_guard_artifact_only",
            recommendation="do_not_mark_contract_qualification_market_data_trading_or_production_status_verified",
            **common,
        ),
    ]


def write_single_symbol_contract_qualification_guard_csv(
    path: PathLike, rows: Sequence[Dict[str, str]]
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_single_symbol_contract_qualification_guard_report(rows: Sequence[Dict[str, str]]) -> str:
    status_lines = [f"- {field}={STATUS_VALUES[field]}" for field in STATUS_FIELDS]
    guard_lines = [
        f"- {row['guard_id']} {row['category']}: {row['result']} / blocks={row['blocked_capability']}"
        for row in rows
    ]
    first = rows[0] if rows else {}
    symbol = first.get("symbol", DEFAULT_SYMBOL)
    asset_class = first.get("asset_class", DEFAULT_ASSET_CLASS)
    exchange = first.get("exchange", DEFAULT_EXCHANGE)
    currency = first.get("currency", DEFAULT_CURRENCY)
    prohibited_actions = [
        "- IBKR, TWS, or IB Gateway connection",
        "- network probe",
        "- market data request",
        "- account read",
        "- positions read",
        "- historical data request",
        "- real contract qualification",
        "- order submission or cancellation",
        "- rebalance action",
        "- Telegram real send",
    ]
    lines = [
        "# Phase 549-552 Single-Symbol Contract Qualification Guard",
        "",
        "## Final Decision",
        "",
        *status_lines,
        "",
        "Single-symbol contract qualification remains blocked. This artifact only prepares the guard wrapper for a possible later operator-approved execution phase.",
        "",
        "## Scope Boundary",
        "",
        "- artifact-only guard for one future candidate symbol",
        "- no real contract qualification is performed",
        "- prior connectivity or permission evidence remains separate from qualification verification",
        "- ready status means this guard artifact is ready only",
        "",
        "## Explicitly Prohibited Actions",
        "",
        *prohibited_actions,
        "",
        "## Single-Symbol Guard",
        "",
        f"- candidate_symbol={symbol}",
        f"- asset_class={asset_class}",
        f"- exchange={exchange}",
        f"- currency={currency}",
        *guard_lines,
        "",
        "## Operator Approval Requirements",
        "",
        "- explicit operator authorization is required before any real single-symbol contract qualification",
        "- approval must be separate from connectivity result archives and permission gate artifacts",
        "- authorization must name exactly one symbol, asset class, exchange, and currency",
        "",
        "## Qualification Preconditions",
        "",
        "- next phase must remain single-symbol only",
        "- next phase must fail closed if authorization or contract metadata is ambiguous",
        "- next phase must still avoid market data, historical data, account, positions, orders, cancellations, rebalances, and Telegram sends unless separately approved",
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_single_symbol_contract_qualification_guard.csv",
        "- report=reports/operator_single_symbol_contract_qualification_guard_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Residual Risks",
        "",
        "- this guard does not prove contract qualification access",
        "- this guard does not prove market data entitlement, account visibility, positions visibility, historical data access, trading readiness, or production readiness",
        "- future execution code still requires explicit review and authorization",
        "",
        "## Next Phase Preconditions",
        "",
        "- explicit user authorization for one single-symbol qualification execution candidate",
        "- reviewed implementation that stops after qualification and emits no data, trading, or real notification request",
        "- no automatic transition from this guard to production-ready status",
    ]
    return "\n".join(lines) + "\n"


def write_single_symbol_contract_qualification_guard_report(
    path: PathLike, rows: Sequence[Dict[str, str]]
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_single_symbol_contract_qualification_guard_report(rows), encoding="utf-8")


def generate_single_symbol_contract_qualification_guard(
    *,
    output_csv: PathLike = "operator_single_symbol_contract_qualification_guard.csv",
    output_report: PathLike = "reports/operator_single_symbol_contract_qualification_guard_report.md",
    symbol: str = DEFAULT_SYMBOL,
    asset_class: str = DEFAULT_ASSET_CLASS,
    exchange: str = DEFAULT_EXCHANGE,
    currency: str = DEFAULT_CURRENCY,
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_single_symbol_contract_qualification_guard_rows(
        symbol=symbol,
        asset_class=asset_class,
        exchange=exchange,
        currency=currency,
        generated_at=generated_at,
    )
    write_single_symbol_contract_qualification_guard_csv(output_csv, rows)
    write_single_symbol_contract_qualification_guard_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 549-552 single-symbol contract qualification guard.")
    parser.add_argument("--output-csv", default="operator_single_symbol_contract_qualification_guard.csv")
    parser.add_argument(
        "--output-report",
        default="reports/operator_single_symbol_contract_qualification_guard_report.md",
    )
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--asset-class", default=DEFAULT_ASSET_CLASS)
    parser.add_argument("--exchange", default=DEFAULT_EXCHANGE)
    parser.add_argument("--currency", default=DEFAULT_CURRENCY)
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_single_symbol_contract_qualification_guard(
        output_csv=args.output_csv,
        output_report=args.output_report,
        symbol=args.symbol,
        asset_class=args.asset_class,
        exchange=args.exchange,
        currency=args.currency,
        generated_at=args.generated_at,
    )
    print("[SINGLE_SYMBOL_CONTRACT_QUALIFICATION_GUARD] generated")
    for field in STATUS_FIELDS:
        print(f"{field}={STATUS_VALUES[field]}")
    print(f"guards={len(rows)}")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
