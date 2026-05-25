from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

FREEZE_SOURCES = (
    "operator_final_daily_packet.csv",
    "operator_latest_strategy_decision.csv",
    "operator_real_market_mvp_completion_gate.csv",
    "operator_daily_checklist.csv",
    "operator_mvp_codebase_map.csv",
)

FREEZE_FIELDS = (
    "generated_at",
    "freeze_report_status",
    "source_files_present",
    "missing_sources",
    "daily_master_run_entrypoint",
    "final_packet_entrypoint",
    "latest_strategy_decision_entrypoint",
    "completion_gate_entrypoint",
    "safe_unavailable_meaning",
    "manual_review_when",
    "block_when",
    "final_packet_status",
    "latest_decision_status",
    "completion_gate_status",
    "checklist_steps",
    "mapped_modules",
    "safety_status",
    "diagnostic_reason",
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


def _contains_safe_unavailable(rows: Sequence[Dict[str, str]]) -> bool:
    return any("SAFE_UNAVAILABLE" in str(value) for row in rows for value in row.values())


def build_daily_freeze_row(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    base = Path(base_dir)
    present = [name for name in FREEZE_SOURCES if (base / name).exists()]
    missing = [name for name in FREEZE_SOURCES if name not in present]

    packet = _latest(base / "operator_final_daily_packet.csv")
    latest = _latest(base / "operator_latest_strategy_decision.csv")
    completion = _latest(base / "operator_real_market_mvp_completion_gate.csv")
    checklist_rows = _read_rows(base / "operator_daily_checklist.csv")
    map_rows = _read_rows(base / "operator_mvp_codebase_map.csv")
    rows = [packet, latest, completion] + checklist_rows + map_rows
    safety_clean = _safety_clean([row for row in rows if row])
    has_safe_unavailable = _contains_safe_unavailable(rows)

    if missing:
        status = "FREEZE_MISSING_SOURCE"
        reason = "missing_sources:" + ",".join(missing)
    elif not safety_clean:
        status = "FREEZE_BLOCKED"
        reason = "forbidden_action_or_read_field_detected"
    elif has_safe_unavailable:
        status = "FREEZE_SAFE_UNAVAILABLE"
        reason = "safe_unavailable_documented_with_clean_boundary"
    else:
        status = "FREEZE_READY"
        reason = "sources_present_and_safety_clean"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "freeze_report_status": status,
        "source_files_present": ",".join(present) if present else "none",
        "missing_sources": ",".join(missing) if missing else "none",
        "daily_master_run_entrypoint": "scripts/operator_daily_master_run.sh",
        "final_packet_entrypoint": "operator_final_daily_packet.csv",
        "latest_strategy_decision_entrypoint": "operator_latest_strategy_decision.csv",
        "completion_gate_entrypoint": "operator_real_market_mvp_completion_gate.csv",
        "safe_unavailable_meaning": "current no real quote state with clean safety boundary",
        "manual_review_when": "after daily master run when final packet latest decision and completion gate are present",
        "block_when": "missing sources or any forbidden action/read/send field is true",
        "final_packet_status": packet.get("final_packet_status", "MISSING"),
        "latest_decision_status": latest.get("latest_decision_status", "MISSING"),
        "completion_gate_status": completion.get("completion_gate_status", "MISSING"),
        "checklist_steps": str(len(checklist_rows)),
        "mapped_modules": str(len(map_rows)),
        "safety_status": "SAFETY_CLEAN" if safety_clean else "SAFETY_BLOCKED",
        "diagnostic_reason": reason,
        "auto_trade_allowed": FALSE_TEXT,
        "account_read_allowed": FALSE_TEXT,
        "position_read_allowed": FALSE_TEXT,
        "historical_data_request_allowed": FALSE_TEXT,
        "telegram_real_send_allowed": FALSE_TEXT,
        "order_action_allowed": FALSE_TEXT,
        "cancel_action_allowed": FALSE_TEXT,
        "rebalance_action_allowed": FALSE_TEXT,
    }


def write_daily_freeze_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(FREEZE_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Operator Daily Freeze Report",
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
            "## Fixed Daily Flow",
            "",
            "- daily master run is the main entrypoint",
            "- final daily packet is the final manual observation packet",
            "- latest strategy decision is the latest strategy status entrypoint",
            "- completion gate is the MVP completion status entrypoint",
            "- SAFE_UNAVAILABLE is the normal state when real quotes are unavailable but the safety boundary is clean",
            "",
            "## Review Rules",
            "",
            "- manual review may proceed after daily master run, final packet, latest strategy decision, completion gate, checklist, and codebase map are present",
            "- block immediately when a source is missing or any forbidden action/read/send field is not false",
            "- no trade instruction is produced by this report",
            "",
            "## Freeze Status",
            "",
            f"- freeze_report_status={row['freeze_report_status']}",
            f"- final_packet_status={row['final_packet_status']}",
            f"- latest_decision_status={row['latest_decision_status']}",
            f"- completion_gate_status={row['completion_gate_status']}",
            f"- checklist_steps={row['checklist_steps']}",
            f"- mapped_modules={row['mapped_modules']}",
            f"- safety_status={row['safety_status']}",
            f"- diagnostic_reason={row['diagnostic_reason']}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_daily_freeze_report(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_daily_freeze_report.csv",
    output_report: PathLike = "reports/operator_daily_freeze_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_daily_freeze_row(base_dir=base_dir, generated_at=generated_at)
    write_daily_freeze_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 466 daily operator freeze report.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_daily_freeze_report.csv")
    parser.add_argument("--output-report", default="reports/operator_daily_freeze_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_daily_freeze_report(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator daily freeze report generated")
    print(f"freeze_report_status={row['freeze_report_status']}:safety_status={row['safety_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
