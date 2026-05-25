from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

FINAL_PACKET_SOURCES = (
    "operator_daily_master_run_summary.csv",
    "operator_mvp_readiness_report.csv",
    "operator_strategy_explanation_upgrade.csv",
    "operator_strategy_quality_report.csv",
    "operator_daily_checklist.csv",
    "operator_real_market_mvp_status.csv",
)

BATCH_I_PACKET_SOURCES = (
    "operator_batch_i_real_market_env_gate.csv",
    "operator_batch_i_real_market_env_check.csv",
    "operator_batch_i_marketdata_permission_check.csv",
    "operator_batch_i_safe_unavailable_review.csv",
)

BATCH_J_PACKET_SOURCES = (
    "operator_batch_j_strategy_threshold_refinement.csv",
    "operator_batch_j_strategy_threshold_gate.csv",
)

FINAL_PACKET_FIELDS = (
    "generated_at",
    "final_packet_status",
    "source_files_present",
    "missing_sources",
    "batch_i_source_files_present",
    "current_readiness",
    "strategy_explanation",
    "quote_availability",
    "safety_status",
    "manual_review_status",
    "batch_i_env_gate_status",
    "batch_i_real_market_environment_status",
    "batch_i_marketdata_permission_status",
    "batch_i_safe_unavailable_review_status",
    "batch_i_manual_only",
    "batch_i_research_only",
    "batch_i_observation_only",
    "batch_i_no_account_read",
    "batch_i_no_position_read",
    "batch_i_no_historical_data",
    "batch_i_no_real_telegram_send",
    "batch_j_source_files_present",
    "batch_j_gate_status",
    "batch_j_threshold_profile_status",
    "batch_j_spread_threshold_status",
    "batch_j_range_threshold_status",
    "batch_j_signal_quality_status",
    "batch_j_risk_label_status",
    "batch_j_safe_unavailable_preserved",
    "batch_j_review_only_preserved",
    "batch_j_production_ready_claim_detected",
    "batch_j_strategy_auto_execution_allowed",
    "batch_j_manual_only",
    "batch_j_research_only",
    "batch_j_observation_only",
    "batch_j_no_account_read",
    "batch_j_no_position_read",
    "batch_j_no_historical_data",
    "batch_j_no_real_telegram_send",
    "operator_next_step",
    "diagnostic_reason",
    "trading_actions_allowed",
    "auto_trade_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "telegram_real_send_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "manual_only",
    "research_only",
    "observation_only",
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


def _is_true(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


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


def _manual_review_required(rows: Sequence[Dict[str, str]]) -> bool:
    return any(
        _is_true(row.get("manual_review_required"))
        or _is_true(row.get("manual_review_only"))
        or str(row.get("readiness_status", "")).endswith("SAFE_UNAVAILABLE")
        or str(row.get("mvp_status", "")).endswith("SAFE_UNAVAILABLE")
        for row in rows
    )


def _quote_available(rows: Sequence[Dict[str, str]]) -> bool:
    return any(_is_true(row.get("real_quote_available")) or row.get("quote_status") == "AVAILABLE" for row in rows)


def _safe_unavailable(rows: Sequence[Dict[str, str]]) -> bool:
    markers = {
        "MASTER_SAFE_UNAVAILABLE",
        "MVP_SAFE_UNAVAILABLE",
        "DATA_UNAVAILABLE_BUT_SAFE",
        "SAFE_UNAVAILABLE",
        "WHY_HOLD_SAFE_UNAVAILABLE",
    }
    return any(_is_true(row.get("safe_unavailable")) or markers.intersection(str(value).strip() for value in row.values()) for row in rows)


def _all_rows_satisfy(rows: Sequence[Dict[str, str]], field: str, expected: str) -> bool:
    matching_rows = [row for row in rows if field in row]
    return bool(matching_rows) and all(str(row.get(field, "")).strip().lower() == expected for row in matching_rows)


def _batch_i_summary(base: Path) -> Dict[str, str]:
    present = [name for name in BATCH_I_PACKET_SOURCES if (base / name).exists()]
    gate = _latest(base / "operator_batch_i_real_market_env_gate.csv")
    environment = _latest(base / "operator_batch_i_real_market_env_check.csv")
    permissions = _read_rows(base / "operator_batch_i_marketdata_permission_check.csv")
    review = _latest(base / "operator_batch_i_safe_unavailable_review.csv")
    rows = [row for row in [gate, environment, review] if row] + permissions

    permission_statuses = sorted({row.get("permission_status", "MISSING") for row in permissions}) or ["MISSING"]
    safety_rows_present = bool(rows)

    return {
        "batch_i_source_files_present": ",".join(present) if present else "none",
        "batch_i_env_gate_status": gate.get("gate_status", "MISSING"),
        "batch_i_real_market_environment_status": environment.get("real_market_environment_status", "MISSING"),
        "batch_i_marketdata_permission_status": "|".join(permission_statuses),
        "batch_i_safe_unavailable_review_status": review.get("safe_unavailable_review_status", "MISSING"),
        "batch_i_manual_only": TRUE_TEXT if _all_rows_satisfy(rows, "manual_only", TRUE_TEXT) else FALSE_TEXT,
        "batch_i_research_only": TRUE_TEXT if _all_rows_satisfy(rows, "research_only", TRUE_TEXT) else FALSE_TEXT,
        "batch_i_observation_only": TRUE_TEXT if _all_rows_satisfy(rows, "observation_only", TRUE_TEXT) else FALSE_TEXT,
        "batch_i_no_account_read": TRUE_TEXT if safety_rows_present and _all_rows_satisfy(rows, "account_read_allowed", FALSE_TEXT) else FALSE_TEXT,
        "batch_i_no_position_read": TRUE_TEXT if safety_rows_present and _all_rows_satisfy(rows, "position_read_allowed", FALSE_TEXT) else FALSE_TEXT,
        "batch_i_no_historical_data": TRUE_TEXT if safety_rows_present and _all_rows_satisfy(rows, "historical_data_request_allowed", FALSE_TEXT) else FALSE_TEXT,
        "batch_i_no_real_telegram_send": TRUE_TEXT if safety_rows_present and _all_rows_satisfy(rows, "telegram_real_send_allowed", FALSE_TEXT) else FALSE_TEXT,
    }


def _batch_j_summary(base: Path) -> Dict[str, str]:
    present = [name for name in BATCH_J_PACKET_SOURCES if (base / name).exists()]
    gate = _latest(base / "operator_batch_j_strategy_threshold_gate.csv")
    refinement_rows = _read_rows(base / "operator_batch_j_strategy_threshold_refinement.csv")
    rows = [gate] if gate else []
    rows.extend(refinement_rows)
    safety_rows_present = bool(rows)

    return {
        "batch_j_source_files_present": ",".join(present) if present else "none",
        "batch_j_gate_status": gate.get("gate_status", "MISSING"),
        "batch_j_threshold_profile_status": gate.get("threshold_profile_status", "MISSING"),
        "batch_j_spread_threshold_status": gate.get("spread_threshold_status", "MISSING"),
        "batch_j_range_threshold_status": gate.get("range_threshold_status", "MISSING"),
        "batch_j_signal_quality_status": gate.get("signal_quality_status", "MISSING"),
        "batch_j_risk_label_status": gate.get("risk_label_status", "MISSING"),
        "batch_j_safe_unavailable_preserved": gate.get("safe_unavailable_preserved", FALSE_TEXT),
        "batch_j_review_only_preserved": (
            TRUE_TEXT if gate.get("threshold_profile_status") == "BATCH_J_THRESHOLD_PROFILE_REVIEW_ONLY" else FALSE_TEXT
        ),
        "batch_j_production_ready_claim_detected": gate.get("production_ready_claim_detected", FALSE_TEXT),
        "batch_j_strategy_auto_execution_allowed": gate.get("strategy_auto_execution_allowed", FALSE_TEXT),
        "batch_j_manual_only": TRUE_TEXT if _all_rows_satisfy(rows, "manual_only", TRUE_TEXT) else FALSE_TEXT,
        "batch_j_research_only": TRUE_TEXT if _all_rows_satisfy(rows, "research_only", TRUE_TEXT) else FALSE_TEXT,
        "batch_j_observation_only": TRUE_TEXT if _all_rows_satisfy(rows, "observation_only", TRUE_TEXT) else FALSE_TEXT,
        "batch_j_no_account_read": (
            TRUE_TEXT if safety_rows_present and _all_rows_satisfy(rows, "account_read_allowed", FALSE_TEXT) else FALSE_TEXT
        ),
        "batch_j_no_position_read": (
            TRUE_TEXT if safety_rows_present and _all_rows_satisfy(rows, "position_read_allowed", FALSE_TEXT) else FALSE_TEXT
        ),
        "batch_j_no_historical_data": (
            TRUE_TEXT
            if safety_rows_present and _all_rows_satisfy(rows, "historical_data_request_allowed", FALSE_TEXT)
            else FALSE_TEXT
        ),
        "batch_j_no_real_telegram_send": (
            TRUE_TEXT
            if safety_rows_present and _all_rows_satisfy(rows, "telegram_real_send_allowed", FALSE_TEXT)
            else FALSE_TEXT
        ),
    }


def build_final_daily_packet_row(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    base = Path(base_dir)
    present = [name for name in FINAL_PACKET_SOURCES if (base / name).exists()]
    missing = [name for name in FINAL_PACKET_SOURCES if name not in present]
    batch_i = _batch_i_summary(base)
    batch_j = _batch_j_summary(base)

    master = _latest(base / "operator_daily_master_run_summary.csv")
    readiness = _latest(base / "operator_mvp_readiness_report.csv")
    explanations = _read_rows(base / "operator_strategy_explanation_upgrade.csv")
    quality = _latest(base / "operator_strategy_quality_report.csv")
    checklist_rows = _read_rows(base / "operator_daily_checklist.csv")
    mvp = _latest(base / "operator_real_market_mvp_status.csv")
    rows: List[Dict[str, str]] = [master, readiness, quality, mvp] + explanations + checklist_rows

    safety_clean = _safety_clean([row for row in rows if row])
    real_quote_available = _quote_available(rows)
    safe_unavailable = _safe_unavailable(rows)
    manual_review = _manual_review_required(rows)
    readiness_status = readiness.get("readiness_status", "MISSING")
    quality_status = quality.get("quality_status", "MISSING")
    mvp_status = mvp.get("mvp_status", "MISSING")
    explanation_statuses = sorted({row.get("explanation_status", "MISSING") for row in explanations}) or ["MISSING"]

    if missing:
        status = "FINAL_PACKET_MISSING_SOURCE"
        reason = "missing_sources:" + ",".join(missing)
        next_step = "generate_missing_final_packet_sources"
    elif not safety_clean:
        status = "FINAL_PACKET_BLOCKED"
        reason = "forbidden_action_or_read_field_detected"
        next_step = "stop_and_review_safety_boundary"
    elif safe_unavailable and not real_quote_available:
        status = "FINAL_PACKET_SAFE_UNAVAILABLE"
        reason = "real_quote_unavailable_but_safety_clean"
        next_step = "review_real_marketdata_connection_continue_observation_only"
    elif readiness_status in {"MVP_BLOCKED", "MVP_MISSING_SOURCE"} or mvp_status.startswith("MVP_BLOCKED"):
        status = "FINAL_PACKET_BLOCKED"
        reason = "mvp_readiness_or_status_blocked"
        next_step = "review_mvp_blocking_sources"
    elif manual_review:
        status = "FINAL_PACKET_REVIEW_REQUIRED"
        reason = "manual_review_required_by_strategy_or_checklist"
        next_step = "manual_review_final_packet"
    else:
        status = "FINAL_PACKET_READY"
        reason = "sources_present_safety_clean_observation_only"
        next_step = "daily_observation_only_review"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "final_packet_status": status,
        "source_files_present": ",".join(present) if present else "none",
        "missing_sources": ",".join(missing) if missing else "none",
        **batch_i,
        **batch_j,
        "current_readiness": readiness_status,
        "strategy_explanation": "|".join(explanation_statuses),
        "quote_availability": "REAL_QUOTE_AVAILABLE" if real_quote_available else ("SAFE_UNAVAILABLE" if safe_unavailable else "INSUFFICIENT_DATA"),
        "safety_status": "SAFETY_CLEAN" if safety_clean else "SAFETY_BLOCKED",
        "manual_review_status": "MANUAL_REVIEW_REQUIRED" if manual_review else "MANUAL_REVIEW_NOT_REQUIRED",
        "operator_next_step": next_step,
        "diagnostic_reason": f"{reason};quality_status={quality_status};mvp_status={mvp_status}",
        "trading_actions_allowed": FALSE_TEXT,
        "auto_trade_allowed": FALSE_TEXT,
        "account_read_allowed": FALSE_TEXT,
        "position_read_allowed": FALSE_TEXT,
        "historical_data_request_allowed": FALSE_TEXT,
        "telegram_real_send_allowed": FALSE_TEXT,
        "order_action_allowed": FALSE_TEXT,
        "cancel_action_allowed": FALSE_TEXT,
        "rebalance_action_allowed": FALSE_TEXT,
        "manual_only": TRUE_TEXT,
        "research_only": TRUE_TEXT,
        "observation_only": TRUE_TEXT,
    }


def write_final_daily_packet_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(FINAL_PACKET_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Operator Final Daily Packet",
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
            "## Final Packet",
            "",
            f"- final_packet_status={row['final_packet_status']}",
            f"- current readiness: {row['current_readiness']}",
            f"- strategy explanation: {row['strategy_explanation']}",
            f"- quote availability: {row['quote_availability']}",
            f"- safety status: {row['safety_status']}",
            f"- manual review status: {row['manual_review_status']}",
            "",
            "## Batch I Real Market Env Status",
            "",
            f"- batch_i_env_gate_status={row['batch_i_env_gate_status']}",
            f"- batch_i_real_market_environment_status={row['batch_i_real_market_environment_status']}",
            f"- batch_i_marketdata_permission_status={row['batch_i_marketdata_permission_status']}",
            f"- batch_i_safe_unavailable_review_status={row['batch_i_safe_unavailable_review_status']}",
            f"- batch_i_manual_only={row['batch_i_manual_only']}",
            f"- batch_i_research_only={row['batch_i_research_only']}",
            f"- batch_i_observation_only={row['batch_i_observation_only']}",
            f"- batch_i_no_account_read={row['batch_i_no_account_read']}",
            f"- batch_i_no_position_read={row['batch_i_no_position_read']}",
            f"- batch_i_no_historical_data={row['batch_i_no_historical_data']}",
            f"- batch_i_no_real_telegram_send={row['batch_i_no_real_telegram_send']}",
            "",
            "## Batch J Threshold Framework Status",
            "",
            "- PASS only means Batch J threshold framework generation PASS",
            "- PASS is not live production PASS, not real market data PASS, and not strategy execution PASS",
            f"- batch_j_gate_status={row['batch_j_gate_status']}",
            f"- batch_j_threshold_profile_status={row['batch_j_threshold_profile_status']}",
            f"- batch_j_spread_threshold_status={row['batch_j_spread_threshold_status']}",
            f"- batch_j_range_threshold_status={row['batch_j_range_threshold_status']}",
            f"- batch_j_signal_quality_status={row['batch_j_signal_quality_status']}",
            f"- batch_j_risk_label_status={row['batch_j_risk_label_status']}",
            f"- batch_j_safe_unavailable_preserved={row['batch_j_safe_unavailable_preserved']}",
            (
                f"- batch_j_safe_unavailable_marker=SAFE_UNAVAILABLE_REVIEW_REQUIRED"
                if row["batch_j_safe_unavailable_preserved"] == TRUE_TEXT
                else "- batch_j_safe_unavailable_marker=MISSING"
            ),
            f"- batch_j_review_only_preserved={row['batch_j_review_only_preserved']}",
            f"- batch_j_production_ready_claim_detected={row['batch_j_production_ready_claim_detected']}",
            f"- batch_j_strategy_auto_execution_allowed={row['batch_j_strategy_auto_execution_allowed']}",
            f"- batch_j_manual_only={row['batch_j_manual_only']}",
            f"- batch_j_research_only={row['batch_j_research_only']}",
            f"- batch_j_observation_only={row['batch_j_observation_only']}",
            f"- batch_j_no_account_read={row['batch_j_no_account_read']}",
            f"- batch_j_no_position_read={row['batch_j_no_position_read']}",
            f"- batch_j_no_historical_data={row['batch_j_no_historical_data']}",
            f"- batch_j_no_real_telegram_send={row['batch_j_no_real_telegram_send']}",
            f"- trading_actions_allowed={row['trading_actions_allowed']}",
            f"- account_read_allowed={row['account_read_allowed']}",
            f"- position_read_allowed={row['position_read_allowed']}",
            f"- historical_data_request_allowed={row['historical_data_request_allowed']}",
            f"- telegram_real_send_allowed={row['telegram_real_send_allowed']}",
            f"- operator next step: {row['operator_next_step']}",
            f"- diagnostic_reason={row['diagnostic_reason']}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_final_daily_packet(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_final_daily_packet.csv",
    output_report: PathLike = "reports/operator_final_daily_packet.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_final_daily_packet_row(base_dir=base_dir, generated_at=generated_at)
    write_final_daily_packet_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 462 final daily operator packet.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_final_daily_packet.csv")
    parser.add_argument("--output-report", default="reports/operator_final_daily_packet.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_final_daily_packet(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator final daily packet generated")
    print(f"final_packet_status={row['final_packet_status']}:safety_status={row['safety_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
