from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


PHASE = "Phase 625-632"
ARCHIVE_ID = "US_ONLY_MVP_ARCHIVE_HANDOFF_PACK"
ARCHIVE_HANDOFF_STATUS = "US_ONLY_MVP_ARCHIVE_HANDOFF_PACK_READY"
FINAL_MVP_STATUS = "US_ONLY_READONLY_MONITORING_MVP_READY_WITH_MARKET_DATA_BLOCKED_BY_SUBSCRIPTION"
US_ONLY_SCOPE = "YES"
SYMBOLS_TEXT = "GLD,SLV"
DASHBOARD_ARTIFACT = "dashboard/us_etf_dashboard_readonly.html"
TELEGRAM_PAYLOAD_PREVIEW = "telegram/us_etf_telegram_payload_preview.md"
FINAL_FREEZE_SUMMARY = "Precious_Metals_Monitor_US_Only_MVP_Final_Freeze_Summary.md"
MARKET_DATA_STATUS = "BLOCKED_BY_SUBSCRIPTION"
MARKET_DATA_CLASSIFICATION = "MARKET_DATA_BLOCKED_BY_SUBSCRIPTION"
IBKR_ERROR_CODE = "10089"
NEXT_REVALIDATION_TRIGGER = "SUBSCRIBE_NETWORK_B_OR_ENABLE_DELAYED_DATA_RETRY"
NEXT_DEVELOPMENT_OPTIONS = (
    "NETWORK_B_REVALIDATION,DASHBOARD_UI_ENHANCEMENT,"
    "TELEGRAM_REAL_SEND_GATE,JP_CN_REACTIVATION"
)
JP_STATUS = "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION"
CN_STATUS = "FROZEN_PENDING_DATA_SOURCE_DECISION"
NO_TEXT = "NO"

CSV_FIELDS = (
    "phase",
    "archive_id",
    "section",
    "status",
    "severity",
    "final_mvp_status",
    "us_only_scope",
    "symbols",
    "dashboard_artifact",
    "telegram_payload_preview",
    "final_freeze_summary",
    "market_data_status",
    "market_data_classification",
    "next_revalidation_trigger",
    "operator_action",
    "external_effect",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

FORBIDDEN_ACTIONS = (
    "Do not connect to IBKR.",
    "Do not request market data, historical data, account data, positions, or contract qualification.",
    "Do not place orders, cancel orders, rebalance, or enable automated trading.",
    "Do not perform Telegram real send or read live Telegram secrets.",
    "Do not run network probes or reclassify subscription-blocked data as ready.",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_us_only_mvp_archive_handoff_pack_row(generated_at: Optional[str] = None) -> Dict[str, str]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "archive_id": ARCHIVE_ID,
        "section": "US_ONLY_MVP_ARCHIVE_OPERATOR_HANDOFF_AND_NEXT_ROADMAP",
        "status": ARCHIVE_HANDOFF_STATUS,
        "severity": "INFO_ARCHIVE_HANDOFF",
        "final_mvp_status": FINAL_MVP_STATUS,
        "us_only_scope": US_ONLY_SCOPE,
        "symbols": SYMBOLS_TEXT,
        "dashboard_artifact": DASHBOARD_ARTIFACT,
        "telegram_payload_preview": TELEGRAM_PAYLOAD_PREVIEW,
        "final_freeze_summary": FINAL_FREEZE_SUMMARY,
        "market_data_status": MARKET_DATA_STATUS,
        "market_data_classification": MARKET_DATA_CLASSIFICATION,
        "next_revalidation_trigger": NEXT_REVALIDATION_TRIGGER,
        "operator_action": "REVIEW_LOCAL_ARCHIVE_HANDOFF_ONLY",
        "external_effect": "NONE_LOCAL_ARTIFACT_GENERATION_ONLY",
        "evidence": (
            "Phase_617_624_final_freeze_complete; GLD_SLV_US_only_scope; "
            "dashboard_readonly_artifact_ready; telegram_payload_preview_ready; "
            "PERMISSION_DENIED_IBKR_ERROR_10089_SUBSCRIPTION_REQUIRED_DELAYED_AVAILABLE"
        ),
        "recommendation": NEXT_DEVELOPMENT_OPTIONS,
        "timestamp_utc": timestamp,
    }


def write_archive_handoff_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_archive_handoff_report(row: Dict[str, str]) -> str:
    lines = [
        "# Phase 625-632 US-only MVP Archive Handoff Pack Report",
        "",
        "## Archive Status",
        "",
        f"- archive_handoff_status={row['status']}",
        f"- final_mvp_status={row['final_mvp_status']}",
        f"- us_only_scope={row['us_only_scope']}",
        f"- symbols={row['symbols']}",
        "",
        "## Artifact Map",
        "",
        f"- dashboard_artifact={row['dashboard_artifact']}",
        f"- telegram_payload_preview={row['telegram_payload_preview']}",
        f"- final_freeze_summary={row['final_freeze_summary']}",
        "",
        "## Market Data Limitation",
        "",
        f"- market_data_status={row['market_data_status']}",
        f"- market_data_classification={row['market_data_classification']}",
        f"- ibkr_error_code={IBKR_ERROR_CODE}",
        "- realtime_market_data_verified=NO",
        "- production_ready=NO",
        "",
        "## Safety Boundary",
        "",
        "- trading_enabled=NO",
        "- account_read_enabled=NO",
        "- positions_read_enabled=NO",
        "- telegram_real_send_enabled=NO",
        "- external_effect=NONE_LOCAL_ARTIFACT_GENERATION_ONLY",
        "",
        "## Next Roadmap",
        "",
        f"- next_revalidation_trigger={row['next_revalidation_trigger']}",
        f"- next_development_options={row['recommendation']}",
        f"- timestamp_utc={row['timestamp_utc']}",
    ]
    return "\n".join(lines) + "\n"


def write_archive_handoff_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_archive_handoff_report(row), encoding="utf-8")


def build_archive_handoff_markdown(row: Dict[str, str]) -> str:
    lines = [
        "# Precious Metals Monitor US-only MVP Archive Handoff Pack",
        "",
        "## Final MVP Status",
        "",
        f"- final_mvp_status={row['final_mvp_status']}",
        "- production_ready=NO",
        "- trading_enabled=NO",
        "",
        "## Current Scope",
        "",
        "- Market: US ETF only.",
        "- Symbols: GLD / SLV.",
        "- Mode: read-only monitoring archive and operator handoff.",
        "",
        "## Completed Components",
        "",
        "- Final audit freeze completed in Phase 617-624.",
        "- Read-only dashboard artifact completed.",
        "- Telegram manual-send preview skeleton completed with real send disabled.",
        "- Market data limitation classified as subscription blocked.",
        "",
        "## Current Artifact Map",
        "",
        f"- CSV: operator_us_only_mvp_archive_handoff_pack.csv",
        f"- report: reports/operator_us_only_mvp_archive_handoff_pack_report.md",
        f"- dashboard_artifact={row['dashboard_artifact']}",
        f"- telegram_payload_preview={row['telegram_payload_preview']}",
        f"- final_freeze_summary={row['final_freeze_summary']}",
        "",
        "## Operator Runbook",
        "",
        "- Review this archive pack and the listed local artifacts.",
        "- Treat all outputs as local handoff material only.",
        "- Revalidate market data only after the next trigger is explicitly satisfied.",
        "",
        "## Dashboard Open Instructions",
        "",
        f"- Open local file: {row['dashboard_artifact']}",
        "- Dashboard availability means read-only artifact availability, not production readiness.",
        "",
        "## Telegram Preview Instructions",
        "",
        f"- Review local preview: {row['telegram_payload_preview']}",
        "- Telegram payload preview means message text is prepared, not sent.",
        "- telegram_real_send_enabled=NO",
        "",
        "## Market Data Limitation",
        "",
        f"- market_data_status={row['market_data_status']}",
        f"- market_data_classification={row['market_data_classification']}",
        f"- ibkr_error_code={IBKR_ERROR_CODE}",
        "- realtime_market_data_verified=NO",
        "- The current limitation remains subscription related with delayed data available.",
        "",
        "## Network B Revalidation Path",
        "",
        f"- next_revalidation_trigger={row['next_revalidation_trigger']}",
        "- Revalidation requires a later explicit operator-approved phase.",
        "- Do not infer market data readiness from this archive.",
        "",
        "## JP / CN Frozen Status",
        "",
        f"- jp_status={JP_STATUS}",
        f"- cn_status={CN_STATUS}",
        "",
        "## Safety Boundaries",
        "",
        "- account_read_enabled=NO",
        "- positions_read_enabled=NO",
        "- telegram_real_send_enabled=NO",
        "- production_ready=NO",
        "- external_effect=NONE_LOCAL_ARTIFACT_GENERATION_ONLY",
        "",
        "## Forbidden Actions",
        "",
        *[f"- {action}" for action in FORBIDDEN_ACTIONS],
        "",
        "## Next Development Options",
        "",
        "- NETWORK_B_REVALIDATION",
        "- DASHBOARD_UI_ENHANCEMENT",
        "- TELEGRAM_REAL_SEND_GATE",
        "- JP_CN_REACTIVATION",
        "",
        "## Codex Resume Context",
        "",
        "- latest_merged_phase=Phase 617-624 / US-only MVP final audit freeze",
        "- current_phase=Phase 625-632 / US-only MVP archive handoff pack",
        f"- final_mvp_status={row['final_mvp_status']}",
        "- market_data remains blocked by subscription and is not production ready.",
        "",
        "## Clean Git State Checklist",
        "",
        "- config.yaml remains uncommitted if locally modified.",
        "- ibkr_market_data_api_errors.csv remains untracked and uncommitted if present.",
        "- Commit only Phase 625-632 source, test, CSV, report, and handoff Markdown artifacts.",
        f"- timestamp_utc={row['timestamp_utc']}",
    ]
    return "\n".join(lines) + "\n"


def write_archive_handoff_markdown(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_archive_handoff_markdown(row), encoding="utf-8")


def generate_us_only_mvp_archive_handoff_pack(
    *,
    output_csv: PathLike = "operator_us_only_mvp_archive_handoff_pack.csv",
    output_report: PathLike = "reports/operator_us_only_mvp_archive_handoff_pack_report.md",
    output_handoff: PathLike = "Precious_Metals_Monitor_US_Only_MVP_Archive_Handoff_Pack.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_us_only_mvp_archive_handoff_pack_row(generated_at=generated_at)
    write_archive_handoff_csv(output_csv, row)
    write_archive_handoff_report(output_report, row)
    write_archive_handoff_markdown(output_handoff, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 625-632 US-only MVP archive handoff pack.")
    parser.add_argument("--output-csv", default="operator_us_only_mvp_archive_handoff_pack.csv")
    parser.add_argument("--output-report", default="reports/operator_us_only_mvp_archive_handoff_pack_report.md")
    parser.add_argument("--output-handoff", default="Precious_Metals_Monitor_US_Only_MVP_Archive_Handoff_Pack.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generate_us_only_mvp_archive_handoff_pack(
        output_csv=args.output_csv,
        output_report=args.output_report,
        output_handoff=args.output_handoff,
        generated_at=args.generated_at,
    )
    print("[US_ONLY_MVP_ARCHIVE_HANDOFF_PACK] generated")
    print(f"archive_handoff_status={ARCHIVE_HANDOFF_STATUS}")
    print(f"final_mvp_status={FINAL_MVP_STATUS}")
    print("us_only_scope=YES")
    print("symbols=GLD,SLV")
    print(f"dashboard_artifact={DASHBOARD_ARTIFACT}")
    print(f"telegram_payload_preview={TELEGRAM_PAYLOAD_PREVIEW}")
    print(f"final_freeze_summary={FINAL_FREEZE_SUMMARY}")
    print("market_data_status=BLOCKED_BY_SUBSCRIPTION")
    print("market_data_classification=MARKET_DATA_BLOCKED_BY_SUBSCRIPTION")
    print("ibkr_error_code=10089")
    print("realtime_market_data_verified=NO")
    print("production_ready=NO")
    print("trading_enabled=NO")
    print("account_read_enabled=NO")
    print("positions_read_enabled=NO")
    print("telegram_real_send_enabled=NO")
    print(f"jp_status={JP_STATUS}")
    print(f"cn_status={CN_STATUS}")
    print(f"next_revalidation_trigger={NEXT_REVALIDATION_TRIGGER}")
    print(f"next_development_options={NEXT_DEVELOPMENT_OPTIONS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
