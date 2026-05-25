from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"
SAFE_UNAVAILABLE_STATUS = "SAFE_UNAVAILABLE_REVIEW_REQUIRED"
REVIEW_ONLY_STATUS = "BATCH_J_THRESHOLD_PROFILE_REVIEW_ONLY"

BATCH_J_FINAL_INTEGRATION_SOURCES = (
    "operator_batch_j_strategy_threshold_refinement.csv",
    "operator_batch_j_strategy_threshold_gate.csv",
    "operator_final_daily_packet.csv",
    "reports/operator_final_daily_packet.md",
)

AUDIT_FIELDS = (
    "generated_at",
    "audit_gate_status",
    "batch_j_gate_status",
    "final_packet_batch_j_gate_status",
    "batch_j_threshold_profile_status",
    "final_packet_batch_j_threshold_profile_status",
    "batch_j_status_consistent",
    "safe_unavailable_preserved",
    "review_only_preserved",
    "production_ready_claim_detected",
    "strategy_auto_execution_allowed",
    "trading_actions_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "telegram_real_send_allowed",
    "manual_only",
    "research_only",
    "observation_only",
    "diagnostic_reason",
)

SAFETY_ASSERTIONS = {
    "strategy_auto_execution_allowed": FALSE_TEXT,
    "trading_actions_allowed": FALSE_TEXT,
    "order_action_allowed": FALSE_TEXT,
    "cancel_action_allowed": FALSE_TEXT,
    "rebalance_action_allowed": FALSE_TEXT,
    "account_read_allowed": FALSE_TEXT,
    "position_read_allowed": FALSE_TEXT,
    "historical_data_request_allowed": FALSE_TEXT,
    "telegram_real_send_allowed": FALSE_TEXT,
    "manual_only": TRUE_TEXT,
    "research_only": TRUE_TEXT,
    "observation_only": TRUE_TEXT,
}

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


def _read_text(path: PathLike) -> str:
    text_path = Path(path)
    if not text_path.exists():
        return ""
    return text_path.read_text(encoding="utf-8")


def _is_expected(value: object, expected: str) -> bool:
    return str(value or "").strip().lower() == expected


def _any_allowed(rows: Sequence[Dict[str, str]], field: str) -> str:
    for row in rows:
        if field in row and not _is_expected(row.get(field), FALSE_TEXT):
            return TRUE_TEXT
    return FALSE_TEXT


def _all_true(rows: Sequence[Dict[str, str]], field: str) -> str:
    if not rows:
        return FALSE_TEXT
    return TRUE_TEXT if all(field in row and _is_expected(row.get(field), TRUE_TEXT) for row in rows) else FALSE_TEXT


def _safety_assertions_complete(rows: Sequence[Dict[str, str]]) -> bool:
    if not rows:
        return False
    for row in rows:
        for field, expected in SAFETY_ASSERTIONS.items():
            if field not in row or not _is_expected(row.get(field), expected):
                return False
    return True


def _production_ready_claim_detected(
    gate: Dict[str, str],
    final_packet: Dict[str, str],
    final_report_text: str,
) -> bool:
    if gate.get("production_ready_claim_detected") == TRUE_TEXT:
        return True
    if final_packet.get("batch_j_production_ready_claim_detected") == TRUE_TEXT:
        return True

    forbidden_values = {"PRODUCTION_READY", "LIVE_READY", "EXECUTION_READY", "AUTO_TRADING_READY"}
    for row in (gate, final_packet):
        for key, value in row.items():
            if not (key.startswith("batch_j_") or key == "gate_status"):
                continue
            normalized = str(value or "").strip().upper().replace(" ", "_").replace("-", "_")
            if normalized in forbidden_values:
                return True

    for line in final_report_text.splitlines():
        normalized = line.strip().upper().replace(" ", "_").replace("-", "_")
        if "PRODUCTION_READY_CLAIM_DETECTED=FALSE" in normalized:
            continue
        if "BATCH_J" not in normalized or normalized.startswith("-_PASS_IS_NOT"):
            continue
        if any(value in normalized for value in forbidden_values):
            return True
    return False


def build_batch_j_final_integration_audit_row(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    base = Path(base_dir)
    missing = [name for name in BATCH_J_FINAL_INTEGRATION_SOURCES if not (base / name).exists()]

    gate = _latest(base / "operator_batch_j_strategy_threshold_gate.csv")
    refinement_rows = _read_rows(base / "operator_batch_j_strategy_threshold_refinement.csv")
    final_packet = _latest(base / "operator_final_daily_packet.csv")
    if final_packet and "strategy_auto_execution_allowed" not in final_packet:
        final_packet = {
            **final_packet,
            "strategy_auto_execution_allowed": final_packet.get("batch_j_strategy_auto_execution_allowed", FALSE_TEXT),
        }
    final_report_text = _read_text(base / "reports/operator_final_daily_packet.md")
    rows = [row for row in (gate, final_packet) if row] + refinement_rows

    batch_j_gate_status = gate.get("gate_status", "MISSING")
    final_packet_batch_j_gate_status = final_packet.get("batch_j_gate_status", "MISSING")
    batch_j_threshold_profile_status = gate.get("threshold_profile_status", "MISSING")
    final_packet_batch_j_threshold_profile_status = final_packet.get("batch_j_threshold_profile_status", "MISSING")
    status_consistent = (
        batch_j_gate_status == final_packet_batch_j_gate_status
        and batch_j_threshold_profile_status == final_packet_batch_j_threshold_profile_status
        and batch_j_gate_status != "MISSING"
        and batch_j_threshold_profile_status != "MISSING"
    )
    report_has_batch_j_status = (
        f"batch_j_gate_status={batch_j_gate_status}" in final_report_text
        and f"batch_j_threshold_profile_status={batch_j_threshold_profile_status}" in final_report_text
    )
    safe_unavailable_preserved = (
        gate.get("safe_unavailable_preserved") == TRUE_TEXT
        and final_packet.get("batch_j_safe_unavailable_preserved") == TRUE_TEXT
        and SAFE_UNAVAILABLE_STATUS in final_report_text
        and any(row.get("safe_unavailable_preserved") == TRUE_TEXT for row in refinement_rows)
    )
    review_only_preserved = (
        batch_j_threshold_profile_status == REVIEW_ONLY_STATUS
        and final_packet_batch_j_threshold_profile_status == REVIEW_ONLY_STATUS
        and final_packet.get("batch_j_review_only_preserved") == TRUE_TEXT
        and REVIEW_ONLY_STATUS in final_report_text
    )
    production_claim = _production_ready_claim_detected(gate, final_packet, final_report_text)
    safety_complete = _safety_assertions_complete(rows)

    if missing:
        status = "BATCH_J_FINAL_INTEGRATION_AUDIT_NO_GO"
        reason = "missing_sources:" + ",".join(missing)
    elif not status_consistent:
        status = "BATCH_J_FINAL_INTEGRATION_AUDIT_REVIEW_REQUIRED"
        reason = "batch_j_gate_or_threshold_profile_status_mismatch"
    elif not report_has_batch_j_status:
        status = "BATCH_J_FINAL_INTEGRATION_AUDIT_REVIEW_REQUIRED"
        reason = "final_packet_report_missing_batch_j_status"
    elif not safe_unavailable_preserved:
        status = "BATCH_J_FINAL_INTEGRATION_AUDIT_REVIEW_REQUIRED"
        reason = "safe_unavailable_review_required_not_preserved"
    elif not review_only_preserved:
        status = "BATCH_J_FINAL_INTEGRATION_AUDIT_REVIEW_REQUIRED"
        reason = "batch_j_threshold_profile_review_only_not_preserved"
    elif production_claim:
        status = "BATCH_J_FINAL_INTEGRATION_AUDIT_REVIEW_REQUIRED"
        reason = "batch_j_production_live_execution_or_auto_trading_ready_claim_detected"
    elif not safety_complete:
        status = "BATCH_J_FINAL_INTEGRATION_AUDIT_REVIEW_REQUIRED"
        reason = "batch_j_safety_assertions_incomplete"
    else:
        status = "PASS"
        reason = "batch_j_integration_audit_pass_only_not_live_production_real_market_data_or_strategy_execution_pass"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "audit_gate_status": status,
        "batch_j_gate_status": batch_j_gate_status,
        "final_packet_batch_j_gate_status": final_packet_batch_j_gate_status,
        "batch_j_threshold_profile_status": batch_j_threshold_profile_status,
        "final_packet_batch_j_threshold_profile_status": final_packet_batch_j_threshold_profile_status,
        "batch_j_status_consistent": TRUE_TEXT if status_consistent else FALSE_TEXT,
        "safe_unavailable_preserved": TRUE_TEXT if safe_unavailable_preserved else FALSE_TEXT,
        "review_only_preserved": TRUE_TEXT if review_only_preserved else FALSE_TEXT,
        "production_ready_claim_detected": TRUE_TEXT if production_claim else FALSE_TEXT,
        "strategy_auto_execution_allowed": _any_allowed(rows, "strategy_auto_execution_allowed"),
        "trading_actions_allowed": _any_allowed(rows, "trading_actions_allowed"),
        "order_action_allowed": _any_allowed(rows, "order_action_allowed"),
        "cancel_action_allowed": _any_allowed(rows, "cancel_action_allowed"),
        "rebalance_action_allowed": _any_allowed(rows, "rebalance_action_allowed"),
        "account_read_allowed": _any_allowed(rows, "account_read_allowed"),
        "position_read_allowed": _any_allowed(rows, "position_read_allowed"),
        "historical_data_request_allowed": _any_allowed(rows, "historical_data_request_allowed"),
        "telegram_real_send_allowed": _any_allowed(rows, "telegram_real_send_allowed"),
        "manual_only": _all_true(rows, "manual_only"),
        "research_only": _all_true(rows, "research_only"),
        "observation_only": _all_true(rows, "observation_only"),
        "diagnostic_reason": reason,
    }


def write_audit_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(AUDIT_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Operator Batch J Final Integration Audit Gate",
            "",
            "## Scope",
            "",
            "- Batch J integration audit PASS only; not live production PASS",
            "- not real market data PASS",
            "- not strategy execution PASS",
            "- threshold framework generation only; manual-only / research-only / observation-only",
            "- no trading, no account reads, no position reads, no historical data requests, no Telegram real send",
            "",
            "## Audit Gate",
            "",
            f"- audit_gate_status={row['audit_gate_status']}",
            f"- batch_j_gate_status={row['batch_j_gate_status']}",
            f"- final_packet_batch_j_gate_status={row['final_packet_batch_j_gate_status']}",
            f"- batch_j_threshold_profile_status={row['batch_j_threshold_profile_status']}",
            f"- final_packet_batch_j_threshold_profile_status={row['final_packet_batch_j_threshold_profile_status']}",
            f"- batch_j_status_consistent={row['batch_j_status_consistent']}",
            f"- safe_unavailable_preserved={row['safe_unavailable_preserved']}",
            f"- review_only_preserved={row['review_only_preserved']}",
            f"- production_ready_claim_detected={row['production_ready_claim_detected']}",
            f"- strategy_auto_execution_allowed={row['strategy_auto_execution_allowed']}",
            f"- trading_actions_allowed={row['trading_actions_allowed']}",
            f"- order_action_allowed={row['order_action_allowed']}",
            f"- cancel_action_allowed={row['cancel_action_allowed']}",
            f"- rebalance_action_allowed={row['rebalance_action_allowed']}",
            f"- account_read_allowed={row['account_read_allowed']}",
            f"- position_read_allowed={row['position_read_allowed']}",
            f"- historical_data_request_allowed={row['historical_data_request_allowed']}",
            f"- telegram_real_send_allowed={row['telegram_real_send_allowed']}",
            f"- manual_only={row['manual_only']}",
            f"- research_only={row['research_only']}",
            f"- observation_only={row['observation_only']}",
            f"- diagnostic_reason={row['diagnostic_reason']}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_batch_j_final_integration_audit_gate(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_batch_j_final_integration_audit_gate.csv",
    output_report: PathLike = "reports/operator_batch_j_final_integration_audit_gate_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_batch_j_final_integration_audit_row(base_dir=base_dir, generated_at=generated_at)
    write_audit_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 482-485 Batch J final integration audit gate.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_batch_j_final_integration_audit_gate.csv")
    parser.add_argument("--output-report", default="reports/operator_batch_j_final_integration_audit_gate_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_batch_j_final_integration_audit_gate(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[BATCH_J_FINAL_INTEGRATION_AUDIT_GATE] generated")
    print(
        "audit_gate_status={}:batch_j_gate_status={}:final_packet_batch_j_gate_status={}".format(
            row["audit_gate_status"],
            row["batch_j_gate_status"],
            row["final_packet_batch_j_gate_status"],
        )
    )
    print("NOTICE: Batch J integration audit PASS is not live production, real market data, or execution PASS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
