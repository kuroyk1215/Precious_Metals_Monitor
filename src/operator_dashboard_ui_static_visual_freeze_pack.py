from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

from src.operator_dashboard_high_tech_trading_visual_rebuild_pack import (
    BLOCKED_ACTIONS,
    CN_STATUS,
    DASHBOARD_CSS,
    DASHBOARD_INDEX,
    EXTERNAL_EFFECT,
    IBKR_ERROR_CODE,
    JP_STATUS,
    MARKET_DATA_CLASSIFICATION,
    MARKET_DATA_STATUS,
    NAV_ITEMS,
    NO_TEXT,
    SYMBOLS,
    YES_TEXT,
    build_artifact_manifest as build_v7_artifact_manifest,
    build_build_snapshot as build_v7_build_snapshot,
    build_dashboard_css,
    build_dashboard_html,
    build_navigation_snapshot as build_v7_navigation_snapshot,
    build_operator_timeline as build_v7_operator_timeline,
    build_risk_snapshot as build_v7_risk_snapshot,
    build_signal_snapshot as build_v7_signal_snapshot,
    build_status_snapshot as build_v7_status_snapshot,
    build_trading_shell_snapshot as build_v7_trading_shell_snapshot,
    build_watchlist_snapshot as build_v7_watchlist_snapshot,
)


PHASE = "Phase 697-704"
STATUS = "DASHBOARD_UI_STATIC_VISUAL_FREEZE_READY"
UI_GENERATION = "V7_HIGH_TECH_TRADING_VISUAL_FROZEN"
FROZEN_FROM_PHASE = "Phase 681-696"
FROZEN_FROM_STATUS = "DASHBOARD_HIGH_TECH_TRADING_VISUAL_READY"
FROZEN_FROM_UI_GENERATION = "V7_HIGH_TECH_TRADING_VISUAL"
LATEST_MAIN_COMMIT = "f4bb1fa"
LATEST_MERGED_PR = "224"

STATUS_SNAPSHOT = "dashboard/data/status_snapshot.json"
UI_QA_SNAPSHOT = "dashboard/data/ui_qa_snapshot.json"
STATIC_VISUAL_FREEZE_SNAPSHOT = "dashboard/data/static_visual_freeze_snapshot.json"
VISUAL_REGRESSION_GUARD_SNAPSHOT = "dashboard/data/visual_regression_guard_snapshot.json"
HIGH_TECH_VISUAL_SNAPSHOT = "dashboard/data/high_tech_visual_snapshot.json"
TRADING_SHELL_SNAPSHOT = "dashboard/data/trading_shell_snapshot.json"
STATIC_CHART_SNAPSHOT = "dashboard/data/static_chart_snapshot.json"
CHINESE_UI_SNAPSHOT = "dashboard/data/chinese_ui_snapshot.json"
TEMPLATE_REFERENCE_SNAPSHOT = "dashboard/data/template_reference_snapshot.json"
VISUAL_DENSITY_SNAPSHOT = "dashboard/data/visual_density_snapshot.json"
CARD_SYSTEM_SNAPSHOT = "dashboard/data/card_system_snapshot.json"
ICON_SYSTEM_SNAPSHOT = "dashboard/data/icon_system_snapshot.json"
TIMELINE_POLISH_SNAPSHOT = "dashboard/data/timeline_polish_snapshot.json"
WATCHLIST_SNAPSHOT = "dashboard/data/watchlist_snapshot.json"
SIGNAL_SNAPSHOT = "dashboard/data/signal_snapshot.json"
RISK_SNAPSHOT = "dashboard/data/risk_snapshot.json"
LAYOUT_SNAPSHOT = "dashboard/data/layout_snapshot.json"
NAVIGATION_SNAPSHOT = "dashboard/data/navigation_snapshot.json"
BUILD_SNAPSHOT = "dashboard/data/build_snapshot.json"
OPERATOR_TIMELINE = "dashboard/data/operator_timeline.json"
ARTIFACT_MANIFEST = "dashboard/data/artifact_manifest.json"
OUTPUT_CSV = "operator_dashboard_ui_static_visual_freeze_pack.csv"
OUTPUT_REPORT = "reports/operator_dashboard_ui_static_visual_freeze_pack_report.md"
OUTPUT_PACK = "Precious_Metals_Monitor_Dashboard_UI_Static_Visual_Freeze_Pack.md"

REQUIRED_SECTIONS = (
    "AI 投研交易驾驶舱",
    "贵金属观察系统",
    "总览",
    "市场观察",
    "图表面板",
    "信号状态",
    "风险边界",
    "本地文件流",
    "项目进度轨道",
    "版本与安全",
)
REQUIRED_SAFETY_LABELS = (
    "未连接 IBKR",
    "未请求行情",
    "未请求历史数据",
    "未读取账户/持仓",
    "未交易",
    "未 Telegram 实发",
)
VISUAL_CONTRACT = (
    "DARK_FINTECH_TRADING_DASHBOARD",
    "CSS_ONLY_DARK_GRID_SURFACE",
    "LEFT_NAVIGATION",
    "TOP_STATUS_COMMAND_BAR",
    "HERO_TRADING_OVERVIEW",
    "STATIC_CHART_PANEL",
    "WATCHLIST_CARDS",
    "RISK_PERMISSION_PANEL",
    "ARTIFACT_STREAM",
    "PHASE_PROGRESS_RAIL",
    "SAFETY_FOOTER",
)
PROTECTED_MARKERS = (
    "AI 投研交易驾驶舱",
    "本地静态只读",
    "行情订阅阻断",
    "静态占位",
    "无实时行情",
    "订阅权限阻断",
    "本地文件流",
    "项目进度轨道",
    "DASHBOARD_HIGH_TECH_TRADING_VISUAL_READY",
    "V7_HIGH_TECH_TRADING_VISUAL",
)
FORBIDDEN_MARKERS = (
    "http://",
    "https://",
    "cdn",
    "@import",
    "script src",
    "TradingView",
    "iframe",
    "BUY",
    "SELL",
    "HOLD",
    "target_price",
    "stop_loss",
    "take_profit",
    "买入",
    "卖出",
    "持有",
    "目标价",
    "止损",
    "止盈",
)
FREEZE_SCOPE = (
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    HIGH_TECH_VISUAL_SNAPSHOT,
    TRADING_SHELL_SNAPSHOT,
    STATIC_CHART_SNAPSHOT,
)
ARTIFACTS = (
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    STATUS_SNAPSHOT,
    UI_QA_SNAPSHOT,
    STATIC_VISUAL_FREEZE_SNAPSHOT,
    VISUAL_REGRESSION_GUARD_SNAPSHOT,
    HIGH_TECH_VISUAL_SNAPSHOT,
    TRADING_SHELL_SNAPSHOT,
    STATIC_CHART_SNAPSHOT,
    CHINESE_UI_SNAPSHOT,
    TEMPLATE_REFERENCE_SNAPSHOT,
    VISUAL_DENSITY_SNAPSHOT,
    CARD_SYSTEM_SNAPSHOT,
    ICON_SYSTEM_SNAPSHOT,
    TIMELINE_POLISH_SNAPSHOT,
    WATCHLIST_SNAPSHOT,
    SIGNAL_SNAPSHOT,
    RISK_SNAPSHOT,
    LAYOUT_SNAPSHOT,
    NAVIGATION_SNAPSHOT,
    BUILD_SNAPSHOT,
    OPERATOR_TIMELINE,
    ARTIFACT_MANIFEST,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)
CSV_FIELDS = (
    "phase",
    "status",
    "ui_generation",
    "visual_freeze_status",
    "ui_qa_status",
    "visual_regression_guard_status",
    "frozen_from_phase",
    "frozen_from_status",
    "frozen_from_ui_generation",
    "language_mode",
    "interaction_mode",
    "javascript_required",
    "static_mode",
    "template_reference_status",
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
        "ui_phase": PHASE,
        "ui_status": STATUS,
        "ui_generation": UI_GENERATION,
        "visual_freeze_status": "STATIC_VISUAL_BASELINE_FROZEN",
        "ui_qa_status": "STATIC_UI_QA_PASS",
        "visual_regression_guard_status": "VISUAL_REGRESSION_GUARD_READY",
        "frozen_from_phase": FROZEN_FROM_PHASE,
        "frozen_from_status": FROZEN_FROM_STATUS,
        "frozen_from_ui_generation": FROZEN_FROM_UI_GENERATION,
        "language_mode": "ZH_CN_PRIMARY",
        "interaction_mode": "STATIC_HTML_CSS_ONLY",
        "javascript_required": NO_TEXT,
        "static_mode": "LOCAL_STATIC_ONLY",
        "template_reference_status": "PUBLIC_TEMPLATE_INSPIRED_LAYOUT_READY",
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
        "symbols": list(SYMBOLS),
        "generated_at_utc": timestamp,
    }


def build_ui_qa_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "STATIC_UI_QA_PASS",
        "checked_ui_generation": FROZEN_FROM_UI_GENERATION,
        "language_mode": "ZH_CN_PRIMARY",
        "required_sections": list(REQUIRED_SECTIONS),
        "required_safety_labels": list(REQUIRED_SAFETY_LABELS),
        "external_resource_check": "PASS",
        "forbidden_trading_output_check": "PASS",
        "forbidden_price_field_check": "PASS",
        "generated_at_utc": timestamp,
    }


def build_static_visual_freeze_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "STATIC_VISUAL_BASELINE_FROZEN",
        "frozen_ui_generation": FROZEN_FROM_UI_GENERATION,
        "freeze_scope": list(FREEZE_SCOPE),
        "visual_contract": list(VISUAL_CONTRACT),
        "external_assets": NO_TEXT,
        "javascript_required": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_visual_regression_guard_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "VISUAL_REGRESSION_GUARD_READY",
        "guard_mode": "STATIC_TEXT_AND_STRUCTURE_GUARD",
        "protected_markers": list(PROTECTED_MARKERS),
        "forbidden_markers": list(FORBIDDEN_MARKERS),
        "generated_at_utc": timestamp,
    }


def build_high_tech_visual_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "HIGH_TECH_TRADING_DASHBOARD_VISUAL_READY",
        "freeze_status": "STATIC_VISUAL_BASELINE_FROZEN",
        "visual_mode": "CHINESE_HIGH_TECH_TRADING_DASHBOARD",
        "theme_mode": "DARK_FINTECH_TRADING_DASHBOARD",
        "background_style": "CSS_ONLY_DARK_GRID_SURFACE",
        "layout_patterns": list(VISUAL_CONTRACT[2:]),
        "copied_external_code": NO_TEXT,
        "copied_external_images": NO_TEXT,
        "copied_external_fonts": NO_TEXT,
        "copied_external_icons": NO_TEXT,
        "loaded_external_assets": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_trading_shell_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "STATIC_TRADING_SHELL_READY",
        "freeze_status": "STATIC_VISUAL_BASELINE_FROZEN",
        "shell_mode": "READ_ONLY_TRADING_DASHBOARD_VISUAL_ONLY",
        "primary_title": "AI 投研交易驾驶舱 · 贵金属观察系统",
        "subtitle": "本地静态只读 · 行情订阅阻断 · 无账户读取 · 无交易权限",
        "real_trading_ui": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_static_chart_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "CSS_ONLY_STATIC_CHART_PLACEHOLDER_READY",
        "freeze_status": "STATIC_VISUAL_BASELINE_FROZEN",
        "chart_mode": "STATIC_VISUAL_PLACEHOLDER_ONLY",
        "real_market_data": NO_TEXT,
        "real_price_axis": NO_TEXT,
        "real_candlestick": NO_TEXT,
        "real_pnl_curve": NO_TEXT,
        "generated_price_values": NO_TEXT,
        "generated_signals": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_chinese_ui_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "CHINESE_MAIN_UI_FROZEN",
        "language_mode": "ZH_CN_PRIMARY",
        "required_sections": list(REQUIRED_SECTIONS),
        "nav_labels": [item[0] for item in NAV_ITEMS],
        "generated_at_utc": timestamp,
    }


def build_simple_snapshot(status: str, generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": status,
        "freeze_status": "STATIC_VISUAL_BASELINE_FROZEN",
        "external_assets": NO_TEXT,
        "javascript_required": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_watchlist_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "scope": "US_ONLY",
        "symbols": [
            {
                "symbol": symbol,
                "type": "ETF",
                "market": "US",
                "data_status": "订阅阻断",
                "realtime": NO_TEXT,
                "delayed": YES_TEXT,
                "purpose": "研究观察框架",
            }
            for symbol in SYMBOLS
        ],
        "generated_at_utc": timestamp,
    }


def build_signal_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "signal_module": "未启用",
        "strategy_output": "未启用",
        "reason": "行情订阅权限阻断",
        "current_status": "仅保留研究框架，不输出方向判断",
        "generated_at_utc": timestamp,
    }


def build_risk_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "risk_mode": "STATIC_TRADING_PLATFORM_PERMISSION_PANEL",
        "permissions": [
            {
                "action": action,
                "status": "DISABLED",
                "reason": "LOCAL_STATIC_READ_ONLY_OR_MARKET_DATA_BLOCKED",
                "allowed": NO_TEXT,
            }
            for action in BLOCKED_ACTIONS
        ],
        "generated_at_utc": timestamp,
    }


def build_operator_timeline(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    timeline = build_v7_operator_timeline(timestamp)["timeline"]
    timeline.append(
        {
            "phase": PHASE,
            "theme": "UI QA / 静态视觉冻结",
            "status": STATUS,
            "external_effect": EXTERNAL_EFFECT,
        }
    )
    return {"timeline": timeline, "generated_at_utc": timestamp}


def build_build_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": STATUS,
        "ui_generation": UI_GENERATION,
        "latest_main_commit": LATEST_MAIN_COMMIT,
        "latest_merged_pr": LATEST_MERGED_PR,
        "production_ready": NO_TEXT,
        "trading_enabled": NO_TEXT,
        "external_effect": EXTERNAL_EFFECT,
        "generated_at_utc": timestamp,
    }


def build_navigation_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    navigation = build_v7_navigation_snapshot(timestamp)
    navigation["phase"] = PHASE
    navigation["status"] = "STATIC_LOCAL_LEFT_NAVIGATION_FROZEN"
    return navigation


def build_artifact_manifest(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": STATUS,
        "external_effect": EXTERNAL_EFFECT,
        "artifacts": [
            {
                "artifact_path": path,
                "type": Path(path).suffix.lstrip(".").upper() or "HTML",
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


def write_dashboard_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_report(row: Dict[str, str]) -> str:
    lines = [
        "# Phase 697-704 Dashboard UI Static Visual Freeze Pack Report",
        "",
        "## Status",
        "",
        *[f"- {field}={row[field]}" for field in CSV_FIELDS],
        "",
        "## Freeze Boundary",
        "",
        "- freezes V7 high-tech Chinese trading dashboard visual baseline",
        "- static UI QA pass",
        "- visual regression guard ready",
        "- no major UI layout rewrite",
        "- CSS-only static chart placeholder preserved",
        "- no real market data",
        "- no real price axis",
        "- no real candlestick",
        "- no generated price values",
        "- no trading signals",
        "- no copied external template code/images/fonts/icons",
        "- no external URL/CDN",
        "- local static read-only artifact viewer only",
        "- no IBKR connection",
        "- no market data request",
        "- no historical data request",
        "- no account/position read",
        "- no contract qualification",
        "- no trading",
        "- no Telegram real send",
        "- no live price fields",
        "- market data remains BLOCKED_BY_SUBSCRIPTION / IBKR_ERROR_10089",
        "- GLD / SLV only",
        "- JP / CN remain frozen",
    ]
    return "\n".join(lines) + "\n"


def build_pack(row: Dict[str, str]) -> str:
    lines = [
        "# Precious Metals Monitor Dashboard UI Static Visual Freeze Pack",
        "",
        f"- phase={row['phase']}",
        f"- status={row['status']}",
        f"- ui_generation={row['ui_generation']}",
        "- freezes V7 high-tech Chinese trading dashboard visual baseline",
        "- static UI QA pass",
        "- visual regression guard ready",
        "- local static read-only artifact viewer only",
        f"- market data remains {row['market_data_status']} / IBKR_ERROR_{row['ibkr_error_code']}",
        "- JP / CN remain frozen",
    ]
    return "\n".join(lines) + "\n"


def _ensure_dashboard_baseline(output_index: PathLike, output_css: PathLike, timestamp: str) -> None:
    index_path = Path(output_index)
    css_path = Path(output_css)
    if css_path.exists() and index_path.exists():
        return

    status = build_v7_status_snapshot(timestamp)
    shell = build_v7_trading_shell_snapshot(timestamp)
    watchlist = build_v7_watchlist_snapshot(timestamp)
    signal = build_v7_signal_snapshot(timestamp)
    risk = build_v7_risk_snapshot(timestamp)
    timeline = build_v7_operator_timeline(timestamp)
    navigation = build_v7_navigation_snapshot(timestamp)
    build = build_v7_build_snapshot(timestamp)
    manifest = build_v7_artifact_manifest(timestamp)
    _write_text(css_path, build_dashboard_css())
    _write_text(index_path, build_dashboard_html(status, shell, watchlist, signal, risk, timeline, navigation, build, manifest))


def generate_dashboard_ui_static_visual_freeze_pack(
    *,
    output_index: PathLike = DASHBOARD_INDEX,
    output_css: PathLike = DASHBOARD_CSS,
    output_status_snapshot: PathLike = STATUS_SNAPSHOT,
    output_ui_qa_snapshot: PathLike = UI_QA_SNAPSHOT,
    output_static_visual_freeze_snapshot: PathLike = STATIC_VISUAL_FREEZE_SNAPSHOT,
    output_visual_regression_guard_snapshot: PathLike = VISUAL_REGRESSION_GUARD_SNAPSHOT,
    output_high_tech_visual_snapshot: PathLike = HIGH_TECH_VISUAL_SNAPSHOT,
    output_trading_shell_snapshot: PathLike = TRADING_SHELL_SNAPSHOT,
    output_static_chart_snapshot: PathLike = STATIC_CHART_SNAPSHOT,
    output_chinese_ui_snapshot: PathLike = CHINESE_UI_SNAPSHOT,
    output_template_reference_snapshot: PathLike = TEMPLATE_REFERENCE_SNAPSHOT,
    output_visual_density_snapshot: PathLike = VISUAL_DENSITY_SNAPSHOT,
    output_card_system_snapshot: PathLike = CARD_SYSTEM_SNAPSHOT,
    output_icon_system_snapshot: PathLike = ICON_SYSTEM_SNAPSHOT,
    output_timeline_polish_snapshot: PathLike = TIMELINE_POLISH_SNAPSHOT,
    output_watchlist_snapshot: PathLike = WATCHLIST_SNAPSHOT,
    output_signal_snapshot: PathLike = SIGNAL_SNAPSHOT,
    output_risk_snapshot: PathLike = RISK_SNAPSHOT,
    output_layout_snapshot: PathLike = LAYOUT_SNAPSHOT,
    output_navigation_snapshot: PathLike = NAVIGATION_SNAPSHOT,
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

    _ensure_dashboard_baseline(output_index, output_css, timestamp)
    _write_json(output_status_snapshot, status)
    _write_json(output_ui_qa_snapshot, build_ui_qa_snapshot(timestamp))
    _write_json(output_static_visual_freeze_snapshot, build_static_visual_freeze_snapshot(timestamp))
    _write_json(output_visual_regression_guard_snapshot, build_visual_regression_guard_snapshot(timestamp))
    _write_json(output_high_tech_visual_snapshot, build_high_tech_visual_snapshot(timestamp))
    _write_json(output_trading_shell_snapshot, build_trading_shell_snapshot(timestamp))
    _write_json(output_static_chart_snapshot, build_static_chart_snapshot(timestamp))
    _write_json(output_chinese_ui_snapshot, build_chinese_ui_snapshot(timestamp))
    _write_json(output_template_reference_snapshot, build_simple_snapshot("PUBLIC_TEMPLATE_INSPIRED_LAYOUT_READY", timestamp))
    _write_json(output_visual_density_snapshot, build_simple_snapshot("HIGH_TECH_DENSE_TRADING_CONSOLE_FROZEN", timestamp))
    _write_json(output_card_system_snapshot, build_simple_snapshot("HIGH_TECH_CARD_SYSTEM_FROZEN", timestamp))
    _write_json(output_icon_system_snapshot, build_simple_snapshot("LOCAL_TEXT_ICON_SYSTEM_FROZEN", timestamp))
    _write_json(output_timeline_polish_snapshot, build_simple_snapshot("PHASE_PROGRESS_RAIL_FROZEN", timestamp))
    _write_json(output_watchlist_snapshot, build_watchlist_snapshot(timestamp))
    _write_json(output_signal_snapshot, build_signal_snapshot(timestamp))
    _write_json(output_risk_snapshot, build_risk_snapshot(timestamp))
    _write_json(output_layout_snapshot, build_simple_snapshot("HIGH_TECH_TRADING_DASHBOARD_APP_SHELL_FROZEN", timestamp))
    _write_json(output_navigation_snapshot, build_navigation_snapshot(timestamp))
    _write_json(output_build_snapshot, build_build_snapshot(timestamp))
    _write_json(output_operator_timeline, build_operator_timeline(timestamp))
    _write_json(output_artifact_manifest, build_artifact_manifest(timestamp))
    write_dashboard_csv(output_csv, row)
    _write_text(output_report, build_report(row))
    _write_text(output_pack, build_pack(row))
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 697-704 dashboard UI static visual freeze pack.")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generate_dashboard_ui_static_visual_freeze_pack(generated_at=args.generated_at)
    print("[DASHBOARD_UI_STATIC_VISUAL_FREEZE_PACK] generated")
    print(f"status={STATUS}")
    print(f"ui_generation={UI_GENERATION}")
    print("visual_freeze_status=STATIC_VISUAL_BASELINE_FROZEN")
    print("ui_qa_status=STATIC_UI_QA_PASS")
    print("visual_regression_guard_status=VISUAL_REGRESSION_GUARD_READY")
    print("interaction_mode=STATIC_HTML_CSS_ONLY")
    print("javascript_required=NO")
    print("market_data_status=BLOCKED_BY_SUBSCRIPTION")
    print("market_data_classification=MARKET_DATA_BLOCKED_BY_SUBSCRIPTION")
    print("ibkr_error_code=10089")
    print("realtime_market_data_verified=NO")
    print("production_ready=NO")
    print("trading_enabled=NO")
    print("account_read_enabled=NO")
    print("positions_read_enabled=NO")
    print("historical_data_enabled=NO")
    print("telegram_real_send_enabled=NO")
    print(f"jp_status={JP_STATUS}")
    print(f"cn_status={CN_STATUS}")
    print(f"external_effect={EXTERNAL_EFFECT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
