from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


PHASE = "Phase 601-616"
TELEGRAM_PACKET_ID = "US_ETF_TELEGRAM_MANUAL_SEND_SKELETON"
TELEGRAM_SKELETON_STATUS = "TELEGRAM_MANUAL_SEND_SKELETON_READY"
TELEGRAM_PERMISSION_DECISION = "DENIED"
TELEGRAM_GUARD_STATUS = "TELEGRAM_MANUAL_SEND_GUARD_READY"
MARKET_DATA_STATUS = "BLOCKED_BY_SUBSCRIPTION"
MARKET_DATA_CLASSIFICATION = "MARKET_DATA_BLOCKED_BY_SUBSCRIPTION"
IBKR_ERROR_CODE = "10089"
SOURCE_DASHBOARD = "dashboard/us_etf_dashboard_readonly.html"
SOURCE_OPERATOR_PACKET = "operator_us_etf_operator_packet_artifact_integration.csv"
PAYLOAD_PREVIEW = "telegram/us_etf_telegram_payload_preview.md"
NEXT_ACTION = "SUBSCRIBE_NETWORK_B_OR_CONTINUE_FRAMEWORK_ONLY_MVP"
SYMBOLS_TEXT = "GLD,SLV"
YES_TEXT = "YES"
NO_TEXT = "NO"

CSV_FIELDS = (
    "phase",
    "telegram_packet_id",
    "source_dashboard",
    "source_operator_packet",
    "symbols",
    "market_data_status",
    "market_data_classification",
    "telegram_permission_decision",
    "telegram_guard_status",
    "telegram_payload_ready",
    "telegram_real_send_enabled",
    "telegram_real_send_attempted",
    "operator_approval_required",
    "operator_approved",
    "archive_ready",
    "external_effect",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

PROHIBITED_ACTIONS = (
    "ibkr_connection=NO",
    "market_data_request=NO",
    "account_read=NO",
    "positions_read=NO",
    "historical_data_request=NO",
    "contract_qualification=NO",
    "order_submit=NO",
    "cancel_order=NO",
    "rebalance=NO",
    "telegram_real_send=NO",
    "network_probe=NO",
    "telegram_token_read=NO",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_telegram_manual_send_skeleton_row(generated_at: Optional[str] = None) -> Dict[str, str]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "telegram_packet_id": TELEGRAM_PACKET_ID,
        "source_dashboard": SOURCE_DASHBOARD,
        "source_operator_packet": SOURCE_OPERATOR_PACKET,
        "symbols": SYMBOLS_TEXT,
        "market_data_status": MARKET_DATA_STATUS,
        "market_data_classification": MARKET_DATA_CLASSIFICATION,
        "telegram_permission_decision": TELEGRAM_PERMISSION_DECISION,
        "telegram_guard_status": TELEGRAM_GUARD_STATUS,
        "telegram_payload_ready": YES_TEXT,
        "telegram_real_send_enabled": NO_TEXT,
        "telegram_real_send_attempted": NO_TEXT,
        "operator_approval_required": YES_TEXT,
        "operator_approved": NO_TEXT,
        "archive_ready": YES_TEXT,
        "external_effect": "NONE_LOCAL_ARTIFACT_GENERATION_ONLY",
        "evidence": (
            "US_ETF_dashboard_readonly_source; GLD_SLV_only; "
            "PERMISSION_DENIED / IBKR_ERROR_10089 / SUBSCRIPTION_REQUIRED / DELAYED_AVAILABLE; "
            "telegram_permission_denied; manual_send_guard_ready; no_network_no_real_send"
        ),
        "recommendation": NEXT_ACTION,
        "timestamp_utc": timestamp,
    }


def write_telegram_manual_send_skeleton_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_telegram_payload_preview(row: Dict[str, str]) -> str:
    lines = [
        "# US ETF Telegram Payload Preview",
        "",
        "**Status:** Telegram-ready payload preview only. This is not a sent message.",
        "",
        "## GLD / SLV Current State",
        "",
        "- Symbols: GLD / SLV",
        f"- Market data status: {row['market_data_status']}",
        f"- Market data classification: {row['market_data_classification']}",
        f"- IBKR error code: {IBKR_ERROR_CODE}",
        "- Market data blocked by subscription / IBKR 10089",
        "- JP / CN frozen",
        "",
        "## Scope",
        "",
        "- read-only",
        "- no trading",
        "- no account reads",
        "- no positions reads",
        "- no historical data requests",
        "- no contract qualification",
        "- no network access",
        "- no Telegram token read",
        "- no real Telegram send",
        "- no chat identifier included",
        "",
        "## Operator Review",
        "",
        "- operator review required",
        "- operator approved: NO",
        f"- next action: {NEXT_ACTION}",
        "",
        "## Archive",
        "",
        f"- source dashboard: {row['source_dashboard']}",
        f"- source operator packet: {row['source_operator_packet']}",
        f"- timestamp UTC: {row['timestamp_utc']}",
    ]
    return "\n".join(lines) + "\n"


def write_telegram_payload_preview(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_telegram_payload_preview(row), encoding="utf-8")


def build_telegram_manual_send_skeleton_report(row: Dict[str, str]) -> str:
    lines = [
        "# Phase 601-616 Telegram Manual Send Skeleton",
        "",
        "## Final Telegram Skeleton Status",
        "",
        f"- telegram_skeleton_status={TELEGRAM_SKELETON_STATUS}",
        f"- symbols={SYMBOLS_TEXT}",
        f"- market_data_status={MARKET_DATA_STATUS}",
        f"- market_data_classification={MARKET_DATA_CLASSIFICATION}",
        f"- ibkr_error_code={IBKR_ERROR_CODE}",
        "",
        "## Scope Boundary",
        "",
        "- US-only GLD / SLV operator packet and dashboard artifact output",
        "- local CSV, Markdown report, and Markdown payload preview only",
        "- JP / CN remain frozen",
        "",
        "## Telegram Permission Gate",
        "",
        f"- telegram_permission_decision={TELEGRAM_PERMISSION_DECISION}",
        "- permission reason: manual-send skeleton is archive-ready but real send is denied",
        "",
        "## Manual Send Guard",
        "",
        f"- telegram_guard_status={TELEGRAM_GUARD_STATUS}",
        "- telegram_payload_ready=YES",
        "- telegram_real_send_enabled=NO",
        "- telegram_real_send_attempted=NO",
        "",
        "## Payload Preview",
        "",
        f"- preview={PAYLOAD_PREVIEW}",
        "- Markdown payload text only",
        "- contains GLD / SLV blocked subscription state and operator review requirement",
        "",
        "## Archive Skeleton",
        "",
        "- archive_ready=YES",
        "- external_effect=NONE_LOCAL_ARTIFACT_GENERATION_ONLY",
        f"- source_dashboard={SOURCE_DASHBOARD}",
        f"- source_operator_packet={SOURCE_OPERATOR_PACKET}",
        "",
        "## Operator Approval Workflow",
        "",
        "- operator_approval_required=YES",
        "- operator_approved=NO",
        f"- recommendation={NEXT_ACTION}",
        "",
        "## Explicitly Prohibited Actions",
        "",
        *[f"- {action}" for action in PROHIBITED_ACTIONS],
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_telegram_manual_send_skeleton.csv",
        "- report=reports/operator_telegram_manual_send_skeleton_report.md",
        f"- payload_preview={PAYLOAD_PREVIEW}",
        f"- timestamp_utc={row['timestamp_utc']}",
        "",
        "## Residual Risks",
        "",
        "- Telegram readiness means local payload preview readiness only",
        "- US ETF realtime market data remains blocked by subscription permission",
        "- Delayed availability does not promote the workflow to production readiness",
        "",
        "## Next Phase Preconditions",
        "",
        f"- {NEXT_ACTION}",
        "- require a separate explicit approval path before any real Telegram send implementation",
    ]
    return "\n".join(lines) + "\n"


def write_telegram_manual_send_skeleton_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_telegram_manual_send_skeleton_report(row), encoding="utf-8")


def generate_telegram_manual_send_skeleton(
    *,
    output_csv: PathLike = "operator_telegram_manual_send_skeleton.csv",
    output_report: PathLike = "reports/operator_telegram_manual_send_skeleton_report.md",
    output_payload_preview: PathLike = PAYLOAD_PREVIEW,
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_telegram_manual_send_skeleton_row(generated_at=generated_at)
    write_telegram_manual_send_skeleton_csv(output_csv, row)
    write_telegram_manual_send_skeleton_report(output_report, row)
    write_telegram_payload_preview(output_payload_preview, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 601-616 Telegram manual-send skeleton artifacts.")
    parser.add_argument("--output-csv", default="operator_telegram_manual_send_skeleton.csv")
    parser.add_argument("--output-report", default="reports/operator_telegram_manual_send_skeleton_report.md")
    parser.add_argument("--output-payload-preview", default=PAYLOAD_PREVIEW)
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generate_telegram_manual_send_skeleton(
        output_csv=args.output_csv,
        output_report=args.output_report,
        output_payload_preview=args.output_payload_preview,
        generated_at=args.generated_at,
    )
    print("[TELEGRAM_MANUAL_SEND_SKELETON] generated")
    print(f"telegram_skeleton_status={TELEGRAM_SKELETON_STATUS}")
    print(f"telegram_permission_decision={TELEGRAM_PERMISSION_DECISION}")
    print(f"telegram_guard_status={TELEGRAM_GUARD_STATUS}")
    print("telegram_payload_ready=YES")
    print("telegram_archive_ready=YES")
    print("telegram_real_send_enabled=NO")
    print("telegram_real_send_attempted=NO")
    print("operator_approval_required=YES")
    print("operator_approved=NO")
    print(f"symbols={SYMBOLS_TEXT}")
    print(f"market_data_status={MARKET_DATA_STATUS}")
    print(f"market_data_classification={MARKET_DATA_CLASSIFICATION}")
    print(f"ibkr_error_code={IBKR_ERROR_CODE}")
    print(f"dashboard_source={SOURCE_DASHBOARD}")
    print("next_phase_final_audit_freeze_candidate=YES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
