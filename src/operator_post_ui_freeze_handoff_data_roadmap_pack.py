from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

from src.operator_dashboard_ui_static_visual_freeze_pack import (
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    EXTERNAL_EFFECT,
    IBKR_ERROR_CODE,
    JP_STATUS,
    MARKET_DATA_CLASSIFICATION,
    MARKET_DATA_STATUS,
    OPERATOR_TIMELINE,
    STATUS_SNAPSHOT,
    ARTIFACTS as FROZEN_ARTIFACTS,
    build_operator_timeline as build_frozen_operator_timeline,
)


PHASE = "Phase 705-720"
STATUS = "POST_UI_FREEZE_HANDOFF_DATA_ROADMAP_READY"
POST_UI_FREEZE_STATUS = "POST_UI_FREEZE_OPERATOR_HANDOFF_READY"
ROADMAP_STATUS = "NEXT_ROADMAP_READY"
MARKET_DATA_SOURCE_DECISION_STATUS = "MARKET_DATA_SOURCE_DECISION_FRAMEWORK_READY"
UI_GENERATION = "V7_HIGH_TECH_TRADING_VISUAL_FROZEN"
UI_FREEZE_STATUS = "DASHBOARD_UI_STATIC_VISUAL_FREEZE_READY"
LATEST_MAIN_COMMIT = "3909b6c"
LATEST_MERGED_PR = 225
NO_TEXT = "NO"
YES_TEXT = "YES"
CN_STATUS = "FROZEN_PENDING_DATA_SOURCE_DECISION"
SYMBOLS_TEXT = "GLD / SLV"

POST_UI_FREEZE_HANDOFF_SNAPSHOT = "dashboard/data/post_ui_freeze_handoff_snapshot.json"
NEXT_ROADMAP_SNAPSHOT = "dashboard/data/next_roadmap_snapshot.json"
MARKET_DATA_SOURCE_DECISION_SNAPSHOT = "dashboard/data/market_data_source_decision_snapshot.json"
MARKET_SCOPE_STATUS_SNAPSHOT = "dashboard/data/market_scope_status_snapshot.json"
OPERATOR_NEXT_ACTIONS_SNAPSHOT = "dashboard/data/operator_next_actions_snapshot.json"
OUTPUT_CSV = "operator_post_ui_freeze_handoff_data_roadmap_pack.csv"
OUTPUT_REPORT = "reports/operator_post_ui_freeze_handoff_data_roadmap_pack_report.md"
OUTPUT_PACK = "Precious_Metals_Monitor_Post_UI_Freeze_Handoff_Data_Roadmap_Pack.md"

NEW_ARTIFACTS = (
    POST_UI_FREEZE_HANDOFF_SNAPSHOT,
    NEXT_ROADMAP_SNAPSHOT,
    MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
    MARKET_SCOPE_STATUS_SNAPSHOT,
    OPERATOR_NEXT_ACTIONS_SNAPSHOT,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)
ARTIFACTS = tuple(dict.fromkeys((*FROZEN_ARTIFACTS, *NEW_ARTIFACTS)))
CSV_FIELDS = (
    "phase",
    "status",
    "post_ui_freeze_status",
    "roadmap_status",
    "market_data_source_decision_status",
    "ui_generation",
    "ui_freeze_status",
    "visual_freeze_status",
    "ui_qa_status",
    "visual_regression_guard_status",
    "next_primary_track",
    "next_secondary_track",
    "market_data_status",
    "market_data_classification",
    "ibkr_error_code",
    "realtime_market_data_verified",
    "production_ready",
    "trading_enabled",
    "account_read_enabled",
    "positions_read_enabled",
    "historical_data_enabled",
    "telegram_real_send_enabled",
    "external_effect",
    "jp_status",
    "cn_status",
    "symbols",
    "generated_at_utc",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: PathLike, payload: Dict[str, object]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: PathLike, text: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def _artifact_category(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".html":
        return "HTML"
    if suffix == ".css":
        return "CSS"
    if suffix == ".json":
        return "JSON"
    if suffix == ".csv":
        return "CSV"
    return "REPORT" if path.startswith("reports/") else "PACK"


def _artifact_local_href(path: str) -> str:
    return path.replace("dashboard/", "", 1) if path.startswith("dashboard/") else f"../{path}"


def build_status_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": STATUS,
        "post_ui_freeze_status": POST_UI_FREEZE_STATUS,
        "roadmap_status": ROADMAP_STATUS,
        "market_data_source_decision_status": MARKET_DATA_SOURCE_DECISION_STATUS,
        "ui_generation": UI_GENERATION,
        "ui_freeze_status": UI_FREEZE_STATUS,
        "visual_freeze_status": "STATIC_VISUAL_BASELINE_FROZEN",
        "ui_qa_status": "STATIC_UI_QA_PASS",
        "visual_regression_guard_status": "VISUAL_REGRESSION_GUARD_READY",
        "next_primary_track": "MARKET_DATA_SOURCE_DECISION",
        "next_secondary_track": "US_GLD_SLV_DATA_ADAPTER_PLAN",
        "interaction_mode": "STATIC_HTML_CSS_ONLY",
        "javascript_required": NO_TEXT,
        "static_mode": "LOCAL_STATIC_ONLY",
        "market_data_status": MARKET_DATA_STATUS,
        "market_data_classification": MARKET_DATA_CLASSIFICATION,
        "ibkr_error_code": IBKR_ERROR_CODE,
        "subscription_required": YES_TEXT,
        "delayed_available": YES_TEXT,
        "realtime_market_data_verified": NO_TEXT,
        "production_ready": NO_TEXT,
        "trading_enabled": NO_TEXT,
        "account_read_enabled": NO_TEXT,
        "positions_read_enabled": NO_TEXT,
        "historical_data_enabled": NO_TEXT,
        "telegram_real_send_enabled": NO_TEXT,
        "external_effect": EXTERNAL_EFFECT,
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "symbols": SYMBOLS_TEXT,
        "generated_at_utc": timestamp,
    }


def build_post_ui_freeze_handoff_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": POST_UI_FREEZE_STATUS,
        "latest_main_commit": LATEST_MAIN_COMMIT,
        "latest_merged_pr": LATEST_MERGED_PR,
        "frozen_ui_generation": UI_GENERATION,
        "frozen_ui_status": UI_FREEZE_STATUS,
        "handoff_purpose": "LOCK_UI_BASELINE_AND_ROUTE_NEXT_DEVELOPMENT",
        "dashboard_open_commands": [
            "open dashboard/index.html",
            "python3 main.py --dashboard-high-tech-trading-visual-rebuild-pack",
            "python3 main.py --dashboard-ui-static-visual-freeze-pack",
        ],
        "generated_artifact_warning": "RUNNING_GENERATORS_REFRESHES_GENERATED_AT_UTC",
        "restore_after_viewing_required": "YES_IF_DASHBOARD_ARTIFACTS_MODIFIED",
        "allowed_local_residue": [
            "M config.yaml",
            "?? ibkr_market_data_api_errors.csv",
        ],
        "forbidden_commit_files": [
            "config.yaml",
            "ibkr_market_data_api_errors.csv",
        ],
        "external_effect": EXTERNAL_EFFECT,
        "generated_at_utc": timestamp,
    }


def build_next_roadmap_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": ROADMAP_STATUS,
        "roadmap_mode": "POST_UI_FREEZE_DEVELOPMENT_SEQUENCE",
        "recommended_sequence": [
            "Phase 721-728 Market Data Source Decision Execution Pack",
            "Phase 729-736 US GLD / SLV Data Source Adapter Plan",
            "Phase 737-744 Watchlist Expansion Policy Pack",
            "Phase 745-752 Telegram Manual Packet Enhancement Pack",
            "Phase 753-760 JP Market Data Source Decision Pack",
            "Phase 761-768 CN Market Data Source Decision Pack",
        ],
        "priority_tracks": [
            "MARKET_DATA_SOURCE_DECISION",
            "US_GLD_SLV_FIRST",
            "WATCHLIST_EXPANSION_AFTER_DATA_SOURCE",
            "JP_CN_REMAIN_FROZEN_UNTIL_SOURCE_DECISION",
        ],
        "not_recommended_now": [
            "MORE_UI_REDESIGN",
            "REALTIME_MONITORING_BEFORE_DATA_SOURCE_DECISION",
            "JP_CN_LIVE_MONITOR_BEFORE_DATA_SOURCE_DECISION",
            "AUTO_TRADING",
            "ACCOUNT_POSITION_READER",
        ],
        "generated_at_utc": timestamp,
    }


def build_market_data_source_decision_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": MARKET_DATA_SOURCE_DECISION_STATUS,
        "current_blocker": "IBKR_ERROR_10089_SUBSCRIPTION_REQUIRED",
        "current_market_data_status": MARKET_DATA_STATUS,
        "realtime_market_data_verified": NO_TEXT,
        "delayed_available": YES_TEXT,
        "source_options": [
            "IBKR_SUBSCRIBE_NETWORK_B_ARCA",
            "FREE_DELAYED_PUBLIC_SOURCE",
            "MANUAL_CSV_SOURCE",
            "PAID_MARKET_DATA_API",
            "HYBRID_SOURCE_ROUTER",
        ],
        "decision_criteria": [
            "COST",
            "RELIABILITY",
            "TERMS_OF_USE",
            "UPDATE_FREQUENCY",
            "SYMBOL_COVERAGE",
            "JP_CN_FUTURE_EXTENSION",
            "LOCAL_STATIC_COMPATIBILITY",
            "NO_ACCOUNT_READ_REQUIRED",
            "NO_TRADING_PERMISSION_REQUIRED",
        ],
        "recommended_initial_path": "DECIDE_US_GLD_SLV_SOURCE_FIRST",
        "ibkr_subscription_decision_required": YES_TEXT,
        "source_connection_implemented": NO_TEXT,
        "live_market_data_enabled": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_market_scope_status_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "MARKET_SCOPE_STATUS_LOCKED",
        "markets": {
            "US": {
                "scope": "GLD_SLV_ONLY",
                "status": "READONLY_FRAMEWORK_READY_MARKET_DATA_BLOCKED",
                "blocker": "IBKR_ERROR_10089_SUBSCRIPTION_REQUIRED",
                "next_step": "MARKET_DATA_SOURCE_DECISION",
            },
            "JP": {
                "scope": "FROZEN",
                "status": JP_STATUS,
                "next_step": "DEFER_UNTIL_US_SOURCE_DECISION",
            },
            "CN": {
                "scope": "FROZEN",
                "status": CN_STATUS,
                "next_step": "DEFER_UNTIL_SOURCE_POLICY",
            },
        },
        "generated_at_utc": timestamp,
    }


def build_operator_next_actions_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "OPERATOR_NEXT_ACTIONS_READY",
        "immediate_next_actions": [
            "Review UI freeze status",
            "Choose next track: market data source decision",
            "Decide whether IBKR Network B / ARCA subscription is acceptable",
            "Compare public delayed data source vs manual CSV vs paid API",
            "Keep JP / CN frozen until source policy is defined",
        ],
        "operator_commands": [
            "python3 main.py --post-ui-freeze-handoff-data-roadmap-pack",
            "open dashboard/index.html",
            "git status --short",
        ],
        "blocked_actions": [
            "IBKR_CONNECT",
            "MARKET_DATA_REQUEST",
            "HISTORICAL_DATA_REQUEST",
            "ACCOUNT_READ",
            "POSITION_READ",
            "CONTRACT_QUALIFICATION",
            "ORDER_SUBMIT",
            "ORDER_CANCEL",
            "REBALANCE",
            "TELEGRAM_REAL_SEND",
        ],
        "generated_at_utc": timestamp,
    }


def build_build_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "latest_main_commit": LATEST_MAIN_COMMIT,
        "latest_merged_pr": LATEST_MERGED_PR,
        "phase": PHASE,
        "status": STATUS,
        "ui_generation": UI_GENERATION,
        "production_ready": NO_TEXT,
        "trading_enabled": NO_TEXT,
        "external_effect": EXTERNAL_EFFECT,
        "generated_at_utc": timestamp,
    }


def build_operator_timeline(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    timeline = build_frozen_operator_timeline(timestamp)["timeline"]
    timeline.append(
        {
            "phase": PHASE,
            "theme": "Post-UI Freeze Handoff / 数据源路线图",
            "status": STATUS,
            "external_effect": EXTERNAL_EFFECT,
        },
    )
    return {"timeline": timeline, "generated_at_utc": timestamp}


def build_artifact_manifest(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": STATUS,
        "external_effect": EXTERNAL_EFFECT,
        "artifacts": [
            {
                "artifact_path": path,
                "type": Path(path).suffix.lstrip(".").upper() or "PACK",
                "category": _artifact_category(path),
                "icon_token": f"{_artifact_category(path)}_LOCAL",
                "local_href": _artifact_local_href(path),
                "external_effect": EXTERNAL_EFFECT,
            }
            for path in ARTIFACTS
        ],
        "generated_at_utc": timestamp,
    }


def _status_row(status: Dict[str, object]) -> Dict[str, str]:
    return {field: str(status[field]) for field in CSV_FIELDS}


def write_pack_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_report(row: Dict[str, str]) -> str:
    lines = [
        "# Phase 705-720 Post-UI Freeze Handoff Data Roadmap Pack Report",
        "",
        "## Status",
        "",
        *[f"- {field}={row[field]}" for field in CSV_FIELDS],
        "",
        "## Boundary",
        "",
        "- post-UI freeze operator handoff ready",
        "- next roadmap ready",
        "- market data source decision framework ready",
        "- V7 high-tech Chinese trading dashboard baseline remains frozen",
        "- no dashboard/index.html changes",
        "- no dashboard/assets/style.css changes",
        "- no real market data",
        "- no source connection implemented",
        "- no IBKR connection",
        "- no market data request",
        "- no historical data request",
        "- no account or position read",
        "- no contract qualification",
        "- no trading",
        "- no Telegram real send",
        "- no directional trading signal",
        "- no target, stop, or take-profit fields",
        "- no live price fields",
        "- market data remains BLOCKED_BY_SUBSCRIPTION / IBKR_ERROR_10089",
        "- GLD / SLV only",
        "- JP / CN remain frozen",
        "- next recommended track: Market Data Source Decision Execution Pack",
    ]
    return "\n".join(lines) + "\n"


def build_pack(row: Dict[str, str]) -> str:
    lines = [
        "# Precious Metals Monitor Post-UI Freeze Handoff Data Roadmap Pack",
        "",
        f"- phase={row['phase']}",
        f"- status={row['status']}",
        f"- post_ui_freeze_status={row['post_ui_freeze_status']}",
        f"- roadmap_status={row['roadmap_status']}",
        f"- market_data_source_decision_status={row['market_data_source_decision_status']}",
        f"- ui_generation={row['ui_generation']}",
        "- frozen dashboard baseline is the stable handoff point",
        "- next primary track is market data source decision",
        "- no source connection implemented",
        "- no external effect beyond local artifact generation",
        f"- market data remains {row['market_data_status']} / IBKR_ERROR_{row['ibkr_error_code']}",
        "- GLD / SLV only",
        "- JP / CN remain frozen",
    ]
    return "\n".join(lines) + "\n"


def generate_post_ui_freeze_handoff_data_roadmap_pack(
    *,
    output_status_snapshot: PathLike = STATUS_SNAPSHOT,
    output_post_ui_freeze_handoff_snapshot: PathLike = POST_UI_FREEZE_HANDOFF_SNAPSHOT,
    output_next_roadmap_snapshot: PathLike = NEXT_ROADMAP_SNAPSHOT,
    output_market_data_source_decision_snapshot: PathLike = MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
    output_market_scope_status_snapshot: PathLike = MARKET_SCOPE_STATUS_SNAPSHOT,
    output_operator_next_actions_snapshot: PathLike = OPERATOR_NEXT_ACTIONS_SNAPSHOT,
    output_build_snapshot: PathLike = BUILD_SNAPSHOT,
    output_operator_timeline: PathLike = OPERATOR_TIMELINE,
    output_artifact_manifest: PathLike = ARTIFACT_MANIFEST,
    output_csv: PathLike = OUTPUT_CSV,
    output_report: PathLike = OUTPUT_REPORT,
    output_pack: PathLike = OUTPUT_PACK,
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    timestamp = generated_at or _now_timestamp()
    status = build_status_snapshot(timestamp)
    row = _status_row(status)

    _write_json(output_status_snapshot, status)
    _write_json(output_post_ui_freeze_handoff_snapshot, build_post_ui_freeze_handoff_snapshot(timestamp))
    _write_json(output_next_roadmap_snapshot, build_next_roadmap_snapshot(timestamp))
    _write_json(output_market_data_source_decision_snapshot, build_market_data_source_decision_snapshot(timestamp))
    _write_json(output_market_scope_status_snapshot, build_market_scope_status_snapshot(timestamp))
    _write_json(output_operator_next_actions_snapshot, build_operator_next_actions_snapshot(timestamp))
    _write_json(output_build_snapshot, build_build_snapshot(timestamp))
    _write_json(output_operator_timeline, build_operator_timeline(timestamp))
    _write_json(output_artifact_manifest, build_artifact_manifest(timestamp))
    write_pack_csv(output_csv, row)
    _write_text(output_report, build_report(row))
    _write_text(output_pack, build_pack(row))
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 705-720 post-UI freeze handoff data roadmap pack.")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_post_ui_freeze_handoff_data_roadmap_pack(generated_at=args.generated_at)
    print("[POST_UI_FREEZE_HANDOFF_DATA_ROADMAP_PACK] generated")
    print(f"status={row['status']}")
    print(f"post_ui_freeze_status={row['post_ui_freeze_status']}")
    print(f"roadmap_status={row['roadmap_status']}")
    print(f"market_data_source_decision_status={row['market_data_source_decision_status']}")
    print(f"ui_generation={row['ui_generation']}")
    print(f"ui_freeze_status={row['ui_freeze_status']}")
    print(f"market_data_status={row['market_data_status']}")
    print(f"market_data_classification={row['market_data_classification']}")
    print(f"ibkr_error_code={row['ibkr_error_code']}")
    print(f"realtime_market_data_verified={row['realtime_market_data_verified']}")
    print(f"production_ready={row['production_ready']}")
    print(f"trading_enabled={row['trading_enabled']}")
    print(f"account_read_enabled={row['account_read_enabled']}")
    print(f"positions_read_enabled={row['positions_read_enabled']}")
    print(f"historical_data_enabled={row['historical_data_enabled']}")
    print(f"telegram_real_send_enabled={row['telegram_real_send_enabled']}")
    print(f"external_effect={row['external_effect']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
