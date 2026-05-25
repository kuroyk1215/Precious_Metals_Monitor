from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import yaml


TRUE_TEXT = "true"
FALSE_TEXT = "false"

READY = "REAL_MARKETDATA_SMOKE_AUDIT_READY"
FAILED = "REAL_MARKETDATA_SMOKE_AUDIT_FAILED"
SAFETY_REVIEW_REQUIRED = "REAL_MARKETDATA_SMOKE_SAFETY_REVIEW_REQUIRED"

SUMMARY_FIELDS = (
    "run_id",
    "started_at",
    "ended_at",
    "top_level_status",
    "wrapper_exit_code",
    "smoke_exit_code",
    "read_only_required",
    "real_connection_allowed_during_run",
    "market_data_request_allowed_during_run",
    "contract_qualification_allowed",
    "historical_data_request_allowed",
    "trading_actions_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "telegram_send_allowed",
    "config_restored",
    "config_file_modified",
    "ibkr_api_request_allowed",
    "req_mkt_data_allowed",
    "req_historical_data_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "final_safety_status",
    "snapshot_rows_detected",
    "connection_succeeded",
    "market_data_request_triggered",
    "historical_data_request_triggered",
    "broker_execution_triggered",
    "account_read_triggered",
    "position_read_triggered",
    "telegram_send_triggered",
    "notes",
)

PathLike = Union[str, Path]


@dataclass(frozen=True)
class SmokeAuditContext:
    started_at: str
    ended_at: str
    wrapper_exit_code: int
    smoke_exit_code: int
    config_restored: bool
    config_file_modified: bool
    real_connection_allowed_during_run: bool
    market_data_request_allowed_during_run: bool
    notes: str = ""


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _run_id(started_at: str) -> str:
    cleaned = started_at.replace("-", "").replace(":", "").replace("+", "_").replace(".", "_")
    return "real_marketdata_smoke_" + cleaned


def _bool_text(value: object) -> str:
    return TRUE_TEXT if bool(value) else FALSE_TEXT


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "allowed", "triggered"}


def load_ibkr_config(path: PathLike) -> Dict[str, object]:
    config_path = Path(path)
    if not config_path.exists():
        return {}
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    ibkr = data.get("ibkr", {}) if isinstance(data, dict) else {}
    return ibkr if isinstance(ibkr, dict) else {}


def read_snapshot_rows(path: PathLike) -> List[Dict[str, str]]:
    snapshot_path = Path(path)
    if not snapshot_path.exists():
        return []
    with snapshot_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _any_snapshot_true(rows: Sequence[Dict[str, str]], field: str) -> bool:
    return any(_truthy(row.get(field)) for row in rows)


def build_summary_row(
    *,
    config: Dict[str, object],
    snapshot_rows: Sequence[Dict[str, str]],
    context: SmokeAuditContext,
) -> Tuple[Dict[str, str], List[str]]:
    warnings: List[str] = []
    read_only_required = config.get("read_only_required") is True
    contract_qualification_allowed = config.get("contract_qualification_allowed") is True
    historical_data_request_allowed = config.get("historical_data_request_allowed") is True
    trading_actions_allowed = config.get("trading_actions_allowed") is True
    final_real_connection_allowed = config.get("real_connection_allowed") is True
    final_market_data_request_allowed = config.get("market_data_request_allowed") is True

    if not read_only_required:
        warnings.append("read_only_required_not_true")
    if contract_qualification_allowed:
        warnings.append("contract_qualification_allowed_true")
    if historical_data_request_allowed:
        warnings.append("historical_data_request_allowed_true")
    if trading_actions_allowed:
        warnings.append("trading_actions_allowed_true")
    if final_real_connection_allowed or final_market_data_request_allowed:
        warnings.append("temporary_marketdata_gates_not_restored")
    if not context.config_restored:
        warnings.append("config_restore_not_confirmed")
    if context.config_file_modified:
        warnings.append("config_file_modified_after_run")

    forbidden_trigger_fields = (
        "historical_data_request_triggered",
        "broker_execution_triggered",
        "account_read_triggered",
        "position_read_triggered",
        "telegram_send_triggered",
    )
    for field in forbidden_trigger_fields:
        if _any_snapshot_true(snapshot_rows, field):
            warnings.append(f"{field}_true")

    market_data_triggered = _any_snapshot_true(snapshot_rows, "market_data_request_triggered")
    connection_succeeded = _any_snapshot_true(snapshot_rows, "connection_succeeded")
    smoke_attempted = context.smoke_exit_code >= 0

    if warnings:
        top_level_status = SAFETY_REVIEW_REQUIRED
        final_safety_status = "SAFETY_REVIEW_REQUIRED"
    elif context.wrapper_exit_code != 0:
        top_level_status = FAILED
        final_safety_status = "AUDIT_FAILED_SAFE_DEFAULTS_RESTORED"
    else:
        top_level_status = READY
        final_safety_status = "PASS_READ_ONLY_MARKETDATA_SMOKE_AUDITED"

    row = {
        "run_id": _run_id(context.started_at),
        "started_at": context.started_at,
        "ended_at": context.ended_at,
        "top_level_status": top_level_status,
        "wrapper_exit_code": str(context.wrapper_exit_code),
        "smoke_exit_code": str(context.smoke_exit_code),
        "read_only_required": _bool_text(read_only_required),
        "real_connection_allowed_during_run": _bool_text(context.real_connection_allowed_during_run),
        "market_data_request_allowed_during_run": _bool_text(context.market_data_request_allowed_during_run),
        "contract_qualification_allowed": _bool_text(contract_qualification_allowed),
        "historical_data_request_allowed": _bool_text(historical_data_request_allowed),
        "trading_actions_allowed": _bool_text(trading_actions_allowed),
        "account_read_allowed": FALSE_TEXT,
        "position_read_allowed": FALSE_TEXT,
        "telegram_send_allowed": FALSE_TEXT,
        "config_restored": _bool_text(context.config_restored),
        "config_file_modified": _bool_text(context.config_file_modified),
        "ibkr_api_request_allowed": _bool_text(smoke_attempted and context.real_connection_allowed_during_run),
        "req_mkt_data_allowed": _bool_text(smoke_attempted and context.market_data_request_allowed_during_run),
        "req_historical_data_allowed": FALSE_TEXT,
        "order_action_allowed": FALSE_TEXT,
        "cancel_action_allowed": FALSE_TEXT,
        "rebalance_action_allowed": FALSE_TEXT,
        "final_safety_status": final_safety_status,
        "snapshot_rows_detected": str(len(snapshot_rows)),
        "connection_succeeded": _bool_text(connection_succeeded),
        "market_data_request_triggered": _bool_text(market_data_triggered),
        "historical_data_request_triggered": _bool_text(_any_snapshot_true(snapshot_rows, "historical_data_request_triggered")),
        "broker_execution_triggered": _bool_text(_any_snapshot_true(snapshot_rows, "broker_execution_triggered")),
        "account_read_triggered": _bool_text(_any_snapshot_true(snapshot_rows, "account_read_triggered")),
        "position_read_triggered": _bool_text(_any_snapshot_true(snapshot_rows, "position_read_triggered")),
        "telegram_send_triggered": _bool_text(_any_snapshot_true(snapshot_rows, "telegram_send_triggered")),
        "notes": context.notes or "manual_only_read_only_marketdata_smoke_audit",
    }
    return row, warnings


def write_summary_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SUMMARY_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str], warnings: Sequence[str]) -> str:
    required_keys = (
        "top_level_status",
        "started_at",
        "ended_at",
        "read_only_required",
        "real_connection_allowed_during_run",
        "market_data_request_allowed_during_run",
        "contract_qualification_allowed",
        "historical_data_request_allowed",
        "trading_actions_allowed",
        "account_read_allowed",
        "position_read_allowed",
        "telegram_send_allowed",
        "config_restored",
        "config_file_modified",
        "ibkr_api_request_allowed",
        "req_mkt_data_allowed",
        "req_historical_data_allowed",
        "order_action_allowed",
        "cancel_action_allowed",
        "rebalance_action_allowed",
        "final_safety_status",
    )
    audit_lines = [f"- {key}={row[key]}" for key in required_keys]
    warning_lines = [f"- {warning}" for warning in warnings] if warnings else ["- none"]

    return "\n".join(
        [
            "# Operator Real Marketdata Smoke Report",
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
            "## Required Audit Fields",
            "",
            *audit_lines,
            "",
            "## Runtime Observations",
            "",
            f"- wrapper_exit_code={row['wrapper_exit_code']}",
            f"- smoke_exit_code={row['smoke_exit_code']}",
            f"- snapshot_rows_detected={row['snapshot_rows_detected']}",
            f"- connection_succeeded={row['connection_succeeded']}",
            f"- market_data_request_triggered={row['market_data_request_triggered']}",
            f"- historical_data_request_triggered={row['historical_data_request_triggered']}",
            f"- broker_execution_triggered={row['broker_execution_triggered']}",
            f"- account_read_triggered={row['account_read_triggered']}",
            f"- position_read_triggered={row['position_read_triggered']}",
            f"- telegram_send_triggered={row['telegram_send_triggered']}",
            "",
            "## Failure / Warning Section",
            "",
            *warning_lines,
            "",
            "## Next Manual Operator Step",
            "",
            "- Review `operator_real_marketdata_smoke_summary.csv` and this report before any next phase decision.",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str], warnings: Sequence[str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row, warnings), encoding="utf-8")


def generate_summary(
    *,
    config_path: PathLike = "config.yaml",
    snapshot_csv: PathLike = "ibkr_market_data_snapshot.csv",
    output_csv: PathLike = "operator_real_marketdata_smoke_summary.csv",
    output_report: PathLike = "reports/operator_real_marketdata_smoke_report.md",
    started_at: Optional[str] = None,
    ended_at: Optional[str] = None,
    wrapper_exit_code: int = 0,
    smoke_exit_code: int = -1,
    config_restored: bool = True,
    config_file_modified: bool = False,
    real_connection_allowed_during_run: bool = False,
    market_data_request_allowed_during_run: bool = False,
    notes: str = "",
) -> Tuple[str, Dict[str, str]]:
    context = SmokeAuditContext(
        started_at=started_at or _now_timestamp(),
        ended_at=ended_at or _now_timestamp(),
        wrapper_exit_code=wrapper_exit_code,
        smoke_exit_code=smoke_exit_code,
        config_restored=config_restored,
        config_file_modified=config_file_modified,
        real_connection_allowed_during_run=real_connection_allowed_during_run,
        market_data_request_allowed_during_run=market_data_request_allowed_during_run,
        notes=notes,
    )
    row, warnings = build_summary_row(
        config=load_ibkr_config(config_path),
        snapshot_rows=read_snapshot_rows(snapshot_csv),
        context=context,
    )
    write_summary_csv(output_csv, row)
    write_markdown_report(output_report, row, warnings)
    return row["top_level_status"], row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the Phase 442 real marketdata smoke audit summary.")
    parser.add_argument("--config-path", default="config.yaml")
    parser.add_argument("--snapshot-csv", default="ibkr_market_data_snapshot.csv")
    parser.add_argument("--output-csv", default="operator_real_marketdata_smoke_summary.csv")
    parser.add_argument("--output-report", default="reports/operator_real_marketdata_smoke_report.md")
    parser.add_argument("--started-at", default=None)
    parser.add_argument("--ended-at", default=None)
    parser.add_argument("--wrapper-exit-code", type=int, default=0)
    parser.add_argument("--smoke-exit-code", type=int, default=-1)
    parser.add_argument("--config-restored", default=TRUE_TEXT)
    parser.add_argument("--config-file-modified", default=FALSE_TEXT)
    parser.add_argument("--real-connection-allowed-during-run", default=FALSE_TEXT)
    parser.add_argument("--market-data-request-allowed-during-run", default=FALSE_TEXT)
    parser.add_argument("--notes", default="")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    top_status, row = generate_summary(
        config_path=args.config_path,
        snapshot_csv=args.snapshot_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        started_at=args.started_at,
        ended_at=args.ended_at,
        wrapper_exit_code=args.wrapper_exit_code,
        smoke_exit_code=args.smoke_exit_code,
        config_restored=_truthy(args.config_restored),
        config_file_modified=_truthy(args.config_file_modified),
        real_connection_allowed_during_run=_truthy(args.real_connection_allowed_during_run),
        market_data_request_allowed_during_run=_truthy(args.market_data_request_allowed_during_run),
        notes=args.notes,
    )
    print("[PASS] Operator real marketdata smoke summary generated")
    print(f"top_level_status={top_status}")
    for field in (
        "read_only_required",
        "real_connection_allowed_during_run",
        "market_data_request_allowed_during_run",
        "contract_qualification_allowed",
        "historical_data_request_allowed",
        "trading_actions_allowed",
        "account_read_allowed",
        "position_read_allowed",
        "telegram_send_allowed",
        "config_restored",
        "config_file_modified",
        "ibkr_api_request_allowed",
        "req_mkt_data_allowed",
        "req_historical_data_allowed",
        "order_action_allowed",
        "cancel_action_allowed",
        "rebalance_action_allowed",
        "final_safety_status",
    ):
        print(f"{field}={row[field]}")
    return 0 if top_status in {READY, FAILED} else 1


if __name__ == "__main__":
    raise SystemExit(main())
