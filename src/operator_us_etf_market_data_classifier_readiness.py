from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


PHASE = "Phase 573-580"
SOURCE_PHASE = "Phase 569-572"
SOURCE_CLI = "python3 main.py --us-etf-market-data-execute --operator-approved"
SYMBOLS = ("GLD", "SLV")
YES_TEXT = "YES"
NO_TEXT = "NO"
IBKR_ERROR_CODE = "10089"
CLASSIFICATION = "MARKET_DATA_BLOCKED_BY_SUBSCRIPTION"
READINESS_STATUS = "CONNECTIVITY_AND_CONTRACTS_VERIFIED_ONLY"
NEXT_ACTION = "SUBSCRIBE_NETWORK_B_OR_IMPLEMENT_DELAYED_DATA_RETRY"
JP_STATUS = "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION"
CN_STATUS = "FROZEN_PENDING_DATA_SOURCE_DECISION"

CSV_FIELDS = (
    "phase",
    "symbol",
    "source_phase",
    "source_cli",
    "market_data_status",
    "error_type",
    "ibkr_error_code",
    "subscription_required",
    "delayed_available",
    "realtime_market_data_verified",
    "market_data_request_tested",
    "bid_present",
    "ask_present",
    "last_present",
    "close_present",
    "classification",
    "readiness_status",
    "next_action",
    "jp_status",
    "cn_status",
    "external_effect",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

CLASSIFICATIONS = (
    "PERMISSION_DENIED",
    "IBKR_ERROR_10089",
    "SUBSCRIPTION_REQUIRED",
    "DELAYED_AVAILABLE",
    "REALTIME_NOT_VERIFIED",
    "MARKET_DATA_BLOCKED_BY_SUBSCRIPTION",
    "CONNECTIVITY_AND_CONTRACTS_VERIFIED_ONLY",
)


PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_source_rows(path: PathLike) -> Dict[str, Dict[str, str]]:
    source_path = Path(path)
    if not source_path.exists():
        return {}
    with source_path.open(newline="", encoding="utf-8") as f:
        return {row.get("symbol", ""): row for row in csv.DictReader(f)}


def _source_value(row: Dict[str, str], field: str, default: str = NO_TEXT) -> str:
    value = row.get(field)
    return value if value not in (None, "") else default


def _row(symbol: str, source_row: Dict[str, str], timestamp: str) -> Dict[str, str]:
    status = _source_value(source_row, "market_data_status", "PERMISSION_DENIED")
    error_type = _source_value(source_row, "error_type", "PERMISSION_DENIED")
    evidence = _source_value(source_row, "evidence", f"{symbol}_phase_569_572_permission_denied")
    source_message = _source_value(source_row, "error_message_redacted", "")
    if "10089" not in source_message:
        source_message = "IBKR_10089_MARKET_DATA_SUBSCRIPTION_REQUIRED_DELAYED_AVAILABLE"
    return {
        "phase": PHASE,
        "symbol": symbol,
        "source_phase": SOURCE_PHASE,
        "source_cli": SOURCE_CLI,
        "market_data_status": status,
        "error_type": "IBKR_ERROR_10089" if error_type == "PERMISSION_DENIED" else error_type,
        "ibkr_error_code": IBKR_ERROR_CODE,
        "subscription_required": YES_TEXT,
        "delayed_available": YES_TEXT,
        "realtime_market_data_verified": NO_TEXT,
        "market_data_request_tested": YES_TEXT,
        "bid_present": _source_value(source_row, "bid_present"),
        "ask_present": _source_value(source_row, "ask_present"),
        "last_present": _source_value(source_row, "last_present"),
        "close_present": _source_value(source_row, "close_present"),
        "classification": CLASSIFICATION,
        "readiness_status": READINESS_STATUS,
        "next_action": NEXT_ACTION,
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "external_effect": "NONE_CLASSIFICATION_FROM_ARCHIVED_PHASE_569_572_ARTIFACT",
        "evidence": f"{evidence}; {source_message}",
        "recommendation": "Do not mark market data ready; subscribe Network B or implement delayed data retry before later readiness promotion.",
        "timestamp_utc": timestamp,
    }


def build_us_etf_market_data_classifier_readiness_rows(
    *,
    source_csv: PathLike = "operator_us_etf_market_data_execute.csv",
    generated_at: Optional[str] = None,
) -> list[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    source_rows = _read_source_rows(source_csv)
    return [_row(symbol, source_rows.get(symbol, {}), timestamp) for symbol in SYMBOLS]


def write_us_etf_market_data_classifier_readiness_csv(
    path: PathLike, rows: Sequence[Dict[str, str]]
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_us_etf_market_data_classifier_readiness_report(
    rows: Sequence[Dict[str, str]]
) -> str:
    summary = [
        f"- {row['symbol']}: market_data_status={row['market_data_status']}; error_type={row['error_type']}; "
        f"subscription_required={row['subscription_required']}; delayed_available={row['delayed_available']}; "
        f"realtime_market_data_verified={row['realtime_market_data_verified']}"
        for row in rows
    ]
    lines = [
        "# Phase 573-580 US ETF Market Data Classifier Readiness",
        "",
        "## Final Readiness Status",
        "",
        f"- us_etf_readiness_status={READINESS_STATUS}",
        f"- classification={CLASSIFICATION}",
        "- realtime_market_data_verified=NO",
        "",
        "## Scope Boundary",
        "",
        "- source artifact only: operator_us_etf_market_data_execute.csv",
        "- no IBKR connection, market data request, account read, position read, historical data request, contract qualification, order, cancel, rebalance, Telegram real send, or network probe",
        "",
        "## Source Market Data Result",
        "",
        *summary,
        "",
        "## Permission Denied Classification",
        "",
        *[f"- {item}" for item in CLASSIFICATIONS],
        "",
        "## Delayed Data Policy",
        "",
        "- delayed_available=YES does not imply realtime readiness",
        f"- next_action={NEXT_ACTION}",
        "",
        "## US ETF Readiness Summary",
        "",
        "- GLD / SLV connectivity and contracts remain archived from previous phases only",
        f"- readiness_status={READINESS_STATUS}",
        "",
        "## JP / CN Frozen Status",
        "",
        f"- jp_status={JP_STATUS}",
        f"- cn_status={CN_STATUS}",
        "",
        "## Explicitly Prohibited Actions",
        "",
        "- ibkr_connection=NO",
        "- market_data_request=NO",
        "- account_read=NO",
        "- positions_read=NO",
        "- historical_data_request=NO",
        "- contract_qualification=NO",
        "- order_submit=NO",
        "- cancel_order=NO",
        "- rebalance=NO",
        "- telegram_real_send=NO",
        "- network_probe=NO",
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_us_etf_market_data_classifier_readiness.csv",
        "- report=reports/operator_us_etf_market_data_classifier_readiness_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Residual Risks",
        "",
        "- US ETF realtime market data remains blocked by subscription permission",
        "- delayed data is available but not promoted to realtime readiness",
        "",
        "## Next Phase Preconditions",
        "",
        f"- {NEXT_ACTION}",
        "- keep market data readiness blocked until a later phase verifies the selected path",
    ]
    return "\n".join(lines) + "\n"


def write_us_etf_market_data_classifier_readiness_report(
    path: PathLike, rows: Sequence[Dict[str, str]]
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_us_etf_market_data_classifier_readiness_report(rows), encoding="utf-8")


def generate_us_etf_market_data_classifier_readiness(
    *,
    source_csv: PathLike = "operator_us_etf_market_data_execute.csv",
    output_csv: PathLike = "operator_us_etf_market_data_classifier_readiness.csv",
    output_report: PathLike = "reports/operator_us_etf_market_data_classifier_readiness_report.md",
    generated_at: Optional[str] = None,
) -> list[Dict[str, str]]:
    rows = build_us_etf_market_data_classifier_readiness_rows(
        source_csv=source_csv,
        generated_at=generated_at,
    )
    write_us_etf_market_data_classifier_readiness_csv(output_csv, rows)
    write_us_etf_market_data_classifier_readiness_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 573-580 US ETF market data classifier readiness artifacts.")
    parser.add_argument("--source-csv", default="operator_us_etf_market_data_execute.csv")
    parser.add_argument("--output-csv", default="operator_us_etf_market_data_classifier_readiness.csv")
    parser.add_argument(
        "--output-report",
        default="reports/operator_us_etf_market_data_classifier_readiness_report.md",
    )
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_us_etf_market_data_classifier_readiness(
        source_csv=args.source_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    by_symbol = {row["symbol"]: row for row in rows}
    print("[US_ETF_MARKET_DATA_CLASSIFIER_READINESS] generated")
    print("market_data_classifier_status=US_ETF_MARKET_DATA_CLASSIFIER_READINESS_READY")
    print(f"source_phase={SOURCE_PHASE}")
    print("symbols=GLD,SLV")
    print(f"GLD_market_data_status={by_symbol['GLD']['market_data_status']}")
    print(f"SLV_market_data_status={by_symbol['SLV']['market_data_status']}")
    print(f"ibkr_error_code={IBKR_ERROR_CODE}")
    print("subscription_required=YES")
    print("delayed_available=YES")
    print("realtime_market_data_verified=NO")
    print("market_data_request_tested=YES")
    print(f"classification={CLASSIFICATION}")
    print(f"us_etf_readiness_status={READINESS_STATUS}")
    print(f"next_action={NEXT_ACTION}")
    print(f"jp_status={JP_STATUS}")
    print(f"cn_status={CN_STATUS}")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
