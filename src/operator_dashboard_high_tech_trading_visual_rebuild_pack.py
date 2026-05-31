from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


PHASE = "Phase 681-696"
STATUS = "DASHBOARD_HIGH_TECH_TRADING_VISUAL_READY"
UI_GENERATION = "V7_HIGH_TECH_TRADING_VISUAL"
LATEST_MAIN_COMMIT = "82afe1b"
LATEST_MERGED_PR = "223"
MARKET_SCOPE = "US_ONLY"
SYMBOLS = ("GLD", "SLV")
MARKET_DATA_STATUS = "BLOCKED_BY_SUBSCRIPTION"
MARKET_DATA_CLASSIFICATION = "MARKET_DATA_BLOCKED_BY_SUBSCRIPTION"
IBKR_ERROR_CODE = "10089"
YES_TEXT = "YES"
NO_TEXT = "NO"
EXTERNAL_EFFECT = "NONE_LOCAL_ARTIFACT_GENERATION_ONLY"
JP_STATUS = "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION"
CN_STATUS = "FROZEN_PENDING_DATA_SOURCE_DECISION"

DASHBOARD_INDEX = "dashboard/index.html"
DASHBOARD_CSS = "dashboard/assets/style.css"
STATUS_SNAPSHOT = "dashboard/data/status_snapshot.json"
HIGH_TECH_VISUAL_SNAPSHOT = "dashboard/data/high_tech_visual_snapshot.json"
TRADING_SHELL_SNAPSHOT = "dashboard/data/trading_shell_snapshot.json"
STATIC_CHART_SNAPSHOT = "dashboard/data/static_chart_snapshot.json"
CHINESE_UI_SNAPSHOT = "dashboard/data/chinese_ui_snapshot.json"
TEMPLATE_REFERENCE_SNAPSHOT = "dashboard/data/template_reference_snapshot.json"
VISUAL_DENSITY_SNAPSHOT = "dashboard/data/visual_density_snapshot.json"
CARD_SYSTEM_SNAPSHOT = "dashboard/data/card_system_snapshot.json"
ICON_SYSTEM_SNAPSHOT = "dashboard/data/icon_system_snapshot.json"
TIMELINE_POLISH_SNAPSHOT = "dashboard/data/timeline_polish_snapshot.json"
BUILD_SNAPSHOT = "dashboard/data/build_snapshot.json"
OPERATOR_TIMELINE = "dashboard/data/operator_timeline.json"
WATCHLIST_SNAPSHOT = "dashboard/data/watchlist_snapshot.json"
SIGNAL_SNAPSHOT = "dashboard/data/signal_snapshot.json"
RISK_SNAPSHOT = "dashboard/data/risk_snapshot.json"
LAYOUT_SNAPSHOT = "dashboard/data/layout_snapshot.json"
NAVIGATION_SNAPSHOT = "dashboard/data/navigation_snapshot.json"
ARTIFACT_MANIFEST = "dashboard/data/artifact_manifest.json"
OUTPUT_CSV = "operator_dashboard_high_tech_trading_visual_rebuild_pack.csv"
OUTPUT_REPORT = "reports/operator_dashboard_high_tech_trading_visual_rebuild_pack_report.md"
OUTPUT_PACK = "Precious_Metals_Monitor_Dashboard_High_Tech_Trading_Visual_Rebuild_Pack.md"

ARTIFACTS = (
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    STATUS_SNAPSHOT,
    HIGH_TECH_VISUAL_SNAPSHOT,
    TRADING_SHELL_SNAPSHOT,
    STATIC_CHART_SNAPSHOT,
    CHINESE_UI_SNAPSHOT,
    TEMPLATE_REFERENCE_SNAPSHOT,
    VISUAL_DENSITY_SNAPSHOT,
    CARD_SYSTEM_SNAPSHOT,
    ICON_SYSTEM_SNAPSHOT,
    TIMELINE_POLISH_SNAPSHOT,
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    OPERATOR_TIMELINE,
    WATCHLIST_SNAPSHOT,
    SIGNAL_SNAPSHOT,
    RISK_SNAPSHOT,
    LAYOUT_SNAPSHOT,
    NAVIGATION_SNAPSHOT,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)

NAV_ITEMS = (
    ("总览", "总", "#overview"),
    ("市场观察", "观", "#watchlist"),
    ("图表面板", "图", "#chart-panel"),
    ("信号状态", "信", "#signals"),
    ("风险边界", "风", "#risk-boundary"),
    ("本地文件", "文", "#artifacts"),
    ("项目进度", "线", "#timeline"),
    ("系统状态", "系", "#system-status"),
)

BLOCKED_ACTIONS = (
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
    "EXTERNAL_URL_LOAD",
)

CSV_FIELDS = (
    "phase",
    "status",
    "ui_generation",
    "high_tech_visual_status",
    "trading_shell_status",
    "static_chart_status",
    "chart_data_status",
    "visual_rebuild_status",
    "language_mode",
    "interaction_mode",
    "javascript_required",
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


def build_status_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": STATUS,
        "ui_phase": PHASE,
        "ui_status": STATUS,
        "ui_generation": UI_GENERATION,
        "language_mode": "ZH_CN_PRIMARY",
        "high_tech_visual_status": "HIGH_TECH_TRADING_DASHBOARD_VISUAL_READY",
        "trading_shell_status": "STATIC_TRADING_SHELL_READY",
        "static_chart_status": "CSS_ONLY_STATIC_CHART_PLACEHOLDER_READY",
        "chart_data_status": "NO_REAL_MARKET_DATA_NO_PRICE_AXIS",
        "visual_rebuild_status": "HIGH_TECH_VISUAL_REBUILD_APPLIED",
        "interaction_mode": "STATIC_HTML_CSS_ONLY",
        "javascript_required": NO_TEXT,
        "template_reference_status": "PUBLIC_TEMPLATE_INSPIRED_LAYOUT_READY",
        "english_status_code_mode": "SECONDARY_TECHNICAL_BADGE_ONLY",
        "static_mode": "LOCAL_STATIC_ONLY",
        "market_scope": MARKET_SCOPE,
        "symbols": list(SYMBOLS),
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
        "generated_at_utc": timestamp,
    }


def build_high_tech_visual_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "HIGH_TECH_TRADING_DASHBOARD_VISUAL_READY",
        "visual_mode": "CHINESE_HIGH_TECH_TRADING_DASHBOARD",
        "theme_mode": "DARK_FINTECH_TRADING_DASHBOARD",
        "background_style": "CSS_ONLY_DARK_GRID_SURFACE",
        "accent_language": ["CYAN", "BLUE", "AMBER", "RISK_RED", "SAFE_GREEN"],
        "layout_patterns": [
            "LEFT_NAVIGATION",
            "TOP_STATUS_COMMAND_BAR",
            "HERO_TRADING_OVERVIEW",
            "STATIC_CHART_PANEL",
            "WATCHLIST_CARDS",
            "RISK_PERMISSION_PANEL",
            "ARTIFACT_STREAM",
            "PHASE_PROGRESS_RAIL",
            "SAFETY_FOOTER",
        ],
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
        "shell_mode": "READ_ONLY_TRADING_DASHBOARD_VISUAL_ONLY",
        "primary_title": "AI 投研交易驾驶舱 · 贵金属观察系统",
        "subtitle": "本地静态只读 · 行情订阅阻断 · 无账户读取 · 无交易权限",
        "hero_panels": ["系统状态", "静态图表占位", "风险边界摘要"],
        "trading_controls": {
            "order_entry": "DISABLED",
            "order_cancel": "DISABLED",
            "rebalance": "DISABLED",
            "telegram_real_send": "DISABLED",
        },
        "real_trading_ui": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_static_chart_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "CSS_ONLY_STATIC_CHART_PLACEHOLDER_READY",
        "chart_mode": "STATIC_VISUAL_PLACEHOLDER_ONLY",
        "real_market_data": NO_TEXT,
        "real_price_axis": NO_TEXT,
        "real_candlestick": NO_TEXT,
        "real_pnl_curve": NO_TEXT,
        "generated_price_values": NO_TEXT,
        "generated_signals": NO_TEXT,
        "purpose": "VISUAL_CONTEXT_ONLY_MARKET_DATA_BLOCKED",
        "generated_at_utc": timestamp,
    }


def build_chinese_ui_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "CHINESE_MAIN_UI_READY",
        "language_mode": "ZH_CN_PRIMARY",
        "primary_title": "AI 投研交易驾驶舱 · 贵金属观察系统",
        "subtitle": "本地静态只读 · 行情订阅阻断 · 无账户读取 · 无交易权限",
        "nav_labels": [item[0] for item in NAV_ITEMS],
        "technical_status_codes": "SECONDARY_TECHNICAL_BADGE_ONLY",
        "generated_at_utc": timestamp,
    }


def build_template_reference_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "PUBLIC_TEMPLATE_INSPIRED_LAYOUT_READY",
        "reference_mode": "PUBLIC_DASHBOARD_LAYOUT_LANGUAGE_ONLY",
        "copied_external_code": NO_TEXT,
        "copied_external_images": NO_TEXT,
        "copied_external_fonts": NO_TEXT,
        "copied_external_icons": NO_TEXT,
        "loaded_external_assets": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_visual_density_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "HIGH_TECH_DENSE_TRADING_CONSOLE_READY",
        "density_mode": "HIGH_INFORMATION_DENSITY_STATIC_TRADING_DASHBOARD",
        "responsive_layout": YES_TEXT,
        "javascript_required": NO_TEXT,
        "external_assets": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_card_system_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "HIGH_TECH_CARD_SYSTEM_READY",
        "card_types": [
            "HERO_STATUS_CARD",
            "STATIC_CHART_CARD",
            "WATCHLIST_CARD",
            "RISK_PERMISSION_CARD",
            "ARTIFACT_STREAM_CARD",
            "PHASE_RAIL_CARD",
        ],
        "external_assets": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_icon_system_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "LOCAL_TEXT_ICON_SYSTEM_READY",
        "icon_mode": "TEXT_ONLY_LOCAL_ICON_TOKENS",
        "icon_tokens": [item[1] for item in NAV_ITEMS] + ["SYS", "CSS", "LOCK", "FILE"],
        "external_icon_library": NO_TEXT,
        "remote_icon_assets": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_timeline_polish_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "PHASE_PROGRESS_RAIL_READY",
        "timeline_mode": "STATIC_OPERATOR_PHASE_RAIL",
        "timeline_items": [
            "Phase 633-640",
            "Phase 641-648",
            "Phase 649-656",
            "Phase 657-664",
            "Phase 665-672",
            "Phase 673-680",
            "Phase 681-696",
        ],
        "external_effect": EXTERNAL_EFFECT,
        "generated_at_utc": timestamp,
    }


def build_watchlist_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "scope": MARKET_SCOPE,
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
        "signal_module": "未启用",
        "strategy_output": "未启用",
        "reason": "行情订阅权限阻断",
        "current_status": "仅保留研究框架，不输出方向判断",
        "generated_at_utc": timestamp,
    }


def build_risk_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
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
    rows = [
        ("Phase 633-640", "控制台 UI 增强", "DASHBOARD_UI_ENHANCEMENT_READY"),
        ("Phase 641-648", "控制台 v2 数据面板", "DASHBOARD_UI_V2_DATA_PANEL_READY"),
        ("Phase 649-656", "控制台 v3 布局优化", "DASHBOARD_UI_V3_LAYOUT_POLISH_READY"),
        ("Phase 657-664", "视觉密度与卡片系统", "DASHBOARD_VISUAL_DENSITY_CARD_SYSTEM_READY"),
        ("Phase 665-672", "图标 / 时间线 / 文件视图优化", "DASHBOARD_ICON_TIMELINE_ARTIFACT_POLISH_READY"),
        ("Phase 673-680", "中文模板柔化优化", "DASHBOARD_CHINESE_TEMPLATE_SOFT_POLISH_READY"),
        (PHASE, "高科技交易驾驶舱视觉重构", STATUS),
    ]
    return {
        "timeline": [
            {"phase": phase, "theme": theme, "status": status, "external_effect": EXTERNAL_EFFECT}
            for phase, theme, status in rows
        ],
        "generated_at_utc": timestamp,
    }


def build_layout_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": STATUS,
        "layout_mode": "HIGH_TECH_TRADING_DASHBOARD_APP_SHELL",
        "sections": [
            "LEFT_NAVIGATION",
            "TOP_STATUS_COMMAND_BAR",
            "HERO_TRADING_OVERVIEW",
            "STATIC_CHART_PANEL",
            "WATCHLIST_CARDS",
            "RISK_PERMISSION_PANEL",
            "ARTIFACT_STREAM",
            "PHASE_PROGRESS_RAIL",
            "SAFETY_FOOTER",
        ],
        "responsive_layout": YES_TEXT,
        "external_assets": NO_TEXT,
        "javascript_required": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_navigation_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "nav_mode": "STATIC_LOCAL_LEFT_NAVIGATION",
        "active": "总览",
        "items": [
            {"label": label, "icon_text": icon, "href": href, "enabled": YES_TEXT, "external_url": NO_TEXT}
            for label, icon, href in NAV_ITEMS
        ],
        "generated_at_utc": timestamp,
    }


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


def build_artifact_manifest(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": STATUS,
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


def _write_json(path: PathLike, payload: Dict[str, object]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _status_row(status: Dict[str, object]) -> Dict[str, str]:
    return {field: str(status[field]) for field in CSV_FIELDS}


def build_dashboard_css() -> str:
    return """\
:root {
  color-scheme: dark;
  --bg: #060a12;
  --panel: rgba(13, 22, 35, 0.92);
  --panel-2: rgba(17, 31, 49, 0.92);
  --line: rgba(103, 232, 249, 0.22);
  --line-strong: rgba(96, 165, 250, 0.42);
  --text: #e5eef8;
  --muted: #8ea4b8;
  --cyan: #22d3ee;
  --blue: #60a5fa;
  --amber: #f59e0b;
  --risk-red: #f87171;
  --safe-green: #34d399;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  min-height: 100vh;
  background:
    linear-gradient(rgba(34, 211, 238, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(96, 165, 250, 0.07) 1px, transparent 1px),
    radial-gradient(circle at 20% 8%, rgba(34, 211, 238, 0.16), transparent 28%),
    radial-gradient(circle at 88% 12%, rgba(245, 158, 11, 0.11), transparent 24%),
    var(--bg);
  background-size: 28px 28px, 28px 28px, auto, auto, auto;
  color: var(--text);
  font-family: Arial, Helvetica, sans-serif;
  font-size: 13px;
  line-height: 1.48;
}
a { color: inherit; text-decoration: none; }
.mono { font-family: Consolas, Monaco, monospace; }
.app-shell { display: grid; grid-template-columns: 236px minmax(0, 1fr); min-height: 100vh; }
.sidebar {
  border-right: 1px solid var(--line);
  background: rgba(5, 10, 19, 0.88);
  padding: 18px 14px;
  position: sticky;
  top: 0;
  height: 100vh;
}
.brand { border: 1px solid var(--line); border-radius: 8px; padding: 12px; margin-bottom: 18px; }
.brand-mark, .nav-icon {
  align-items: center;
  border: 1px solid var(--line-strong);
  border-radius: 7px;
  color: var(--cyan);
  display: inline-flex;
  font-weight: 800;
  height: 30px;
  justify-content: center;
  margin-right: 8px;
  width: 30px;
}
.brand-title { display: block; font-size: 14px; font-weight: 800; }
.brand-subtitle, .label, .eyebrow, .caption { color: var(--muted); font-size: 11px; font-weight: 700; }
.sidebar-nav { display: grid; gap: 7px; }
.nav-item {
  align-items: center;
  border: 1px solid transparent;
  border-radius: 8px;
  color: #b9c9d8;
  display: flex;
  min-height: 38px;
  padding: 5px 8px;
}
.nav-item.active, .nav-item:hover { background: rgba(34, 211, 238, 0.08); border-color: var(--line); color: #fff; }
.sidebar-note { border: 1px solid rgba(245, 158, 11, 0.32); border-radius: 8px; color: var(--amber); margin-top: 20px; padding: 10px; }
.content { min-width: 0; padding: 18px 22px 72px; }
.command-bar {
  align-items: start;
  background: rgba(8, 14, 25, 0.84);
  border: 1px solid var(--line);
  border-radius: 8px;
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(0, 1fr) auto;
  padding: 16px;
}
h1 { font-size: 25px; line-height: 1.15; margin: 0; }
h2 { font-size: 15px; margin: 0; }
.subtitle { color: var(--muted); margin: 7px 0 0; }
.badge-row { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 12px; }
.badge, .token {
  border: 1px solid var(--line);
  border-radius: 999px;
  display: inline-flex;
  font-size: 11px;
  font-weight: 800;
  min-height: 24px;
  padding: 3px 9px;
}
.secondary { color: var(--muted); font-size: 9px; opacity: 0.86; }
.safe { border-color: rgba(52, 211, 153, 0.42); color: var(--safe-green); }
.warn { border-color: rgba(245, 158, 11, 0.48); color: var(--amber); }
.blocked, .disabled { border-color: rgba(248, 113, 113, 0.48); color: var(--risk-red); }
.build-chip { border: 1px solid var(--line); border-radius: 8px; min-width: 260px; padding: 10px 12px; }
.hero-grid { display: grid; gap: 12px; grid-template-columns: 1fr 1.35fr 1fr; margin: 14px 0; }
.panel, .card {
  background: linear-gradient(180deg, var(--panel), rgba(7, 13, 24, 0.94));
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: 0 0 0 1px rgba(96, 165, 250, 0.05), 0 20px 50px rgba(0, 0, 0, 0.26);
  min-width: 0;
  padding: 14px;
}
.panel-header, .card-header { align-items: center; border-bottom: 1px solid rgba(142, 164, 184, 0.14); display: flex; justify-content: space-between; margin-bottom: 10px; padding-bottom: 8px; }
.big-copy { display: block; font-size: 18px; font-weight: 800; margin-top: 16px; }
.small-copy { color: var(--muted); display: block; margin-top: 5px; }
.chart-shell {
  background:
    linear-gradient(rgba(34, 211, 238, 0.12) 1px, transparent 1px),
    linear-gradient(90deg, rgba(96, 165, 250, 0.10) 1px, transparent 1px),
    linear-gradient(180deg, rgba(13, 22, 35, 0.38), rgba(5, 10, 19, 0.7));
  background-size: 24px 24px, 24px 24px, auto;
  border: 1px solid rgba(34, 211, 238, 0.28);
  border-radius: 8px;
  height: 230px;
  overflow: hidden;
  position: relative;
}
.chart-shell::before {
  background: linear-gradient(120deg, transparent 0 12%, var(--cyan) 12% 13%, transparent 13% 32%, var(--blue) 32% 33%, transparent 33% 52%, var(--amber) 52% 53%, transparent 53%);
  content: "";
  height: 120px;
  left: 6%;
  opacity: 0.72;
  position: absolute;
  right: 5%;
  top: 58px;
  transform: skewY(-8deg);
}
.chart-shell::after {
  background: linear-gradient(180deg, transparent, rgba(34, 211, 238, 0.18), transparent);
  content: "";
  height: 42px;
  left: 0;
  position: absolute;
  right: 0;
  top: 86px;
}
.chart-watermark {
  border: 1px solid rgba(248, 113, 113, 0.45);
  border-radius: 999px;
  color: var(--risk-red);
  font-weight: 800;
  left: 50%;
  padding: 6px 12px;
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  white-space: nowrap;
}
.bar-row { bottom: 16px; display: flex; gap: 7px; left: 18px; position: absolute; right: 18px; }
.bar-row span { background: rgba(34, 211, 238, 0.28); border: 1px solid rgba(34, 211, 238, 0.38); flex: 1; min-height: 22px; }
.bar-row span:nth-child(2n) { min-height: 46px; }
.bar-row span:nth-child(3n) { min-height: 34px; }
.metric-list, .risk-list { display: grid; gap: 8px; margin-top: 14px; }
.metric, .risk-item, .watch-card, .file-card, .phase-card {
  background: rgba(17, 31, 49, 0.72);
  border: 1px solid rgba(142, 164, 184, 0.16);
  border-radius: 8px;
  padding: 10px;
}
.risk-item { align-items: center; display: grid; gap: 8px; grid-template-columns: 10px minmax(0, 1fr) auto auto; }
.lamp { background: var(--risk-red); border-radius: 999px; box-shadow: 0 0 12px rgba(248, 113, 113, 0.65); height: 9px; width: 9px; }
.main-grid { display: grid; gap: 12px; grid-template-columns: repeat(12, minmax(0, 1fr)); }
.card { grid-column: span 6; }
.card.full { grid-column: 1 / -1; }
.watch-grid, .file-stream, .phase-rail { display: grid; gap: 10px; }
.watch-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.watch-card dl, .version-table { display: grid; gap: 6px; margin: 10px 0 0; }
.watch-card div, .version-row { display: flex; gap: 10px; justify-content: space-between; }
.file-card { display: grid; gap: 8px; grid-template-columns: 120px minmax(0, 1fr) 90px 150px; }
.local-link { color: var(--safe-green); overflow-wrap: anywhere; }
.phase-rail { grid-template-columns: repeat(7, minmax(150px, 1fr)); overflow-x: auto; padding-bottom: 4px; }
.phase-card { border-top: 3px solid var(--blue); min-height: 132px; }
.muted { color: var(--muted); }
.footer-safety-bar {
  background: rgba(5, 10, 19, 0.95);
  border-top: 1px solid var(--line);
  bottom: 0;
  color: var(--muted);
  font-weight: 800;
  left: 236px;
  padding: 11px 22px;
  position: fixed;
  right: 0;
}
@media (max-width: 1100px) {
  .app-shell { grid-template-columns: 1fr; }
  .sidebar { height: auto; position: relative; }
  .sidebar-nav { grid-template-columns: repeat(4, minmax(0, 1fr)); display: grid; }
  .hero-grid, .command-bar { grid-template-columns: 1fr; }
  .footer-safety-bar { left: 0; }
}
@media (max-width: 760px) {
  .content { padding: 14px 12px 92px; }
  .card { grid-column: 1 / -1; }
  .watch-grid, .file-card { grid-template-columns: 1fr; }
}
"""


def _e(value: object) -> str:
    return escape(str(value))


def build_dashboard_html(
    status: Dict[str, object],
    shell: Dict[str, object],
    watchlist: Dict[str, object],
    signal: Dict[str, object],
    risk: Dict[str, object],
    timeline: Dict[str, object],
    navigation: Dict[str, object],
    build: Dict[str, object],
    manifest: Dict[str, object],
) -> str:
    nav_links = "\n".join(
        f'          <a class="nav-item{" active" if item["href"] == "#overview" else ""}" href="{_e(item["href"])}"><span class="nav-icon">{_e(item["icon_text"])}</span><span>{_e(item["label"])}</span></a>'
        for item in navigation["items"]
    )
    watch_cards = "\n".join(
        f"""\
              <article class="watch-card">
                <div><strong class="mono">{_e(item["symbol"])}</strong><span class="token blocked">{_e(item["data_status"])}</span></div>
                <dl>
                  <div><dt>类型</dt><dd>{_e(item["type"])}</dd></div>
                  <div><dt>市场</dt><dd class="mono">{_e(item["market"])}</dd></div>
                  <div><dt>实时行情</dt><dd class="mono">{_e(item["realtime"])}</dd></div>
                  <div><dt>延迟可用</dt><dd class="mono">{_e(item["delayed"])}</dd></div>
                  <div><dt>用途</dt><dd>{_e(item["purpose"])}</dd></div>
                </dl>
              </article>"""
        for item in watchlist["symbols"]
    )
    risk_items = "\n".join(
        f'              <div class="risk-item"><span class="lamp"></span><span class="mono">{_e(item["action"])}</span><span class="token disabled">{_e(item["status"])}</span><span class="mono">{_e(item["allowed"])}</span></div>'
        for item in risk["permissions"]
    )
    file_cards = "\n".join(
        f'              <article class="file-card"><span class="token mono">{_e(item["icon_token"])}</span><span class="mono">{_e(item["artifact_path"])}</span><span>{_e(item["category"])}</span><a class="local-link mono" href="{_e(item["local_href"])}">本地链接</a><span class="mono muted">{_e(item["external_effect"])}</span></article>'
        for item in manifest["artifacts"]
    )
    phase_cards = "\n".join(
        f'              <article class="phase-card"><strong class="mono">{_e(item["phase"])}</strong><p>{_e(item["theme"])}</p><span class="token safe mono">{_e(item["status"])}</span><p class="muted mono">{_e(item["external_effect"])}</p></article>'
        for item in timeline["timeline"]
    )
    version_rows = "\n".join(
        f'              <div class="version-row"><span>{label}</span><strong class="mono">{_e(value)}</strong></div>'
        for label, value in (
            ("当前阶段", build["phase"]),
            ("当前状态", build["status"]),
            ("UI 代际", build["ui_generation"]),
            ("最新 main commit", build["latest_main_commit"]),
            ("最新合并 PR", build["latest_merged_pr"]),
            ("是否生产环境", build["production_ready"]),
            ("是否允许交易", build["trading_enabled"]),
            ("外部影响", build["external_effect"]),
            ("生成时间", build["generated_at_utc"]),
        )
    )
    return f"""\
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{_e(shell["primary_title"])}</title>
    <link rel="stylesheet" href="assets/style.css">
  </head>
  <body>
    <div class="app-shell">
      <aside class="sidebar" aria-label="左侧导航">
        <div class="brand"><span class="brand-mark">AI</span><span class="brand-title">AI 投研交易驾驶舱</span><span class="brand-subtitle">贵金属观察系统</span></div>
        <nav class="sidebar-nav">
{nav_links}
        </nav>
        <div class="sidebar-note">本地静态只读 · 不连接 IBKR · 不请求行情</div>
      </aside>
      <div class="content">
        <header class="command-bar">
          <div>
            <h1>{_e(shell["primary_title"])}</h1>
            <p class="subtitle">{_e(shell["subtitle"])}</p>
            <div class="badge-row">
              <span class="badge safe">美股观察</span>
              <span class="badge safe">GLD / SLV</span>
              <span class="badge safe">只读模式</span>
              <span class="badge blocked">行情阻断</span>
              <span class="badge warn">非生产环境</span>
              <span class="badge safe">本地静态</span>
              <span class="badge secondary mono">US_ONLY</span>
              <span class="badge secondary mono">BLOCKED_BY_SUBSCRIPTION</span>
              <span class="badge secondary mono">IBKR_ERROR_10089</span>
              <span class="badge secondary mono">V7_HIGH_TECH_TRADING_VISUAL</span>
            </div>
          </div>
          <section class="build-chip"><span class="label">generated_at_utc</span><strong class="big-copy mono">{_e(status["generated_at_utc"])}</strong></section>
        </header>

        <section class="hero-grid" id="overview">
          <article class="panel" id="system-status">
            <div class="panel-header"><div><span class="eyebrow">系统状态</span><h2>系统状态</h2></div><span class="token safe">READY</span></div>
            <strong class="big-copy">本地只读投研驾驶舱已就绪</strong>
            <span class="small-copy mono">{_e(status["ui_status"])}</span>
          </article>
          <article class="panel" id="chart-panel">
            <div class="panel-header"><div><span class="eyebrow">静态图表占位</span><h2>图表面板</h2></div><span class="token warn">CSS ONLY</span></div>
            <div class="chart-shell" aria-label="静态占位 · 无实时行情"><span class="chart-watermark">静态占位 · 无实时行情</span><div class="bar-row"><span></span><span></span><span></span><span></span><span></span><span></span></div></div>
          </article>
          <article class="panel">
            <div class="panel-header"><div><span class="eyebrow">风险边界摘要</span><h2>安全边界</h2></div><span class="token disabled">LOCKED</span></div>
            <strong class="big-copy">所有外部动作已禁用</strong>
            <div class="metric-list">
              <div class="metric">IBKR 连接：禁用</div>
              <div class="metric">行情请求：禁用</div>
              <div class="metric">账户读取：禁用</div>
              <div class="metric">交易：禁用</div>
            </div>
          </article>
        </section>

        <main class="main-grid">
          <section class="card" id="market-data">
            <div class="card-header"><h2>行情权限状态</h2><span class="token blocked">IBKR 10089</span></div>
            <div class="version-table">
              <div class="version-row"><span>当前状态</span><strong>订阅权限阻断</strong></div>
              <div class="version-row"><span>IBKR 错误码</span><strong class="mono">10089</strong></div>
              <div class="version-row"><span>是否请求行情</span><strong>否</strong></div>
              <div class="version-row"><span>实时行情验证</span><strong>否</strong></div>
              <div class="version-row"><span>延迟行情可用</span><strong>是</strong></div>
            </div>
            <p class="muted">当前页面仅显示本地静态研究状态，不会发起行情请求或连接 IBKR。</p>
          </section>

          <section class="card" id="watchlist">
            <div class="card-header"><h2>市场观察</h2><span class="token safe">GLD / SLV</span></div>
            <div class="watch-grid">
{watch_cards}
            </div>
          </section>

          <section class="card">
            <div class="card-header"><h2>信号状态</h2><span class="token disabled">未启用</span></div>
            <div class="version-table">
              <div class="version-row"><span>信号模块</span><strong>{_e(signal["signal_module"])}</strong></div>
              <div class="version-row"><span>策略建议</span><strong>{_e(signal["strategy_output"])}</strong></div>
              <div class="version-row"><span>原因</span><strong>{_e(signal["reason"])}</strong></div>
              <div class="version-row"><span>当前状态</span><strong>{_e(signal["current_status"])}</strong></div>
            </div>
          </section>

          <section class="card full" id="risk-boundary">
            <div class="card-header"><h2>风险边界</h2><span class="token disabled">ALL DISABLED</span></div>
            <div class="risk-list">
{risk_items}
            </div>
          </section>

          <section class="card full" id="artifacts">
            <div class="card-header"><h2>本地文件流</h2><span class="token safe">LOCAL ARTIFACTS</span></div>
            <div class="file-stream">
{file_cards}
            </div>
          </section>

          <section class="card full" id="timeline">
            <div class="card-header"><h2>项目进度轨道</h2><span class="token safe">Phase 681-696</span></div>
            <div class="phase-rail">
{phase_cards}
            </div>
          </section>

          <section class="card full">
            <div class="card-header"><h2>版本与安全</h2><span class="token safe">LOCAL STATIC</span></div>
            <div class="version-table">
{version_rows}
            </div>
          </section>
        </main>
      </div>
    </div>
    <footer class="footer-safety-bar">未连接 IBKR · 未请求行情 · 未请求历史数据 · 未读取账户/持仓 · 未交易 · 未 Telegram 实发</footer>
  </body>
</html>
"""


def write_dashboard_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def _write_text(path: PathLike, text: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def build_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Phase 681-696 Dashboard High-Tech Trading Visual Rebuild Pack Report",
            "",
            "## Status",
            "",
            *[f"- {field}={row[field]}" for field in CSV_FIELDS],
            "",
            "## Safety Boundary",
            "",
            "- CSS-only static chart placeholder",
            "- no real market data",
            "- no real price axis",
            "- no real candlestick",
            "- no generated price values",
            "- no trading signals",
            "- no external URL/CDN",
            "- no IBKR connection",
            "- no market data request",
            "- no historical data request",
            "- no account/position read",
            "- no contract qualification",
            "- no trading",
            "- no Telegram real send",
            "- GLD / SLV only",
            "- JP / CN remain frozen",
        ]
    ) + "\n"


def build_pack(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Precious Metals Monitor Dashboard High-Tech Trading Visual Rebuild Pack",
            "",
            f"- phase={row['phase']}",
            f"- status={row['status']}",
            f"- ui_generation={row['ui_generation']}",
            "- high-tech Chinese trading dashboard visual rebuild",
            "- CSS-only static chart placeholder",
            "- public dashboard template-inspired layout language only",
            "- no copied external template code/images/fonts/icons",
            "- local static read-only artifact viewer only",
            f"- market data remains {row['market_data_status']} / IBKR_ERROR_{row['ibkr_error_code']}",
        ]
    ) + "\n"


def generate_dashboard_high_tech_trading_visual_rebuild_pack(
    *,
    output_index: PathLike = DASHBOARD_INDEX,
    output_css: PathLike = DASHBOARD_CSS,
    output_status_snapshot: PathLike = STATUS_SNAPSHOT,
    output_high_tech_visual_snapshot: PathLike = HIGH_TECH_VISUAL_SNAPSHOT,
    output_trading_shell_snapshot: PathLike = TRADING_SHELL_SNAPSHOT,
    output_static_chart_snapshot: PathLike = STATIC_CHART_SNAPSHOT,
    output_chinese_ui_snapshot: PathLike = CHINESE_UI_SNAPSHOT,
    output_template_reference_snapshot: PathLike = TEMPLATE_REFERENCE_SNAPSHOT,
    output_visual_density_snapshot: PathLike = VISUAL_DENSITY_SNAPSHOT,
    output_card_system_snapshot: PathLike = CARD_SYSTEM_SNAPSHOT,
    output_icon_system_snapshot: PathLike = ICON_SYSTEM_SNAPSHOT,
    output_timeline_polish_snapshot: PathLike = TIMELINE_POLISH_SNAPSHOT,
    output_build_snapshot: PathLike = BUILD_SNAPSHOT,
    output_operator_timeline: PathLike = OPERATOR_TIMELINE,
    output_watchlist_snapshot: PathLike = WATCHLIST_SNAPSHOT,
    output_signal_snapshot: PathLike = SIGNAL_SNAPSHOT,
    output_risk_snapshot: PathLike = RISK_SNAPSHOT,
    output_layout_snapshot: PathLike = LAYOUT_SNAPSHOT,
    output_navigation_snapshot: PathLike = NAVIGATION_SNAPSHOT,
    output_artifact_manifest: PathLike = ARTIFACT_MANIFEST,
    output_csv: PathLike = OUTPUT_CSV,
    output_report: PathLike = OUTPUT_REPORT,
    output_pack: PathLike = OUTPUT_PACK,
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    timestamp = generated_at or _now_timestamp()
    status = build_status_snapshot(timestamp)
    high_tech_visual = build_high_tech_visual_snapshot(timestamp)
    shell = build_trading_shell_snapshot(timestamp)
    static_chart = build_static_chart_snapshot(timestamp)
    chinese_ui = build_chinese_ui_snapshot(timestamp)
    template_reference = build_template_reference_snapshot(timestamp)
    visual_density = build_visual_density_snapshot(timestamp)
    card_system = build_card_system_snapshot(timestamp)
    icon_system = build_icon_system_snapshot(timestamp)
    timeline_polish = build_timeline_polish_snapshot(timestamp)
    build = build_build_snapshot(timestamp)
    timeline = build_operator_timeline(timestamp)
    watchlist = build_watchlist_snapshot(timestamp)
    signal = build_signal_snapshot(timestamp)
    risk = build_risk_snapshot(timestamp)
    layout = build_layout_snapshot(timestamp)
    navigation = build_navigation_snapshot(timestamp)
    manifest = build_artifact_manifest(timestamp)
    row = _status_row(status)

    _write_json(output_status_snapshot, status)
    _write_json(output_high_tech_visual_snapshot, high_tech_visual)
    _write_json(output_trading_shell_snapshot, shell)
    _write_json(output_static_chart_snapshot, static_chart)
    _write_json(output_chinese_ui_snapshot, chinese_ui)
    _write_json(output_template_reference_snapshot, template_reference)
    _write_json(output_visual_density_snapshot, visual_density)
    _write_json(output_card_system_snapshot, card_system)
    _write_json(output_icon_system_snapshot, icon_system)
    _write_json(output_timeline_polish_snapshot, timeline_polish)
    _write_json(output_build_snapshot, build)
    _write_json(output_operator_timeline, timeline)
    _write_json(output_watchlist_snapshot, watchlist)
    _write_json(output_signal_snapshot, signal)
    _write_json(output_risk_snapshot, risk)
    _write_json(output_layout_snapshot, layout)
    _write_json(output_navigation_snapshot, navigation)
    _write_json(output_artifact_manifest, manifest)
    _write_text(output_css, build_dashboard_css())
    _write_text(output_index, build_dashboard_html(status, shell, watchlist, signal, risk, timeline, navigation, build, manifest))
    write_dashboard_csv(output_csv, row)
    _write_text(output_report, build_report(row))
    _write_text(output_pack, build_pack(row))
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 681-696 dashboard high-tech trading visual rebuild pack.")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generate_dashboard_high_tech_trading_visual_rebuild_pack(generated_at=args.generated_at)
    print("[DASHBOARD_HIGH_TECH_TRADING_VISUAL_REBUILD_PACK] generated")
    print(f"status={STATUS}")
    print(f"ui_generation={UI_GENERATION}")
    print("high_tech_visual_status=HIGH_TECH_TRADING_DASHBOARD_VISUAL_READY")
    print("trading_shell_status=STATIC_TRADING_SHELL_READY")
    print("static_chart_status=CSS_ONLY_STATIC_CHART_PLACEHOLDER_READY")
    print("chart_data_status=NO_REAL_MARKET_DATA_NO_PRICE_AXIS")
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
