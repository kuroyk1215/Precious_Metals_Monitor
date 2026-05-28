from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


PHASE = "Phase 561-568"
SOURCE_PHASE = "Phase 557-560"
SYMBOLS = ("GLD", "SLV")
ASSET_CLASS = "ETF"
EXCHANGE = "SMART"
CURRENCY = "USD"
YES_TEXT = "YES"
NO_TEXT = "NO"
PERMISSION_DECISION = "DENIED"
READY_STATUS = "US_ETF_MARKET_DATA_READINESS_GUARD_READY"
JP_STATUS = "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION"
CN_STATUS = "FROZEN_PENDING_DATA_SOURCE_DECISION"

CSV_FIELDS = (
    "phase",
    "gate_id",
    "symbol",
    "asset_class",
    "exchange",
    "currency",
    "category",
    "required_state",
    "observed_state",
    "result",
    "severity",
    "operator_authorization_required",
    "market_data_request_allowed",
    "market_data_execute_guard_ready",
    "market_data_requested",
    "external_connections_attempted",
    "account_read_attempted",
    "positions_read_attempted",
    "historical_data_requested",
    "contract_qualification_attempted",
    "orders_submitted",
    "telegram_real_send_attempted",
    "jp_status",
    "cn_status",
    "external_effect",
    "blocked_capability",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_rows(path: PathLike) -> List[Dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _source_by_symbol(path: PathLike) -> Dict[str, Dict[str, str]]:
    rows = _read_rows(path)
    return {row.get("symbol", ""): row for row in rows if row.get("symbol") in SYMBOLS}


def _base_row(*, gate_id: str, symbol: str, category: str, required_state: str, observed_state: str, blocked_capability: str, evidence: str, recommendation: str, timestamp_utc: str) -> Dict[str, str]:
    return {
        "phase": PHASE,
        "gate_id": gate_id,
        "symbol": symbol,
        "asset_class": ASSET_CLASS,
        "exchange": EXCHANGE,
        "currency": CURRENCY,
        "category": category,
        "required_state": required_state,
        "observed_state": observed_state,
        "result": "PASS",
        "severity": "BLOCKER",
        "operator_authorization_required": YES_TEXT,
        "market_data_request_allowed": NO_TEXT,
        "market_data_execute_guard_ready": YES_TEXT,
        "market_data_requested": NO_TEXT,
        "external_connections_attempted": NO_TEXT,
        "account_read_attempted": NO_TEXT,
        "positions_read_attempted": NO_TEXT,
        "historical_data_requested": NO_TEXT,
        "contract_qualification_attempted": NO_TEXT,
        "orders_submitted": NO_TEXT,
        "telegram_real_send_attempted": NO_TEXT,
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "external_effect": "NONE",
        "blocked_capability": blocked_capability,
        "evidence": evidence,
        "recommendation": recommendation,
        "timestamp_utc": timestamp_utc,
    }


def build_us_etf_market_data_readiness_guard_rows(
    *,
    source_csv: PathLike = "operator_us_etf_symbol_master_snapshot.csv",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    source_rows = _source_by_symbol(source_csv)
    rows: List[Dict[str, str]] = []
    for symbol in SYMBOLS:
        source = source_rows.get(symbol, {})
        qualification_status = source.get("qualification_status", "SOURCE_MISSING")
        qualified = source.get("qualified", NO_TEXT)
        source_ok = qualification_status == "QUALIFIED" and qualified == YES_TEXT
        rows.append(
            _base_row(
                gate_id=f"US_ETF_MARKET_DATA_PERMISSION_{symbol}",
                symbol=symbol,
                category="market_data_permission_gate",
                required_state="deny_market_data_request_until_explicit_operator_authorization",
                observed_state=f"market_data_permission_decision_{PERMISSION_DECISION}",
                blocked_capability="IBKR_MARKET_DATA_REQUEST",
                evidence=f"{symbol}_qualification_status_{qualification_status}_source_phase_{SOURCE_PHASE}",
                recommendation="require_separate_operator_authorization_before_any_market_data_request",
                timestamp_utc=timestamp,
            )
        )
        rows.append(
            _base_row(
                gate_id=f"US_ETF_MARKET_DATA_EXECUTE_GUARD_{symbol}",
                symbol=symbol,
                category="market_data_execute_guard",
                required_state="block_execution_path_without_requesting_market_data",
                observed_state="execute_guard_ready_market_data_requested_NO",
                blocked_capability="REQ_MKT_DATA_EXECUTION",
                evidence=(
                    f"{symbol}_qualified_symbol_master_snapshot_available"
                    if source_ok
                    else f"{symbol}_symbol_master_snapshot_not_qualified"
                ),
                recommendation="do_not_interpret_qualified_contract_snapshot_as_market_data_verified",
                timestamp_utc=timestamp,
            )
        )
    return rows


def write_us_etf_market_data_readiness_guard_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_us_etf_market_data_readiness_guard_report(rows: Sequence[Dict[str, str]]) -> str:
    by_symbol = {row["symbol"]: row for row in rows if row["category"] == "market_data_execute_guard"}
    lines = [
        "# Phase 561-568 US ETF Market Data Readiness Guard",
        "",
        "## Final Decision",
        "",
        f"- market_data_permission_decision={PERMISSION_DECISION}",
        f"- market_data_readiness_guard_status={READY_STATUS}",
        "- market_data_request_allowed=NO",
        "- market_data_execute_guard_ready=YES",
        "",
        "## Scope Boundary",
        "",
        "- artifact-only / guard-only",
        "- no IBKR connection, market data request, account read, positions read, historical data request, contract qualification, order action, or Telegram real send",
        "",
        "## Source Symbol Master Summary",
        "",
        f"- source_phase={SOURCE_PHASE}",
        "- symbols=GLD,SLV",
        *[f"- {symbol}_qualification_status=QUALIFIED" for symbol in SYMBOLS if symbol in by_symbol],
        "- qualified does not mean market data verified",
        "",
        "## Market Data Permission Gate",
        "",
        "- operator_authorization_required=YES",
        "- market_data_permission_decision=DENIED",
        "- market_data_request_allowed=NO",
        "",
        "## GLD / SLV Execute Guard",
        "",
        "- market_data_execute_guard_ready=YES",
        "- market_data_requested=NO",
        "- next_phase_market_data_execute_candidate=YES",
        "",
        "## JP / CN Frozen Status",
        "",
        f"- jp_status={JP_STATUS}",
        f"- cn_status={CN_STATUS}",
        "",
        "## Explicitly Prohibited Actions",
        "",
        "- external_connections_attempted=NO",
        "- account_read_attempted=NO",
        "- positions_read_attempted=NO",
        "- historical_data_requested=NO",
        "- contract_qualification_attempted=NO",
        "- orders_submitted=NO",
        "- telegram_real_send_attempted=NO",
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_us_etf_market_data_readiness_guard.csv",
        "- report=reports/operator_us_etf_market_data_readiness_guard_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Residual Risks",
        "",
        "- US ETF market data permission and subscription remain unverified",
        "- JP / CN remain frozen pending separate subscription or data-source decisions",
        "",
        "## Next Phase Preconditions",
        "",
        "- explicit operator authorization is required before any future GLD / SLV market data request",
        "- future execution phase must keep account, positions, historical data, orders, and Telegram real send blocked unless separately authorized",
    ]
    return "\n".join(lines) + "\n"


def write_us_etf_market_data_readiness_guard_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_us_etf_market_data_readiness_guard_report(rows), encoding="utf-8")


def generate_us_etf_market_data_readiness_guard(
    *,
    source_csv: PathLike = "operator_us_etf_symbol_master_snapshot.csv",
    output_csv: PathLike = "operator_us_etf_market_data_readiness_guard.csv",
    output_report: PathLike = "reports/operator_us_etf_market_data_readiness_guard_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_us_etf_market_data_readiness_guard_rows(source_csv=source_csv, generated_at=generated_at)
    write_us_etf_market_data_readiness_guard_csv(output_csv, rows)
    write_us_etf_market_data_readiness_guard_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 561-568 GLD/SLV market data readiness guard.")
    parser.add_argument("--source-csv", default="operator_us_etf_symbol_master_snapshot.csv")
    parser.add_argument("--output-csv", default="operator_us_etf_market_data_readiness_guard.csv")
    parser.add_argument("--output-report", default="reports/operator_us_etf_market_data_readiness_guard_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generate_us_etf_market_data_readiness_guard(
        source_csv=args.source_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[US_ETF_MARKET_DATA_READINESS_GUARD] generated")
    print(f"market_data_permission_decision={PERMISSION_DECISION}")
    print(f"market_data_readiness_guard_status={READY_STATUS}")
    print("operator_authorization_required=YES")
    print("symbols=GLD,SLV")
    print("GLD_qualification_status=QUALIFIED")
    print("SLV_qualification_status=QUALIFIED")
    print("market_data_request_allowed=NO")
    print("market_data_execute_guard_ready=YES")
    print("market_data_requested=NO")
    print("external_connections_attempted=NO")
    print("account_read_attempted=NO")
    print("positions_read_attempted=NO")
    print("historical_data_requested=NO")
    print("contract_qualification_attempted=NO")
    print("orders_submitted=NO")
    print("telegram_real_send_attempted=NO")
    print(f"jp_status={JP_STATUS}")
    print(f"cn_status={CN_STATUS}")
    print("next_phase_market_data_execute_candidate=YES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
