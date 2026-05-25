from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union


TRUE_TEXT = "true"
FALSE_TEXT = "false"

PASS_READY = "PASS_READY"
SAFE_FAILURE = "SAFE_FAILURE"
CONFIG_RESTORE_FAILURE = "CONFIG_RESTORE_FAILURE"
FORBIDDEN_ACTION_RISK = "FORBIDDEN_ACTION_RISK"
MISSING_SOURCE = "MISSING_SOURCE"

ARCHIVE_FIELDS = (
    "archive_generated_at",
    "source_summary_file",
    "source_report_file",
    "source_exists",
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
    "diagnostic_category",
    "diagnostic_reason",
    "operator_next_step",
)

SAFETY_FALSE_FIELDS = (
    "contract_qualification_allowed",
    "historical_data_request_allowed",
    "trading_actions_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "telegram_send_allowed",
    "req_historical_data_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
)

FORBIDDEN_TRIGGER_FIELDS = (
    "historical_data_request_triggered",
    "broker_execution_triggered",
    "account_read_triggered",
    "position_read_triggered",
    "telegram_send_triggered",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _bool_text(value: object) -> str:
    return TRUE_TEXT if bool(value) else FALSE_TEXT


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "allowed", "triggered"}


def _read_latest_summary_row(path: PathLike) -> Optional[Dict[str, str]]:
    summary_path = Path(path)
    if not summary_path.exists():
        return None
    with summary_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[-1] if rows else None


def _default_missing_row(
    *,
    archive_generated_at: str,
    source_summary_file: PathLike,
    source_report_file: PathLike,
) -> Dict[str, str]:
    row = {
        "archive_generated_at": archive_generated_at,
        "source_summary_file": str(source_summary_file),
        "source_report_file": str(source_report_file),
        "source_exists": FALSE_TEXT,
        "top_level_status": "SOURCE_MISSING",
        "final_safety_status": "SOURCE_MISSING",
        "config_restored": FALSE_TEXT,
        "config_file_modified": FALSE_TEXT,
        "real_connection_allowed_during_run": FALSE_TEXT,
        "market_data_request_allowed_during_run": FALSE_TEXT,
        "contract_qualification_allowed": FALSE_TEXT,
        "historical_data_request_allowed": FALSE_TEXT,
        "trading_actions_allowed": FALSE_TEXT,
        "account_read_allowed": FALSE_TEXT,
        "position_read_allowed": FALSE_TEXT,
        "telegram_send_allowed": FALSE_TEXT,
        "req_mkt_data_allowed": FALSE_TEXT,
        "req_historical_data_allowed": FALSE_TEXT,
        "order_action_allowed": FALSE_TEXT,
        "cancel_action_allowed": FALSE_TEXT,
        "rebalance_action_allowed": FALSE_TEXT,
        "diagnostic_category": MISSING_SOURCE,
        "diagnostic_reason": "phase442_summary_or_report_missing",
        "operator_next_step": "keep_safety_gates_closed",
    }
    return row


def _copy_bool_field(source: Dict[str, str], field: str) -> str:
    return _bool_text(_truthy(source.get(field)))


def _forbidden_risk_reasons(source: Dict[str, str]) -> List[str]:
    reasons: List[str] = []
    for field in SAFETY_FALSE_FIELDS:
        if _truthy(source.get(field)):
            reasons.append(f"{field}_true")
    for field in FORBIDDEN_TRIGGER_FIELDS:
        if _truthy(source.get(field)):
            reasons.append(f"{field}_true")
    return reasons


def classify_archive_row(source: Dict[str, str], source_exists: bool) -> Tuple[str, str, str]:
    if not source_exists:
        return MISSING_SOURCE, "phase442_summary_or_report_missing", "keep_safety_gates_closed"

    risk_reasons = _forbidden_risk_reasons(source)
    if risk_reasons:
        return FORBIDDEN_ACTION_RISK, ",".join(risk_reasons), "do_not_proceed_to_telegram_send"

    if not _truthy(source.get("config_restored")) or _truthy(source.get("config_file_modified")):
        return CONFIG_RESTORE_FAILURE, "config_not_confirmed_restored", "keep_safety_gates_closed"

    top_level_status = source.get("top_level_status", "")
    final_safety_status = source.get("final_safety_status", "")
    if top_level_status == "REAL_MARKETDATA_SMOKE_AUDIT_READY" and final_safety_status == "PASS_READ_ONLY_MARKETDATA_SMOKE_AUDITED":
        return PASS_READY, "phase442_smoke_ready_and_safety_gates_preserved", "review_real_marketdata_connection"

    return SAFE_FAILURE, "phase442_smoke_failed_or_not_ready_but_safety_gates_preserved", "inspect_ibkr_permissions"


def build_archive_row(
    *,
    source_summary_file: PathLike = "operator_real_marketdata_smoke_summary.csv",
    source_report_file: PathLike = "reports/operator_real_marketdata_smoke_report.md",
    archive_generated_at: Optional[str] = None,
) -> Dict[str, str]:
    generated_at = archive_generated_at or _now_timestamp()
    summary_path = Path(source_summary_file)
    report_path = Path(source_report_file)
    source_row = _read_latest_summary_row(summary_path)
    source_exists = source_row is not None and report_path.exists()

    if source_row is None or not source_exists:
        return _default_missing_row(
            archive_generated_at=generated_at,
            source_summary_file=source_summary_file,
            source_report_file=source_report_file,
        )

    diagnostic_category, diagnostic_reason, operator_next_step = classify_archive_row(source_row, source_exists)
    row = {
        "archive_generated_at": generated_at,
        "source_summary_file": str(source_summary_file),
        "source_report_file": str(source_report_file),
        "source_exists": _bool_text(source_exists),
        "top_level_status": source_row.get("top_level_status", ""),
        "final_safety_status": source_row.get("final_safety_status", ""),
        "config_restored": _copy_bool_field(source_row, "config_restored"),
        "config_file_modified": _copy_bool_field(source_row, "config_file_modified"),
        "real_connection_allowed_during_run": _copy_bool_field(source_row, "real_connection_allowed_during_run"),
        "market_data_request_allowed_during_run": _copy_bool_field(source_row, "market_data_request_allowed_during_run"),
        "contract_qualification_allowed": _copy_bool_field(source_row, "contract_qualification_allowed"),
        "historical_data_request_allowed": _copy_bool_field(source_row, "historical_data_request_allowed"),
        "trading_actions_allowed": _copy_bool_field(source_row, "trading_actions_allowed"),
        "account_read_allowed": _copy_bool_field(source_row, "account_read_allowed"),
        "position_read_allowed": _copy_bool_field(source_row, "position_read_allowed"),
        "telegram_send_allowed": _copy_bool_field(source_row, "telegram_send_allowed"),
        "req_mkt_data_allowed": _copy_bool_field(source_row, "req_mkt_data_allowed"),
        "req_historical_data_allowed": _copy_bool_field(source_row, "req_historical_data_allowed"),
        "order_action_allowed": _copy_bool_field(source_row, "order_action_allowed"),
        "cancel_action_allowed": _copy_bool_field(source_row, "cancel_action_allowed"),
        "rebalance_action_allowed": _copy_bool_field(source_row, "rebalance_action_allowed"),
        "diagnostic_category": diagnostic_category,
        "diagnostic_reason": diagnostic_reason,
        "operator_next_step": operator_next_step,
    }
    return row


def write_archive_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(ARCHIVE_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    archive_lines = [f"- {field}={row[field]}" for field in ARCHIVE_FIELDS]
    return "\n".join(
        [
            "# Operator Real Marketdata Smoke Diagnostics Archive",
            "",
            "## Safety Banner",
            "",
            "- read-only / manual-only / audit-first",
            "- no automatic trading",
            "- no account read",
            "- no position read",
            "- no historical data request",
            "- no Telegram real send",
            "- no dashboard or UI expansion",
            "",
            "## Archive Fields",
            "",
            *archive_lines,
            "",
            "## Diagnostic Decision",
            "",
            f"- diagnostic_category={row['diagnostic_category']}",
            f"- diagnostic_reason={row['diagnostic_reason']}",
            f"- operator_next_step={row['operator_next_step']}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_archive(
    *,
    source_summary_file: PathLike = "operator_real_marketdata_smoke_summary.csv",
    source_report_file: PathLike = "reports/operator_real_marketdata_smoke_report.md",
    output_csv: PathLike = "operator_real_marketdata_smoke_archive.csv",
    output_report: PathLike = "reports/operator_real_marketdata_smoke_archive_report.md",
    archive_generated_at: Optional[str] = None,
) -> Tuple[str, Dict[str, str]]:
    row = build_archive_row(
        source_summary_file=source_summary_file,
        source_report_file=source_report_file,
        archive_generated_at=archive_generated_at,
    )
    write_archive_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row["diagnostic_category"], row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the Phase 443 real marketdata smoke diagnostics archive.")
    parser.add_argument("--source-summary-file", default="operator_real_marketdata_smoke_summary.csv")
    parser.add_argument("--source-report-file", default="reports/operator_real_marketdata_smoke_report.md")
    parser.add_argument("--output-csv", default="operator_real_marketdata_smoke_archive.csv")
    parser.add_argument("--output-report", default="reports/operator_real_marketdata_smoke_archive_report.md")
    parser.add_argument("--archive-generated-at", default=None)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    diagnostic_category, row = generate_archive(
        source_summary_file=args.source_summary_file,
        source_report_file=args.source_report_file,
        output_csv=args.output_csv,
        output_report=args.output_report,
        archive_generated_at=args.archive_generated_at,
    )
    print("[PASS] Operator real marketdata smoke diagnostics archive generated")
    for field in (
        "source_exists",
        "top_level_status",
        "final_safety_status",
        "config_restored",
        "config_file_modified",
        "contract_qualification_allowed",
        "historical_data_request_allowed",
        "trading_actions_allowed",
        "account_read_allowed",
        "position_read_allowed",
        "telegram_send_allowed",
        "req_historical_data_allowed",
        "order_action_allowed",
        "cancel_action_allowed",
        "rebalance_action_allowed",
        "diagnostic_category",
        "diagnostic_reason",
        "operator_next_step",
    ):
        print(f"{field}={row[field]}")
    return 0 if diagnostic_category in {PASS_READY, SAFE_FAILURE, MISSING_SOURCE} else 1


if __name__ == "__main__":
    raise SystemExit(main())
