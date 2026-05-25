from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple, Union


TRUE_TEXT = "true"
FALSE_TEXT = "false"

LATEST_FIELDS = (
    "latest_generated_at",
    "source_summary_file",
    "source_archive_file",
    "source_decision_file",
    "summary_exists",
    "archive_exists",
    "decision_exists",
    "latest_status",
    "operator_decision",
    "source_diagnostic_category",
    "top_level_status",
    "final_safety_status",
    "config_restored",
    "config_file_modified",
    "real_connection_allowed_during_run",
    "market_data_request_allowed_during_run",
    "contract_qualification_allowed",
    "historical_data_request_allowed",
    "trading_actions_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "telegram_send_allowed",
    "req_mkt_data_allowed",
    "req_historical_data_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "latest_pointer",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _bool_text(value: object) -> str:
    return TRUE_TEXT if bool(value) else FALSE_TEXT


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "allowed", "triggered"}


def _read_latest_row(path: PathLike) -> Optional[Dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return None
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[-1] if rows else None


def _copy_bool(source: Optional[Dict[str, str]], field: str) -> str:
    if source is None:
        return FALSE_TEXT
    return _bool_text(_truthy(source.get(field)))


def _latest_status(decision: Optional[Dict[str, str]], summary: Optional[Dict[str, str]], archive: Optional[Dict[str, str]]) -> str:
    if decision is None or archive is None or summary is None:
        return "LATEST_INCOMPLETE"
    return decision.get("operator_decision") or "LATEST_INCOMPLETE"


def build_latest_row(
    *,
    source_summary_file: PathLike = "operator_real_marketdata_smoke_summary.csv",
    source_archive_file: PathLike = "operator_real_marketdata_smoke_archive.csv",
    source_decision_file: PathLike = "operator_real_marketdata_decision_gate.csv",
    latest_generated_at: Optional[str] = None,
) -> Dict[str, str]:
    summary = _read_latest_row(source_summary_file)
    archive = _read_latest_row(source_archive_file)
    decision = _read_latest_row(source_decision_file)
    status = _latest_status(decision, summary, archive)
    row = {
        "latest_generated_at": latest_generated_at or _now_timestamp(),
        "source_summary_file": str(source_summary_file),
        "source_archive_file": str(source_archive_file),
        "source_decision_file": str(source_decision_file),
        "summary_exists": _bool_text(summary is not None),
        "archive_exists": _bool_text(archive is not None),
        "decision_exists": _bool_text(decision is not None),
        "latest_status": status,
        "operator_decision": decision.get("operator_decision", "") if decision else "",
        "source_diagnostic_category": decision.get("source_diagnostic_category", "") if decision else "",
        "top_level_status": (summary or archive or {}).get("top_level_status", ""),
        "final_safety_status": (summary or archive or {}).get("final_safety_status", ""),
        "latest_pointer": str(source_decision_file) if decision else "",
    }
    source = decision or archive or summary
    for field in LATEST_FIELDS[12:27]:
        row[field] = _copy_bool(source, field)
    return row


def write_latest_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(LATEST_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    lines = [f"- {field}={row[field]}" for field in LATEST_FIELDS]
    return "\n".join(
        [
            "# Operator Real Marketdata Latest Report",
            "",
            "## Safety Banner",
            "",
            "- read-only / manual-only / audit-first",
            "- no automatic trading",
            "- no account read",
            "- no position read",
            "- no historical data request",
            "- no Telegram real send",
            "",
            "## Latest Fields",
            "",
            *lines,
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_latest(
    *,
    source_summary_file: PathLike = "operator_real_marketdata_smoke_summary.csv",
    source_archive_file: PathLike = "operator_real_marketdata_smoke_archive.csv",
    source_decision_file: PathLike = "operator_real_marketdata_decision_gate.csv",
    output_csv: PathLike = "operator_real_marketdata_latest.csv",
    output_report: PathLike = "reports/operator_real_marketdata_latest_report.md",
    latest_generated_at: Optional[str] = None,
) -> Tuple[str, Dict[str, str]]:
    row = build_latest_row(
        source_summary_file=source_summary_file,
        source_archive_file=source_archive_file,
        source_decision_file=source_decision_file,
        latest_generated_at=latest_generated_at,
    )
    write_latest_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row["latest_status"], row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the Phase 445 real marketdata latest pointer.")
    parser.add_argument("--source-summary-file", default="operator_real_marketdata_smoke_summary.csv")
    parser.add_argument("--source-archive-file", default="operator_real_marketdata_smoke_archive.csv")
    parser.add_argument("--source-decision-file", default="operator_real_marketdata_decision_gate.csv")
    parser.add_argument("--output-csv", default="operator_real_marketdata_latest.csv")
    parser.add_argument("--output-report", default="reports/operator_real_marketdata_latest_report.md")
    parser.add_argument("--latest-generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    latest_status, row = generate_latest(
        source_summary_file=args.source_summary_file,
        source_archive_file=args.source_archive_file,
        source_decision_file=args.source_decision_file,
        output_csv=args.output_csv,
        output_report=args.output_report,
        latest_generated_at=args.latest_generated_at,
    )
    print("[PASS] Operator real marketdata latest generated")
    for field in (
        "summary_exists",
        "archive_exists",
        "decision_exists",
        "latest_status",
        "operator_decision",
        "config_restored",
        "config_file_modified",
        "account_read_allowed",
        "position_read_allowed",
        "telegram_send_allowed",
    ):
        print(f"{field}={row[field]}")
    return 0 if latest_status != "LATEST_INCOMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
