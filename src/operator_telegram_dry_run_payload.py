from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

from src.operator_dashboard_artifact_reader import build_dashboard_artifact_reader_row


FALSE_TEXT = "false"
TRUE_TEXT = "true"
SAFE_UNAVAILABLE_STATUS = "SAFE_UNAVAILABLE_REVIEW_REQUIRED"
TELEGRAM_DRY_RUN_READY = "TELEGRAM_DRY_RUN_READY"
TELEGRAM_APPROVAL_REVIEW_REQUIRED = "TELEGRAM_APPROVAL_REVIEW_REQUIRED"

DRY_RUN_FIELDS = (
    "generated_at",
    "telegram_payload_status",
    "dashboard_status",
    "final_packet_status",
    "batch_i_env_gate_status",
    "batch_j_threshold_profile_status",
    "safe_unavailable_status",
    "message_title",
    "message_body",
    "message_mode",
    "dry_run_only",
    "no_real_send",
    "manual_approval_required",
    "telegram_real_send_allowed",
    "trading_actions_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "manual_only",
    "research_only",
    "observation_only",
    "diagnostic_reason",
)

APPROVAL_FIELDS = (
    "generated_at",
    "approval_gate_status",
    "telegram_payload_status",
    "dashboard_status",
    "dry_run_payload_present",
    "manual_approval_required",
    "no_real_send",
    "telegram_real_send_allowed",
    "production_ready_claim_detected",
    "execution_ready_claim_detected",
    "trading_actions_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "manual_only",
    "research_only",
    "observation_only",
    "diagnostic_reason",
)

SAFETY_FALSE_FIELDS = (
    "telegram_real_send_allowed",
    "trading_actions_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
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


def _read_json_object(path: PathLike) -> Dict[str, str]:
    json_path = Path(path)
    if not json_path.exists():
        return {}
    data = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items()}


def _is_false(value: object) -> bool:
    return str(value or "").strip().lower() in {"", "false", "0", "no"}


def _is_true(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _safety_diagnostic(reason: str) -> str:
    markers = [
        "dry_run_payload_only",
        "no_real_send=true",
        "manual_approval_required=true",
        "telegram_real_send_allowed=false",
        "trading_actions_allowed=false",
        "order_action_allowed=false",
        "cancel_action_allowed=false",
        "rebalance_action_allowed=false",
        "account_read_allowed=false",
        "position_read_allowed=false",
        "historical_data_request_allowed=false",
    ]
    return reason + ";" + ";".join(markers)


def _message_body(dashboard: Dict[str, str]) -> str:
    return (
        "Dashboard: {dashboard_status}. Final packet: {final_packet_status}. "
        "Batch I: {batch_i_env_gate_status}. Batch J threshold: {batch_j_threshold_profile_status}. "
        "SAFE_UNAVAILABLE_REVIEW_REQUIRED remains active. "
        "Manual-only, research-only, observation-only. No auto trade. No real Telegram send."
    ).format(
        dashboard_status=dashboard.get("dashboard_status", "MISSING"),
        final_packet_status=dashboard.get("final_packet_status", "MISSING"),
        batch_i_env_gate_status=dashboard.get("batch_i_env_gate_status", "MISSING"),
        batch_j_threshold_profile_status=dashboard.get("batch_j_threshold_profile_status", "MISSING"),
    )


def build_telegram_dry_run_payload_row(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    dashboard = build_dashboard_artifact_reader_row(base_dir=base_dir, generated_at=generated_at)
    readable_dashboard = dashboard.get("dashboard_status", "MISSING") != "MISSING"
    telegram_payload_status = TELEGRAM_DRY_RUN_READY if readable_dashboard else "TELEGRAM_DRY_RUN_REVIEW_REQUIRED"
    reason = (
        "dashboard_artifact_reader_readable_telegram_dry_run_payload_ready"
        if telegram_payload_status == TELEGRAM_DRY_RUN_READY
        else "dashboard_artifact_reader_unreadable_telegram_dry_run_payload_review_required"
    )

    row = {
        "generated_at": generated_at or _now_timestamp(),
        "telegram_payload_status": telegram_payload_status,
        "dashboard_status": dashboard.get("dashboard_status", "MISSING"),
        "final_packet_status": dashboard.get("final_packet_status", "MISSING"),
        "batch_i_env_gate_status": dashboard.get("batch_i_env_gate_status", "MISSING"),
        "batch_j_threshold_profile_status": dashboard.get("batch_j_threshold_profile_status", "MISSING"),
        "safe_unavailable_status": SAFE_UNAVAILABLE_STATUS,
        "message_title": "Precious Metals Monitor dry-run review",
        "message_body": _message_body(dashboard),
        "message_mode": "telegram_dry_run_payload_only",
        "dry_run_only": TRUE_TEXT,
        "no_real_send": TRUE_TEXT,
        "manual_approval_required": TRUE_TEXT,
        "telegram_real_send_allowed": FALSE_TEXT,
        "trading_actions_allowed": FALSE_TEXT,
        "order_action_allowed": FALSE_TEXT,
        "cancel_action_allowed": FALSE_TEXT,
        "rebalance_action_allowed": FALSE_TEXT,
        "account_read_allowed": FALSE_TEXT,
        "position_read_allowed": FALSE_TEXT,
        "historical_data_request_allowed": FALSE_TEXT,
        "manual_only": TRUE_TEXT,
        "research_only": TRUE_TEXT,
        "observation_only": TRUE_TEXT,
        "diagnostic_reason": _safety_diagnostic(reason),
    }
    return row


def _write_csv(path: PathLike, row: Dict[str, str], fields: Sequence[str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def _write_json(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_dry_run_markdown(row: Dict[str, str]) -> str:
    lines = [
        "# Operator Telegram Dry-Run Payload",
        "",
        "## Scope",
        "",
        "- Telegram-ready draft only",
        "- no Telegram API client, token read, network send, or real send",
        "- manual-only / research-only / observation-only",
        "",
        "## Payload",
        "",
    ]
    lines.extend(f"- {field}={row[field]}" for field in DRY_RUN_FIELDS)
    return "\n".join(lines) + "\n"


def _write_markdown(path: PathLike, text: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def generate_telegram_dry_run_payload(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_telegram_dry_run_payload.csv",
    output_json: PathLike = "operator_telegram_dry_run_payload.json",
    output_report: PathLike = "reports/operator_telegram_dry_run_payload.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_telegram_dry_run_payload_row(base_dir=base_dir, generated_at=generated_at)
    _write_csv(output_csv, row, DRY_RUN_FIELDS)
    _write_json(output_json, row)
    _write_markdown(output_report, build_dry_run_markdown(row))
    return row


def _claim_detected(row: Dict[str, str], fragments: Sequence[str]) -> str:
    skip_fields = {"production_ready_claim_detected", "execution_ready_claim_detected", "diagnostic_reason"}
    for key, value in row.items():
        if key in skip_fields or key.endswith("_allowed"):
            continue
        normalized = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
        if not normalized or normalized in {"FALSE", "TRUE", "READY"}:
            continue
        if any(fragment in normalized for fragment in fragments):
            if any(("NOT_" + fragment) in normalized or ("NO_" + fragment) in normalized for fragment in fragments):
                continue
            return TRUE_TEXT
    return FALSE_TEXT


def build_telegram_approval_gate_row(
    *,
    payload_csv: PathLike = "operator_telegram_dry_run_payload.csv",
    payload_json: PathLike = "operator_telegram_dry_run_payload.json",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    payload = _latest(payload_csv) or _read_json_object(payload_json)
    payload_present = bool(payload)
    manual_required = _is_true(payload.get("manual_approval_required"))
    no_real_send = _is_true(payload.get("no_real_send"))
    real_send_allowed = not _is_false(payload.get("telegram_real_send_allowed"))
    status = (
        TELEGRAM_APPROVAL_REVIEW_REQUIRED
        if payload_present and no_real_send and manual_required
        else "TELEGRAM_APPROVAL_GATE_REVIEW_BLOCKED"
    )
    reason = (
        "dry_run_payload_present_manual_review_required_no_real_send"
        if status == TELEGRAM_APPROVAL_REVIEW_REQUIRED
        else "dry_run_payload_missing_or_required_safety_markers_absent"
    )

    row = {
        "generated_at": generated_at or _now_timestamp(),
        "approval_gate_status": status,
        "telegram_payload_status": payload.get("telegram_payload_status", "MISSING"),
        "dashboard_status": payload.get("dashboard_status", "MISSING"),
        "dry_run_payload_present": TRUE_TEXT if payload_present else FALSE_TEXT,
        "manual_approval_required": TRUE_TEXT if manual_required else FALSE_TEXT,
        "no_real_send": TRUE_TEXT if no_real_send else FALSE_TEXT,
        "telegram_real_send_allowed": TRUE_TEXT if real_send_allowed else FALSE_TEXT,
        "production_ready_claim_detected": _claim_detected(payload, ("PRODUCTION_READY", "LIVE_READY")),
        "execution_ready_claim_detected": _claim_detected(payload, ("EXECUTION_READY", "AUTO_SEND_READY", "TELEGRAM_SEND_READY", "SENT")),
        "trading_actions_allowed": FALSE_TEXT,
        "order_action_allowed": FALSE_TEXT,
        "cancel_action_allowed": FALSE_TEXT,
        "rebalance_action_allowed": FALSE_TEXT,
        "account_read_allowed": FALSE_TEXT,
        "position_read_allowed": FALSE_TEXT,
        "historical_data_request_allowed": FALSE_TEXT,
        "manual_only": TRUE_TEXT,
        "research_only": TRUE_TEXT,
        "observation_only": TRUE_TEXT,
        "diagnostic_reason": _safety_diagnostic(reason),
    }
    return row


def build_approval_markdown(row: Dict[str, str]) -> str:
    lines = [
        "# Operator Telegram Approval Gate Report",
        "",
        "## Scope",
        "",
        "- human review gate only",
        "- no Telegram API client, token read, network send, or real send",
        "- no automatic push or background task",
        "",
        "## Gate",
        "",
    ]
    lines.extend(f"- {field}={row[field]}" for field in APPROVAL_FIELDS)
    return "\n".join(lines) + "\n"


def generate_telegram_approval_gate(
    *,
    payload_csv: PathLike = "operator_telegram_dry_run_payload.csv",
    payload_json: PathLike = "operator_telegram_dry_run_payload.json",
    output_csv: PathLike = "operator_telegram_approval_gate.csv",
    output_report: PathLike = "reports/operator_telegram_approval_gate_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_telegram_approval_gate_row(
        payload_csv=payload_csv,
        payload_json=payload_json,
        generated_at=generated_at,
    )
    _write_csv(output_csv, row, APPROVAL_FIELDS)
    _write_markdown(output_report, build_approval_markdown(row))
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 490-493 Telegram dry-run payload and approval gate.")
    subparsers = parser.add_subparsers(dest="command")

    payload = subparsers.add_parser("payload", help="Build Telegram dry-run payload artifacts.")
    payload.add_argument("--base-dir", default=".")
    payload.add_argument("--output-csv", default="operator_telegram_dry_run_payload.csv")
    payload.add_argument("--output-json", default="operator_telegram_dry_run_payload.json")
    payload.add_argument("--output-report", default="reports/operator_telegram_dry_run_payload.md")
    payload.add_argument("--generated-at", default=None)

    gate = subparsers.add_parser("gate", help="Build Telegram manual approval gate artifacts.")
    gate.add_argument("--payload-csv", default="operator_telegram_dry_run_payload.csv")
    gate.add_argument("--payload-json", default="operator_telegram_dry_run_payload.json")
    gate.add_argument("--output-csv", default="operator_telegram_approval_gate.csv")
    gate.add_argument("--output-report", default="reports/operator_telegram_approval_gate_report.md")
    gate.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if args.command == "payload":
        row = generate_telegram_dry_run_payload(
            base_dir=args.base_dir,
            output_csv=args.output_csv,
            output_json=args.output_json,
            output_report=args.output_report,
            generated_at=args.generated_at,
        )
        print("[TELEGRAM_DRY_RUN_PAYLOAD] generated")
        print(
            "telegram_payload_status={}:dashboard_status={}:no_real_send=true:manual_approval_required=true".format(
                row["telegram_payload_status"],
                row["dashboard_status"],
            )
        )
        print("NOTICE: Draft payload only. No Telegram API, token read, network send, or real send.")
        return 0
    if args.command == "gate":
        row = generate_telegram_approval_gate(
            payload_csv=args.payload_csv,
            payload_json=args.payload_json,
            output_csv=args.output_csv,
            output_report=args.output_report,
            generated_at=args.generated_at,
        )
        print("[TELEGRAM_APPROVAL_GATE] generated")
        print(
            "approval_gate_status={}:telegram_payload_status={}:telegram_real_send_allowed=false".format(
                row["approval_gate_status"],
                row["telegram_payload_status"],
            )
        )
        print("NOTICE: Human review gate only. No send is allowed or attempted.")
        return 0
    _build_arg_parser().print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
