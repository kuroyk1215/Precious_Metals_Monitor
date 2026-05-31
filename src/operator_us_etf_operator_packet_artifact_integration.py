from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


PHASE = "Phase 581-588"
PACKET_ID = "US_ETF_OPERATOR_PACKET_ARTIFACT_INTEGRATION"
SYMBOLS = ("GLD", "SLV")
ASSET_CLASS = "US_ETF"
CONTRACT_QUALIFICATION_STATUS = "GLD_SLV_QUALIFIED"
CONNECTIVITY_STATUS = "VERIFIED_CONNECT_DISCONNECT"
MARKET_DATA_STATUS = "BLOCKED_BY_SUBSCRIPTION"
MARKET_DATA_CLASSIFICATION = "MARKET_DATA_BLOCKED_BY_SUBSCRIPTION"
IBKR_ERROR_CODE = "10089"
YES_TEXT = "YES"
NO_TEXT = "NO"
JP_STATUS = "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION"
CN_STATUS = "FROZEN_PENDING_DATA_SOURCE_DECISION"
OPERATOR_ACTION = "ARCHIVE_PACKET_AND_USE_READONLY_DASHBOARD_ARTIFACT_ONLY"
RECOMMENDATION = (
    "Keep US ETF market data blocked until subscription or delayed-data retry path is explicitly verified; "
    "use this packet as a read-only dashboard and Telegram artifact."
)

CSV_FIELDS = (
    "phase",
    "packet_id",
    "symbol",
    "asset_class",
    "contract_qualification_status",
    "connectivity_status",
    "market_data_status",
    "market_data_classification",
    "subscription_required",
    "delayed_available",
    "realtime_market_data_verified",
    "operator_action",
    "dashboard_ready",
    "telegram_ready",
    "jp_status",
    "cn_status",
    "external_effect",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

PROHIBITED_ACTIONS = (
    "ibkr_connection=NO",
    "market_data_request=NO",
    "account_read=NO",
    "positions_read=NO",
    "historical_data_request=NO",
    "contract_qualification=NO",
    "order_submit=NO",
    "cancel_order=NO",
    "rebalance=NO",
    "telegram_real_send=NO",
    "network_probe=NO",
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


def _source_value(row: Dict[str, str], field: str, default: str) -> str:
    value = row.get(field)
    return value if value not in (None, "") else default


def _row(symbol: str, source_row: Dict[str, str], timestamp: str) -> Dict[str, str]:
    source_evidence = _source_value(
        source_row,
        "evidence",
        f"{symbol}_phase_573_580_market_data_blocked_by_subscription",
    )
    source_status = _source_value(source_row, "market_data_status", "PERMISSION_DENIED")
    source_classification = _source_value(
        source_row,
        "classification",
        MARKET_DATA_CLASSIFICATION,
    )
    return {
        "phase": PHASE,
        "packet_id": PACKET_ID,
        "symbol": symbol,
        "asset_class": ASSET_CLASS,
        "contract_qualification_status": CONTRACT_QUALIFICATION_STATUS,
        "connectivity_status": CONNECTIVITY_STATUS,
        "market_data_status": MARKET_DATA_STATUS,
        "market_data_classification": MARKET_DATA_CLASSIFICATION,
        "subscription_required": YES_TEXT,
        "delayed_available": YES_TEXT,
        "realtime_market_data_verified": NO_TEXT,
        "operator_action": OPERATOR_ACTION,
        "dashboard_ready": YES_TEXT,
        "telegram_ready": YES_TEXT,
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "external_effect": "NONE_LOCAL_ARTIFACT_GENERATION_ONLY",
        "evidence": (
            f"phase_573_580_status={source_status}; classification={source_classification}; "
            f"ibkr_error_code={IBKR_ERROR_CODE}; {source_evidence}"
        ),
        "recommendation": RECOMMENDATION,
        "timestamp_utc": timestamp,
    }


def build_us_etf_operator_packet_artifact_integration_rows(
    *,
    source_csv: PathLike = "operator_us_etf_market_data_classifier_readiness.csv",
    generated_at: Optional[str] = None,
) -> list[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    source_rows = _read_source_rows(source_csv)
    return [_row(symbol, source_rows.get(symbol, {}), timestamp) for symbol in SYMBOLS]


def write_us_etf_operator_packet_artifact_integration_csv(
    path: PathLike, rows: Sequence[Dict[str, str]]
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_us_etf_operator_packet_artifact_integration_report(
    rows: Sequence[Dict[str, str]]
) -> str:
    packet_lines = [
        f"- {row['symbol']}: contract_qualification_status={row['contract_qualification_status']}; "
        f"connectivity_status={row['connectivity_status']}; market_data_status={row['market_data_status']}; "
        f"market_data_classification={row['market_data_classification']}; dashboard_ready={row['dashboard_ready']}; "
        f"telegram_ready={row['telegram_ready']}; realtime_market_data_verified={row['realtime_market_data_verified']}"
        for row in rows
    ]
    lines = [
        "# Phase 581-588 US ETF Operator Packet Artifact Integration",
        "",
        "## Final Packet Status",
        "",
        f"- operator_packet_status={PACKET_ID}_READY",
        f"- packet_id={PACKET_ID}",
        "- symbols=GLD,SLV",
        "",
        "## Scope Boundary",
        "",
        "- local artifact generation only",
        "- no IBKR connection, market data request, account read, position read, historical data request, contract qualification, order, cancel, rebalance, Telegram real send, or network probe",
        "",
        "## US ETF Status Summary",
        "",
        f"- connectivity_status={CONNECTIVITY_STATUS}",
        f"- contract_qualification_status={CONTRACT_QUALIFICATION_STATUS}",
        f"- market_data_status={MARKET_DATA_STATUS}",
        f"- market_data_classification={MARKET_DATA_CLASSIFICATION}",
        "",
        "## GLD / SLV Operator Packet",
        "",
        *packet_lines,
        "",
        "## Market Data Blocked Classification",
        "",
        "- source_status=PERMISSION_DENIED / IBKR_ERROR_10089 / SUBSCRIPTION_REQUIRED / DELAYED_AVAILABLE",
        f"- ibkr_error_code={IBKR_ERROR_CODE}",
        "- subscription_required=YES",
        "- delayed_available=YES",
        "- realtime_market_data_verified=NO",
        "- delayed_available does not imply realtime readiness",
        "",
        "## JP / CN Frozen Status",
        "",
        f"- jp_status={JP_STATUS}",
        f"- cn_status={CN_STATUS}",
        "",
        "## Dashboard Readiness",
        "",
        "- dashboard_artifact_ready=YES",
        "- dashboard scope is read-only artifact display",
        "",
        "## Telegram Readiness",
        "",
        "- telegram_artifact_ready=YES",
        "- telegram_real_send=NO",
        "",
        "## Explicitly Prohibited Actions",
        "",
        *[f"- {action}" for action in PROHIBITED_ACTIONS],
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_us_etf_operator_packet_artifact_integration.csv",
        "- report=reports/operator_us_etf_operator_packet_artifact_integration_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Residual Risks",
        "",
        "- US ETF realtime market data remains blocked by subscription permission",
        "- Dashboard and Telegram readiness are artifact-readiness only",
        "",
        "## Next Phase Preconditions",
        "",
        "- next_phase_dashboard_readonly_candidate=YES",
        "- do not promote market data readiness without a later verified subscription or delayed-data retry result",
    ]
    return "\n".join(lines) + "\n"


def write_us_etf_operator_packet_artifact_integration_report(
    path: PathLike, rows: Sequence[Dict[str, str]]
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_us_etf_operator_packet_artifact_integration_report(rows),
        encoding="utf-8",
    )


def generate_us_etf_operator_packet_artifact_integration(
    *,
    source_csv: PathLike = "operator_us_etf_market_data_classifier_readiness.csv",
    output_csv: PathLike = "operator_us_etf_operator_packet_artifact_integration.csv",
    output_report: PathLike = "reports/operator_us_etf_operator_packet_artifact_integration_report.md",
    generated_at: Optional[str] = None,
) -> list[Dict[str, str]]:
    rows = build_us_etf_operator_packet_artifact_integration_rows(
        source_csv=source_csv,
        generated_at=generated_at,
    )
    write_us_etf_operator_packet_artifact_integration_csv(output_csv, rows)
    write_us_etf_operator_packet_artifact_integration_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 581-588 US ETF operator packet artifact integration.")
    parser.add_argument("--source-csv", default="operator_us_etf_market_data_classifier_readiness.csv")
    parser.add_argument("--output-csv", default="operator_us_etf_operator_packet_artifact_integration.csv")
    parser.add_argument(
        "--output-report",
        default="reports/operator_us_etf_operator_packet_artifact_integration_report.md",
    )
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generate_us_etf_operator_packet_artifact_integration(
        source_csv=args.source_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[US_ETF_OPERATOR_PACKET_ARTIFACT_INTEGRATION] generated")
    print(f"operator_packet_status={PACKET_ID}_READY")
    print("symbols=GLD,SLV")
    print(f"connectivity_status={CONNECTIVITY_STATUS}")
    print(f"contract_qualification_status={CONTRACT_QUALIFICATION_STATUS}")
    print(f"market_data_status={MARKET_DATA_STATUS}")
    print(f"market_data_classification={MARKET_DATA_CLASSIFICATION}")
    print(f"ibkr_error_code={IBKR_ERROR_CODE}")
    print("subscription_required=YES")
    print("delayed_available=YES")
    print("realtime_market_data_verified=NO")
    print(f"jp_status={JP_STATUS}")
    print(f"cn_status={CN_STATUS}")
    print("dashboard_artifact_ready=YES")
    print("telegram_artifact_ready=YES")
    print("next_phase_dashboard_readonly_candidate=YES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
