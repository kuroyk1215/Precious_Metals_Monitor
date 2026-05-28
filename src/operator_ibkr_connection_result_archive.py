from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


PHASE = "Phase 541-544"
SOURCE_PHASE = "Phase 537-540"
SOURCE_CLI = "python3 main.py --ibkr-connect-only-dryrun-execute --operator-approved"
SOURCE_RESULT = "CONNECTED_THEN_DISCONNECTED"
ARCHIVE_STATUS = "IBKR_CONNECTION_RESULT_ARCHIVE_READY"
CLASSIFICATION = "CONNECTIVITY_VERIFIED_ONLY"
YES_TEXT = "YES"
NO_TEXT = "NO"

ERROR_TAXONOMY = (
    "CONNECTED_THEN_DISCONNECTED",
    "TWS_NOT_RUNNING",
    "API_DISABLED",
    "PORT_REFUSED",
    "CLIENT_ID_CONFLICT",
    "TIMEOUT",
    "IB_INSYNC_MISSING",
    "CONFIG_MISSING",
    "OPERATOR_APPROVAL_REQUIRED",
    "UNKNOWN_ERROR",
)

CSV_FIELDS = (
    "phase",
    "archive_id",
    "source_phase",
    "source_cli",
    "result_category",
    "connection_status",
    "connected",
    "disconnected",
    "operator_approved",
    "connection_attempted",
    "market_data_requested",
    "account_read_attempted",
    "positions_read_attempted",
    "historical_data_requested",
    "contract_qualification_attempted",
    "orders_submitted",
    "telegram_real_send_attempted",
    "error_type",
    "error_message_redacted",
    "classification",
    "severity",
    "external_effect",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _archive_id(timestamp_utc: str) -> str:
    safe = timestamp_utc.replace("+00:00", "Z").replace(":", "").replace("-", "")
    return f"IBKR-CONNECTION-RESULT-ARCHIVE-{safe}"


def build_ibkr_connection_result_archive_rows(generated_at: Optional[str] = None) -> List[Dict[str, str]]:
    timestamp_utc = generated_at or _now_timestamp()
    return [
        {
            "phase": PHASE,
            "archive_id": _archive_id(timestamp_utc),
            "source_phase": SOURCE_PHASE,
            "source_cli": SOURCE_CLI,
            "result_category": "CONNECT_ONLY_DRY_RUN_RESULT",
            "connection_status": SOURCE_RESULT,
            "connected": YES_TEXT,
            "disconnected": YES_TEXT,
            "operator_approved": YES_TEXT,
            "connection_attempted": YES_TEXT,
            "market_data_requested": NO_TEXT,
            "account_read_attempted": NO_TEXT,
            "positions_read_attempted": NO_TEXT,
            "historical_data_requested": NO_TEXT,
            "contract_qualification_attempted": NO_TEXT,
            "orders_submitted": NO_TEXT,
            "telegram_real_send_attempted": NO_TEXT,
            "error_type": SOURCE_RESULT,
            "error_message_redacted": "",
            "classification": CLASSIFICATION,
            "severity": "INFO",
            "external_effect": "ONE_CONNECT_DISCONNECT_FROM_SOURCE_PHASE_ONLY",
            "evidence": (
                "Phase 537-540 recorded a connect-only dry-run result of "
                "CONNECTED_THEN_DISCONNECTED; this archive performs no new external action."
            ),
            "recommendation": (
                "Use this archive as connectivity-only evidence. Gate any future contract "
                "qualification, market data, account, positions, historical data, trading, "
                "or Telegram real-send step separately."
            ),
            "timestamp_utc": timestamp_utc,
        }
    ]


def write_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def _taxonomy_lines() -> List[str]:
    descriptions = {
        "CONNECTED_THEN_DISCONNECTED": "Source phase reached IBKR connectivity and disconnected; connectivity only.",
        "TWS_NOT_RUNNING": "TWS/Gateway was unavailable or not accepting API sessions.",
        "API_DISABLED": "TWS/Gateway API access was disabled.",
        "PORT_REFUSED": "Configured local API port refused a connection.",
        "CLIENT_ID_CONFLICT": "The client id was already in use.",
        "TIMEOUT": "The connect-only attempt exceeded its timeout.",
        "IB_INSYNC_MISSING": "Required local Python package was unavailable.",
        "CONFIG_MISSING": "Required local connection configuration was absent or incomplete.",
        "OPERATOR_APPROVAL_REQUIRED": "A gated connect-only command lacked explicit operator approval.",
        "UNKNOWN_ERROR": "Failure did not match the known taxonomy.",
    }
    return [f"- `{key}`: {descriptions[key]}" for key in ERROR_TAXONOMY]


def write_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> Path:
    row = rows[0]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 541-544 IBKR Connection Result Archive",
        "",
        "## Final Archive Status",
        f"- archive_status={ARCHIVE_STATUS}",
        f"- classification={CLASSIFICATION}",
        "- production_ready=NO",
        "",
        "## Scope Boundary",
        "- Artifact-only archive of a previous connect-only dry-run result.",
        "- No new IBKR connection, market data request, account read, positions read, historical data request, contract qualification, order, cancel order, rebalance, Telegram real send, or network probe is performed.",
        "- CONNECTED_THEN_DISCONNECTED is connectivity-only evidence and is not market-data-verified or production-ready evidence.",
        "",
        "## Source Phase Summary",
        f"- source_phase={row['source_phase']}",
        f"- source_cli={row['source_cli']}",
        f"- source_result={row['connection_status']}",
        "- ibkr_connectivity_verified=YES",
        "- market_data_verified=NO",
        "- account_read_verified=NO",
        "- positions_read_verified=NO",
        "- historical_data_verified=NO",
        "- contract_qualification_verified=NO",
        "- trading_verified=NO",
        "- telegram_real_send_verified=NO",
        "",
        "## Result Classification",
        f"- result_category={row['result_category']}",
        f"- classification={row['classification']}",
        f"- severity={row['severity']}",
        f"- external_effect={row['external_effect']}",
        "",
        "## Error Taxonomy",
        *_taxonomy_lines(),
        "",
        "## Explicitly Prohibited Actions",
        "- No import of IBKR client libraries.",
        "- No IBKR connect or disconnect attempt in this phase.",
        "- No market data request, historical data request, account read, positions read, contract qualification, order submission, order cancellation, rebalance, Telegram real send, or network probe.",
        "",
        "## Artifact Summary",
        "- operator_ibkr_connection_result_archive.csv",
        "- reports/operator_ibkr_connection_result_archive_report.md",
        "",
        "## Residual Risks",
        "- Connectivity does not prove market data entitlement, account visibility, positions visibility, historical data access, contract qualification readiness, trading readiness, or production readiness.",
        "- Future phases still require explicit gates before any broader external action.",
        "",
        "## Next Phase Preconditions",
        "- next_phase_contract_qualification_gate_candidate=YES",
        "- Require a separate operator-approved gate before any contract qualification attempt.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def generate_ibkr_connection_result_archive(
    output_csv: PathLike = "operator_ibkr_connection_result_archive.csv",
    output_report: PathLike = "reports/operator_ibkr_connection_result_archive_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_ibkr_connection_result_archive_rows(generated_at=generated_at)
    write_csv(output_csv, rows)
    write_report(output_report, rows)
    return rows


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build Phase 541-544 IBKR connection result archive.")
    parser.add_argument("--output-csv", default="operator_ibkr_connection_result_archive.csv")
    parser.add_argument("--output-report", default="reports/operator_ibkr_connection_result_archive_report.md")
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args(argv)
    generate_ibkr_connection_result_archive(
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[IBKR_CONNECTION_RESULT_ARCHIVE] generated")
    print(f"archive_status={ARCHIVE_STATUS}")
    print(f"source_phase={SOURCE_PHASE}")
    print(f"source_result={SOURCE_RESULT}")
    print(f"classification={CLASSIFICATION}")
    print("ibkr_connectivity_verified=YES")
    print("market_data_verified=NO")
    print("account_read_verified=NO")
    print("positions_read_verified=NO")
    print("historical_data_verified=NO")
    print("contract_qualification_verified=NO")
    print("trading_verified=NO")
    print("telegram_real_send_verified=NO")
    print("next_phase_contract_qualification_gate_candidate=YES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
