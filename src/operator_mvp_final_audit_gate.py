from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

AUDIT_SOURCES = (
    "operator_mvp_codebase_map.csv",
    "operator_daily_freeze_report.csv",
    "operator_real_market_mvp_completion_gate.csv",
    "operator_mvp_readiness_report.csv",
    "operator_real_market_mvp_regression.csv",
)

AUDIT_FIELDS = (
    "generated_at",
    "final_audit_status",
    "source_files_present",
    "missing_sources",
    "codebase_modules",
    "freeze_report_status",
    "completion_gate_status",
    "readiness_status",
    "regression_status",
    "safety_status",
    "safe_unavailable",
    "diagnostic_reason",
    "operator_next_step",
    "auto_trade_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "telegram_real_send_allowed",
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


def _latest(path: PathLike) -> Dict[str, str]:
    rows = _read_rows(path)
    return rows[-1] if rows else {}


def _is_false(value: object) -> bool:
    return str(value or "").strip().lower() in {"false", "0", "no", ""}


def _is_true(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _safety_clean(rows: Sequence[Dict[str, str]]) -> bool:
    fields = (
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
        "broker_execution_triggered",
    )
    for row in rows:
        for field in fields:
            if field in row and not _is_false(row.get(field)):
                return False
    return True


def _has_safe_unavailable(rows: Sequence[Dict[str, str]]) -> bool:
    return any(_is_true(row.get("safe_unavailable")) or any("SAFE_UNAVAILABLE" in str(value) for value in row.values()) for row in rows)


def build_final_audit_row(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    base = Path(base_dir)
    present = [name for name in AUDIT_SOURCES if (base / name).exists()]
    missing = [name for name in AUDIT_SOURCES if name not in present]

    map_rows = _read_rows(base / "operator_mvp_codebase_map.csv")
    freeze = _latest(base / "operator_daily_freeze_report.csv")
    completion = _latest(base / "operator_real_market_mvp_completion_gate.csv")
    readiness = _latest(base / "operator_mvp_readiness_report.csv")
    regression = _latest(base / "operator_real_market_mvp_regression.csv")
    rows = map_rows + [freeze, completion, readiness, regression]

    safety_clean = _safety_clean([row for row in rows if row])
    safe_unavailable = _has_safe_unavailable(rows)
    completion_status = completion.get("completion_gate_status", "MISSING")
    readiness_status = readiness.get("readiness_status", "MISSING")
    regression_status = regression.get("regression_status", "MISSING")
    freeze_status = freeze.get("freeze_report_status", "MISSING")

    if missing:
        status = "MVP_MISSING_SOURCE"
        reason = "missing_sources:" + ",".join(missing)
        next_step = "generate_missing_audit_sources"
    elif not safety_clean:
        status = "MVP_BLOCKED"
        reason = "forbidden_action_or_read_field_detected"
        next_step = "stop_and_review_safety_boundary"
    elif regression_status == "FAIL" or completion_status.endswith("BLOCKED") or readiness_status == "MVP_BLOCKED":
        status = "MVP_BLOCKED"
        reason = "regression_completion_or_readiness_blocked"
        next_step = "review_blocked_audit_sources"
    elif safe_unavailable and completion_status != "MISSING":
        status = "MVP_SKELETON_COMPLETE_WITH_SAFE_UNAVAILABLE"
        reason = "no_real_quote_currently_available_but_completion_gate_exists_and_safety_clean"
        next_step = "manual_review_final_packet_and_connection_permissions"
    elif freeze_status.endswith("READY") and completion_status.endswith("READY_FOR_SAFE_DAILY_USE"):
        status = "MVP_SKELETON_COMPLETE"
        reason = "freeze_and_completion_sources_ready"
        next_step = "daily_manual_observation_use"
    else:
        status = "MVP_REVIEW_REQUIRED"
        reason = "sources_present_but_final_audit_not_decisive"
        next_step = "manual_review_audit_sources"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "final_audit_status": status,
        "source_files_present": ",".join(present) if present else "none",
        "missing_sources": ",".join(missing) if missing else "none",
        "codebase_modules": str(len(map_rows)),
        "freeze_report_status": freeze_status,
        "completion_gate_status": completion_status,
        "readiness_status": readiness_status,
        "regression_status": regression_status,
        "safety_status": "SAFETY_CLEAN" if safety_clean else "SAFETY_BLOCKED",
        "safe_unavailable": TRUE_TEXT if safe_unavailable else FALSE_TEXT,
        "diagnostic_reason": reason,
        "operator_next_step": next_step,
        "auto_trade_allowed": FALSE_TEXT,
        "account_read_allowed": FALSE_TEXT,
        "position_read_allowed": FALSE_TEXT,
        "historical_data_request_allowed": FALSE_TEXT,
        "telegram_real_send_allowed": FALSE_TEXT,
        "order_action_allowed": FALSE_TEXT,
        "cancel_action_allowed": FALSE_TEXT,
        "rebalance_action_allowed": FALSE_TEXT,
    }


def write_final_audit_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(AUDIT_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Operator MVP Final Audit Gate",
            "",
            "## Safety Boundary",
            "",
            "- no auto trading",
            "- no account reads",
            "- no position reads",
            "- no historical data requests",
            "- no Telegram real send",
            "- no order/cancel/rebalance",
            "- config.yaml remains local-only",
            "- ibkr_market_data_api_errors.csv remains local-only",
            "",
            "## Final Audit",
            "",
            f"- final_audit_status={row['final_audit_status']}",
            f"- codebase_modules={row['codebase_modules']}",
            f"- freeze_report_status={row['freeze_report_status']}",
            f"- completion_gate_status={row['completion_gate_status']}",
            f"- readiness_status={row['readiness_status']}",
            f"- regression_status={row['regression_status']}",
            f"- safety_status={row['safety_status']}",
            f"- safe_unavailable={row['safe_unavailable']}",
            f"- diagnostic_reason={row['diagnostic_reason']}",
            f"- operator_next_step={row['operator_next_step']}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_mvp_final_audit_gate(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_mvp_final_audit_gate.csv",
    output_report: PathLike = "reports/operator_mvp_final_audit_gate_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_final_audit_row(base_dir=base_dir, generated_at=generated_at)
    write_final_audit_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 467 MVP final audit gate.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_mvp_final_audit_gate.csv")
    parser.add_argument("--output-report", default="reports/operator_mvp_final_audit_gate_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_mvp_final_audit_gate(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator MVP final audit gate generated")
    print(f"final_audit_status={row['final_audit_status']}:safety_status={row['safety_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
