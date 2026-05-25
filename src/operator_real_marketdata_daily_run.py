from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple, Union


TRUE_TEXT = "true"
FALSE_TEXT = "false"

DAILY_FIELDS = (
    "daily_run_generated_at",
    "smoke_exit_code",
    "archive_exit_code",
    "decision_exit_code",
    "latest_exit_code",
    "daily_run_status",
    "latest_status",
    "operator_decision",
    "source_diagnostic_category",
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


def _daily_status(latest: Optional[Dict[str, str]], archive_exit_code: int, latest_exit_code: int) -> str:
    if latest is None or archive_exit_code != 0 or latest_exit_code != 0:
        return "DAILY_OPERATOR_CHAIN_INCOMPLETE"
    decision = latest.get("operator_decision", "")
    if decision == "PROCEED_TO_OBSERVATION":
        return "DAILY_OPERATOR_CHAIN_READY"
    if decision == "HOLD_SAFE_FAILURE":
        return "DAILY_OPERATOR_CHAIN_HOLD_SAFE_FAILURE"
    return "DAILY_OPERATOR_CHAIN_BLOCKED"


def build_daily_row(
    *,
    smoke_exit_code: int,
    archive_exit_code: int,
    decision_exit_code: int,
    latest_exit_code: int,
    latest_csv: PathLike = "operator_real_marketdata_latest.csv",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    latest = _read_latest_row(latest_csv)
    status = _daily_status(latest, archive_exit_code, latest_exit_code)
    row = {
        "daily_run_generated_at": generated_at or _now_timestamp(),
        "smoke_exit_code": str(smoke_exit_code),
        "archive_exit_code": str(archive_exit_code),
        "decision_exit_code": str(decision_exit_code),
        "latest_exit_code": str(latest_exit_code),
        "daily_run_status": status,
        "latest_status": latest.get("latest_status", "") if latest else "",
        "operator_decision": latest.get("operator_decision", "") if latest else "",
        "source_diagnostic_category": latest.get("source_diagnostic_category", "") if latest else "",
    }
    for field in DAILY_FIELDS[9:]:
        row[field] = _copy_bool(latest, field)
    return row


def write_daily_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(DAILY_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    lines = [f"- {field}={row[field]}" for field in DAILY_FIELDS]
    return "\n".join(
        [
            "# Operator Real Marketdata Daily Run Report",
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
            "## Daily Run Fields",
            "",
            *lines,
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_daily_summary(
    *,
    smoke_exit_code: int,
    archive_exit_code: int,
    decision_exit_code: int,
    latest_exit_code: int,
    latest_csv: PathLike = "operator_real_marketdata_latest.csv",
    output_csv: PathLike = "operator_real_marketdata_daily_run_summary.csv",
    output_report: PathLike = "reports/operator_real_marketdata_daily_run_report.md",
    generated_at: Optional[str] = None,
) -> Tuple[str, Dict[str, str]]:
    row = build_daily_row(
        smoke_exit_code=smoke_exit_code,
        archive_exit_code=archive_exit_code,
        decision_exit_code=decision_exit_code,
        latest_exit_code=latest_exit_code,
        latest_csv=latest_csv,
        generated_at=generated_at,
    )
    write_daily_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row["daily_run_status"], row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the Phase 446 real marketdata daily run summary.")
    parser.add_argument("--smoke-exit-code", type=int, required=True)
    parser.add_argument("--archive-exit-code", type=int, required=True)
    parser.add_argument("--decision-exit-code", type=int, required=True)
    parser.add_argument("--latest-exit-code", type=int, required=True)
    parser.add_argument("--latest-csv", default="operator_real_marketdata_latest.csv")
    parser.add_argument("--output-csv", default="operator_real_marketdata_daily_run_summary.csv")
    parser.add_argument("--output-report", default="reports/operator_real_marketdata_daily_run_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    status, row = generate_daily_summary(
        smoke_exit_code=args.smoke_exit_code,
        archive_exit_code=args.archive_exit_code,
        decision_exit_code=args.decision_exit_code,
        latest_exit_code=args.latest_exit_code,
        latest_csv=args.latest_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator real marketdata daily run summary generated")
    for field in (
        "daily_run_status",
        "smoke_exit_code",
        "archive_exit_code",
        "decision_exit_code",
        "latest_exit_code",
        "operator_decision",
        "config_restored",
        "config_file_modified",
    ):
        print(f"{field}={row[field]}")
    return 0 if status in {"DAILY_OPERATOR_CHAIN_READY", "DAILY_OPERATOR_CHAIN_HOLD_SAFE_FAILURE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
