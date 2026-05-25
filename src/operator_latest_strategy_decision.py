from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

LATEST_DECISION_SOURCES = (
    "operator_final_daily_packet.csv",
    "operator_strategy_explanation_upgrade.csv",
    "operator_mvp_readiness_report.csv",
    "operator_real_market_range_framework.csv",
    "operator_gld_slv_spread_framework.csv",
)

LATEST_DECISION_FIELDS = (
    "generated_at",
    "latest_decision_status",
    "source_files_present",
    "missing_sources",
    "final_packet_status",
    "readiness_status",
    "strategy_explanation_status",
    "range_status",
    "spread_observation_status",
    "manual_action_required",
    "diagnostic_reason",
    "operator_next_step",
    "auto_trade_allowed",
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


def _statuses(rows: Sequence[Dict[str, str]], field: str, default: str) -> str:
    values = sorted({row.get(field, default) or default for row in rows})
    return "|".join(values) if values else default


def build_latest_strategy_decision_row(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    base = Path(base_dir)
    present = [name for name in LATEST_DECISION_SOURCES if (base / name).exists()]
    missing = [name for name in LATEST_DECISION_SOURCES if name not in present]

    packet = _latest(base / "operator_final_daily_packet.csv")
    explanations = _read_rows(base / "operator_strategy_explanation_upgrade.csv")
    readiness = _latest(base / "operator_mvp_readiness_report.csv")
    range_rows = _read_rows(base / "operator_real_market_range_framework.csv")
    spread = _latest(base / "operator_gld_slv_spread_framework.csv")

    packet_status = packet.get("final_packet_status", "MISSING")
    readiness_status = readiness.get("readiness_status", "MISSING")
    explanation_status = _statuses(explanations, "explanation_status", "MISSING")
    range_status = _statuses(range_rows, "range_status", "MISSING")
    spread_status = spread.get("spread_observation_status", "MISSING")

    if missing:
        status = "LATEST_INSUFFICIENT_DATA"
        reason = "missing_sources:" + ",".join(missing)
        next_step = "generate_missing_latest_decision_sources"
        manual_action_required = TRUE_TEXT
    elif packet_status == "FINAL_PACKET_SAFE_UNAVAILABLE" or readiness_status == "MVP_SAFE_UNAVAILABLE":
        status = "LATEST_HOLD_SAFE_UNAVAILABLE"
        reason = "real_quote_unavailable_but_final_packet_safety_clean"
        next_step = "review_real_marketdata_connection_continue_observation_only"
        manual_action_required = TRUE_TEXT
    elif packet_status in {"FINAL_PACKET_BLOCKED", "FINAL_PACKET_MISSING_SOURCE"} or readiness_status.startswith("MVP_BLOCKED"):
        status = "LATEST_MVP_NOT_READY"
        reason = "final_packet_or_mvp_readiness_not_ready"
        next_step = "review_blocked_mvp_sources"
        manual_action_required = TRUE_TEXT
    elif packet_status == "FINAL_PACKET_REVIEW_REQUIRED" or "WHY_MANUAL_REVIEW_ONLY" in explanation_status:
        status = "LATEST_MANUAL_REVIEW_REQUIRED"
        reason = "manual_review_required_by_final_packet_or_strategy_explanation"
        next_step = "manual_review_strategy_context_only"
        manual_action_required = TRUE_TEXT
    elif "RANGE_INSUFFICIENT_DATA" in range_status or spread_status == "MISSING":
        status = "LATEST_INSUFFICIENT_DATA"
        reason = "range_or_spread_context_insufficient"
        next_step = "regenerate_strategy_context_sources"
        manual_action_required = TRUE_TEXT
    else:
        status = "LATEST_OBSERVE_ONLY"
        reason = "latest_strategy_context_available_observation_only"
        next_step = "daily_observation_only_review"
        manual_action_required = FALSE_TEXT

    return {
        "generated_at": generated_at or _now_timestamp(),
        "latest_decision_status": status,
        "source_files_present": ",".join(present) if present else "none",
        "missing_sources": ",".join(missing) if missing else "none",
        "final_packet_status": packet_status,
        "readiness_status": readiness_status,
        "strategy_explanation_status": explanation_status,
        "range_status": range_status,
        "spread_observation_status": spread_status,
        "manual_action_required": manual_action_required,
        "diagnostic_reason": reason,
        "operator_next_step": next_step,
        "auto_trade_allowed": FALSE_TEXT,
        "order_action_allowed": FALSE_TEXT,
        "cancel_action_allowed": FALSE_TEXT,
        "rebalance_action_allowed": FALSE_TEXT,
    }


def write_latest_strategy_decision_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(LATEST_DECISION_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Operator Latest Strategy Decision",
            "",
            "## Safety Banner",
            "",
            "- observation-only decision pointer",
            "- no auto trading",
            "- no account reads",
            "- no position reads",
            "- no historical data requests",
            "- no Telegram real send",
            "- no order/cancel/rebalance",
            "",
            "## Latest Decision",
            "",
            f"- latest_decision_status={row['latest_decision_status']}",
            f"- final_packet_status={row['final_packet_status']}",
            f"- readiness_status={row['readiness_status']}",
            f"- manual_action_required={row['manual_action_required']}",
            f"- auto_trade_allowed={row['auto_trade_allowed']}",
            f"- order_action_allowed={row['order_action_allowed']}",
            f"- cancel_action_allowed={row['cancel_action_allowed']}",
            f"- rebalance_action_allowed={row['rebalance_action_allowed']}",
            f"- operator_next_step={row['operator_next_step']}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_latest_strategy_decision(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_latest_strategy_decision.csv",
    output_report: PathLike = "reports/operator_latest_strategy_decision_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_latest_strategy_decision_row(base_dir=base_dir, generated_at=generated_at)
    write_latest_strategy_decision_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 463 latest strategy decision pointer.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_latest_strategy_decision.csv")
    parser.add_argument("--output-report", default="reports/operator_latest_strategy_decision_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_latest_strategy_decision(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator latest strategy decision generated")
    print(f"latest_decision_status={row['latest_decision_status']}:manual_action_required={row['manual_action_required']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
