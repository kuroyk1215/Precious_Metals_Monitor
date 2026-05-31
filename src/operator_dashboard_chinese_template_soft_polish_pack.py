from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


PHASE = "Phase 673-680"
STATUS = "DASHBOARD_CHINESE_TEMPLATE_SOFT_POLISH_READY"
UI_MODE = "LOCAL_STATIC_RESEARCH_CONSOLE"
UI_GENERATION = "V6_CHINESE_TEMPLATE_SOFT_POLISH"
LATEST_MAIN_COMMIT = "53c5d1f"
LATEST_MERGED_PR = "222"
CURRENT_BRANCH_BASIS = "main"
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
NEXT_OPERATOR_ACTION = "SUBSCRIBE_NETWORK_B_OR_KEEP_FRAMEWORK_ONLY_READONLY_MVP"

DASHBOARD_INDEX = "dashboard/index.html"
DASHBOARD_CSS = "dashboard/assets/style.css"
STATUS_SNAPSHOT = "dashboard/data/status_snapshot.json"
VISUAL_DENSITY_SNAPSHOT = "dashboard/data/visual_density_snapshot.json"
CARD_SYSTEM_SNAPSHOT = "dashboard/data/card_system_snapshot.json"
ICON_SYSTEM_SNAPSHOT = "dashboard/data/icon_system_snapshot.json"
TIMELINE_POLISH_SNAPSHOT = "dashboard/data/timeline_polish_snapshot.json"
CHINESE_UI_SNAPSHOT = "dashboard/data/chinese_ui_snapshot.json"
TEMPLATE_REFERENCE_SNAPSHOT = "dashboard/data/template_reference_snapshot.json"
WATCHLIST_SNAPSHOT = "dashboard/data/watchlist_snapshot.json"
SIGNAL_SNAPSHOT = "dashboard/data/signal_snapshot.json"
RISK_SNAPSHOT = "dashboard/data/risk_snapshot.json"
OPERATOR_TIMELINE = "dashboard/data/operator_timeline.json"
LAYOUT_SNAPSHOT = "dashboard/data/layout_snapshot.json"
NAVIGATION_SNAPSHOT = "dashboard/data/navigation_snapshot.json"
BUILD_SNAPSHOT = "dashboard/data/build_snapshot.json"
ARTIFACT_MANIFEST = "dashboard/data/artifact_manifest.json"
OUTPUT_CSV = "operator_dashboard_chinese_template_soft_polish_pack.csv"
OUTPUT_REPORT = "reports/operator_dashboard_chinese_template_soft_polish_pack_report.md"
OUTPUT_PACK = "Precious_Metals_Monitor_Dashboard_Chinese_Template_Soft_Polish_Pack.md"

SECTIONS = (
    "SIDEBAR",
    "TOP_HEADER",
    "STATUS_TOKEN_BAR",
    "SUMMARY_CARD_STRIP",
    "DENSE_MATRIX_GRID",
    "ARTIFACT_READER",
    "SAFETY_FOOTER",
    "BUILD_VERSION_PANEL",
)

NAV_ITEMS = (
    ("Dashboard", "DASHBOARD", "#dashboard"),
    ("Watchlist", "WATCHLIST", "#watchlist"),
    ("Signals", "SIGNAL", "#signals"),
    ("Risk Boundary", "RISK", "#risk-boundary"),
    ("Artifacts", "ARTIFACT", "#artifacts"),
    ("Timeline", "TIMELINE", "#timeline"),
    ("System Status", "SYSTEM", "#system-status"),
    ("Settings", "SETTINGS", "#settings"),
)

ICON_TOKENS = (
    "DASHBOARD",
    "WATCHLIST",
    "SIGNAL",
    "RISK",
    "ARTIFACT",
    "TIMELINE",
    "SYSTEM",
    "SETTINGS",
    "LOCAL",
    "READ_ONLY",
    "BLOCKED",
    "WARNING",
    "SAFETY",
)

TIMELINE_ITEMS = (
    "Phase 633-640",
    "Phase 641-648",
    "Phase 649-656",
    "Phase 657-664",
    "Phase 665-672",
    "Phase 673-680",
)

CARD_TYPES = (
    "SUMMARY_CARD",
    "STATUS_CARD",
    "MATRIX_CARD",
    "TABLE_CARD",
    "TIMELINE_CARD",
    "ARTIFACT_CARD",
    "ACTION_CARD",
    "SAFETY_CARD",
)

STATUS_TOKENS = (
    "SAFE",
    "WARNING",
    "DISABLED",
    "BLOCKED",
    "LOCAL_ONLY",
    "READ_ONLY",
    "NOT_PRODUCTION",
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

ARTIFACTS = (
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    STATUS_SNAPSHOT,
    VISUAL_DENSITY_SNAPSHOT,
    CARD_SYSTEM_SNAPSHOT,
    ICON_SYSTEM_SNAPSHOT,
    TIMELINE_POLISH_SNAPSHOT,
    CHINESE_UI_SNAPSHOT,
    TEMPLATE_REFERENCE_SNAPSHOT,
    WATCHLIST_SNAPSHOT,
    SIGNAL_SNAPSHOT,
    RISK_SNAPSHOT,
    OPERATOR_TIMELINE,
    ARTIFACT_MANIFEST,
    LAYOUT_SNAPSHOT,
    NAVIGATION_SNAPSHOT,
    BUILD_SNAPSHOT,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)

CSV_FIELDS = (
    "phase",
    "status",
    "ui_mode",
    "ui_generation",
    "visual_density_status",
    "card_system_status",
    "icon_system_status",
    "timeline_polish_status",
    "chinese_ui_status",
    "language_mode",
    "template_reference_status",
    "reference_mode",
    "copied_external_code",
    "loaded_external_assets",
    "soft_polish_status",
    "matrix_status",
    "artifact_reader_status",
    "build_panel_status",
    "market_scope",
    "symbols",
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
        "ui_mode": UI_MODE,
        "ui_generation": UI_GENERATION,
        "layout_status": "SIDEBAR_HEADER_FOOTER_READY",
        "navigation_status": "STATIC_NAVIGATION_READY",
        "visual_polish_status": "PLATFORM_SHELL_POLISHED",
        "visual_density_status": "HIGH_DENSITY_CONSOLE_READY",
        "card_system_status": "CARD_SYSTEM_READY",
        "icon_system_status": "LOCAL_ICON_SYSTEM_READY",
        "timeline_polish_status": "COMPACT_TIMELINE_POLISHED",
        "chinese_ui_status": "CHINESE_MAIN_UI_READY",
        "template_reference_status": "PUBLIC_TEMPLATE_INSPIRED_LAYOUT_READY",
        "language_mode": "ZH_CN_PRIMARY",
        "reference_mode": "PUBLIC_DASHBOARD_LAYOUT_LANGUAGE_ONLY",
        "copied_external_code": NO_TEXT,
        "loaded_external_assets": NO_TEXT,
        "soft_polish_status": "SOFT_POLISH_APPLIED",
        "matrix_status": "RISK_SIGNAL_MATRIX_READY",
        "artifact_reader_status": "FILE_BROWSER_STYLE_READY",
        "build_panel_status": "BUILD_VERSION_SAFETY_DENSE_READY",
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


def build_visual_density_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": STATUS,
        "density_mode": "HIGH_INFORMATION_DENSITY_STATIC_CONSOLE",
        "table_density": "COMPACT",
        "card_spacing": "COMPACT",
        "status_badge_density": "HIGH",
        "footer_safety_bar": "ENABLED",
        "responsive_layout": YES_TEXT,
        "external_assets": NO_TEXT,
        "javascript_required": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_card_system_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "CARD_SYSTEM_READY",
        "card_types": list(CARD_TYPES),
        "status_tokens": list(STATUS_TOKENS),
        "external_assets": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_icon_system_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "LOCAL_ICON_SYSTEM_READY",
        "icon_mode": "TEXT_ONLY_LOCAL_ICON_TOKENS",
        "external_icon_library": NO_TEXT,
        "remote_icon_assets": NO_TEXT,
        "icon_tokens": list(ICON_TOKENS),
        "generated_at_utc": timestamp,
    }


def build_timeline_polish_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "COMPACT_TIMELINE_POLISHED",
        "timeline_mode": "STATIC_OPERATOR_PHASE_TIMELINE",
        "timeline_items": list(TIMELINE_ITEMS),
        "external_effect": EXTERNAL_EFFECT,
        "generated_at_utc": timestamp,
    }


def build_chinese_ui_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "CHINESE_MAIN_UI_READY",
        "language_mode": "ZH_CN_PRIMARY",
        "primary_title": "AI 投研控制台 · 贵金属观察系统",
        "subtitle": "本地静态只读 · 非生产环境 · 无外部连接 · 无交易权限",
        "nav_labels": ["总览", "观察列表", "信号面板", "风险边界", "产物浏览", "阶段时间线", "系统状态", "设置"],
        "panel_labels": [
            "市场数据阻断",
            "观察列表",
            "信号面板",
            "风险边界",
            "产物浏览",
            "操作阶段时间线",
            "卡片系统",
            "构建 / 版本 / 安全",
        ],
        "technical_status_codes": "SECONDARY_ONLY",
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
        "inspiration_types": [
            "LEFT_NAV_TOP_SUMMARY_DENSE_DATA_GRID",
            "CHINESE_ENTERPRISE_DASHBOARD_SPACING_LANGUAGE",
            "SOFT_PAPER_SURFACE_ACCENT_LANGUAGE",
        ],
        "applied_design_patterns": [
            "LOCAL_STATIC_APP_SHELL",
            "COMPACT_STATUS_TOKEN_BAR",
            "DENSE_READ_ONLY_ARTIFACT_TABLE",
            "DISABLED_RISK_SIGNAL_MATRIX",
        ],
        "generated_at_utc": timestamp,
    }


def build_watchlist_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "scope": MARKET_SCOPE,
        "symbols": [
            {
                "symbol": symbol,
                "asset": "ETF",
                "market": "US",
                "data_status": MARKET_DATA_STATUS,
                "realtime": NO_TEXT,
                "delayed": YES_TEXT,
                "tradability_view": "RESEARCH_ONLY_NO_TRADING_ACTION",
            }
            for symbol in SYMBOLS
        ],
        "generated_at_utc": timestamp,
    }


def build_signal_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "signal_mode": "STATIC_DISABLED_MATRIX",
        "trading_signal_enabled": NO_TEXT,
        "recommendation_enabled": NO_TEXT,
        "symbols": [
            {
                "symbol": symbol,
                "short": "DISABLED",
                "mid": "DISABLED",
                "long": "DISABLED",
                "rolling": "DISABLED",
                "reason": MARKET_DATA_CLASSIFICATION,
            }
            for symbol in SYMBOLS
        ],
        "generated_at_utc": timestamp,
    }


def build_risk_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "risk_mode": "STATIC_DISABLED_PERMISSION_MATRIX",
        "max_external_effect": EXTERNAL_EFFECT,
        "permissions": [
            {"action": action, "function": action, "status": "DISABLED", "allowed": NO_TEXT}
            for action in BLOCKED_ACTIONS
        ],
        "generated_at_utc": timestamp,
    }


def build_operator_timeline(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "timeline": [
            {
                "phase": "Phase 633-640",
                "theme": "Dashboard UI enhancement",
                "status": "DASHBOARD_UI_ENHANCEMENT_READY",
                "visual_tier": "V1_STATIC_SHELL",
                "external_effect": EXTERNAL_EFFECT,
                "notes": "Initial local static dashboard shell.",
            },
            {
                "phase": "Phase 641-648",
                "theme": "Dashboard UI v2 data panels",
                "status": "DASHBOARD_UI_V2_DATA_PANEL_READY",
                "visual_tier": "V2_DATA_PANELS",
                "external_effect": EXTERNAL_EFFECT,
                "notes": "Added dense local data panels and artifact reader.",
            },
            {
                "phase": "Phase 649-656",
                "theme": "Dashboard UI v3 layout polish",
                "status": "DASHBOARD_UI_V3_LAYOUT_POLISH_READY",
                "visual_tier": "V3_LAYOUT_POLISH",
                "external_effect": EXTERNAL_EFFECT,
                "notes": "Added sidebar, header, summary strip, and safety footer.",
            },
            {
                "phase": "Phase 657-664",
                "theme": "Visual density and card system",
                "status": "DASHBOARD_VISUAL_DENSITY_CARD_SYSTEM_READY",
                "visual_tier": "V4_VISUAL_DENSITY",
                "external_effect": EXTERNAL_EFFECT,
                "notes": "Upgraded matrix tables, card hierarchy, and compact reader density.",
            },
            {
                "phase": "Phase 665-672",
                "theme": "Icon / Timeline / Artifact polish",
                "status": "DASHBOARD_ICON_TIMELINE_ARTIFACT_POLISH_READY",
                "visual_tier": "V5_ICON_TIMELINE_ARTIFACT_POLISH",
                "external_effect": EXTERNAL_EFFECT,
                "notes": "Added local icon tokens, compact timeline polish, file browser artifact reader, and dense build safety metadata.",
            },
            {
                "phase": PHASE,
                "theme": "Chinese Template-Inspired Soft Polish",
                "status": STATUS,
                "visual_tier": "V6_CHINESE_TEMPLATE_SOFT_POLISH",
                "external_effect": EXTERNAL_EFFECT,
                "notes": "Applied soft paper surfaces, restrained ink-red/gold/jade accents, and Chinese enterprise dashboard-inspired spacing while preserving the local read-only boundary.",
            },
        ],
        "generated_at_utc": timestamp,
    }


def build_layout_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": STATUS,
        "layout_mode": "DESKTOP_STATIC_APP_SHELL",
        "sections": list(SECTIONS),
        "responsive_layout": YES_TEXT,
        "external_assets": NO_TEXT,
        "javascript_required": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_navigation_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "nav_mode": "STATIC_LOCAL_NAVIGATION",
        "active": "Dashboard",
        "items": [
            {"label": label, "icon_text": icon_text, "href": href, "enabled": YES_TEXT, "external_url": NO_TEXT}
            for label, icon_text, href in NAV_ITEMS
        ],
        "generated_at_utc": timestamp,
    }


def build_build_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": STATUS,
        "latest_main_commit": LATEST_MAIN_COMMIT,
        "latest_merged_pr": LATEST_MERGED_PR,
        "current_branch_basis": CURRENT_BRANCH_BASIS,
        "ui_generation": UI_GENERATION,
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
    if path.startswith("reports/"):
        return "REPORT"
    return "PACK"


def _artifact_icon_token(path: str) -> str:
    category = _artifact_category(path)
    if category == "HTML":
        return "HTML_DOC"
    if category == "CSS":
        return "CSS_STYLE"
    if category == "JSON":
        return "JSON_DATA"
    if category == "CSV":
        return "CSV_TABLE"
    if category == "REPORT":
        return "MD_REPORT"
    return "HANDOFF_PACK"


def _artifact_local_href_value(path: str) -> str:
    if path.startswith("dashboard/"):
        return path.replace("dashboard/", "", 1)
    return f"../{path}"


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
                "icon_token": _artifact_icon_token(path),
                "local_href": _artifact_local_href_value(path),
                "external_effect": EXTERNAL_EFFECT,
            }
            for path in ARTIFACTS
        ],
        "generated_at_utc": timestamp,
    }


def _write_json(path: PathLike, payload: Dict[str, object]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _snapshot_to_row(snapshot: Dict[str, object]) -> Dict[str, str]:
    return {
        "phase": str(snapshot["phase"]),
        "status": str(snapshot["status"]),
        "ui_mode": str(snapshot["ui_mode"]),
        "ui_generation": str(snapshot["ui_generation"]),
        "visual_density_status": str(snapshot["visual_density_status"]),
        "card_system_status": str(snapshot["card_system_status"]),
        "icon_system_status": str(snapshot["icon_system_status"]),
        "timeline_polish_status": str(snapshot["timeline_polish_status"]),
        "chinese_ui_status": str(snapshot["chinese_ui_status"]),
        "language_mode": "ZH_CN_PRIMARY",
        "template_reference_status": str(snapshot["template_reference_status"]),
        "reference_mode": "PUBLIC_DASHBOARD_LAYOUT_LANGUAGE_ONLY",
        "copied_external_code": NO_TEXT,
        "loaded_external_assets": NO_TEXT,
        "soft_polish_status": str(snapshot["soft_polish_status"]),
        "matrix_status": str(snapshot["matrix_status"]),
        "artifact_reader_status": str(snapshot["artifact_reader_status"]),
        "build_panel_status": str(snapshot["build_panel_status"]),
        "market_scope": str(snapshot["market_scope"]),
        "symbols": ",".join(str(symbol) for symbol in snapshot["symbols"]),
        "market_data_status": str(snapshot["market_data_status"]),
        "market_data_classification": str(snapshot["market_data_classification"]),
        "ibkr_error_code": str(snapshot["ibkr_error_code"]),
        "realtime_market_data_verified": str(snapshot["realtime_market_data_verified"]),
        "production_ready": str(snapshot["production_ready"]),
        "trading_enabled": str(snapshot["trading_enabled"]),
        "account_read_enabled": str(snapshot["account_read_enabled"]),
        "positions_read_enabled": str(snapshot["positions_read_enabled"]),
        "historical_data_enabled": str(snapshot["historical_data_enabled"]),
        "telegram_real_send_enabled": str(snapshot["telegram_real_send_enabled"]),
        "external_effect": str(snapshot["external_effect"]),
        "jp_status": str(snapshot["jp_status"]),
        "cn_status": str(snapshot["cn_status"]),
        "generated_at_utc": str(snapshot["generated_at_utc"]),
    }


def write_dashboard_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_dashboard_css() -> str:
    return """\
:root {
  color-scheme: light;
  --bg: #f5f7f8;
  --sidebar: #1d252e;
  --panel: #ffffff;
  --panel-2: #f0f3f5;
  --panel-3: #eef1f2;
  --line: #d7dee2;
  --line-soft: #e6ebee;
  --text: #1b252c;
  --muted: #667580;
  --blue: #2f6fb0;
  --cyan: #1a8b96;
  --green: #1d8a5a;
  --amber: #b7791f;
  --red: #b63a36;
  --ink: #26313a;
  --gold-soft: #f5e6bd;
  --jade-soft: #dcefe7;
  --red-soft: #f6ded9;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background:
    linear-gradient(180deg, rgba(246, 222, 217, 0.55), rgba(245, 247, 248, 0) 230px),
    var(--bg);
  color: var(--text);
  font-family: Arial, Helvetica, sans-serif;
  font-size: 13px;
  line-height: 1.38;
}
a { color: inherit; text-decoration: none; }
.app-shell {
  display: grid;
  grid-template-columns: 252px minmax(0, 1fr);
  min-height: 100vh;
}
.sidebar {
  background: var(--sidebar);
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 18px 14px;
}
.brand, .summary-top, .card-header {
  align-items: center;
  display: flex;
  gap: 10px;
}
.brand-mark, .nav-icon, .summary-icon {
  align-items: center;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 8px;
  display: inline-flex;
  flex: 0 0 auto;
  font-weight: 800;
  height: 32px;
  justify-content: center;
  width: 32px;
}
.icon-token {
  border-color: rgba(245, 230, 189, 0.6);
  color: #f7ddb0;
  font-family: Consolas, Monaco, monospace;
  font-size: 8px;
  letter-spacing: 0;
  overflow: hidden;
  padding: 0 3px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.nav-icon.icon-token {
  width: 58px;
}
.summary-icon.icon-token {
  width: 72px;
}
.brand-title { display: block; font-size: 13px; font-weight: 800; }
.brand-title, .brand-subtitle, .nav-section-label, .sidebar .badge { color: #f4f7f8; }
.brand-subtitle, .nav-section-label, .caption, .label, .eyebrow {
  color: var(--muted);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}
.sidebar-nav { display: grid; gap: 5px; }
.nav-item {
  align-items: center;
  border: 1px solid transparent;
  border-radius: 8px;
  color: #c3cbd0;
  display: flex;
  gap: 9px;
  min-height: 38px;
  padding: 5px 8px;
}
.nav-item.active {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(245, 230, 189, 0.56);
  color: #ffffff;
}
.console-mode {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 8px;
  margin-top: auto;
  padding: 10px;
}
.mode-list, .token-stack { display: grid; gap: 6px; margin-top: 8px; }
.content { min-width: 0; padding: 18px 22px 68px; }
.topbar {
  align-items: start;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid var(--line);
  border-radius: 8px;
  display: grid;
  gap: 14px;
  grid-template-columns: minmax(0, 1fr) auto;
  padding: 16px;
}
h1 { font-size: 26px; line-height: 1.1; margin: 0; }
.subtitle { color: var(--muted); margin: 7px 0 0; }
.badge-bar, .flag-row { display: flex; flex-wrap: wrap; gap: 6px; }
.badge, .token {
  align-items: center;
  background: #ffffff;
  border: 1px solid var(--line);
  border-radius: 999px;
  display: inline-flex;
  font-size: 10px;
  font-weight: 800;
  min-height: 24px;
  padding: 3px 8px;
}
.safe, .status-safe { border-color: rgba(112, 214, 143, 0.55); color: var(--green); }
.warn, .status-warn { border-color: rgba(242, 189, 85, 0.65); color: var(--amber); }
.disabled, .blocked, .status-disabled { border-color: rgba(255, 116, 104, 0.6); color: var(--red); }
.build-box, .summary-card, .card {
  background: var(--panel);
  border: 1px solid var(--line);
  box-shadow: 0 8px 22px rgba(29, 37, 46, 0.05);
  border-radius: 8px;
  min-width: 0;
}
.build-box { min-width: 270px; padding: 10px 12px; }
.summary-strip {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 14px 0;
}
.summary-card { padding: 12px; }
.summary-card:nth-child(1) { border-top: 3px solid var(--red); }
.summary-card:nth-child(2) { border-top: 3px solid var(--amber); }
.summary-card:nth-child(3) { border-top: 3px solid var(--green); }
.summary-card:nth-child(4) { border-top: 3px solid var(--blue); }
.summary-value {
  display: block;
  font-size: 14px;
  font-weight: 800;
  margin-top: 6px;
  overflow-wrap: anywhere;
}
.summary-note { color: var(--muted); display: block; font-size: 11px; margin-top: 4px; }
.card-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(12, minmax(0, 1fr));
}
.card { grid-column: span 4; padding: 13px; }
.card.wide { grid-column: span 8; }
.card.full { grid-column: 1 / -1; }
.card-header {
  border-bottom: 1px solid var(--line-soft);
  justify-content: space-between;
  margin: -2px 0 10px;
  padding-bottom: 8px;
}
.card h2 { font-size: 15px; margin: 0; }
.mono { font-family: Consolas, Monaco, monospace; }
.dense-table, .matrix-table, .artifact-table, .timeline-table {
  border-collapse: collapse;
  font-size: 12px;
  width: 100%;
}
th, td {
  border-bottom: 1px solid var(--line-soft);
  padding: 6px 8px;
  text-align: left;
  vertical-align: top;
}
th {
  color: var(--muted);
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
}
tbody tr {
  transition: background-color 120ms ease, border-color 120ms ease;
}
tbody tr:hover td {
  background: rgba(47, 111, 176, 0.055);
}
td:first-child, th:first-child { padding-left: 0; }
.risk-disabled-row td, .signal-disabled-row td { background: rgba(255, 116, 104, 0.035); }
.card-header {
  background: linear-gradient(90deg, rgba(246, 222, 217, 0.55), rgba(220, 239, 231, 0));
}
.artifact-table td:first-child { overflow-wrap: anywhere; }
.artifact-path {
  max-width: 360px;
  overflow-wrap: anywhere;
}
.artifact-icon, .phase-badge, .local-link {
  border: 1px solid var(--line);
  border-radius: 999px;
  display: inline-flex;
  font-size: 10px;
  font-weight: 800;
  max-width: 100%;
  min-height: 22px;
  padding: 3px 7px;
}
.artifact-icon {
  background: rgba(85, 200, 217, 0.08);
  border-color: rgba(85, 200, 217, 0.42);
  color: var(--cyan);
}
.phase-badge {
  background: rgba(121, 173, 255, 0.08);
  border-color: rgba(121, 173, 255, 0.45);
  color: var(--blue);
  white-space: nowrap;
}
.local-link {
  background: rgba(112, 214, 143, 0.07);
  border-color: rgba(112, 214, 143, 0.45);
  color: var(--green);
  overflow-wrap: anywhere;
}
.row-note {
  color: var(--muted);
  display: block;
  font-size: 11px;
  margin-top: 3px;
}
.warning-strip {
  background: rgba(242, 189, 85, 0.08);
  border: 1px solid rgba(242, 189, 85, 0.38);
  border-radius: 8px;
  color: var(--amber);
  font-weight: 800;
  margin-top: 10px;
  padding: 9px 10px;
}
.danger-strip {
  background: rgba(255, 116, 104, 0.08);
  border-color: rgba(255, 116, 104, 0.42);
  color: var(--red);
}
.footer-safety-bar {
  background: var(--ink);
  border-top: 1px solid var(--line);
  bottom: 0;
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
  left: 252px;
  padding: 11px 22px;
  position: fixed;
  right: 0;
  z-index: 5;
}
@media (max-width: 1100px) {
  .app-shell { grid-template-columns: 1fr; }
  .sidebar { border-bottom: 1px solid var(--line); border-right: 0; }
  .sidebar-nav { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .console-mode { margin-top: 0; }
  .footer-safety-bar { left: 0; }
  .summary-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .card, .card.wide { grid-column: span 6; }
}
@media (max-width: 720px) {
  .content { padding: 16px 12px 92px; }
  .topbar { grid-template-columns: 1fr; }
  .build-box { min-width: 0; }
  .sidebar-nav, .summary-strip { grid-template-columns: 1fr; }
  .card, .card.wide { grid-column: 1 / -1; }
  .dense-table, .matrix-table, .artifact-table, .timeline-table { display: block; overflow-x: auto; }
}
"""


def _dd(value: object) -> str:
    return escape(str(value))


def _artifact_href(path: str) -> str:
    if path.startswith("dashboard/"):
        return escape(path.replace("dashboard/", "", 1))
    return "../" + escape(path)


def _card_header(title: str, eyebrow: str, token: str, token_class: str = "safe") -> str:
    return (
        f'            <div class="card-header"><div><span class="eyebrow">{escape(eyebrow)}</span>'
        f"<h2>{escape(title)}</h2></div><span class=\"token {token_class}\">{escape(token)}</span></div>"
    )


def build_dashboard_html(
    status: Dict[str, object],
    visual_density: Dict[str, object],
    card_system: Dict[str, object],
    icon_system: Dict[str, object],
    timeline_polish: Dict[str, object],
    chinese_ui: Dict[str, object],
    template_reference: Dict[str, object],
    watchlist: Dict[str, object],
    signal: Dict[str, object],
    risk: Dict[str, object],
    timeline: Dict[str, object],
    layout: Dict[str, object],
    navigation: Dict[str, object],
    build: Dict[str, object],
    manifest: Dict[str, object],
) -> str:
    nav_label_by_icon = {
        "DASHBOARD": "总览",
        "WATCHLIST": "观察列表",
        "SIGNAL": "信号面板",
        "RISK": "风险边界",
        "ARTIFACT": "产物浏览",
        "TIMELINE": "阶段时间线",
        "SYSTEM": "系统状态",
        "SETTINGS": "设置",
    }
    nav_links = "\n".join(
        f'          <a class="nav-item{" active" if item["label"] == "Dashboard" else ""}" href="{escape(item["href"])}"><span class="nav-icon icon-token">{escape(item["icon_text"])}</span><span>{escape(nav_label_by_icon.get(str(item["icon_text"]), str(item["label"])))}</span></a>'
        for item in navigation["items"]
    )
    watchlist_rows = "\n".join(
        f"              <tr><td class=\"mono\">{escape(item['symbol'])}</td><td>{escape(item['asset'])}</td><td>{escape(item['market'])}</td><td class=\"mono status-disabled\">{escape(item['data_status'])}</td><td class=\"mono status-safe\">{escape(item['realtime'])}</td><td class=\"mono status-warn\">{escape(item['delayed'])}</td><td class=\"mono\">{escape(item['tradability_view'])}</td></tr>"
        for item in watchlist["symbols"]
    )
    signal_rows = "\n".join(
        f"              <tr class=\"signal-disabled-row\"><td class=\"mono\">{escape(item['symbol'])}</td><td class=\"mono status-disabled\">{escape(item['short'])}</td><td class=\"mono status-disabled\">{escape(item['mid'])}</td><td class=\"mono status-disabled\">{escape(item['long'])}</td><td class=\"mono status-disabled\">{escape(item['rolling'])}</td><td class=\"mono\">{escape(item['reason'])}</td></tr>"
        for item in signal["symbols"]
    )
    risk_rows = "\n".join(
        f"              <tr class=\"risk-disabled-row\"><td class=\"mono\">{escape(item['action'])}</td><td>{escape(item['function'])}</td><td class=\"mono status-disabled\">{escape(item['status'])}</td><td class=\"mono status-safe\">{escape(item['allowed'])}</td></tr>"
        for item in risk["permissions"]
    )
    timeline_rows = "\n".join(
        f"              <tr><td><span class=\"phase-badge mono\">{escape(item['phase'])}</span></td><td><strong>{escape(item['theme'])}</strong><span class=\"row-note\">{escape(item['notes'])}</span></td><td class=\"mono status-safe\">{escape(item['status'])}</td><td class=\"mono\">{escape(item['visual_tier'])}</td><td class=\"mono\">{escape(item['external_effect'])}</td></tr>"
        for item in timeline["timeline"]
    )
    artifact_rows = "\n".join(
        f'              <tr><td><span class="artifact-icon mono">{escape(item["icon_token"])}</span></td><td class="mono artifact-path">{escape(item["artifact_path"])}</td><td class="mono">{escape(item["type"])}</td><td class="mono">{escape(item["category"])}</td><td><a class="local-link mono" href="{escape(item["local_href"])}">{escape(item["local_href"])}</a></td><td class="mono status-safe">{escape(item["external_effect"])}</td></tr>'
        for item in manifest["artifacts"]
    )
    market_data_rows = "\n".join(
        f"              <tr><td class=\"mono\">{field}</td><td class=\"mono {klass}\">{value}</td><td class=\"mono {severity_class}\">{severity}</td></tr>"
        for field, value, klass, severity, severity_class in (
            ("ibkr_error_code", _dd(status["ibkr_error_code"]), "", "BLOCKED", "status-disabled"),
            ("subscription_required", _dd(status["subscription_required"]), "status-warn", "WARNING", "status-warn"),
            ("delayed_available", _dd(status["delayed_available"]), "status-warn", "WARNING", "status-warn"),
            (
                "realtime_market_data_verified",
                _dd(status["realtime_market_data_verified"]),
                "status-safe",
                "BLOCKED",
                "status-disabled",
            ),
        )
    )
    symbols_text = escape(" / ".join(str(symbol) for symbol in status["symbols"]))
    return f"""\
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{_dd(chinese_ui["primary_title"])}</title>
    <link rel="stylesheet" href="assets/style.css">
  </head>
  <body>
    <div class="app-shell" id="dashboard">
      <aside class="sidebar" aria-label="Sidebar navigation">
        <div class="brand">
            <span class="brand-mark">PM</span>
          <div>
            <span class="brand-title">AI 投研控制台</span>
            <span class="brand-subtitle">贵金属观察系统</span>
          </div>
        </div>
        <div>
          <div class="nav-section-label">导航</div>
          <nav class="sidebar-nav">
{nav_links}
          </nav>
        </div>
        <section class="console-mode" aria-label="Console Mode">
          <div class="nav-section-label">控制台模式</div>
          <div class="mode-list">
            <span class="badge safe">LOCAL_ONLY</span>
            <span class="badge safe">READ_ONLY</span>
            <span class="badge disabled">BLOCKED</span>
            <span class="badge warn">NOT_PRODUCTION</span>
          </div>
        </section>
      </aside>

      <div class="content">
        <header class="topbar">
          <div>
            <h1>{_dd(chinese_ui["primary_title"])}</h1>
            <p class="subtitle">{_dd(chinese_ui["subtitle"])}</p>
            <div class="badge-bar" aria-label="status token bar">
              <span class="badge safe">US_ONLY</span>
              <span class="badge safe">READ_ONLY</span>
              <span class="badge disabled">DATA_BLOCKED</span>
              <span class="badge warn">NOT_PRODUCTION</span>
              <span class="badge safe">V6_SOFT_POLISH</span>
              <span class="badge safe">CHINESE_TEMPLATE</span>
              <span class="badge safe">LOCAL_ICONS</span>
              <span class="badge safe">STATIC_ARTIFACTS</span>
            </div>
          </div>
          <section class="build-box" aria-label="build box">
            <span class="label">generated_at_utc</span>
            <strong class="summary-value mono">{_dd(status["generated_at_utc"])}</strong>
            <span class="caption">file local static</span>
          </section>
        </header>

        <section class="summary-strip" aria-label="summary cards">
          <div class="summary-card"><div class="summary-top"><span class="summary-icon icon-token">SYSTEM</span><span class="label">界面状态</span></div><span class="summary-value mono">{_dd(status["ui_status"])}</span><span class="summary-note">Phase 673-680 Chinese template-inspired soft polish</span></div>
          <div class="summary-card"><div class="summary-top"><span class="summary-icon icon-token">BLOCKED</span><span class="label">市场数据</span></div><span class="summary-value mono status-disabled">{_dd(status["market_data_status"])}</span><span class="summary-note">IBKR error code {_dd(status["ibkr_error_code"])}</span></div>
          <div class="summary-card"><div class="summary-top"><span class="summary-icon icon-token">WATCHLIST</span><span class="label">观察列表</span></div><span class="summary-value mono">{symbols_text}</span><span class="summary-note">US ETF scope only</span></div>
          <div class="summary-card"><div class="summary-top"><span class="summary-icon icon-token">LOCAL</span><span class="label">外部影响</span></div><span class="summary-value mono status-warn">{_dd(status["external_effect"])}</span><span class="summary-note">Local artifact generation only</span></div>
        </section>

        <main class="card-grid">
          <section class="card" id="system-status">
{_card_header("Market Data Block", "status matrix", "BLOCKED", "blocked")}
            <table class="matrix-table">
              <thead><tr><th>Field</th><th>Value</th><th>Severity</th></tr></thead>
              <tbody>
{market_data_rows}
              </tbody>
            </table>
            <div class="warning-strip danger-strip">Market data access blocked by subscription. No market data requests will be made.</div>
          </section>

          <section class="card wide" id="watchlist">
{_card_header("Watchlist", "compact table", "GLD / SLV", "safe")}
            <table class="dense-table">
              <thead><tr><th>Symbol</th><th>Asset</th><th>Market</th><th>Data Status</th><th>Realtime</th><th>Delayed</th><th>Tradability View</th></tr></thead>
              <tbody>
{watchlist_rows}
              </tbody>
            </table>
          </section>

          <section class="card wide" id="signals">
{_card_header("Signal Panel", "disabled matrix", "DISABLED", "disabled")}
            <table class="matrix-table">
              <thead><tr><th>Symbol</th><th>Short</th><th>Mid</th><th>Long</th><th>Rolling</th><th>Reason</th></tr></thead>
              <tbody>
{signal_rows}
              </tbody>
            </table>
            <div class="warning-strip">trading_signal_enabled={_dd(signal["trading_signal_enabled"])} · recommendation_enabled={_dd(signal["recommendation_enabled"])}</div>
          </section>

          <section class="card full" id="risk-boundary">
{_card_header("Risk Boundary", "permission matrix", "ALL DISABLED", "disabled")}
            <table class="matrix-table">
              <thead><tr><th>Action / Function</th><th>Function</th><th>Status</th><th>Allowed</th></tr></thead>
              <tbody>
{risk_rows}
              </tbody>
            </table>
            <div class="warning-strip danger-strip">All functions are disabled in this read-only research console.</div>
          </section>

          <section class="card wide" id="artifacts">
{_card_header("Artifact Reader", "static manifest", "READ_ONLY", "safe")}
            <table class="artifact-table">
              <thead><tr><th>Icon</th><th>Artifact Path</th><th>Type</th><th>Category</th><th>Local Link</th><th>External Effect</th></tr></thead>
              <tbody>
{artifact_rows}
              </tbody>
            </table>
          </section>

          <section class="card" id="timeline">
{_card_header("Operator Timeline", "compact timeline", "6 PHASES", "safe")}
            <table class="timeline-table">
              <thead><tr><th>Phase</th><th>Theme / Notes</th><th>Status</th><th>Visual Tier</th><th>External Effect</th></tr></thead>
              <tbody>
{timeline_rows}
              </tbody>
            </table>
          </section>

          <section class="card">
{_card_header("Card System", "design tokens", "CARD_SYSTEM_READY", "safe")}
            <table class="dense-table">
              <tbody>
                <tr><th>visual_density_status</th><td class="mono">{_dd(status["visual_density_status"])}</td></tr>
                <tr><th>card_system_status</th><td class="mono">{_dd(status["card_system_status"])}</td></tr>
                <tr><th>icon_system_status</th><td class="mono">{_dd(status["icon_system_status"])}</td></tr>
                <tr><th>icon_mode</th><td class="mono">{_dd(icon_system["icon_mode"])}</td></tr>
                <tr><th>timeline_polish_status</th><td class="mono">{_dd(timeline_polish["status"])}</td></tr>
                <tr><th>soft_polish_status</th><td class="mono">{_dd(status["soft_polish_status"])}</td></tr>
                <tr><th>chinese_ui_status</th><td class="mono">{_dd(chinese_ui["status"])}</td></tr>
                <tr><th>language_mode</th><td class="mono">{_dd(chinese_ui["language_mode"])}</td></tr>
                <tr><th>technical_status_codes</th><td class="mono">{_dd(chinese_ui["technical_status_codes"])}</td></tr>
                <tr><th>template_reference_status</th><td class="mono">{_dd(template_reference["status"])}</td></tr>
                <tr><th>reference_mode</th><td class="mono">{_dd(template_reference["reference_mode"])}</td></tr>
                <tr><th>loaded_external_assets</th><td class="mono">{_dd(template_reference["loaded_external_assets"])}</td></tr>
                <tr><th>matrix_status</th><td class="mono">{_dd(status["matrix_status"])}</td></tr>
                <tr><th>artifact_reader_status</th><td class="mono">{_dd(status["artifact_reader_status"])}</td></tr>
                <tr><th>density_mode</th><td class="mono">{_dd(visual_density["density_mode"])}</td></tr>
                <tr><th>card_types</th><td class="mono">{escape(", ".join(card_system["card_types"]))}</td></tr>
              </tbody>
            </table>
          </section>

          <section class="card" id="settings">
{_card_header("JP / CN Frozen Scope", "operator action", "FROZEN", "warn")}
            <table class="dense-table">
              <tbody>
                <tr><th>jp_status</th><td class="mono">{_dd(status["jp_status"])}</td></tr>
                <tr><th>cn_status</th><td class="mono">{_dd(status["cn_status"])}</td></tr>
                <tr><th>action</th><td class="mono">{NEXT_OPERATOR_ACTION}</td></tr>
              </tbody>
            </table>
          </section>

          <section class="card wide">
{_card_header("Build / Version / Safety", "version control", "LOCAL_ONLY", "safe")}
            <table class="dense-table">
              <tbody>
                <tr><th>phase</th><td class="mono">{_dd(build["phase"])}</td></tr>
                <tr><th>status</th><td class="mono">{_dd(build["status"])}</td></tr>
                <tr><th>ui_generation</th><td class="mono">{_dd(build["ui_generation"])}</td></tr>
                <tr><th>latest_main_commit</th><td class="mono">{_dd(build["latest_main_commit"])}</td></tr>
                <tr><th>latest_merged_pr</th><td class="mono">{_dd(build["latest_merged_pr"])}</td></tr>
                <tr><th>current_branch_basis</th><td class="mono">{_dd(build["current_branch_basis"])}</td></tr>
                <tr><th>production_ready</th><td class="mono status-safe">{_dd(build["production_ready"])}</td></tr>
                <tr><th>trading_enabled</th><td class="mono status-safe">{_dd(build["trading_enabled"])}</td></tr>
                <tr><th>external_effect</th><td class="mono">{_dd(build["external_effect"])}</td></tr>
                <tr><th>generated_at_utc</th><td class="mono">{_dd(build["generated_at_utc"])}</td></tr>
              </tbody>
            </table>
          </section>
        </main>
      </div>
    </div>
    <footer class="footer-safety-bar">No IBKR connection · No market data request · No historical data · No account/position read · No trading · No Telegram real send</footer>
  </body>
</html>
"""


def write_dashboard_css(path: PathLike) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_dashboard_css(), encoding="utf-8")


def write_dashboard_html(
    path: PathLike,
    status: Dict[str, object],
    visual_density: Dict[str, object],
    card_system: Dict[str, object],
    icon_system: Dict[str, object],
    timeline_polish: Dict[str, object],
    chinese_ui: Dict[str, object],
    template_reference: Dict[str, object],
    watchlist: Dict[str, object],
    signal: Dict[str, object],
    risk: Dict[str, object],
    timeline: Dict[str, object],
    layout: Dict[str, object],
    navigation: Dict[str, object],
    build: Dict[str, object],
    manifest: Dict[str, object],
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_dashboard_html(
            status,
            visual_density,
            card_system,
            icon_system,
            timeline_polish,
            chinese_ui,
            template_reference,
            watchlist,
            signal,
            risk,
            timeline,
            layout,
            navigation,
            build,
            manifest,
        ),
        encoding="utf-8",
    )


def build_report(row: Dict[str, str]) -> str:
    lines = [
        "# Phase 673-680 Dashboard Chinese Template Soft Polish Pack Report",
        "",
        "## Status",
        "",
        f"- status={row['status']}",
        f"- ui_generation={row['ui_generation']}",
        f"- visual_density_status={row['visual_density_status']}",
        f"- card_system_status={row['card_system_status']}",
        f"- icon_system_status={row['icon_system_status']}",
        f"- timeline_polish_status={row['timeline_polish_status']}",
        f"- chinese_ui_status={row['chinese_ui_status']}",
        f"- language_mode={row['language_mode']}",
        f"- template_reference_status={row['template_reference_status']}",
        f"- reference_mode={row['reference_mode']}",
        f"- copied_external_code={row['copied_external_code']}",
        f"- loaded_external_assets={row['loaded_external_assets']}",
        f"- soft_polish_status={row['soft_polish_status']}",
        f"- matrix_status={row['matrix_status']}",
        f"- artifact_reader_status={row['artifact_reader_status']}",
        f"- build_panel_status={row['build_panel_status']}",
        "",
        "## Generated Artifacts",
        "",
        *[f"- {artifact}" for artifact in ARTIFACTS],
        "",
        "## Safety Boundary",
        "",
        f"- market_data_status={row['market_data_status']}",
        f"- market_data_classification={row['market_data_classification']}",
        f"- ibkr_error_code={row['ibkr_error_code']}",
        f"- realtime_market_data_verified={row['realtime_market_data_verified']}",
        f"- production_ready={row['production_ready']}",
        f"- trading_enabled={row['trading_enabled']}",
        f"- account_read_enabled={row['account_read_enabled']}",
        f"- positions_read_enabled={row['positions_read_enabled']}",
        f"- historical_data_enabled={row['historical_data_enabled']}",
        f"- telegram_real_send_enabled={row['telegram_real_send_enabled']}",
        f"- external_effect={row['external_effect']}",
        "",
        "## Frozen Scope",
        "",
        f"- jp_status={row['jp_status']}",
        f"- cn_status={row['cn_status']}",
    ]
    return "\n".join(lines) + "\n"


def write_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_report(row), encoding="utf-8")


def build_pack(row: Dict[str, str]) -> str:
    lines = [
        "# Precious Metals Monitor Dashboard Chinese Template Soft Polish Pack",
        "",
        "## Phase Status",
        "",
        f"- phase={row['phase']}",
        f"- status={row['status']}",
        f"- generation={row['ui_generation']}",
        f"- chinese_ui_status={row['chinese_ui_status']}",
        f"- language_mode={row['language_mode']}",
        f"- template_reference_status={row['template_reference_status']}",
        f"- copied_external_code={row['copied_external_code']}",
        f"- loaded_external_assets={row['loaded_external_assets']}",
        "",
        "## Console Boundary",
        "",
        "- local static read-only artifact viewer only",
        "- no external URL/CDN",
        "- no remote icons/images/fonts",
        "- no IBKR connection",
        "- no market data request",
        "- no historical data request",
        "- no account/position read",
        "- no contract qualification",
        "- no trading",
        "- no Telegram real send",
        "- no directional trading signal",
        "- no target/stop/take-profit",
        f"- market data remains {row['market_data_status']} / IBKR_ERROR_{row['ibkr_error_code']}",
        "- GLD / SLV only",
        "- JP / CN remain frozen",
        "",
        "## Generated Files",
        "",
        *[f"- {artifact}" for artifact in ARTIFACTS],
    ]
    return "\n".join(lines) + "\n"


def write_pack(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.write_text(build_pack(row), encoding="utf-8")


def generate_dashboard_chinese_template_soft_polish_pack(
    *,
    output_index: PathLike = DASHBOARD_INDEX,
    output_css: PathLike = DASHBOARD_CSS,
    output_status_snapshot: PathLike = STATUS_SNAPSHOT,
    output_visual_density_snapshot: PathLike = VISUAL_DENSITY_SNAPSHOT,
    output_card_system_snapshot: PathLike = CARD_SYSTEM_SNAPSHOT,
    output_icon_system_snapshot: PathLike = ICON_SYSTEM_SNAPSHOT,
    output_timeline_polish_snapshot: PathLike = TIMELINE_POLISH_SNAPSHOT,
    output_chinese_ui_snapshot: PathLike = CHINESE_UI_SNAPSHOT,
    output_template_reference_snapshot: PathLike = TEMPLATE_REFERENCE_SNAPSHOT,
    output_watchlist_snapshot: PathLike = WATCHLIST_SNAPSHOT,
    output_signal_snapshot: PathLike = SIGNAL_SNAPSHOT,
    output_risk_snapshot: PathLike = RISK_SNAPSHOT,
    output_operator_timeline: PathLike = OPERATOR_TIMELINE,
    output_layout_snapshot: PathLike = LAYOUT_SNAPSHOT,
    output_navigation_snapshot: PathLike = NAVIGATION_SNAPSHOT,
    output_build_snapshot: PathLike = BUILD_SNAPSHOT,
    output_artifact_manifest: PathLike = ARTIFACT_MANIFEST,
    output_csv: PathLike = OUTPUT_CSV,
    output_report: PathLike = OUTPUT_REPORT,
    output_pack: PathLike = OUTPUT_PACK,
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    timestamp = generated_at or _now_timestamp()
    status = build_status_snapshot(generated_at=timestamp)
    visual_density = build_visual_density_snapshot(generated_at=timestamp)
    card_system = build_card_system_snapshot(generated_at=timestamp)
    icon_system = build_icon_system_snapshot(generated_at=timestamp)
    timeline_polish = build_timeline_polish_snapshot(generated_at=timestamp)
    chinese_ui = build_chinese_ui_snapshot(generated_at=timestamp)
    template_reference = build_template_reference_snapshot(generated_at=timestamp)
    watchlist = build_watchlist_snapshot(generated_at=timestamp)
    signal = build_signal_snapshot(generated_at=timestamp)
    risk = build_risk_snapshot(generated_at=timestamp)
    timeline = build_operator_timeline(generated_at=timestamp)
    layout = build_layout_snapshot(generated_at=timestamp)
    navigation = build_navigation_snapshot(generated_at=timestamp)
    build = build_build_snapshot(generated_at=timestamp)
    manifest = build_artifact_manifest(generated_at=timestamp)
    row = _snapshot_to_row(status)

    _write_json(output_status_snapshot, status)
    _write_json(output_visual_density_snapshot, visual_density)
    _write_json(output_card_system_snapshot, card_system)
    _write_json(output_icon_system_snapshot, icon_system)
    _write_json(output_timeline_polish_snapshot, timeline_polish)
    _write_json(output_chinese_ui_snapshot, chinese_ui)
    _write_json(output_template_reference_snapshot, template_reference)
    _write_json(output_watchlist_snapshot, watchlist)
    _write_json(output_signal_snapshot, signal)
    _write_json(output_risk_snapshot, risk)
    _write_json(output_operator_timeline, timeline)
    _write_json(output_layout_snapshot, layout)
    _write_json(output_navigation_snapshot, navigation)
    _write_json(output_build_snapshot, build)
    _write_json(output_artifact_manifest, manifest)
    write_dashboard_css(output_css)
    write_dashboard_html(
        output_index,
        status,
        visual_density,
        card_system,
        icon_system,
        timeline_polish,
        chinese_ui,
        template_reference,
        watchlist,
        signal,
        risk,
        timeline,
        layout,
        navigation,
        build,
        manifest,
    )
    write_dashboard_csv(output_csv, row)
    write_report(output_report, row)
    write_pack(output_pack, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 673-680 dashboard chinese template soft polish pack.")
    parser.add_argument("--output-index", default=DASHBOARD_INDEX)
    parser.add_argument("--output-css", default=DASHBOARD_CSS)
    parser.add_argument("--output-status-snapshot", default=STATUS_SNAPSHOT)
    parser.add_argument("--output-visual-density-snapshot", default=VISUAL_DENSITY_SNAPSHOT)
    parser.add_argument("--output-card-system-snapshot", default=CARD_SYSTEM_SNAPSHOT)
    parser.add_argument("--output-icon-system-snapshot", default=ICON_SYSTEM_SNAPSHOT)
    parser.add_argument("--output-timeline-polish-snapshot", default=TIMELINE_POLISH_SNAPSHOT)
    parser.add_argument("--output-chinese-ui-snapshot", default=CHINESE_UI_SNAPSHOT)
    parser.add_argument("--output-template-reference-snapshot", default=TEMPLATE_REFERENCE_SNAPSHOT)
    parser.add_argument("--output-watchlist-snapshot", default=WATCHLIST_SNAPSHOT)
    parser.add_argument("--output-signal-snapshot", default=SIGNAL_SNAPSHOT)
    parser.add_argument("--output-risk-snapshot", default=RISK_SNAPSHOT)
    parser.add_argument("--output-operator-timeline", default=OPERATOR_TIMELINE)
    parser.add_argument("--output-layout-snapshot", default=LAYOUT_SNAPSHOT)
    parser.add_argument("--output-navigation-snapshot", default=NAVIGATION_SNAPSHOT)
    parser.add_argument("--output-build-snapshot", default=BUILD_SNAPSHOT)
    parser.add_argument("--output-artifact-manifest", default=ARTIFACT_MANIFEST)
    parser.add_argument("--output-csv", default=OUTPUT_CSV)
    parser.add_argument("--output-report", default=OUTPUT_REPORT)
    parser.add_argument("--output-pack", default=OUTPUT_PACK)
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generate_dashboard_chinese_template_soft_polish_pack(
        output_index=args.output_index,
        output_css=args.output_css,
        output_status_snapshot=args.output_status_snapshot,
        output_visual_density_snapshot=args.output_visual_density_snapshot,
        output_card_system_snapshot=args.output_card_system_snapshot,
        output_icon_system_snapshot=args.output_icon_system_snapshot,
        output_timeline_polish_snapshot=args.output_timeline_polish_snapshot,
        output_chinese_ui_snapshot=args.output_chinese_ui_snapshot,
        output_template_reference_snapshot=args.output_template_reference_snapshot,
        output_watchlist_snapshot=args.output_watchlist_snapshot,
        output_signal_snapshot=args.output_signal_snapshot,
        output_risk_snapshot=args.output_risk_snapshot,
        output_operator_timeline=args.output_operator_timeline,
        output_layout_snapshot=args.output_layout_snapshot,
        output_navigation_snapshot=args.output_navigation_snapshot,
        output_build_snapshot=args.output_build_snapshot,
        output_artifact_manifest=args.output_artifact_manifest,
        output_csv=args.output_csv,
        output_report=args.output_report,
        output_pack=args.output_pack,
        generated_at=args.generated_at,
    )
    print("[DASHBOARD_CHINESE_TEMPLATE_SOFT_POLISH_PACK] generated")
    print(f"status={STATUS}")
    print(f"ui_mode={UI_MODE}")
    print(f"ui_generation={UI_GENERATION}")
    print("visual_density_status=HIGH_DENSITY_CONSOLE_READY")
    print("card_system_status=CARD_SYSTEM_READY")
    print("icon_system_status=LOCAL_ICON_SYSTEM_READY")
    print("timeline_polish_status=COMPACT_TIMELINE_POLISHED")
    print("chinese_ui_status=CHINESE_MAIN_UI_READY")
    print("language_mode=ZH_CN_PRIMARY")
    print("template_reference_status=PUBLIC_TEMPLATE_INSPIRED_LAYOUT_READY")
    print("reference_mode=PUBLIC_DASHBOARD_LAYOUT_LANGUAGE_ONLY")
    print("copied_external_code=NO")
    print("loaded_external_assets=NO")
    print("soft_polish_status=SOFT_POLISH_APPLIED")
    print("matrix_status=RISK_SIGNAL_MATRIX_READY")
    print("artifact_reader_status=FILE_BROWSER_STYLE_READY")
    print("build_panel_status=BUILD_VERSION_SAFETY_DENSE_READY")
    print("dashboard_index=dashboard/index.html")
    print("dashboard_css=dashboard/assets/style.css")
    print("status_snapshot=dashboard/data/status_snapshot.json")
    print("visual_density_snapshot=dashboard/data/visual_density_snapshot.json")
    print("card_system_snapshot=dashboard/data/card_system_snapshot.json")
    print("icon_system_snapshot=dashboard/data/icon_system_snapshot.json")
    print("timeline_polish_snapshot=dashboard/data/timeline_polish_snapshot.json")
    print("chinese_ui_snapshot=dashboard/data/chinese_ui_snapshot.json")
    print("template_reference_snapshot=dashboard/data/template_reference_snapshot.json")
    print("market_scope=US_ONLY")
    print("symbols=GLD,SLV")
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
