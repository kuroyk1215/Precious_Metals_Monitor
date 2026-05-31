from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


PHASE = "Phase 617-624"
AUDIT_ID = "US_ONLY_MVP_FINAL_AUDIT_FREEZE"
FINAL_MVP_STATUS = "US_ONLY_READONLY_MONITORING_MVP_READY_WITH_MARKET_DATA_BLOCKED_BY_SUBSCRIPTION"
SYMBOLS_TEXT = "GLD,SLV"
MARKET_DATA_STATUS = "BLOCKED_BY_SUBSCRIPTION"
MARKET_DATA_CLASSIFICATION = "MARKET_DATA_BLOCKED_BY_SUBSCRIPTION"
IBKR_ERROR_CODE = "10089"
JP_STATUS = "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION"
CN_STATUS = "FROZEN_PENDING_DATA_SOURCE_DECISION"
NEXT_REVALIDATION_TRIGGER = "SUBSCRIBE_NETWORK_B_OR_ENABLE_DELAYED_DATA_RETRY"
YES_TEXT = "YES"
NO_TEXT = "NO"

CSV_FIELDS = (
    "phase",
    "audit_id",
    "component",
    "status",
    "severity",
    "us_only_scope",
    "symbols",
    "connectivity_verified",
    "contract_qualification_verified",
    "market_data_request_tested",
    "market_data_status",
    "market_data_classification",
    "realtime_market_data_verified",
    "dashboard_ready",
    "telegram_skeleton_ready",
    "telegram_real_send_enabled",
    "jp_status",
    "cn_status",
    "trading_enabled",
    "account_read_enabled",
    "positions_read_enabled",
    "production_ready",
    "external_effect",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

PROHIBITED_ACTIONS = (
    "IBKR connection",
    "market data request",
    "account read",
    "positions read",
    "historical data request",
    "contract qualification",
    "order placement",
    "order cancellation",
    "rebalance",
    "Telegram real send",
    "network probe",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_us_only_mvp_final_audit_freeze_row(generated_at: Optional[str] = None) -> Dict[str, str]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "audit_id": AUDIT_ID,
        "component": "US_ONLY_READONLY_MONITORING_MVP_FINAL_GATE",
        "status": FINAL_MVP_STATUS,
        "severity": "INFO_FREEZE",
        "us_only_scope": YES_TEXT,
        "symbols": SYMBOLS_TEXT,
        "connectivity_verified": YES_TEXT,
        "contract_qualification_verified": YES_TEXT,
        "market_data_request_tested": YES_TEXT,
        "market_data_status": MARKET_DATA_STATUS,
        "market_data_classification": MARKET_DATA_CLASSIFICATION,
        "realtime_market_data_verified": NO_TEXT,
        "dashboard_ready": YES_TEXT,
        "telegram_skeleton_ready": YES_TEXT,
        "telegram_real_send_enabled": NO_TEXT,
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "trading_enabled": NO_TEXT,
        "account_read_enabled": NO_TEXT,
        "positions_read_enabled": NO_TEXT,
        "production_ready": NO_TEXT,
        "external_effect": "NONE_LOCAL_ARTIFACT_GENERATION_ONLY",
        "evidence": (
            "GLD_SLV_only; connectivity_verified_prior_phase; contract_qualification_verified_prior_phase; "
            "PERMISSION_DENIED / IBKR_ERROR_10089 / SUBSCRIPTION_REQUIRED / DELAYED_AVAILABLE; "
            "dashboard_readonly_artifact_ready; telegram_manual_send_skeleton_ready; JP_CN_frozen"
        ),
        "recommendation": NEXT_REVALIDATION_TRIGGER,
        "timestamp_utc": timestamp,
    }


def write_us_only_mvp_final_audit_freeze_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_us_only_mvp_final_audit_freeze_report(row: Dict[str, str]) -> str:
    lines = [
        "# Phase 617-624 US-only MVP Final Audit Freeze",
        "",
        "## Final Decision",
        "",
        f"- final_mvp_status={row['status']}",
        "- production_ready=NO",
        "- trading_enabled=NO",
        "",
        "## Scope Boundary",
        "",
        "- US-only read-only monitoring MVP.",
        "- Covered symbols: GLD / SLV.",
        "- JP and CN remain frozen.",
        "",
        "## US-only MVP Components",
        "",
        "- connectivity_verified=YES",
        "- contract_qualification_verified=YES",
        "- market_data_request_tested=YES",
        "- dashboard_ready=YES",
        "- telegram_skeleton_ready=YES",
        "",
        "## GLD / SLV Status",
        "",
        f"- symbols={row['symbols']}",
        f"- market_data_status={row['market_data_status']}",
        f"- market_data_classification={row['market_data_classification']}",
        "",
        "## Market Data Limitation",
        "",
        f"- ibkr_error_code={IBKR_ERROR_CODE}",
        "- subscription_required=YES",
        "- delayed_available=YES",
        "- realtime_market_data_verified=NO",
        "- market_data_blocked_by_subscription is not market_data_ready.",
        "",
        "## Dashboard Status",
        "",
        "- dashboard_ready=YES",
        "- dashboard_ready means read-only artifact ready, not production ready.",
        "",
        "## Telegram Skeleton Status",
        "",
        "- telegram_skeleton_ready=YES",
        "- telegram_real_send_enabled=NO",
        "- telegram_payload_ready is not telegram_sent.",
        "",
        "## JP / CN Frozen Status",
        "",
        f"- jp_status={row['jp_status']}",
        f"- cn_status={row['cn_status']}",
        "",
        "## Explicitly Prohibited Actions",
        "",
        *[f"- {action}" for action in PROHIBITED_ACTIONS],
        "",
        "## Residual Risks",
        "",
        "- Realtime US ETF market data remains blocked by subscription entitlement.",
        "- Delayed availability requires a future separately approved retry path.",
        "- This freeze does not authorize automated or production trading.",
        "",
        "## Operator Handoff",
        "",
        "- Use the read-only dashboard and local Telegram skeleton artifacts for review only.",
        "- Do not run live send, account, positions, data, or trading actions from this phase.",
        "",
        "## Future Revalidation Path",
        "",
        f"- next_revalidation_trigger={NEXT_REVALIDATION_TRIGGER}",
        f"- timestamp_utc={row['timestamp_utc']}",
    ]
    return "\n".join(lines) + "\n"


def write_us_only_mvp_final_audit_freeze_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_us_only_mvp_final_audit_freeze_report(row), encoding="utf-8")


def build_final_freeze_summary(row: Dict[str, str]) -> str:
    lines = [
        "# Precious Metals Monitor US-only MVP Final Freeze Summary",
        "",
        "## Final Status",
        "",
        f"- final_mvp_status={row['status']}",
        "- US-only read-only monitoring MVP is frozen with market data blocked by subscription.",
        "",
        "## What Is Completed",
        "",
        "- GLD / SLV scope is finalized.",
        "- Connectivity and contract qualification are recorded as previously verified.",
        "- Dashboard read-only artifact is ready.",
        "- Telegram manual-send skeleton is ready with real send disabled.",
        "",
        "## What Is Not Completed",
        "",
        "- Realtime market data is not verified.",
        "- Production readiness is not granted.",
        "- Trading, account reads, and positions reads remain disabled.",
        "",
        "## Current Market Data Limitation",
        "",
        f"- market_data_status={row['market_data_status']}",
        f"- market_data_classification={row['market_data_classification']}",
        f"- ibkr_error_code={IBKR_ERROR_CODE}",
        "- subscription_required=YES",
        "- delayed_available=YES",
        "",
        "## Safety Boundaries",
        "",
        "- trading_enabled=NO",
        "- account_read_enabled=NO",
        "- positions_read_enabled=NO",
        "- telegram_real_send_enabled=NO",
        "- production_ready=NO",
        "- external_effect=NONE_LOCAL_ARTIFACT_GENERATION_ONLY",
        "",
        "## Operator Workflow",
        "",
        "- Review local CSV and Markdown artifacts only.",
        "- Treat dashboard and Telegram outputs as read-only handoff material.",
        "- Keep JP / CN frozen until a later explicit decision.",
        "",
        "## Future Upgrade Path",
        "",
        "- Subscribe Network B or add an explicitly approved delayed-data retry path.",
        "- Revalidate market data before any production readiness statement.",
        "",
        "## Next Revalidation Trigger",
        "",
        f"- {NEXT_REVALIDATION_TRIGGER}",
        f"- timestamp_utc={row['timestamp_utc']}",
    ]
    return "\n".join(lines) + "\n"


def write_final_freeze_summary(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_final_freeze_summary(row), encoding="utf-8")


def generate_us_only_mvp_final_audit_freeze(
    *,
    output_csv: PathLike = "operator_us_only_mvp_final_audit_freeze.csv",
    output_report: PathLike = "reports/operator_us_only_mvp_final_audit_freeze_report.md",
    output_summary: PathLike = "Precious_Metals_Monitor_US_Only_MVP_Final_Freeze_Summary.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_us_only_mvp_final_audit_freeze_row(generated_at=generated_at)
    write_us_only_mvp_final_audit_freeze_csv(output_csv, row)
    write_us_only_mvp_final_audit_freeze_report(output_report, row)
    write_final_freeze_summary(output_summary, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 617-624 US-only MVP final audit freeze artifacts.")
    parser.add_argument("--output-csv", default="operator_us_only_mvp_final_audit_freeze.csv")
    parser.add_argument("--output-report", default="reports/operator_us_only_mvp_final_audit_freeze_report.md")
    parser.add_argument("--output-summary", default="Precious_Metals_Monitor_US_Only_MVP_Final_Freeze_Summary.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generate_us_only_mvp_final_audit_freeze(
        output_csv=args.output_csv,
        output_report=args.output_report,
        output_summary=args.output_summary,
        generated_at=args.generated_at,
    )
    print("[US_ONLY_MVP_FINAL_AUDIT_FREEZE] generated")
    print(f"final_mvp_status={FINAL_MVP_STATUS}")
    print("us_only_scope=YES")
    print("symbols=GLD,SLV")
    print("connectivity_verified=YES")
    print("contract_qualification_verified=YES")
    print("market_data_request_tested=YES")
    print("market_data_status=BLOCKED_BY_SUBSCRIPTION")
    print("market_data_classification=MARKET_DATA_BLOCKED_BY_SUBSCRIPTION")
    print("ibkr_error_code=10089")
    print("subscription_required=YES")
    print("delayed_available=YES")
    print("realtime_market_data_verified=NO")
    print("dashboard_ready=YES")
    print("telegram_skeleton_ready=YES")
    print("telegram_real_send_enabled=NO")
    print("jp_status=FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION")
    print("cn_status=FROZEN_PENDING_DATA_SOURCE_DECISION")
    print("trading_enabled=NO")
    print("account_read_enabled=NO")
    print("positions_read_enabled=NO")
    print("production_ready=NO")
    print("external_connections_attempted=NO")
    print(f"next_revalidation_trigger={NEXT_REVALIDATION_TRIGGER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
