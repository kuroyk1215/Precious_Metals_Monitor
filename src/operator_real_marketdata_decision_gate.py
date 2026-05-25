from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union


TRUE_TEXT = "true"
FALSE_TEXT = "false"

PROCEED_TO_OBSERVATION = "PROCEED_TO_OBSERVATION"
HOLD_SAFE_FAILURE = "HOLD_SAFE_FAILURE"
BLOCK_CONFIG_RESTORE_FAILURE = "BLOCK_CONFIG_RESTORE_FAILURE"
BLOCK_FORBIDDEN_ACTION_RISK = "BLOCK_FORBIDDEN_ACTION_RISK"
BLOCK_MISSING_SOURCE = "BLOCK_MISSING_SOURCE"

DECISION_FIELDS = (
    "decision_generated_at",
    "source_archive_file",
    "source_exists",
    "source_diagnostic_category",
    "operator_decision",
    "decision_reason",
    "operator_next_step",
    "source_summary_file",
    "summary_exists",
    "smoke_exit_code",
    "snapshot_rows_detected",
    "connection_succeeded",
    "market_data_request_triggered",
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


def _copy_bool_field(source: Dict[str, str], field: str) -> str:
    return _bool_text(_truthy(source.get(field)))


def _forbidden_reasons(source: Dict[str, str]) -> List[str]:
    return [f"{field}_true" for field in SAFETY_FALSE_FIELDS if _truthy(source.get(field))]


def _source_summary_path(source_archive_file: PathLike, source: Optional[Dict[str, str]]) -> Optional[Path]:
    if source is None:
        return None
    value = source.get("source_summary_file")
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return Path(source_archive_file).parent / path


def _smoke_not_observation_ready_reasons(summary: Optional[Dict[str, str]]) -> List[str]:
    if summary is None:
        return ["smoke_summary_missing"]
    reasons: List[str] = []
    if not _truthy(summary.get("connection_succeeded")):
        reasons.append("connection_succeeded_false")
    if not _truthy(summary.get("market_data_request_triggered")):
        reasons.append("market_data_request_triggered_false")
    try:
        snapshot_rows = int(str(summary.get("snapshot_rows_detected") or "0"))
    except ValueError:
        snapshot_rows = 0
    if snapshot_rows <= 0:
        reasons.append("snapshot_rows_missing")
    if str(summary.get("smoke_exit_code") or "0") != "0":
        reasons.append("smoke_exit_code_nonzero")
    return reasons


def classify_decision(source: Optional[Dict[str, str]], summary: Optional[Dict[str, str]] = None) -> Tuple[str, str, str]:
    if source is None or not _truthy(source.get("source_exists")):
        return BLOCK_MISSING_SOURCE, "phase443_archive_missing_or_source_missing", "restore_phase442_phase443_sources"

    forbidden_reasons = _forbidden_reasons(source)
    if source.get("diagnostic_category") == "FORBIDDEN_ACTION_RISK" or forbidden_reasons:
        reason = source.get("diagnostic_reason") or ",".join(forbidden_reasons) or "forbidden_action_risk"
        return BLOCK_FORBIDDEN_ACTION_RISK, reason, "stop_operator_chain_and_review_safety"

    if source.get("diagnostic_category") == "CONFIG_RESTORE_FAILURE" or not _truthy(source.get("config_restored")) or _truthy(source.get("config_file_modified")):
        return BLOCK_CONFIG_RESTORE_FAILURE, "config_restore_not_confirmed", "restore_config_before_any_observation"

    if source.get("diagnostic_category") == "PASS_READY":
        observation_reasons = _smoke_not_observation_ready_reasons(summary)
        if observation_reasons:
            return HOLD_SAFE_FAILURE, ",".join(observation_reasons), "hold_and_inspect_real_marketdata_connection"
        return PROCEED_TO_OBSERVATION, "real_marketdata_smoke_ready_and_read_only_gates_preserved", "manual_observation_only"

    if source.get("diagnostic_category") == "SAFE_FAILURE":
        return HOLD_SAFE_FAILURE, "real_marketdata_smoke_failed_but_safety_gates_preserved", "hold_and_inspect_ibkr_permissions"

    if source.get("diagnostic_category") == "MISSING_SOURCE":
        return BLOCK_MISSING_SOURCE, "phase443_archive_reports_missing_source", "restore_phase442_phase443_sources"

    return HOLD_SAFE_FAILURE, "unknown_archive_diagnostic_but_safety_gates_preserved", "hold_and_review_archive"


def build_decision_row(
    *,
    source_archive_file: PathLike = "operator_real_marketdata_smoke_archive.csv",
    decision_generated_at: Optional[str] = None,
) -> Dict[str, str]:
    generated_at = decision_generated_at or _now_timestamp()
    source_row = _read_latest_row(source_archive_file)
    source_summary_path = _source_summary_path(source_archive_file, source_row)
    summary_row = _read_latest_row(source_summary_path) if source_summary_path is not None else None
    decision, reason, next_step = classify_decision(source_row, summary_row)
    source_exists = source_row is not None and _truthy(source_row.get("source_exists"))
    summary_exists = summary_row is not None

    row = {
        "decision_generated_at": generated_at,
        "source_archive_file": str(source_archive_file),
        "source_exists": _bool_text(source_exists),
        "source_diagnostic_category": source_row.get("diagnostic_category", "SOURCE_MISSING") if source_row else "SOURCE_MISSING",
        "operator_decision": decision,
        "decision_reason": reason,
        "operator_next_step": next_step,
        "source_summary_file": str(source_summary_path) if source_summary_path is not None else "",
        "summary_exists": _bool_text(summary_exists),
        "smoke_exit_code": summary_row.get("smoke_exit_code", "") if summary_row else "",
        "snapshot_rows_detected": summary_row.get("snapshot_rows_detected", "") if summary_row else "",
        "connection_succeeded": _copy_bool_field(summary_row, "connection_succeeded") if summary_row else FALSE_TEXT,
        "market_data_request_triggered": _copy_bool_field(summary_row, "market_data_request_triggered") if summary_row else FALSE_TEXT,
    }
    for field in DECISION_FIELDS[13:]:
        if source_row is None:
            row[field] = FALSE_TEXT if field.endswith("_allowed") or field in {"config_restored", "config_file_modified"} else ""
        elif field in {
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
        }:
            row[field] = _copy_bool_field(source_row, field)
        else:
            row[field] = source_row.get(field, "")
    return row


def write_decision_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(DECISION_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    field_lines = [f"- {field}={row[field]}" for field in DECISION_FIELDS]
    return "\n".join(
        [
            "# Operator Real Marketdata Decision Gate Report",
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
            "## Decision Fields",
            "",
            *field_lines,
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_decision(
    *,
    source_archive_file: PathLike = "operator_real_marketdata_smoke_archive.csv",
    output_csv: PathLike = "operator_real_marketdata_decision_gate.csv",
    output_report: PathLike = "reports/operator_real_marketdata_decision_gate_report.md",
    decision_generated_at: Optional[str] = None,
) -> Tuple[str, Dict[str, str]]:
    row = build_decision_row(
        source_archive_file=source_archive_file,
        decision_generated_at=decision_generated_at,
    )
    write_decision_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row["operator_decision"], row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the Phase 444 real marketdata operator decision gate.")
    parser.add_argument("--source-archive-file", default="operator_real_marketdata_smoke_archive.csv")
    parser.add_argument("--output-csv", default="operator_real_marketdata_decision_gate.csv")
    parser.add_argument("--output-report", default="reports/operator_real_marketdata_decision_gate_report.md")
    parser.add_argument("--decision-generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    decision, row = generate_decision(
        source_archive_file=args.source_archive_file,
        output_csv=args.output_csv,
        output_report=args.output_report,
        decision_generated_at=args.decision_generated_at,
    )
    print("[PASS] Operator real marketdata decision gate generated")
    for field in (
        "source_exists",
        "source_diagnostic_category",
        "operator_decision",
        "decision_reason",
        "operator_next_step",
        "summary_exists",
        "smoke_exit_code",
        "snapshot_rows_detected",
        "connection_succeeded",
        "market_data_request_triggered",
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
    ):
        print(f"{field}={row[field]}")
    return 0 if decision in {PROCEED_TO_OBSERVATION, HOLD_SAFE_FAILURE} else 1


if __name__ == "__main__":
    raise SystemExit(main())
