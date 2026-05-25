from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

COMPLETION_GATE_SOURCES = (
    "operator_final_daily_packet.csv",
    "operator_latest_strategy_decision.csv",
    "operator_mvp_readiness_report.csv",
    "operator_real_market_mvp_regression.csv",
    "operator_continuity_archive_index.csv",
)

COMPLETION_GATE_FIELDS = (
    "generated_at",
    "completion_gate_status",
    "source_files_present",
    "missing_sources",
    "final_packet_status",
    "latest_decision_status",
    "readiness_status",
    "regression_status",
    "continuity_status",
    "safety_status",
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


def build_completion_gate_row(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    base = Path(base_dir)
    present = [name for name in COMPLETION_GATE_SOURCES if (base / name).exists()]
    missing = [name for name in COMPLETION_GATE_SOURCES if name not in present]

    packet = _latest(base / "operator_final_daily_packet.csv")
    latest = _latest(base / "operator_latest_strategy_decision.csv")
    readiness = _latest(base / "operator_mvp_readiness_report.csv")
    regression = _latest(base / "operator_real_market_mvp_regression.csv")
    continuity = _latest(base / "operator_continuity_archive_index.csv")
    rows = [packet, latest, readiness, regression, continuity]
    safety_clean = _safety_clean([row for row in rows if row])

    packet_status = packet.get("final_packet_status", "MISSING")
    latest_status = latest.get("latest_decision_status", "MISSING")
    readiness_status = readiness.get("readiness_status", "MISSING")
    regression_status = regression.get("regression_status", "MISSING")
    continuity_status = continuity.get("continuity_status", "MISSING")

    if missing:
        status = "MVP_COMPLETION_MISSING_SOURCE"
        reason = "missing_sources:" + ",".join(missing)
        next_step = "generate_missing_completion_gate_sources"
    elif not safety_clean:
        status = "MVP_COMPLETION_BLOCKED"
        reason = "forbidden_action_or_read_field_detected"
        next_step = "stop_and_review_safety_boundary"
    elif packet_status == "FINAL_PACKET_SAFE_UNAVAILABLE" or latest_status == "LATEST_HOLD_SAFE_UNAVAILABLE" or readiness_status == "MVP_SAFE_UNAVAILABLE":
        status = "MVP_COMPLETION_SAFE_UNAVAILABLE"
        reason = "real_quote_unavailable_but_safety_clean"
        next_step = "continue_safe_daily_use_after_manual_connection_review"
    elif regression_status == "FAIL" or packet_status == "FINAL_PACKET_BLOCKED" or latest_status == "LATEST_MVP_NOT_READY":
        status = "MVP_COMPLETION_BLOCKED"
        reason = "regression_or_final_packet_blocked"
        next_step = "review_blocked_completion_sources"
    elif packet_status == "FINAL_PACKET_REVIEW_REQUIRED" or latest_status == "LATEST_MANUAL_REVIEW_REQUIRED":
        status = "MVP_COMPLETION_REVIEW_REQUIRED"
        reason = "manual_review_required_before_safe_daily_use"
        next_step = "manual_review_completion_gate"
    else:
        status = "MVP_COMPLETION_READY_FOR_SAFE_DAILY_USE"
        reason = "all_completion_sources_present_safety_clean"
        next_step = "use_daily_manual_observation_packet"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "completion_gate_status": status,
        "source_files_present": ",".join(present) if present else "none",
        "missing_sources": ",".join(missing) if missing else "none",
        "final_packet_status": packet_status,
        "latest_decision_status": latest_status,
        "readiness_status": readiness_status,
        "regression_status": regression_status,
        "continuity_status": continuity_status,
        "safety_status": "SAFETY_CLEAN" if safety_clean else "SAFETY_BLOCKED",
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


def write_completion_gate_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(COMPLETION_GATE_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Operator Real Market MVP Completion Gate",
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
            "## Completion Gate",
            "",
            f"- completion_gate_status={row['completion_gate_status']}",
            f"- final_packet_status={row['final_packet_status']}",
            f"- latest_decision_status={row['latest_decision_status']}",
            f"- readiness_status={row['readiness_status']}",
            f"- regression_status={row['regression_status']}",
            f"- continuity_status={row['continuity_status']}",
            f"- safety_status={row['safety_status']}",
            f"- diagnostic_reason={row['diagnostic_reason']}",
            f"- operator_next_step={row['operator_next_step']}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_mvp_completion_gate(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_real_market_mvp_completion_gate.csv",
    output_report: PathLike = "reports/operator_real_market_mvp_completion_gate_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_completion_gate_row(base_dir=base_dir, generated_at=generated_at)
    write_completion_gate_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 464 real-market MVP completion gate.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_real_market_mvp_completion_gate.csv")
    parser.add_argument("--output-report", default="reports/operator_real_market_mvp_completion_gate_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_mvp_completion_gate(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator real-market MVP completion gate generated")
    print(f"completion_gate_status={row['completion_gate_status']}:safety_status={row['safety_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
