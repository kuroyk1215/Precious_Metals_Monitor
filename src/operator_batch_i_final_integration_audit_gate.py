from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"
SAFE_UNAVAILABLE_STATUS = "SAFE_UNAVAILABLE_REVIEW_REQUIRED"

BATCH_I_FINAL_INTEGRATION_SOURCES = (
    "operator_batch_i_real_market_env_gate.csv",
    "operator_batch_i_real_market_env_check.csv",
    "operator_batch_i_marketdata_permission_check.csv",
    "operator_batch_i_safe_unavailable_review.csv",
    "operator_final_daily_packet.csv",
    "reports/operator_final_daily_packet.md",
)

AUDIT_FIELDS = (
    "generated_at",
    "audit_gate_status",
    "batch_i_gate_status",
    "final_packet_batch_i_gate_status",
    "batch_i_status_consistent",
    "safe_unavailable_preserved",
    "production_ready_claim_detected",
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


def _safety_assertions_complete(rows: Sequence[Dict[str, str]]) -> bool:
    if not rows:
        return False
    for row in rows:
        for field, expected in SAFETY_ASSERTIONS.items():
            if field not in row or not _is_expected(row.get(field), expected):
                return False
    return True


def _any_allowed(rows: Sequence[Dict[str, str]], field: str) -> str:
    for row in rows:
        if field in row and not _is_expected(row.get(field), FALSE_TEXT):
            return TRUE_TEXT
    return FALSE_TEXT


def _all_true(rows: Sequence[Dict[str, str]], field: str) -> str:
    if not rows:
        return FALSE_TEXT
    return TRUE_TEXT if all(field in row and _is_expected(row.get(field), TRUE_TEXT) for row in rows) else FALSE_TEXT


def _batch_i_report_lines(report_text: str) -> List[str]:
    return [line.strip() for line in report_text.splitlines() if "batch_i" in line]


def _production_ready_claim_detected(final_packet: Dict[str, str], report_text: str) -> bool:
    forbidden_values = {"PASS", "READY", "PRODUCTION_READY"}
    for key, value in final_packet.items():
        if not key.startswith("batch_i_"):
            continue
        normalized = str(value).strip().upper()
        if normalized in forbidden_values or "PRODUCTION_READY" in normalized:
            return True
    for line in _batch_i_report_lines(report_text):
        normalized = line.upper()
        if "PRODUCTION_READY" in normalized or normalized.endswith("=PASS") or normalized.endswith("=READY"):
            return True
    return False


def build_batch_i_final_integration_audit_row(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    base = Path(base_dir)
    missing = [name for name in BATCH_I_FINAL_INTEGRATION_SOURCES if not (base / name).exists()]

    gate = _latest(base / "operator_batch_i_real_market_env_gate.csv")
    environment = _latest(base / "operator_batch_i_real_market_env_check.csv")
    permissions = _read_rows(base / "operator_batch_i_marketdata_permission_check.csv")
    review = _latest(base / "operator_batch_i_safe_unavailable_review.csv")
    final_packet = _latest(base / "operator_final_daily_packet.csv")
    final_report_text = _read_text(base / "reports/operator_final_daily_packet.md")

    batch_rows = [row for row in (gate, environment, review, final_packet) if row] + permissions
    batch_i_gate_status = gate.get("gate_status", "MISSING")
    final_packet_batch_i_gate_status = final_packet.get("batch_i_env_gate_status", "MISSING")
    status_consistent = batch_i_gate_status == final_packet_batch_i_gate_status and batch_i_gate_status != "MISSING"
    report_has_batch_i_status = f"batch_i_env_gate_status={batch_i_gate_status}" in final_report_text
    safe_unavailable_preserved = (
        batch_i_gate_status == SAFE_UNAVAILABLE_STATUS
        and environment.get("real_market_environment_status") == SAFE_UNAVAILABLE_STATUS
        and review.get("safe_unavailable_review_status") == SAFE_UNAVAILABLE_STATUS
        and final_packet_batch_i_gate_status == SAFE_UNAVAILABLE_STATUS
        and SAFE_UNAVAILABLE_STATUS in final_report_text
    )
    production_claim = _production_ready_claim_detected(final_packet, final_report_text)
    safety_complete = _safety_assertions_complete(batch_rows)

    if missing:
        status = "BATCH_I_FINAL_INTEGRATION_AUDIT_NO_GO"
        reason = "missing_sources:" + ",".join(missing)
    elif not status_consistent:
        status = "BATCH_I_FINAL_INTEGRATION_AUDIT_REVIEW_REQUIRED"
        reason = "batch_i_gate_status_mismatch"
    elif not safe_unavailable_preserved:
        status = "BATCH_I_FINAL_INTEGRATION_AUDIT_REVIEW_REQUIRED"
        reason = "safe_unavailable_review_required_not_preserved"
    elif not report_has_batch_i_status:
        status = "BATCH_I_FINAL_INTEGRATION_AUDIT_REVIEW_REQUIRED"
        reason = "final_packet_report_missing_batch_i_status"
    elif production_claim:
        status = "BATCH_I_FINAL_INTEGRATION_AUDIT_REVIEW_REQUIRED"
        reason = "batch_i_production_ready_or_pass_claim_detected"
    elif not safety_complete:
        status = "BATCH_I_FINAL_INTEGRATION_AUDIT_REVIEW_REQUIRED"
        reason = "batch_i_safety_assertions_incomplete"
    else:
        status = "PASS"
        reason = "integration_audit_pass_only_not_live_production_or_real_market_data_pass"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "audit_gate_status": status,
        "batch_i_gate_status": batch_i_gate_status,
        "final_packet_batch_i_gate_status": final_packet_batch_i_gate_status,
        "batch_i_status_consistent": TRUE_TEXT if status_consistent else FALSE_TEXT,
        "safe_unavailable_preserved": TRUE_TEXT if safe_unavailable_preserved else FALSE_TEXT,
        "production_ready_claim_detected": TRUE_TEXT if production_claim else FALSE_TEXT,
        "trading_actions_allowed": _any_allowed(batch_rows, "trading_actions_allowed"),
        "order_action_allowed": _any_allowed(batch_rows, "order_action_allowed"),
        "cancel_action_allowed": _any_allowed(batch_rows, "cancel_action_allowed"),
        "rebalance_action_allowed": _any_allowed(batch_rows, "rebalance_action_allowed"),
        "account_read_allowed": _any_allowed(batch_rows, "account_read_allowed"),
        "position_read_allowed": _any_allowed(batch_rows, "position_read_allowed"),
        "historical_data_request_allowed": _any_allowed(batch_rows, "historical_data_request_allowed"),
        "telegram_real_send_allowed": _any_allowed(batch_rows, "telegram_real_send_allowed"),
        "manual_only": _all_true(batch_rows, "manual_only"),
        "research_only": _all_true(batch_rows, "research_only"),
        "observation_only": _all_true(batch_rows, "observation_only"),
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
            "# Operator Batch I Final Integration Audit Gate",
            "",
            "## Scope",
            "",
            "- integration audit PASS only; not live production PASS",
            "- not real market data PASS",
            "- manual-only / research-only / observation-only",
            "- no trading, no account reads, no position reads, no historical data requests, no Telegram real send",
            "",
            "## Audit Gate",
            "",
            f"- audit_gate_status={row['audit_gate_status']}",
            f"- batch_i_gate_status={row['batch_i_gate_status']}",
            f"- final_packet_batch_i_gate_status={row['final_packet_batch_i_gate_status']}",
            f"- batch_i_status_consistent={row['batch_i_status_consistent']}",
            f"- safe_unavailable_preserved={row['safe_unavailable_preserved']}",
            f"- production_ready_claim_detected={row['production_ready_claim_detected']}",
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


def generate_batch_i_final_integration_audit_gate(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_batch_i_final_integration_audit_gate.csv",
    output_report: PathLike = "reports/operator_batch_i_final_integration_audit_gate_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_batch_i_final_integration_audit_row(base_dir=base_dir, generated_at=generated_at)
    write_audit_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 475-477 Batch I final integration audit gate.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_batch_i_final_integration_audit_gate.csv")
    parser.add_argument("--output-report", default="reports/operator_batch_i_final_integration_audit_gate_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_batch_i_final_integration_audit_gate(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[BATCH_I_FINAL_INTEGRATION_AUDIT_GATE] generated")
    print(
        "audit_gate_status={}:batch_i_gate_status={}:final_packet_batch_i_gate_status={}".format(
            row["audit_gate_status"],
            row["batch_i_gate_status"],
            row["final_packet_batch_i_gate_status"],
        )
    )
    print("NOTICE: Integration audit PASS is not live production PASS and not real market data PASS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
