from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

SOURCE_FILES = (
    "operator_real_marketdata_smoke_summary.csv",
    "operator_real_marketdata_smoke_archive.csv",
    "operator_real_marketdata_decision_gate.csv",
    "operator_real_marketdata_latest.csv",
    "operator_real_marketdata_daily_run_summary.csv",
    "operator_real_quote_normalization.csv",
    "operator_real_quote_signal_bridge.csv",
    "operator_daily_real_market_report.csv",
)

MVP_STATUS_FIELDS = (
    "generated_at",
    "source_files_present",
    "smoke_status",
    "archive_status",
    "decision_status",
    "latest_status",
    "quote_status",
    "signal_bridge_status",
    "daily_report_status",
    "safety_clean",
    "real_quote_available",
    "safe_unavailable",
    "permission_or_connection_failure",
    "manual_review_only",
    "mvp_status",
    "diagnostic_reason",
    "operator_next_step",
    "auto_trade_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "telegram_send_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_rows(path: PathLike) -> List[Dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _latest_row(path: PathLike) -> Dict[str, str]:
    rows = _read_rows(path)
    return rows[-1] if rows else {}


def _is_false(value: object) -> bool:
    return str(value).strip().lower() in {"false", "0", "no", ""}


def _is_true(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _field_clean(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> bool:
    for row in rows:
        for field in fields:
            if field in row and not _is_false(row.get(field, "")):
                return False
    return True


def _safe_unavailable(rows: Sequence[Dict[str, str]]) -> bool:
    if not rows:
        return False
    markers = {"SAFE_UNAVAILABLE", "HOLD_NO_REAL_QUOTE", "HOLD_SAFE_FAILURE", "PERMISSION_OR_CONNECTION_FAILURE"}
    for row in rows:
        values = {str(value).strip() for value in row.values()}
        if values.intersection(markers):
            return True
    return False


def _real_quote_available(rows: Sequence[Dict[str, str]]) -> bool:
    for row in rows:
        if row.get("quote_status") == "AVAILABLE" and row.get("normalized_status") == "NORMALIZED":
            return True
        if row.get("real_quote_state") == "REAL_QUOTE_AVAILABLE":
            return True
    return False


def _permission_or_connection_failure(rows: Sequence[Dict[str, str]]) -> bool:
    for row in rows:
        if row.get("diagnostic_category") == "PERMISSION_OR_CONNECTION_FAILURE":
            return True
        if row.get("real_quote_state") == "PERMISSION_OR_CONNECTION_FAILURE":
            return True
        if _is_true(row.get("permission_or_connection_failure", "")):
            return True
    return False


def _status(row: Dict[str, str], candidates: Sequence[str], default: str) -> str:
    for key in candidates:
        value = str(row.get(key, "")).strip()
        if value:
            return value
    return default


def build_mvp_status_row(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    base = Path(base_dir)
    paths = {name: base / name for name in SOURCE_FILES}
    present = [name for name, path in paths.items() if path.exists()]
    missing = [name for name in SOURCE_FILES if name not in present]

    smoke = _latest_row(paths["operator_real_marketdata_smoke_summary.csv"])
    archive = _latest_row(paths["operator_real_marketdata_smoke_archive.csv"])
    decision = _latest_row(paths["operator_real_marketdata_decision_gate.csv"])
    latest = _latest_row(paths["operator_real_marketdata_latest.csv"])
    daily_run = _latest_row(paths["operator_real_marketdata_daily_run_summary.csv"])
    quote_rows = _read_rows(paths["operator_real_quote_normalization.csv"])
    bridge_rows = _read_rows(paths["operator_real_quote_signal_bridge.csv"])
    daily_report_rows = _read_rows(paths["operator_daily_real_market_report.csv"])

    safety_rows: List[Dict[str, str]] = [smoke, archive, decision, latest, daily_run] + quote_rows + bridge_rows + daily_report_rows
    forbidden_fields = (
        "auto_trade_allowed",
        "account_read_allowed",
        "position_read_allowed",
        "historical_data_request_allowed",
        "telegram_send_allowed",
        "telegram_real_send_allowed",
        "order_action_allowed",
        "cancel_action_allowed",
        "rebalance_action_allowed",
        "trading_actions_allowed",
        "contract_qualification_allowed",
        "req_historical_data_allowed",
        "historical_data_request_triggered",
        "broker_execution_triggered",
        "account_read_triggered",
        "position_read_triggered",
        "telegram_send_triggered",
    )
    safety_clean = _field_clean([row for row in safety_rows if row], forbidden_fields)
    config_restored = any(_is_false(row.get("config_restored", "true")) for row in safety_rows if row)
    config_modified = any(_is_true(row.get("config_file_modified", "false")) for row in safety_rows if row)
    real_quote_available = _real_quote_available(quote_rows + daily_report_rows)
    safe_unavailable = _safe_unavailable(quote_rows + bridge_rows + daily_report_rows + [latest, daily_run])
    permission_failure = _permission_or_connection_failure(quote_rows + daily_report_rows)
    manual_review_only = True

    if missing:
        mvp_status = "MVP_MISSING_SOURCE"
        reason = "missing_source_files:" + ",".join(missing)
        next_step = "generate_missing_phase442_449_sources"
    elif not safety_clean:
        mvp_status = "MVP_BLOCKED_FORBIDDEN_ACTION"
        reason = "forbidden_action_or_read_field_detected"
        next_step = "stop_and_review_safety_boundary"
    elif config_restored or config_modified:
        mvp_status = "MVP_BLOCKED_CONFIG_RESTORE"
        reason = "config_restore_or_config_modification_detected"
        next_step = "restore_config_yaml_local_only_state"
    elif real_quote_available:
        mvp_status = "MVP_READY"
        reason = "real_quote_available_safety_clean_manual_review_only"
        next_step = "manual_review_decision_quote_signal_status"
    elif safe_unavailable and safety_clean:
        mvp_status = "MVP_SAFE_UNAVAILABLE"
        reason = "real_quote_unavailable_but_safety_clean"
        next_step = "review_connection_permission_then_rerun_daily_chain"
    else:
        mvp_status = "MVP_REVIEW_REQUIRED"
        reason = "source_files_present_but_status_not_decisive"
        next_step = "manual_review_decision_quote_signal_status"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "source_files_present": ",".join(present) if present else "none",
        "smoke_status": _status(smoke, ("top_level_status", "final_safety_status"), "MISSING"),
        "archive_status": _status(archive, ("diagnostic_category", "top_level_status"), "MISSING"),
        "decision_status": _status(decision, ("operator_decision", "decision_reason"), "MISSING"),
        "latest_status": _status(latest, ("latest_status", "operator_decision"), "MISSING"),
        "quote_status": "REAL_QUOTE_AVAILABLE" if real_quote_available else ("SAFE_UNAVAILABLE" if quote_rows else "MISSING"),
        "signal_bridge_status": _status(bridge_rows[-1] if bridge_rows else {}, ("signal_bridge_status",), "MISSING"),
        "daily_report_status": _status(daily_report_rows[-1] if daily_report_rows else {}, ("real_quote_state",), "MISSING"),
        "safety_clean": TRUE_TEXT if safety_clean else FALSE_TEXT,
        "real_quote_available": TRUE_TEXT if real_quote_available else FALSE_TEXT,
        "safe_unavailable": TRUE_TEXT if safe_unavailable else FALSE_TEXT,
        "permission_or_connection_failure": TRUE_TEXT if permission_failure else FALSE_TEXT,
        "manual_review_only": TRUE_TEXT if manual_review_only else FALSE_TEXT,
        "mvp_status": mvp_status,
        "diagnostic_reason": reason,
        "operator_next_step": next_step,
        "auto_trade_allowed": FALSE_TEXT,
        "account_read_allowed": FALSE_TEXT,
        "position_read_allowed": FALSE_TEXT,
        "historical_data_request_allowed": FALSE_TEXT,
        "telegram_send_allowed": FALSE_TEXT,
        "order_action_allowed": FALSE_TEXT,
        "cancel_action_allowed": FALSE_TEXT,
        "rebalance_action_allowed": FALSE_TEXT,
    }


def write_mvp_status_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(MVP_STATUS_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Operator Real Market MVP Status Report",
            "",
            "## Safety Banner",
            "",
            "- no auto trading",
            "- no account reads",
            "- no position reads",
            "- no historical data requests",
            "- no Telegram real send",
            "- no order/cancel/rebalance",
            "",
            "## MVP Status",
            "",
            f"- mvp_status={row['mvp_status']}",
            f"- safety_clean={row['safety_clean']}",
            f"- real_quote_available={row['real_quote_available']}",
            f"- safe_unavailable={row['safe_unavailable']}",
            f"- permission_or_connection_failure={row['permission_or_connection_failure']}",
            f"- manual_review_only={row['manual_review_only']}",
            f"- diagnostic_reason={row['diagnostic_reason']}",
            f"- operator_next_step={row['operator_next_step']}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_mvp_status(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_real_market_mvp_status.csv",
    output_report: PathLike = "reports/operator_real_market_mvp_status_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_mvp_status_row(base_dir=base_dir, generated_at=generated_at)
    write_mvp_status_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 450 real-market MVP status aggregator.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_real_market_mvp_status.csv")
    parser.add_argument("--output-report", default="reports/operator_real_market_mvp_status_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_mvp_status(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator real-market MVP status generated")
    print(f"mvp_status={row['mvp_status']}:safety_clean={row['safety_clean']}:real_quote_available={row['real_quote_available']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
