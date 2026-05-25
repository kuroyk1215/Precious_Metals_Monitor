from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"
SAFE_UNAVAILABLE_STATUS = "SAFE_UNAVAILABLE_REVIEW_REQUIRED"
THRESHOLD_REVIEW_ONLY_STATUS = "BATCH_J_THRESHOLD_PROFILE_REVIEW_ONLY"

DASHBOARD_FIELDS = (
    "generated_at",
    "dashboard_status",
    "final_packet_status",
    "batch_i_env_gate_status",
    "batch_i_audit_gate_status",
    "batch_j_gate_status",
    "batch_j_threshold_profile_status",
    "batch_j_audit_gate_status",
    "safe_unavailable_status",
    "production_ready_claim_detected",
    "real_market_data_verified",
    "strategy_execution_ready",
    "operator_display_mode",
    "dashboard_data_source",
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

ARTIFACT_PRIORITY = (
    "operator_final_daily_packet.csv",
    "reports/operator_final_daily_packet.md",
    "operator_batch_i_final_integration_audit_gate.csv",
    "operator_batch_j_final_integration_audit_gate.csv",
    "operator_batch_j_strategy_threshold_gate.csv",
    "operator_mvp_final_audit_gate.csv",
    "operator_real_market_mvp_completion_gate.csv",
)

SAFETY_FALSE_FIELDS = (
    "trading_actions_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "telegram_real_send_allowed",
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


def _read_text(path: PathLike) -> str:
    text_path = Path(path)
    if not text_path.exists():
        return ""
    return text_path.read_text(encoding="utf-8")


def _is_false(value: object) -> bool:
    return str(value or "").strip().lower() in {"", "false", "0", "no"}


def _is_true(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _any_allowed(rows: Sequence[Dict[str, str]], field: str) -> str:
    for row in rows:
        if field in row and not _is_false(row.get(field)):
            return TRUE_TEXT
    return FALSE_TEXT


def _all_true(rows: Sequence[Dict[str, str]], field: str) -> str:
    matching = [row for row in rows if field in row]
    return TRUE_TEXT if matching and all(_is_true(row.get(field)) for row in matching) else FALSE_TEXT


def _normalize_claim_text(value: object) -> str:
    return str(value or "").strip().upper().replace("-", "_").replace(" ", "_")


def _production_ready_claim_detected(rows: Sequence[Dict[str, str]], report_text: str) -> bool:
    forbidden_values = {
        "PRODUCTION_READY",
        "LIVE_READY",
        "EXECUTION_READY",
        "AUTO_TRADING_READY",
        "STRATEGY_EXECUTION_READY",
        "LIVE_PRODUCTION_READY",
    }
    forbidden_fragments = (
        "PRODUCTION_READY",
        "LIVE_READY",
        "EXECUTION_READY",
        "AUTO_TRADING_READY",
        "STRATEGY_EXECUTION_READY",
        "LIVE_PRODUCTION_READY",
    )
    negated_fragments = (
        "NOT_PRODUCTION_READY",
        "NOT_LIVE_READY",
        "NOT_EXECUTION_READY",
        "NOT_AUTO_TRADING_READY",
        "NOT_STRATEGY_EXECUTION_READY",
        "NOT_LIVE_PRODUCTION_READY",
    )

    for row in rows:
        if row.get("production_ready_claim_detected") == TRUE_TEXT:
            return True
        if row.get("batch_j_production_ready_claim_detected") == TRUE_TEXT:
            return True
        for key, value in row.items():
            normalized = _normalize_claim_text(value)
            if key.endswith("_allowed") or normalized in {"PASS", "READY"}:
                continue
            if any(marker in normalized for marker in negated_fragments):
                continue
            if normalized in forbidden_values:
                return True

    for raw_line in report_text.splitlines():
        normalized = _normalize_claim_text(raw_line)
        if "CLAIM_DETECTED=FALSE" in normalized:
            continue
        if any(marker in normalized for marker in negated_fragments):
            continue
        if any(marker in normalized for marker in forbidden_fragments):
            return True
    return False


def _readable_status(value: object) -> bool:
    return str(value or "").strip() not in {"", "MISSING"}


def _data_sources(base: Path) -> tuple[List[str], List[str]]:
    present = [name for name in ARTIFACT_PRIORITY if (base / name).exists()]
    missing = [name for name in ARTIFACT_PRIORITY if name not in present]
    return present, missing


def build_dashboard_artifact_reader_row(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    base = Path(base_dir)
    present, missing = _data_sources(base)

    final_packet = _latest(base / "operator_final_daily_packet.csv")
    final_report_text = _read_text(base / "reports/operator_final_daily_packet.md")
    batch_i_audit = _latest(base / "operator_batch_i_final_integration_audit_gate.csv")
    batch_j_audit = _latest(base / "operator_batch_j_final_integration_audit_gate.csv")
    batch_j_gate = _latest(base / "operator_batch_j_strategy_threshold_gate.csv")
    mvp_audit = _latest(base / "operator_mvp_final_audit_gate.csv")
    completion_gate = _latest(base / "operator_real_market_mvp_completion_gate.csv")
    rows = [row for row in (final_packet, batch_i_audit, batch_j_audit, batch_j_gate, mvp_audit, completion_gate) if row]

    final_packet_status = final_packet.get("final_packet_status", "MISSING")
    batch_i_env_gate_status = final_packet.get(
        "batch_i_env_gate_status",
        batch_i_audit.get("batch_i_gate_status", "MISSING"),
    )
    batch_i_audit_gate_status = batch_i_audit.get("audit_gate_status", "MISSING")
    batch_j_gate_status = final_packet.get("batch_j_gate_status", batch_j_gate.get("gate_status", "MISSING"))
    batch_j_threshold_profile_status = final_packet.get(
        "batch_j_threshold_profile_status",
        batch_j_gate.get("threshold_profile_status", "MISSING"),
    )
    batch_j_audit_gate_status = batch_j_audit.get("audit_gate_status", "MISSING")
    safe_unavailable_status = (
        SAFE_UNAVAILABLE_STATUS
        if batch_i_env_gate_status == SAFE_UNAVAILABLE_STATUS
        or final_packet.get("batch_i_safe_unavailable_review_status") == SAFE_UNAVAILABLE_STATUS
        or SAFE_UNAVAILABLE_STATUS in final_report_text
        else "MISSING"
    )
    production_claim = _production_ready_claim_detected(rows, final_report_text)
    status_readable = (
        _readable_status(final_packet_status)
        and _readable_status(batch_i_env_gate_status)
        and _readable_status(batch_i_audit_gate_status)
        and _readable_status(batch_j_gate_status)
        and _readable_status(batch_j_threshold_profile_status)
        and _readable_status(batch_j_audit_gate_status)
    )
    key_missing = missing or not status_readable

    if production_claim:
        dashboard_status = "DASHBOARD_ARTIFACT_READER_NO_GO"
        operator_display_mode = "DASHBOARD_NO_GO"
        reason = "production_live_execution_or_auto_trading_ready_claim_detected"
    elif key_missing:
        dashboard_status = "DASHBOARD_ARTIFACT_READER_REVIEW_REQUIRED"
        operator_display_mode = "DASHBOARD_REVIEW_REQUIRED"
        missing_reason = ",".join(missing) if missing else "unreadable_required_status"
        reason = "missing_or_unreadable_dashboard_sources:" + missing_reason
    else:
        dashboard_status = "DASHBOARD_ARTIFACT_READER_READY"
        if safe_unavailable_status == SAFE_UNAVAILABLE_STATUS:
            operator_display_mode = "SAFE_UNAVAILABLE_REVIEW_ONLY"
        elif batch_j_threshold_profile_status == THRESHOLD_REVIEW_ONLY_STATUS:
            operator_display_mode = "THRESHOLD_REVIEW_ONLY"
        else:
            operator_display_mode = "DASHBOARD_REVIEW_REQUIRED"
        reason = "local_dashboard_artifact_reader_ready_for_review_only_summary"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "dashboard_status": dashboard_status,
        "final_packet_status": final_packet_status,
        "batch_i_env_gate_status": batch_i_env_gate_status,
        "batch_i_audit_gate_status": batch_i_audit_gate_status,
        "batch_j_gate_status": batch_j_gate_status,
        "batch_j_threshold_profile_status": batch_j_threshold_profile_status,
        "batch_j_audit_gate_status": batch_j_audit_gate_status,
        "safe_unavailable_status": safe_unavailable_status,
        "production_ready_claim_detected": TRUE_TEXT if production_claim else FALSE_TEXT,
        "real_market_data_verified": FALSE_TEXT,
        "strategy_execution_ready": FALSE_TEXT,
        "operator_display_mode": operator_display_mode,
        "dashboard_data_source": ",".join(present) if present else "none",
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


def write_dashboard_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(DASHBOARD_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def write_dashboard_json(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_markdown_report(row: Dict[str, str]) -> str:
    lines = [
        "# Operator Dashboard Artifact Reader",
        "",
        "## Scope",
        "",
        "- local read-only dashboard artifact summary",
        "- no UI frontend and no web service",
        "- no IBKR, account, position, historical data, Telegram real send, or trading action path",
        "",
        "## Dashboard Summary",
        "",
    ]
    lines.extend(f"- {field}={row[field]}" for field in DASHBOARD_FIELDS)
    return "\n".join(lines) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_dashboard_artifact_reader(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_dashboard_artifact_reader.csv",
    output_json: PathLike = "operator_dashboard_artifact_reader.json",
    output_report: PathLike = "reports/operator_dashboard_artifact_reader.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_dashboard_artifact_reader_row(base_dir=base_dir, generated_at=generated_at)
    write_dashboard_csv(output_csv, row)
    write_dashboard_json(output_json, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 486-489 dashboard artifact reader summary.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_dashboard_artifact_reader.csv")
    parser.add_argument("--output-json", default="operator_dashboard_artifact_reader.json")
    parser.add_argument("--output-report", default="reports/operator_dashboard_artifact_reader.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_dashboard_artifact_reader(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_json=args.output_json,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[DASHBOARD_ARTIFACT_READER] generated")
    print(
        "dashboard_status={}:final_packet_status={}:operator_display_mode={}".format(
            row["dashboard_status"],
            row["final_packet_status"],
            row["operator_display_mode"],
        )
    )
    print("NOTICE: Local read-only dashboard artifacts only. No web app, no IBKR, no trading, no sending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
