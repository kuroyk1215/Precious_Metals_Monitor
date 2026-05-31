from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


PHASE = "Phase 649-656"
STATUS = "DASHBOARD_UI_V3_LAYOUT_POLISH_READY"
UI_MODE = "LOCAL_STATIC_RESEARCH_CONSOLE"
UI_GENERATION = "V3_LAYOUT_POLISH"
LATEST_MAIN_COMMIT = "fa365c6"
LATEST_MERGED_PR = "219"
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
WATCHLIST_SNAPSHOT = "dashboard/data/watchlist_snapshot.json"
SIGNAL_SNAPSHOT = "dashboard/data/signal_snapshot.json"
RISK_SNAPSHOT = "dashboard/data/risk_snapshot.json"
OPERATOR_TIMELINE = "dashboard/data/operator_timeline.json"
LAYOUT_SNAPSHOT = "dashboard/data/layout_snapshot.json"
NAVIGATION_SNAPSHOT = "dashboard/data/navigation_snapshot.json"
BUILD_SNAPSHOT = "dashboard/data/build_snapshot.json"
ARTIFACT_MANIFEST = "dashboard/data/artifact_manifest.json"
OUTPUT_CSV = "operator_dashboard_ui_v3_layout_polish_pack.csv"
OUTPUT_REPORT = "reports/operator_dashboard_ui_v3_layout_polish_pack_report.md"
OUTPUT_PACK = "Precious_Metals_Monitor_Dashboard_UI_V3_Layout_Polish_Pack.md"

SECTIONS = (
    "SIDEBAR",
    "TOP_HEADER",
    "STATUS_BADGE_BAR",
    "SUMMARY_STRIP",
    "MAIN_CARD_GRID",
    "SAFETY_FOOTER",
    "BUILD_VERSION_PANEL",
)

NAV_ITEMS = (
    ("Dashboard", "D", "#dashboard"),
    ("Watchlist", "W", "#watchlist"),
    ("Signals", "S", "#signals"),
    ("Risk Boundary", "R", "#risk-boundary"),
    ("Artifacts", "A", "#artifacts"),
    ("Timeline", "T", "#timeline"),
    ("System Status", "Y", "#system-status"),
    ("Settings", "G", "#settings"),
)

PANELS = (
    "MARKET_DATA_BLOCK",
    "WATCHLIST",
    "SIGNAL_PANEL",
    "RISK_BOUNDARY",
    "OPERATOR_TIMELINE",
    "ARTIFACT_READER",
    "JP_CN_FROZEN_SCOPE",
    "NEXT_OPERATOR_ACTION",
    "BUILD_VERSION_SAFETY",
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
    LAYOUT_SNAPSHOT,
    NAVIGATION_SNAPSHOT,
    BUILD_SNAPSHOT,
    WATCHLIST_SNAPSHOT,
    SIGNAL_SNAPSHOT,
    RISK_SNAPSHOT,
    OPERATOR_TIMELINE,
    ARTIFACT_MANIFEST,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)

CSV_FIELDS = (
    "phase",
    "status",
    "ui_mode",
    "ui_generation",
    "layout_status",
    "navigation_status",
    "visual_polish_status",
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
        "panel_count": len(PANELS),
        "panels": list(PANELS),
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "generated_at_utc": timestamp,
    }


def build_watchlist_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "scope": MARKET_SCOPE,
        "symbols": [
            {
                "symbol": symbol,
                "asset_class": "ETF",
                "market": "US",
                "data_status": MARKET_DATA_STATUS,
                "realtime_price_available": NO_TEXT,
                "delayed_available": YES_TEXT,
                "subscription_required": YES_TEXT,
                "tradability_view": "RESEARCH_ONLY_NOT_TRADE_SIGNAL",
                "notes": "Static US ETF watchlist member. No quote, holding, or account value is embedded.",
            }
            for symbol in SYMBOLS
        ],
        "generated_at_utc": timestamp,
    }


def build_signal_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "signal_mode": "STATIC_RESEARCH_PLACEHOLDER",
        "trading_signal_enabled": NO_TEXT,
        "recommendation_enabled": NO_TEXT,
        "symbols": [
            {
                "symbol": symbol,
                "signal_status": "NOT_AVAILABLE_MARKET_DATA_BLOCKED",
                "short_term_signal": "DISABLED",
                "mid_term_signal": "DISABLED",
                "long_term_signal": "DISABLED",
                "rolling_t_signal": "DISABLED",
                "reason": MARKET_DATA_CLASSIFICATION,
            }
            for symbol in SYMBOLS
        ],
        "generated_at_utc": timestamp,
    }


def build_risk_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    enabled_flags = {
        "ibkr_connect_enabled": NO_TEXT,
        "market_data_request_enabled": NO_TEXT,
        "historical_data_request_enabled": NO_TEXT,
        "account_read_enabled": NO_TEXT,
        "positions_read_enabled": NO_TEXT,
        "contract_qualification_enabled": NO_TEXT,
        "order_submit_enabled": NO_TEXT,
        "order_cancel_enabled": NO_TEXT,
        "rebalance_enabled": NO_TEXT,
        "telegram_real_send_enabled": NO_TEXT,
        "external_url_load_enabled": NO_TEXT,
    }
    return {
        "risk_mode": "STATIC_BOUNDARY_VIEW",
        "max_external_effect": EXTERNAL_EFFECT,
        "enabled_flags": enabled_flags,
        "blocked_actions": list(BLOCKED_ACTIONS),
        "generated_at_utc": timestamp,
    }


def build_operator_timeline(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "timeline": [
            {
                "phase": "Phase 633-640",
                "title": "Dashboard UI enhancement pack",
                "status": "DASHBOARD_UI_ENHANCEMENT_READY",
                "external_effect": EXTERNAL_EFFECT,
                "notes": "Added the first local static dashboard shell.",
            },
            {
                "phase": "Phase 641-648",
                "title": "Dashboard UI v2 data panel pack",
                "status": "DASHBOARD_UI_V2_DATA_PANEL_READY",
                "external_effect": EXTERNAL_EFFECT,
                "notes": "Expanded local static data panels and artifact reader.",
            },
            {
                "phase": PHASE,
                "title": "Dashboard UI v3 layout polish pack",
                "status": STATUS,
                "external_effect": EXTERNAL_EFFECT,
                "notes": "Polished the local app shell with sidebar, header, summary strip, and safety footer.",
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
            {
                "label": label,
                "icon_text": icon_text,
                "href": href,
                "enabled": YES_TEXT,
                "external_url": NO_TEXT,
            }
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
        "production_ready": NO_TEXT,
        "trading_enabled": NO_TEXT,
        "external_effect": EXTERNAL_EFFECT,
        "generated_at_utc": timestamp,
    }


def build_artifact_manifest(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": STATUS,
        "artifacts": [
            {
                "path": path,
                "external_effect": EXTERNAL_EFFECT,
                "artifact_type": Path(path).suffix.lstrip(".") or "html",
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
        "layout_status": str(snapshot["layout_status"]),
        "navigation_status": str(snapshot["navigation_status"]),
        "visual_polish_status": str(snapshot["visual_polish_status"]),
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
  color-scheme: dark;
  --bg: #080b10;
  --sidebar: #0d1219;
  --panel: #121923;
  --panel-2: #172231;
  --panel-3: #1d2a3a;
  --line: #2a3849;
  --line-soft: #203040;
  --text: #edf3f8;
  --muted: #9aa9b8;
  --blue: #6ca8ff;
  --cyan: #53c7d8;
  --green: #68d391;
  --amber: #f3bd4e;
  --red: #ff7568;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Arial, Helvetica, sans-serif;
  line-height: 1.45;
}

a {
  color: inherit;
  text-decoration: none;
}

.app-shell {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  min-height: 100vh;
}

.sidebar {
  background: var(--sidebar);
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: 22px 16px;
}

.brand {
  display: flex;
  gap: 12px;
  align-items: center;
}

.brand-mark,
.nav-icon {
  align-items: center;
  background: var(--panel-3);
  border: 1px solid var(--line);
  border-radius: 8px;
  display: inline-flex;
  font-weight: 800;
  height: 34px;
  justify-content: center;
  width: 34px;
}

.brand-title {
  display: block;
  font-size: 13px;
  font-weight: 800;
}

.brand-subtitle,
.nav-section-label,
.caption,
.label {
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.sidebar-nav {
  display: grid;
  gap: 6px;
}

.nav-item {
  align-items: center;
  border: 1px solid transparent;
  border-radius: 8px;
  color: var(--muted);
  display: flex;
  gap: 10px;
  min-height: 42px;
  padding: 6px 8px;
}

.nav-item.active {
  background: var(--panel-2);
  border-color: rgba(108, 168, 255, 0.5);
  color: var(--text);
}

.console-mode {
  border: 1px solid var(--line);
  border-radius: 8px;
  margin-top: auto;
  padding: 12px;
  background: var(--panel);
}

.mode-list {
  display: grid;
  gap: 7px;
  margin-top: 10px;
}

.content {
  min-width: 0;
  padding: 22px 24px 72px;
}

.topbar {
  align-items: flex-start;
  border-bottom: 1px solid var(--line);
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(0, 1fr) auto;
  padding-bottom: 18px;
}

h1 {
  font-size: 30px;
  line-height: 1.1;
  margin: 0;
}

.subtitle {
  color: var(--muted);
  margin: 8px 0 0;
}

.badge-bar,
.flag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.badge {
  align-items: center;
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 999px;
  display: inline-flex;
  font-size: 11px;
  font-weight: 800;
  min-height: 28px;
  padding: 4px 10px;
}

.badge.safe,
.status-safe {
  border-color: rgba(104, 211, 145, 0.55);
  color: var(--green);
}

.badge.warn,
.status-warn {
  border-color: rgba(243, 189, 78, 0.65);
  color: var(--amber);
}

.badge.disabled,
.status-disabled {
  border-color: rgba(255, 117, 104, 0.55);
  color: var(--red);
}

.build-box {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  min-width: 260px;
  padding: 12px;
}

.summary-strip {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 18px 0;
}

.summary-card,
.card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  min-width: 0;
}

.summary-card {
  padding: 14px;
}

.summary-value {
  display: block;
  font-size: 15px;
  font-weight: 800;
  margin-top: 6px;
  overflow-wrap: anywhere;
}

.card-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(12, minmax(0, 1fr));
}

.card {
  grid-column: span 4;
  padding: 16px;
}

.card.wide {
  grid-column: span 8;
}

.card.full {
  grid-column: 1 / -1;
}

.card h2 {
  font-size: 16px;
  margin: 0 0 12px;
}

.kv {
  display: grid;
  gap: 8px 12px;
  grid-template-columns: minmax(150px, 42%) 1fr;
  margin: 0;
}

.kv dt {
  color: var(--muted);
}

.kv dd {
  margin: 0;
  overflow-wrap: anywhere;
}

.mono {
  font-family: Consolas, Monaco, monospace;
}

.dense-table,
.artifact-table,
.risk-matrix {
  border-collapse: collapse;
  font-size: 13px;
  width: 100%;
}

th,
td {
  border-bottom: 1px solid var(--line-soft);
  padding: 7px 8px 7px 0;
  text-align: left;
  vertical-align: top;
}

th {
  color: var(--muted);
  font-weight: 800;
}

.flag {
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 999px;
  display: inline-flex;
  font-size: 11px;
  font-weight: 800;
  padding: 5px 9px;
}

.warning-box {
  background: rgba(243, 189, 78, 0.08);
  border: 1px solid rgba(243, 189, 78, 0.35);
  border-radius: 8px;
  color: var(--amber);
  margin-top: 12px;
  padding: 10px;
}

.timeline {
  display: grid;
  gap: 10px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.timeline li {
  border-left: 2px solid var(--cyan);
  padding-left: 12px;
}

.timeline strong,
.timeline span {
  display: block;
}

.footer-safety-bar {
  background: var(--sidebar);
  border-top: 1px solid var(--line);
  bottom: 0;
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
  left: 260px;
  padding: 12px 24px;
  position: fixed;
  right: 0;
  z-index: 5;
}

@media (max-width: 1100px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-bottom: 1px solid var(--line);
    border-right: 0;
    position: static;
  }

  .sidebar-nav {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .console-mode {
    margin-top: 0;
  }

  .footer-safety-bar {
    left: 0;
  }

  .summary-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .card,
  .card.wide {
    grid-column: span 6;
  }
}

@media (max-width: 720px) {
  .content {
    padding: 18px 14px 92px;
  }

  .topbar {
    grid-template-columns: 1fr;
  }

  .build-box {
    min-width: 0;
  }

  .sidebar-nav,
  .summary-strip {
    grid-template-columns: 1fr;
  }

  .card,
  .card.wide {
    grid-column: 1 / -1;
  }

  .kv {
    grid-template-columns: 1fr;
  }

  .artifact-table,
  .risk-matrix,
  .dense-table {
    display: block;
    overflow-x: auto;
  }
}
"""


def _dd(value: object) -> str:
    return escape(str(value))


def _artifact_href(path: str) -> str:
    if path.startswith("dashboard/"):
        return escape(path.replace("dashboard/", "", 1))
    return "../" + escape(path)


def build_dashboard_html(
    status: Dict[str, object],
    watchlist: Dict[str, object],
    signal: Dict[str, object],
    risk: Dict[str, object],
    timeline: Dict[str, object],
    layout: Dict[str, object],
    navigation: Dict[str, object],
    build: Dict[str, object],
    manifest: Dict[str, object],
) -> str:
    nav_links = "\n".join(
        f'          <a class="nav-item{" active" if item["label"] == "Dashboard" else ""}" href="{escape(item["href"])}"><span class="nav-icon">{escape(item["icon_text"])}</span><span>{escape(item["label"])}</span></a>'
        for item in navigation["items"]
    )
    watchlist_rows = "\n".join(
        f"              <tr><td class=\"mono\">{escape(item['symbol'])}</td><td>{escape(item['asset_class'])}</td><td>{escape(item['market'])}</td><td class=\"mono status-disabled\">{escape(item['data_status'])}</td><td class=\"mono status-safe\">{escape(item['realtime_price_available'])}</td><td class=\"mono\">{escape(item['delayed_available'])}</td></tr>"
        for item in watchlist["symbols"]
    )
    signal_rows = "\n".join(
        f"              <tr><td class=\"mono\">{escape(item['symbol'])}</td><td class=\"mono status-disabled\">{escape(item['signal_status'])}</td><td class=\"mono\">{escape(item['short_term_signal'])}</td><td class=\"mono\">{escape(item['mid_term_signal'])}</td><td class=\"mono\">{escape(item['long_term_signal'])}</td></tr>"
        for item in signal["symbols"]
    )
    risk_rows = "\n".join(
        f"              <tr><th>{escape(key)}</th><td class=\"mono status-safe\">{escape(value)}</td></tr>"
        for key, value in risk["enabled_flags"].items()
    )
    blocked_flags = "\n".join(
        f'            <span class="flag status-warn">{escape(action)}</span>' for action in risk["blocked_actions"]
    )
    timeline_items = "\n".join(
        f"            <li><strong>{escape(item['phase'])}: {escape(item['title'])}</strong><span class=\"mono\">{escape(item['status'])}</span><span class=\"caption\">{escape(item['notes'])}</span></li>"
        for item in timeline["timeline"]
    )
    artifact_rows = "\n".join(
        f'              <tr><td><a href="{_artifact_href(item["path"])}">{escape(item["path"])}</a></td><td class="mono">{escape(item["artifact_type"])}</td><td class="mono status-safe">{escape(item["external_effect"])}</td></tr>'
        for item in manifest["artifacts"]
    )
    section_rows = "\n".join(
        f"              <tr><td class=\"mono\">{escape(str(section))}</td><td class=\"mono status-safe\">READY</td></tr>"
        for section in layout["sections"]
    )
    symbols_text = escape(" / ".join(str(symbol) for symbol in status["symbols"]))
    return f"""\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI Research Console / Precious Metals Monitor</title>
    <link rel="stylesheet" href="assets/style.css">
  </head>
  <body>
    <div class="app-shell" id="dashboard">
      <aside class="sidebar" aria-label="Sidebar navigation">
        <div class="brand">
          <span class="brand-mark">PM</span>
          <div>
            <span class="brand-title">AI Research Console</span>
            <span class="brand-subtitle">Precious Metals Monitor</span>
          </div>
        </div>
        <div>
          <div class="nav-section-label">Navigation</div>
          <nav class="sidebar-nav">
{nav_links}
          </nav>
        </div>
        <section class="console-mode" aria-label="Console Mode">
          <div class="nav-section-label">Console Mode</div>
          <div class="mode-list">
            <span class="badge safe">LOCAL ONLY</span>
            <span class="badge safe">READ-ONLY</span>
            <span class="badge safe">NO EXTERNAL EFFECTS</span>
            <span class="badge warn">NOT FOR PRODUCTION</span>
          </div>
        </section>
      </aside>

      <div class="content">
        <header class="topbar">
          <div>
            <h1>AI Research Console / Precious Metals Monitor</h1>
            <p class="subtitle">Local Static Read-Only Research Console · Not for Production · No External Effects</p>
            <div class="badge-bar" aria-label="status badge bar">
              <span class="badge safe">US_ONLY</span>
              <span class="badge safe">READ_ONLY</span>
              <span class="badge warn">DATA_BLOCKED</span>
              <span class="badge warn">NOT_PRODUCTION</span>
              <span class="badge safe">UI_V3</span>
            </div>
          </div>
          <section class="build-box" aria-label="build box">
            <span class="label">generated_at_utc</span>
            <strong class="summary-value mono">{_dd(status["generated_at_utc"])}</strong>
            <span class="caption">local static</span>
          </section>
        </header>

        <section class="summary-strip" aria-label="summary strip">
          <div class="summary-card"><span class="label">MVP Status</span><span class="summary-value mono">{_dd(status["ui_status"])}</span></div>
          <div class="summary-card"><span class="label">Market Data</span><span class="summary-value mono status-disabled">{_dd(status["market_data_status"])}</span></div>
          <div class="summary-card"><span class="label">Symbols</span><span class="summary-value mono">{symbols_text}</span></div>
          <div class="summary-card"><span class="label">External Effect</span><span class="summary-value mono">{_dd(status["external_effect"])}</span></div>
        </section>

        <main class="card-grid">
          <section class="card" id="system-status">
            <h2>Market Data Block</h2>
            <dl class="kv">
              <dt>market_data_status</dt><dd class="mono status-disabled">{_dd(status["market_data_status"])}</dd>
              <dt>market_data_classification</dt><dd class="mono status-disabled">{_dd(status["market_data_classification"])}</dd>
              <dt>ibkr_error_code</dt><dd class="mono">{_dd(status["ibkr_error_code"])}</dd>
              <dt>subscription_required</dt><dd class="mono">{_dd(status["subscription_required"])}</dd>
              <dt>delayed_available</dt><dd class="mono">{_dd(status["delayed_available"])}</dd>
              <dt>realtime_market_data_verified</dt><dd class="mono status-safe">{_dd(status["realtime_market_data_verified"])}</dd>
            </dl>
            <div class="warning-box">Market data remains blocked by subscription. This console is a local artifact viewer only.</div>
          </section>

          <section class="card wide" id="watchlist">
            <h2>Watchlist</h2>
            <table class="dense-table">
              <thead><tr><th>Symbol</th><th>Asset</th><th>Market</th><th>Data Status</th><th>Realtime</th><th>Delayed</th></tr></thead>
              <tbody>
{watchlist_rows}
              </tbody>
            </table>
          </section>

          <section class="card wide" id="signals">
            <h2>Signal Panel</h2>
            <table class="dense-table">
              <thead><tr><th>Symbol</th><th>Status</th><th>Short</th><th>Mid</th><th>Long</th></tr></thead>
              <tbody>
{signal_rows}
              </tbody>
            </table>
          </section>

          <section class="card" id="risk-boundary">
            <h2>Risk Boundary</h2>
            <table class="risk-matrix">
              <tbody>
                <tr><th>production_ready</th><td class="mono status-safe">{_dd(status["production_ready"])}</td></tr>
                <tr><th>trading_enabled</th><td class="mono status-safe">{_dd(status["trading_enabled"])}</td></tr>
                <tr><th>account_read_enabled</th><td class="mono status-safe">{_dd(status["account_read_enabled"])}</td></tr>
                <tr><th>positions_read_enabled</th><td class="mono status-safe">{_dd(status["positions_read_enabled"])}</td></tr>
                <tr><th>historical_data_enabled</th><td class="mono status-safe">{_dd(status["historical_data_enabled"])}</td></tr>
                <tr><th>telegram_real_send_enabled</th><td class="mono status-safe">{_dd(status["telegram_real_send_enabled"])}</td></tr>
{risk_rows}
              </tbody>
            </table>
          </section>

          <section class="card full">
            <h2>Disabled Permission Matrix</h2>
            <div class="flag-row">
{blocked_flags}
            </div>
          </section>

          <section class="card" id="timeline">
            <h2>Operator Timeline</h2>
            <ol class="timeline">
{timeline_items}
            </ol>
          </section>

          <section class="card wide" id="artifacts">
            <h2>Artifact Reader</h2>
            <table class="artifact-table">
              <thead><tr><th>Local File</th><th>Type</th><th>External Effect</th></tr></thead>
              <tbody>
{artifact_rows}
              </tbody>
            </table>
          </section>

          <section class="card">
            <h2>JP / CN Frozen Scope</h2>
            <dl class="kv">
              <dt>jp_status</dt><dd class="mono">{_dd(status["jp_status"])}</dd>
              <dt>cn_status</dt><dd class="mono">{_dd(status["cn_status"])}</dd>
            </dl>
          </section>

          <section class="card" id="settings">
            <h2>Next Operator Action</h2>
            <dl class="kv">
              <dt>action</dt><dd class="mono">{NEXT_OPERATOR_ACTION}</dd>
              <dt>nav_mode</dt><dd class="mono">{_dd(navigation["nav_mode"])}</dd>
              <dt>javascript_required</dt><dd class="mono status-safe">{_dd(layout["javascript_required"])}</dd>
            </dl>
          </section>

          <section class="card wide">
            <h2>Build / Version / Safety</h2>
            <dl class="kv">
              <dt>phase</dt><dd class="mono">{_dd(build["phase"])}</dd>
              <dt>status</dt><dd class="mono">{_dd(build["status"])}</dd>
              <dt>latest_main_commit</dt><dd class="mono">{_dd(build["latest_main_commit"])}</dd>
              <dt>latest_merged_pr</dt><dd class="mono">{_dd(build["latest_merged_pr"])}</dd>
              <dt>current_branch_basis</dt><dd class="mono">{_dd(build["current_branch_basis"])}</dd>
              <dt>production_ready</dt><dd class="mono status-safe">{_dd(build["production_ready"])}</dd>
              <dt>trading_enabled</dt><dd class="mono status-safe">{_dd(build["trading_enabled"])}</dd>
              <dt>external_effect</dt><dd class="mono">{_dd(build["external_effect"])}</dd>
            </dl>
          </section>

          <section class="card full">
            <h2>Layout Snapshot</h2>
            <table class="dense-table">
              <thead><tr><th>Section</th><th>Status</th></tr></thead>
              <tbody>
{section_rows}
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
        build_dashboard_html(status, watchlist, signal, risk, timeline, layout, navigation, build, manifest),
        encoding="utf-8",
    )


def build_report(row: Dict[str, str]) -> str:
    lines = [
        "# Phase 649-656 Dashboard UI v3 Layout Polish Pack Report",
        "",
        "## Status",
        "",
        f"- status={row['status']}",
        f"- ui_mode={row['ui_mode']}",
        f"- ui_generation={row['ui_generation']}",
        f"- layout_status={row['layout_status']}",
        f"- navigation_status={row['navigation_status']}",
        f"- visual_polish_status={row['visual_polish_status']}",
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
        "# Precious Metals Monitor Dashboard UI V3 Layout Polish Pack",
        "",
        "## Phase Status",
        "",
        f"- phase={row['phase']}",
        f"- status={row['status']}",
        f"- mode={row['ui_mode']}",
        f"- generation={row['ui_generation']}",
        "",
        "## Console Boundary",
        "",
        "- local static read-only artifact viewer only",
        "- no external URL/CDN",
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


def generate_dashboard_ui_v3_layout_polish_pack(
    *,
    output_index: PathLike = DASHBOARD_INDEX,
    output_css: PathLike = DASHBOARD_CSS,
    output_status_snapshot: PathLike = STATUS_SNAPSHOT,
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
    _write_json(output_watchlist_snapshot, watchlist)
    _write_json(output_signal_snapshot, signal)
    _write_json(output_risk_snapshot, risk)
    _write_json(output_operator_timeline, timeline)
    _write_json(output_layout_snapshot, layout)
    _write_json(output_navigation_snapshot, navigation)
    _write_json(output_build_snapshot, build)
    _write_json(output_artifact_manifest, manifest)
    write_dashboard_css(output_css)
    write_dashboard_html(output_index, status, watchlist, signal, risk, timeline, layout, navigation, build, manifest)
    write_dashboard_csv(output_csv, row)
    write_report(output_report, row)
    write_pack(output_pack, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 649-656 dashboard UI v3 layout polish pack.")
    parser.add_argument("--output-index", default=DASHBOARD_INDEX)
    parser.add_argument("--output-css", default=DASHBOARD_CSS)
    parser.add_argument("--output-status-snapshot", default=STATUS_SNAPSHOT)
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
    generate_dashboard_ui_v3_layout_polish_pack(
        output_index=args.output_index,
        output_css=args.output_css,
        output_status_snapshot=args.output_status_snapshot,
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
    print("[DASHBOARD_UI_V3_LAYOUT_POLISH_PACK] generated")
    print(f"status={STATUS}")
    print(f"ui_mode={UI_MODE}")
    print(f"ui_generation={UI_GENERATION}")
    print("layout_status=SIDEBAR_HEADER_FOOTER_READY")
    print("navigation_status=STATIC_NAVIGATION_READY")
    print("visual_polish_status=PLATFORM_SHELL_POLISHED")
    print("dashboard_index=dashboard/index.html")
    print("dashboard_css=dashboard/assets/style.css")
    print("status_snapshot=dashboard/data/status_snapshot.json")
    print("layout_snapshot=dashboard/data/layout_snapshot.json")
    print("navigation_snapshot=dashboard/data/navigation_snapshot.json")
    print("build_snapshot=dashboard/data/build_snapshot.json")
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
