from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


PHASE = "Phase 641-648"
STATUS = "DASHBOARD_UI_V2_DATA_PANEL_READY"
UI_MODE = "LOCAL_STATIC_RESEARCH_CONSOLE"
FINAL_MVP_STATUS = "US_ONLY_READONLY_MONITORING_MVP_READY_WITH_MARKET_DATA_BLOCKED_BY_SUBSCRIPTION"
ARCHIVE_HANDOFF_STATUS = "US_ONLY_MVP_ARCHIVE_HANDOFF_PACK_READY"
PREVIOUS_UI_STATUS = "DASHBOARD_UI_ENHANCEMENT_READY"
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
ARTIFACT_MANIFEST = "dashboard/data/artifact_manifest.json"
OUTPUT_CSV = "operator_dashboard_ui_v2_data_panel_pack.csv"
OUTPUT_REPORT = "reports/operator_dashboard_ui_v2_data_panel_pack_report.md"
OUTPUT_PACK = "Precious_Metals_Monitor_Dashboard_UI_V2_Data_Panel_Pack.md"

PANELS = (
    "MVP_STATUS",
    "MARKET_DATA_BLOCK",
    "WATCHLIST",
    "SIGNAL_PANEL",
    "RISK_PANEL",
    "OPERATOR_TIMELINE",
    "ARTIFACT_READER",
    "JP_CN_FROZEN_SCOPE",
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
    WATCHLIST_SNAPSHOT,
    SIGNAL_SNAPSHOT,
    RISK_SNAPSHOT,
    OPERATOR_TIMELINE,
    ARTIFACT_MANIFEST,
    "dashboard/us_etf_dashboard_readonly.html",
    "telegram/us_etf_telegram_payload_preview.md",
    "Precious_Metals_Monitor_US_Only_MVP_Final_Freeze_Summary.md",
    "Precious_Metals_Monitor_US_Only_MVP_Archive_Handoff_Pack.md",
    "Precious_Metals_Monitor_Dashboard_UI_Enhancement_Pack.md",
)

CSV_FIELDS = (
    "phase",
    "status",
    "ui_mode",
    "panel_count",
    "panels",
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
        "previous_ui_status": PREVIOUS_UI_STATUS,
        "final_mvp_status": FINAL_MVP_STATUS,
        "archive_handoff_status": ARCHIVE_HANDOFF_STATUS,
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
                "symbol": "GLD",
                "asset_class": "ETF",
                "market": "US",
                "data_status": MARKET_DATA_STATUS,
                "realtime_price_available": NO_TEXT,
                "delayed_available": YES_TEXT,
                "subscription_required": YES_TEXT,
                "tradability_view": "RESEARCH_ONLY_NOT_TRADE_SIGNAL",
                "notes": "Static US ETF watchlist member. No quote, holding, or account value is embedded.",
            },
            {
                "symbol": "SLV",
                "asset_class": "ETF",
                "market": "US",
                "data_status": MARKET_DATA_STATUS,
                "realtime_price_available": NO_TEXT,
                "delayed_available": YES_TEXT,
                "subscription_required": YES_TEXT,
                "tradability_view": "RESEARCH_ONLY_NOT_TRADE_SIGNAL",
                "notes": "Static US ETF watchlist member. No quote, holding, or account value is embedded.",
            },
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
                "phase": "Phase 617-624",
                "title": "US-only MVP final audit freeze",
                "status": "US_ONLY_MVP_FINAL_AUDIT_FREEZE_READY",
                "external_effect": EXTERNAL_EFFECT,
                "notes": "Locked GLD / SLV MVP boundary while market data remained subscription-blocked.",
            },
            {
                "phase": "Phase 625-632",
                "title": "US-only MVP archive handoff pack",
                "status": ARCHIVE_HANDOFF_STATUS,
                "external_effect": EXTERNAL_EFFECT,
                "notes": "Prepared local archive handoff artifacts without external system access.",
            },
            {
                "phase": "Phase 633-640",
                "title": "Dashboard UI enhancement pack",
                "status": PREVIOUS_UI_STATUS,
                "external_effect": EXTERNAL_EFFECT,
                "notes": "Added local static dashboard shell and status snapshot.",
            },
            {
                "phase": PHASE,
                "title": "Dashboard UI v2 data panel expansion pack",
                "status": STATUS,
                "external_effect": EXTERNAL_EFFECT,
                "notes": "Expanded local static research console panels with JSON artifacts only.",
            },
        ],
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
        "panel_count": str(snapshot["panel_count"]),
        "panels": ",".join(str(panel) for panel in snapshot["panels"]),
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
  --bg: #090d12;
  --surface: #101820;
  --surface-2: #15212b;
  --surface-3: #1c2c39;
  --line: #2c3d4d;
  --text: #eef4f8;
  --muted: #9cadba;
  --amber: #f1b84b;
  --green: #5fd09c;
  --red: #ff6f61;
  --blue: #77b7ff;
  --cyan: #62d7e6;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Arial, Helvetica, sans-serif;
  line-height: 1.5;
}

a {
  color: var(--blue);
  overflow-wrap: anywhere;
}

.shell {
  width: min(1320px, calc(100% - 32px));
  margin: 0 auto;
  padding: 26px 0 42px;
}

.topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 22px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 20px;
}

h1 {
  margin: 0;
  font-size: clamp(28px, 4vw, 46px);
  font-weight: 800;
}

.subtitle {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 15px;
}

.badges,
.flag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.badges {
  justify-content: flex-end;
}

.badge,
.flag {
  border: 1px solid var(--line);
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
}

.badge,
.flag {
  background: var(--surface-2);
}

.safe {
  border-color: rgba(95, 208, 156, 0.55);
  color: var(--green);
}

.warn {
  border-color: rgba(241, 184, 75, 0.65);
  color: var(--amber);
}

.danger {
  color: var(--red);
}

.ok {
  color: var(--green);
}

.mono {
  font-family: Consolas, Monaco, monospace;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.summary-item {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 14px;
  min-width: 0;
}

.label {
  color: var(--muted);
  display: block;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 6px;
  text-transform: uppercase;
}

.value {
  display: block;
  font-size: 15px;
  font-weight: 800;
  overflow-wrap: anywhere;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 18px;
}

.card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 18px;
  min-width: 0;
}

.card.wide {
  grid-column: span 2;
}

.card h2 {
  margin: 0 0 12px;
  font-size: 18px;
}

.kv {
  display: grid;
  grid-template-columns: minmax(155px, 44%) 1fr;
  gap: 8px 12px;
  margin: 0;
}

.kv dt {
  color: var(--muted);
}

.kv dd {
  margin: 0;
  font-weight: 700;
  overflow-wrap: anywhere;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

th,
td {
  border-bottom: 1px solid var(--line);
  padding: 8px 8px 8px 0;
  text-align: left;
  vertical-align: top;
}

th {
  color: var(--muted);
  font-weight: 700;
}

.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
}

.timeline li {
  border-left: 2px solid var(--cyan);
  padding: 0 0 16px 14px;
  position: relative;
}

.timeline li::before {
  background: var(--cyan);
  border-radius: 999px;
  content: "";
  height: 9px;
  left: -5px;
  position: absolute;
  top: 5px;
  width: 9px;
}

.timeline li:last-child {
  padding-bottom: 0;
}

.timeline strong {
  display: block;
}

.timeline span {
  color: var(--muted);
  display: block;
  font-size: 13px;
}

.artifact-list {
  display: grid;
  gap: 8px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.artifact-list li {
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 8px 10px;
}

@media (max-width: 1040px) {
  .card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .summary-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .topbar {
    display: block;
  }

  .badges {
    justify-content: flex-start;
    margin-top: 14px;
  }

  .card-grid,
  .summary-strip {
    grid-template-columns: 1fr;
  }

  .card.wide {
    grid-column: span 1;
  }

  .kv {
    grid-template-columns: 1fr;
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
    manifest: Dict[str, object],
) -> str:
    safety_rows = "\n".join(
        f"              <tr><th>{escape(key)}</th><td class=\"mono ok\">{escape(str(status[key]))}</td></tr>"
        for key in (
            "realtime_market_data_verified",
            "production_ready",
            "trading_enabled",
            "account_read_enabled",
            "positions_read_enabled",
            "historical_data_enabled",
            "telegram_real_send_enabled",
        )
    )
    watchlist_rows = "\n".join(
        f"              <tr><td class=\"mono\">{escape(item['symbol'])}</td><td>{escape(item['asset_class'])}</td><td>{escape(item['market'])}</td><td class=\"mono danger\">{escape(item['data_status'])}</td><td class=\"mono ok\">{escape(item['realtime_price_available'])}</td><td class=\"mono\">{escape(item['delayed_available'])}</td></tr>"
        for item in watchlist["symbols"]
    )
    signal_rows = "\n".join(
        f"              <tr><td class=\"mono\">{escape(item['symbol'])}</td><td class=\"mono danger\">{escape(item['signal_status'])}</td><td class=\"mono\">{escape(item['short_term_signal'])}</td><td class=\"mono\">{escape(item['mid_term_signal'])}</td><td class=\"mono\">{escape(item['long_term_signal'])}</td></tr>"
        for item in signal["symbols"]
    )
    risk_rows = "\n".join(
        f"              <tr><th>{escape(key)}</th><td class=\"mono ok\">{escape(value)}</td></tr>"
        for key, value in risk["enabled_flags"].items()
    )
    blocked_flags = "\n".join(
        f'            <span class="flag warn">{escape(action)}</span>' for action in risk["blocked_actions"]
    )
    timeline_items = "\n".join(
        f"            <li><strong>{escape(item['phase'])}: {escape(item['title'])}</strong><span class=\"mono\">{escape(item['status'])}</span><span>{escape(item['notes'])}</span></li>"
        for item in timeline["timeline"]
    )
    artifact_items = "\n".join(
        f'            <li><a href="{_artifact_href(item["path"])}">{escape(item["path"])}</a></li>'
        for item in manifest["artifacts"]
    )
    symbols_text = escape(", ".join(str(symbol) for symbol in status["symbols"]))
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
    <div class="shell">
      <header class="topbar">
        <div>
          <h1>AI Research Console / Precious Metals Monitor</h1>
          <p class="subtitle">Local static research console for GLD / SLV read-only artifact review.</p>
        </div>
        <div class="badges" aria-label="status badges">
          <span class="badge safe">US_ONLY</span>
          <span class="badge safe">READ_ONLY</span>
          <span class="badge warn">DATA_BLOCKED</span>
          <span class="badge warn">NOT_PRODUCTION</span>
          <span class="badge safe">UI_V2</span>
        </div>
      </header>

      <section class="summary-strip" aria-label="summary strip">
        <div class="summary-item"><span class="label">MVP Status</span><span class="value mono">{_dd(status["final_mvp_status"])}</span></div>
        <div class="summary-item"><span class="label">Market Data</span><span class="value mono danger">{_dd(status["market_data_status"])}</span></div>
        <div class="summary-item"><span class="label">Symbols</span><span class="value mono">{symbols_text}</span></div>
        <div class="summary-item"><span class="label">External Effect</span><span class="value mono">{_dd(status["external_effect"])}</span></div>
      </section>

      <main class="card-grid">
        <section class="card wide">
          <h2>MVP Status</h2>
          <dl class="kv">
            <dt>ui_phase</dt><dd class="mono">{_dd(status["ui_phase"])}</dd>
            <dt>ui_status</dt><dd class="mono">{_dd(status["ui_status"])}</dd>
            <dt>ui_mode</dt><dd class="mono">{_dd(status["ui_mode"])}</dd>
            <dt>panel_count</dt><dd class="mono">{_dd(status["panel_count"])}</dd>
            <dt>market_scope</dt><dd class="mono">{_dd(status["market_scope"])}</dd>
            <dt>symbols</dt><dd class="mono">{symbols_text}</dd>
          </dl>
        </section>

        <section class="card">
          <h2>Market Data Block</h2>
          <dl class="kv">
            <dt>market_data_status</dt><dd class="mono danger">{_dd(status["market_data_status"])}</dd>
            <dt>market_data_classification</dt><dd class="mono danger">{_dd(status["market_data_classification"])}</dd>
            <dt>ibkr_error_code</dt><dd class="mono">{_dd(status["ibkr_error_code"])}</dd>
            <dt>subscription_required</dt><dd class="mono">{_dd(status["subscription_required"])}</dd>
            <dt>delayed_available</dt><dd class="mono">{_dd(status["delayed_available"])}</dd>
            <dt>realtime_market_data_verified</dt><dd class="mono ok">{_dd(status["realtime_market_data_verified"])}</dd>
          </dl>
        </section>

        <section class="card wide">
          <h2>Watchlist</h2>
          <table class="watchlist-table">
            <thead><tr><th>Symbol</th><th>Asset</th><th>Market</th><th>Data Status</th><th>Realtime</th><th>Delayed</th></tr></thead>
            <tbody>
{watchlist_rows}
            </tbody>
          </table>
        </section>

        <section class="card">
          <h2>Signal Panel</h2>
          <dl class="kv">
            <dt>signal_mode</dt><dd class="mono">{_dd(signal["signal_mode"])}</dd>
            <dt>trading_signal_enabled</dt><dd class="mono ok">{_dd(signal["trading_signal_enabled"])}</dd>
            <dt>recommendation_enabled</dt><dd class="mono ok">{_dd(signal["recommendation_enabled"])}</dd>
          </dl>
          <table>
            <thead><tr><th>Symbol</th><th>Status</th><th>Short</th><th>Mid</th><th>Long</th></tr></thead>
            <tbody>
{signal_rows}
            </tbody>
          </table>
        </section>

        <section class="card wide">
          <h2>Risk Boundary</h2>
          <table class="risk-flag-table">
            <tbody>
{safety_rows}
              <tr><th>external_effect</th><td class="mono">{_dd(status["external_effect"])}</td></tr>
{risk_rows}
            </tbody>
          </table>
          <div class="flag-row" aria-label="blocked actions">
{blocked_flags}
          </div>
        </section>

        <section class="card">
          <h2>Operator Timeline</h2>
          <ol class="timeline">
{timeline_items}
          </ol>
        </section>

        <section class="card wide">
          <h2>Artifact Reader</h2>
          <ul class="artifact-list">
{artifact_items}
          </ul>
        </section>

        <section class="card">
          <h2>JP / CN Frozen Scope</h2>
          <dl class="kv">
            <dt>jp_status</dt><dd class="mono">{_dd(status["jp_status"])}</dd>
            <dt>cn_status</dt><dd class="mono">{_dd(status["cn_status"])}</dd>
          </dl>
        </section>

        <section class="card">
          <h2>Next Operator Action</h2>
          <dl class="kv">
            <dt>action</dt><dd class="mono">{NEXT_OPERATOR_ACTION}</dd>
            <dt>generated_at_utc</dt><dd class="mono">{_dd(status["generated_at_utc"])}</dd>
          </dl>
        </section>
      </main>
    </div>
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
    manifest: Dict[str, object],
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_dashboard_html(status, watchlist, signal, risk, timeline, manifest),
        encoding="utf-8",
    )


def build_report(row: Dict[str, str]) -> str:
    lines = [
        "# Phase 641-648 Dashboard UI v2 Data Panel Pack Report",
        "",
        "## Status",
        "",
        f"- status={row['status']}",
        f"- ui_mode={row['ui_mode']}",
        f"- panel_count={row['panel_count']}",
        f"- panels={row['panels']}",
        "",
        "## Generated Artifacts",
        "",
        *[f"- {artifact}" for artifact in ARTIFACTS],
        f"- {OUTPUT_CSV}",
        f"- {OUTPUT_REPORT}",
        f"- {OUTPUT_PACK}",
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
        "# Precious Metals Monitor Dashboard UI V2 Data Panel Pack",
        "",
        "## Phase Status",
        "",
        f"- phase={row['phase']}",
        f"- status={row['status']}",
        f"- mode={row['ui_mode']}",
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
        "- no BUY/SELL signal",
        f"- market data remains {row['market_data_status']} / IBKR_ERROR_{row['ibkr_error_code']}",
        "- GLD / SLV only",
        "- JP / CN remain frozen",
        "",
        "## Generated Files",
        "",
        *[f"- {artifact}" for artifact in ARTIFACTS],
        f"- {OUTPUT_CSV}",
        f"- {OUTPUT_REPORT}",
        f"- {OUTPUT_PACK}",
    ]
    return "\n".join(lines) + "\n"


def write_pack(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.write_text(build_pack(row), encoding="utf-8")


def generate_dashboard_ui_v2_data_panel_pack(
    *,
    output_index: PathLike = DASHBOARD_INDEX,
    output_css: PathLike = DASHBOARD_CSS,
    output_status_snapshot: PathLike = STATUS_SNAPSHOT,
    output_watchlist_snapshot: PathLike = WATCHLIST_SNAPSHOT,
    output_signal_snapshot: PathLike = SIGNAL_SNAPSHOT,
    output_risk_snapshot: PathLike = RISK_SNAPSHOT,
    output_operator_timeline: PathLike = OPERATOR_TIMELINE,
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
    manifest = build_artifact_manifest(generated_at=timestamp)
    row = _snapshot_to_row(status)

    _write_json(output_status_snapshot, status)
    _write_json(output_watchlist_snapshot, watchlist)
    _write_json(output_signal_snapshot, signal)
    _write_json(output_risk_snapshot, risk)
    _write_json(output_operator_timeline, timeline)
    _write_json(output_artifact_manifest, manifest)
    write_dashboard_css(output_css)
    write_dashboard_html(output_index, status, watchlist, signal, risk, timeline, manifest)
    write_dashboard_csv(output_csv, row)
    write_report(output_report, row)
    write_pack(output_pack, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 641-648 dashboard UI v2 data panel pack.")
    parser.add_argument("--output-index", default=DASHBOARD_INDEX)
    parser.add_argument("--output-css", default=DASHBOARD_CSS)
    parser.add_argument("--output-status-snapshot", default=STATUS_SNAPSHOT)
    parser.add_argument("--output-watchlist-snapshot", default=WATCHLIST_SNAPSHOT)
    parser.add_argument("--output-signal-snapshot", default=SIGNAL_SNAPSHOT)
    parser.add_argument("--output-risk-snapshot", default=RISK_SNAPSHOT)
    parser.add_argument("--output-operator-timeline", default=OPERATOR_TIMELINE)
    parser.add_argument("--output-artifact-manifest", default=ARTIFACT_MANIFEST)
    parser.add_argument("--output-csv", default=OUTPUT_CSV)
    parser.add_argument("--output-report", default=OUTPUT_REPORT)
    parser.add_argument("--output-pack", default=OUTPUT_PACK)
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generate_dashboard_ui_v2_data_panel_pack(
        output_index=args.output_index,
        output_css=args.output_css,
        output_status_snapshot=args.output_status_snapshot,
        output_watchlist_snapshot=args.output_watchlist_snapshot,
        output_signal_snapshot=args.output_signal_snapshot,
        output_risk_snapshot=args.output_risk_snapshot,
        output_operator_timeline=args.output_operator_timeline,
        output_artifact_manifest=args.output_artifact_manifest,
        output_csv=args.output_csv,
        output_report=args.output_report,
        output_pack=args.output_pack,
        generated_at=args.generated_at,
    )
    print("[DASHBOARD_UI_V2_DATA_PANEL_PACK] generated")
    print(f"status={STATUS}")
    print(f"ui_mode={UI_MODE}")
    print("dashboard_index=dashboard/index.html")
    print("dashboard_css=dashboard/assets/style.css")
    print("status_snapshot=dashboard/data/status_snapshot.json")
    print("watchlist_snapshot=dashboard/data/watchlist_snapshot.json")
    print("signal_snapshot=dashboard/data/signal_snapshot.json")
    print("risk_snapshot=dashboard/data/risk_snapshot.json")
    print("operator_timeline=dashboard/data/operator_timeline.json")
    print("artifact_manifest=dashboard/data/artifact_manifest.json")
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
