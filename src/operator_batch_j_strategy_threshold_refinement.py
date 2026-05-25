from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"
SAFE_UNAVAILABLE_STATUS = "SAFE_UNAVAILABLE_REVIEW_REQUIRED"

BATCH_J_SOURCES = (
    "operator_batch_i_final_integration_audit_gate.csv",
    "operator_final_daily_packet.csv",
    "reports/operator_final_daily_packet.md",
)

REFINEMENT_FIELDS = (
    "generated_at",
    "symbol",
    "threshold_profile_status",
    "spread_status",
    "spread_threshold_status",
    "range_status",
    "range_threshold_status",
    "signal_quality",
    "signal_quality_status",
    "risk_label",
    "risk_label_status",
    "batch_i_env_gate_status",
    "batch_i_audit_gate_status",
    "safe_unavailable_preserved",
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

GATE_FIELDS = (
    "generated_at",
    "gate_status",
    "threshold_profile_status",
    "spread_threshold_status",
    "range_threshold_status",
    "signal_quality_status",
    "risk_label_status",
    "batch_i_env_gate_status",
    "batch_i_audit_gate_status",
    "safe_unavailable_preserved",
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

SAFETY_DEFAULTS = {
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
    relevant = [row for row in rows if field in row]
    if not relevant:
        return TRUE_TEXT
    return TRUE_TEXT if all(_is_expected(row.get(field), TRUE_TEXT) for row in relevant) else FALSE_TEXT


def _production_ready_claim_detected(
    audit_gate: Dict[str, str],
    final_packet: Dict[str, str],
    final_report_text: str,
) -> bool:
    for row in (audit_gate, final_packet):
        for key, value in row.items():
            if "batch_i" not in key and "production_ready" not in key:
                continue
            normalized = str(value or "").strip().upper()
            if normalized in {"READY", "PRODUCTION_READY"} or "PRODUCTION_READY" in normalized:
                return True
    for line in final_report_text.splitlines():
        normalized = line.strip().upper()
        if "BATCH_I" in normalized and ("PRODUCTION_READY" in normalized or normalized.endswith("=READY")):
            return True
    return False


def _batch_i_context(base_dir: PathLike) -> Dict[str, object]:
    base = Path(base_dir)
    audit_gate = _latest(base / "operator_batch_i_final_integration_audit_gate.csv")
    final_packet = _latest(base / "operator_final_daily_packet.csv")
    final_report_text = _read_text(base / "reports/operator_final_daily_packet.md")
    rows = [row for row in (audit_gate, final_packet) if row]
    missing = [name for name in BATCH_J_SOURCES if not (base / name).exists()]

    batch_i_env_gate_status = final_packet.get("batch_i_env_gate_status", "MISSING")
    if batch_i_env_gate_status == "MISSING":
        batch_i_env_gate_status = audit_gate.get("batch_i_gate_status", "MISSING")
    batch_i_audit_gate_status = audit_gate.get("audit_gate_status", "MISSING")
    safe_unavailable_preserved = (
        batch_i_env_gate_status == SAFE_UNAVAILABLE_STATUS
        and audit_gate.get("safe_unavailable_preserved") == TRUE_TEXT
        and SAFE_UNAVAILABLE_STATUS in final_report_text
    )
    production_claim = _production_ready_claim_detected(audit_gate, final_packet, final_report_text)

    return {
        "rows": rows,
        "missing": missing,
        "batch_i_env_gate_status": batch_i_env_gate_status,
        "batch_i_audit_gate_status": batch_i_audit_gate_status,
        "safe_unavailable_preserved": safe_unavailable_preserved,
        "production_ready_claim_detected": production_claim,
    }


def build_batch_j_threshold_refinement_rows(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    generated = generated_at or _now_timestamp()
    context = _batch_i_context(base_dir)
    missing = context["missing"]
    safe_unavailable_preserved = bool(context["safe_unavailable_preserved"])
    production_claim = bool(context["production_ready_claim_detected"])

    if missing:
        profile_status = "BATCH_J_THRESHOLD_PROFILE_REVIEW_REQUIRED"
        reason = "missing_batch_i_sources:" + ",".join(str(item) for item in missing)
    elif production_claim:
        profile_status = "BATCH_J_THRESHOLD_PROFILE_REVIEW_REQUIRED"
        reason = "batch_i_production_ready_claim_blocks_strategy_threshold_promotion"
    elif safe_unavailable_preserved:
        profile_status = "BATCH_J_THRESHOLD_PROFILE_REVIEW_ONLY"
        reason = "SAFE_UNAVAILABLE_REVIEW_REQUIRED_preserved_threshold_framework_only"
    else:
        profile_status = "BATCH_J_THRESHOLD_PROFILE_REVIEW_REQUIRED"
        reason = "batch_i_safe_unavailable_review_required_not_confirmed"

    common = {
        "generated_at": generated,
        "threshold_profile_status": profile_status,
        "spread_status": "unavailable",
        "spread_threshold_status": "review_required",
        "range_status": "unavailable",
        "range_threshold_status": "review_required",
        "signal_quality": "low",
        "signal_quality_status": "review_required",
        "risk_label": "safe_unavailable",
        "risk_label_status": "review_required",
        "batch_i_env_gate_status": str(context["batch_i_env_gate_status"]),
        "batch_i_audit_gate_status": str(context["batch_i_audit_gate_status"]),
        "safe_unavailable_preserved": TRUE_TEXT if safe_unavailable_preserved else FALSE_TEXT,
        "production_ready_claim_detected": TRUE_TEXT if production_claim else FALSE_TEXT,
        "diagnostic_reason": reason,
    }
    common.update(SAFETY_DEFAULTS)
    return [dict(common, symbol=symbol) for symbol in ("GLD", "SLV")]


def build_batch_j_gate_row(
    rows: Sequence[Dict[str, str]],
    *,
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    generated = generated_at or (rows[0]["generated_at"] if rows else _now_timestamp())
    if not rows:
        return {
            "generated_at": generated,
            "gate_status": "BATCH_J_THRESHOLD_GATE_NO_GO",
            "threshold_profile_status": "MISSING",
            "spread_threshold_status": "MISSING",
            "range_threshold_status": "MISSING",
            "signal_quality_status": "MISSING",
            "risk_label_status": "MISSING",
            "batch_i_env_gate_status": "MISSING",
            "batch_i_audit_gate_status": "MISSING",
            "safe_unavailable_preserved": FALSE_TEXT,
            "production_ready_claim_detected": FALSE_TEXT,
            "diagnostic_reason": "missing_threshold_refinement_rows",
            **SAFETY_DEFAULTS,
        }

    first = rows[0]
    generated_rows_ok = all(row.get("symbol") in {"GLD", "SLV"} for row in rows) and len(rows) == 2
    safety_clean = all(row.get(field) == value for row in rows for field, value in SAFETY_DEFAULTS.items())
    production_claim = any(row.get("production_ready_claim_detected") == TRUE_TEXT for row in rows)

    if not generated_rows_ok:
        gate_status = "BATCH_J_THRESHOLD_GATE_NO_GO"
        reason = "threshold_rows_missing_gld_slv"
    elif not safety_clean:
        gate_status = "BATCH_J_THRESHOLD_GATE_NO_GO"
        reason = "batch_j_safety_assertions_failed"
    elif production_claim:
        gate_status = "BATCH_J_THRESHOLD_GATE_REVIEW_REQUIRED"
        reason = "production_ready_claim_detected_no_strategy_promotion"
    else:
        gate_status = "PASS"
        reason = "batch_j_threshold_framework_generated_pass_only_not_production_or_execution_ready"

    return {
        "generated_at": generated,
        "gate_status": gate_status,
        "threshold_profile_status": first["threshold_profile_status"],
        "spread_threshold_status": first["spread_threshold_status"],
        "range_threshold_status": first["range_threshold_status"],
        "signal_quality_status": first["signal_quality_status"],
        "risk_label_status": first["risk_label_status"],
        "batch_i_env_gate_status": first["batch_i_env_gate_status"],
        "batch_i_audit_gate_status": first["batch_i_audit_gate_status"],
        "safe_unavailable_preserved": first["safe_unavailable_preserved"],
        "production_ready_claim_detected": TRUE_TEXT if production_claim else FALSE_TEXT,
        "diagnostic_reason": reason,
        **SAFETY_DEFAULTS,
    }


def write_csv(path: PathLike, rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_refinement_report(rows: Sequence[Dict[str, str]]) -> str:
    lines = [
        "# Operator Batch J Strategy Threshold Refinement",
        "",
        "## Scope",
        "",
        "- threshold framework only; manual observation wording only",
        "- no automatic trading, no order, no cancel, no rebalance",
        "- no account reads, no position reads, no historical data requests",
        "- no TWS or IB Gateway connection and no Telegram real send",
        "",
        "## Threshold Rows",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"- symbol={row['symbol']}",
                f"  - threshold_profile_status={row['threshold_profile_status']}",
                f"  - spread_status={row['spread_status']}",
                f"  - range_status={row['range_status']}",
                f"  - signal_quality={row['signal_quality']}",
                f"  - risk_label={row['risk_label']}",
                f"  - batch_i_env_gate_status={row['batch_i_env_gate_status']}",
                f"  - safe_unavailable_preserved={row['safe_unavailable_preserved']}",
                f"  - production_ready_claim_detected={row['production_ready_claim_detected']}",
                f"  - trading_actions_allowed={row['trading_actions_allowed']}",
                f"  - account_read_allowed={row['account_read_allowed']}",
                f"  - position_read_allowed={row['position_read_allowed']}",
                f"  - historical_data_request_allowed={row['historical_data_request_allowed']}",
                f"  - telegram_real_send_allowed={row['telegram_real_send_allowed']}",
                f"  - diagnostic_reason={row['diagnostic_reason']}",
            ]
        )
    return "\n".join(lines) + "\n"


def build_gate_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Operator Batch J Strategy Threshold Gate",
            "",
            "## Scope",
            "",
            "- PASS only means Batch J threshold framework generation succeeded",
            "- PASS does not mean live production ready",
            "- PASS does not mean real market data verified",
            "- PASS does not mean strategy ready for execution or auto trading ready",
            "",
            "## Gate",
            "",
            f"- gate_status={row['gate_status']}",
            f"- threshold_profile_status={row['threshold_profile_status']}",
            f"- spread_threshold_status={row['spread_threshold_status']}",
            f"- range_threshold_status={row['range_threshold_status']}",
            f"- signal_quality_status={row['signal_quality_status']}",
            f"- risk_label_status={row['risk_label_status']}",
            f"- batch_i_env_gate_status={row['batch_i_env_gate_status']}",
            f"- batch_i_audit_gate_status={row['batch_i_audit_gate_status']}",
            f"- safe_unavailable_preserved={row['safe_unavailable_preserved']}",
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


def generate_batch_j_strategy_threshold_refinement(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_batch_j_strategy_threshold_refinement.csv",
    output_report: PathLike = "reports/operator_batch_j_strategy_threshold_refinement_report.md",
    gate_csv: PathLike = "operator_batch_j_strategy_threshold_gate.csv",
    gate_report: PathLike = "reports/operator_batch_j_strategy_threshold_gate_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, object]:
    rows = build_batch_j_threshold_refinement_rows(base_dir=base_dir, generated_at=generated_at)
    gate = build_batch_j_gate_row(rows, generated_at=generated_at)
    write_csv(output_csv, rows, REFINEMENT_FIELDS)
    Path(output_report).parent.mkdir(parents=True, exist_ok=True)
    Path(output_report).write_text(build_refinement_report(rows), encoding="utf-8")
    write_csv(gate_csv, [gate], GATE_FIELDS)
    Path(gate_report).parent.mkdir(parents=True, exist_ok=True)
    Path(gate_report).write_text(build_gate_report(gate), encoding="utf-8")
    return {"rows": rows, "gate": gate}


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 478-481 Batch J strategy threshold refinement skeleton.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_batch_j_strategy_threshold_refinement.csv")
    parser.add_argument("--output-report", default="reports/operator_batch_j_strategy_threshold_refinement_report.md")
    parser.add_argument("--gate-csv", default="operator_batch_j_strategy_threshold_gate.csv")
    parser.add_argument("--gate-report", default="reports/operator_batch_j_strategy_threshold_gate_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    result = generate_batch_j_strategy_threshold_refinement(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_report=args.output_report,
        gate_csv=args.gate_csv,
        gate_report=args.gate_report,
        generated_at=args.generated_at,
    )
    gate = result["gate"]
    print("[BATCH_J_STRATEGY_THRESHOLD_REFINEMENT] generated")
    print(
        "gate_status={}:batch_i_env_gate_status={}:threshold_profile_status={}".format(
            gate["gate_status"],
            gate["batch_i_env_gate_status"],
            gate["threshold_profile_status"],
        )
    )
    print("NOTICE: Batch J PASS is framework generation only, not production or strategy execution readiness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
