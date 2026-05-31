from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


PHASE = "Phase 633-640"
STATUS = "DASHBOARD_UI_ENHANCEMENT_READY"
FINAL_MVP_STATUS = "US_ONLY_READONLY_MONITORING_MVP_READY_WITH_MARKET_DATA_BLOCKED_BY_SUBSCRIPTION"
ARCHIVE_HANDOFF_STATUS = "US_ONLY_MVP_ARCHIVE_HANDOFF_PACK_READY"
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
DASHBOARD_SNAPSHOT = "dashboard/data/status_snapshot.json"
OUTPUT_CSV = "operator_dashboard_ui_enhancement_pack.csv"
OUTPUT_REPORT = "reports/operator_dashboard_ui_enhancement_pack_report.md"
OUTPUT_PACK = "Precious_Metals_Monitor_Dashboard_UI_Enhancement_Pack.md"

PRESERVED_ARTIFACTS = (
    "dashboard/us_etf_dashboard_readonly.html",
    "telegram/us_etf_telegram_payload_preview.md",
    "Precious_Metals_Monitor_US_Only_MVP_Final_Freeze_Summary.md",
    "Precious_Metals_Monitor_US_Only_MVP_Archive_Handoff_Pack.md",
)

CSV_FIELDS = (
    "phase",
    "status",
    "final_mvp_status",
    "archive_handoff_status",
    "market_scope",
    "symbols",
    "market_data_status",
    "market_data_classification",
    "ibkr_error_code",
    "subscription_required",
    "delayed_available",
    "realtime_market_data_verified",
    "production_ready",
    "trading_enabled",
    "account_read_enabled",
    "positions_read_enabled",
    "historical_data_enabled",
    "telegram_real_send_enabled",
    "external_effect",
    "dashboard_index",
    "dashboard_css",
    "status_snapshot",
    "jp_status",
    "cn_status",
    "next_operator_action",
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
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "artifacts": list(PRESERVED_ARTIFACTS),
        "generated_at_utc": timestamp,
    }


def _snapshot_to_row(snapshot: Dict[str, object]) -> Dict[str, str]:
    return {
        "phase": str(snapshot["phase"]),
        "status": str(snapshot["status"]),
        "final_mvp_status": str(snapshot["final_mvp_status"]),
        "archive_handoff_status": str(snapshot["archive_handoff_status"]),
        "market_scope": str(snapshot["market_scope"]),
        "symbols": ",".join(str(symbol) for symbol in snapshot["symbols"]),
        "market_data_status": str(snapshot["market_data_status"]),
        "market_data_classification": str(snapshot["market_data_classification"]),
        "ibkr_error_code": str(snapshot["ibkr_error_code"]),
        "subscription_required": str(snapshot["subscription_required"]),
        "delayed_available": str(snapshot["delayed_available"]),
        "realtime_market_data_verified": str(snapshot["realtime_market_data_verified"]),
        "production_ready": str(snapshot["production_ready"]),
        "trading_enabled": str(snapshot["trading_enabled"]),
        "account_read_enabled": str(snapshot["account_read_enabled"]),
        "positions_read_enabled": str(snapshot["positions_read_enabled"]),
        "historical_data_enabled": str(snapshot["historical_data_enabled"]),
        "telegram_real_send_enabled": str(snapshot["telegram_real_send_enabled"]),
        "external_effect": str(snapshot["external_effect"]),
        "dashboard_index": DASHBOARD_INDEX,
        "dashboard_css": DASHBOARD_CSS,
        "status_snapshot": DASHBOARD_SNAPSHOT,
        "jp_status": str(snapshot["jp_status"]),
        "cn_status": str(snapshot["cn_status"]),
        "next_operator_action": NEXT_OPERATOR_ACTION,
        "generated_at_utc": str(snapshot["generated_at_utc"]),
    }


def write_status_snapshot(path: PathLike, snapshot: Dict[str, object]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
  --bg: #0b1117;
  --panel: #111a24;
  --panel-strong: #162331;
  --line: #2a3a4d;
  --text: #e6edf3;
  --muted: #9fb0c2;
  --amber: #f0b429;
  --green: #46c28e;
  --red: #ff6b6b;
  --blue: #64a7ff;
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
}

.shell {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
  padding: 28px 0 40px;
}

.topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding-bottom: 22px;
  border-bottom: 1px solid var(--line);
}

h1 {
  margin: 0;
  font-size: clamp(26px, 4vw, 44px);
  font-weight: 800;
}

.subtitle {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 15px;
}

.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.badge {
  border: 1px solid var(--line);
  background: var(--panel-strong);
  border-radius: 999px;
  color: var(--text);
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 700;
}

.badge.warn {
  border-color: rgba(240, 180, 41, 0.65);
  color: var(--amber);
}

.badge.safe {
  border-color: rgba(70, 194, 142, 0.55);
  color: var(--green);
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 18px;
  min-width: 0;
}

.card h2 {
  margin: 0 0 12px;
  font-size: 18px;
}

.kv {
  display: grid;
  grid-template-columns: minmax(150px, 42%) 1fr;
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
  padding: 8px 0;
  text-align: left;
  vertical-align: top;
}

th {
  color: var(--muted);
  font-weight: 700;
}

ul {
  margin: 0;
  padding-left: 19px;
}

li {
  margin: 7px 0;
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

@media (max-width: 760px) {
  .topbar {
    display: block;
  }

  .badges {
    justify-content: flex-start;
    margin-top: 14px;
  }

  .grid {
    grid-template-columns: 1fr;
  }

  .kv {
    grid-template-columns: 1fr;
  }
}
"""


def write_dashboard_css(path: PathLike) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_dashboard_css(), encoding="utf-8")


def _dd(value: object) -> str:
    return escape(str(value))


def build_dashboard_html(snapshot: Dict[str, object]) -> str:
    artifacts = "\n".join(
        f'            <li><a href="../{escape(artifact)}">{escape(artifact)}</a></li>'
        for artifact in snapshot["artifacts"]
    )
    safety_rows = "\n".join(
        f"              <tr><th>{escape(key)}</th><td class=\"mono ok\">{escape(str(snapshot[key]))}</td></tr>"
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
          <p class="subtitle">Local static read-only console for GLD / SLV archive review.</p>
        </div>
        <div class="badges" aria-label="status badges">
          <span class="badge safe">US_ONLY</span>
          <span class="badge safe">READ_ONLY</span>
          <span class="badge warn">MARKET_DATA_BLOCKED_BY_SUBSCRIPTION</span>
          <span class="badge warn">NOT_PRODUCTION</span>
        </div>
      </header>

      <main class="grid">
        <section class="card">
          <h2>MVP Status</h2>
          <dl class="kv">
            <dt>phase</dt><dd class="mono">{_dd(snapshot["phase"])}</dd>
            <dt>status</dt><dd class="mono">{_dd(snapshot["status"])}</dd>
            <dt>final_mvp_status</dt><dd class="mono">{_dd(snapshot["final_mvp_status"])}</dd>
            <dt>archive_handoff_status</dt><dd class="mono">{_dd(snapshot["archive_handoff_status"])}</dd>
            <dt>market_scope</dt><dd class="mono">{_dd(snapshot["market_scope"])}</dd>
            <dt>symbols</dt><dd class="mono">{escape(", ".join(str(symbol) for symbol in snapshot["symbols"]))}</dd>
          </dl>
        </section>

        <section class="card">
          <h2>Market Data Block</h2>
          <dl class="kv">
            <dt>market_data_status</dt><dd class="mono danger">{_dd(snapshot["market_data_status"])}</dd>
            <dt>market_data_classification</dt><dd class="mono danger">{_dd(snapshot["market_data_classification"])}</dd>
            <dt>ibkr_error_code</dt><dd class="mono">{_dd(snapshot["ibkr_error_code"])}</dd>
            <dt>subscription_required</dt><dd class="mono">{_dd(snapshot["subscription_required"])}</dd>
            <dt>delayed_available</dt><dd class="mono">{_dd(snapshot["delayed_available"])}</dd>
            <dt>realtime_market_data_verified</dt><dd class="mono ok">{_dd(snapshot["realtime_market_data_verified"])}</dd>
          </dl>
        </section>

        <section class="card">
          <h2>Safety Boundary</h2>
          <table>
            <tbody>
{safety_rows}
              <tr><th>external_effect</th><td class="mono">{_dd(snapshot["external_effect"])}</td></tr>
            </tbody>
          </table>
        </section>

        <section class="card">
          <h2>Artifact Map</h2>
          <ul>
{artifacts}
            <li><a href="data/status_snapshot.json">dashboard/data/status_snapshot.json</a></li>
          </ul>
        </section>

        <section class="card">
          <h2>JP / CN Frozen Scope</h2>
          <dl class="kv">
            <dt>jp_status</dt><dd class="mono">{_dd(snapshot["jp_status"])}</dd>
            <dt>cn_status</dt><dd class="mono">{_dd(snapshot["cn_status"])}</dd>
          </dl>
        </section>

        <section class="card">
          <h2>Next Operator Action</h2>
          <dl class="kv">
            <dt>action</dt><dd class="mono">{NEXT_OPERATOR_ACTION}</dd>
            <dt>generated_at_utc</dt><dd class="mono">{_dd(snapshot["generated_at_utc"])}</dd>
          </dl>
        </section>
      </main>
    </div>
  </body>
</html>
"""


def write_dashboard_html(path: PathLike, snapshot: Dict[str, object]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_dashboard_html(snapshot), encoding="utf-8")


def build_dashboard_report(row: Dict[str, str]) -> str:
    lines = [
        "# Phase 633-640 Dashboard UI Enhancement Pack Report",
        "",
        "## Status",
        "",
        f"- status={row['status']}",
        f"- final_mvp_status={row['final_mvp_status']}",
        f"- archive_handoff_status={row['archive_handoff_status']}",
        f"- market_scope={row['market_scope']}",
        f"- symbols={row['symbols']}",
        "",
        "## Generated Console Artifacts",
        "",
        f"- dashboard_index={row['dashboard_index']}",
        f"- dashboard_css={row['dashboard_css']}",
        f"- status_snapshot={row['status_snapshot']}",
        "- csv=operator_dashboard_ui_enhancement_pack.csv",
        "- report=reports/operator_dashboard_ui_enhancement_pack_report.md",
        "- pack=Precious_Metals_Monitor_Dashboard_UI_Enhancement_Pack.md",
        "",
        "## Market Data Limitation",
        "",
        f"- market_data_status={row['market_data_status']}",
        f"- market_data_classification={row['market_data_classification']}",
        f"- ibkr_error_code={row['ibkr_error_code']}",
        f"- subscription_required={row['subscription_required']}",
        f"- delayed_available={row['delayed_available']}",
        f"- realtime_market_data_verified={row['realtime_market_data_verified']}",
        "",
        "## Safety Boundary",
        "",
        f"- production_ready={row['production_ready']}",
        f"- trading_enabled={row['trading_enabled']}",
        f"- account_read_enabled={row['account_read_enabled']}",
        f"- positions_read_enabled={row['positions_read_enabled']}",
        f"- historical_data_enabled={row['historical_data_enabled']}",
        f"- telegram_real_send_enabled={row['telegram_real_send_enabled']}",
        f"- external_effect={row['external_effect']}",
        "",
        "## JP / CN",
        "",
        f"- jp_status={row['jp_status']}",
        f"- cn_status={row['cn_status']}",
        "",
        "## Preserved Artifacts",
        "",
        *[f"- {artifact}" for artifact in PRESERVED_ARTIFACTS],
    ]
    return "\n".join(lines) + "\n"


def write_dashboard_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_dashboard_report(row), encoding="utf-8")


def build_dashboard_pack(row: Dict[str, str]) -> str:
    lines = [
        "# Precious Metals Monitor Dashboard UI Enhancement Pack",
        "",
        "## Phase Status",
        "",
        f"- phase={row['phase']}",
        f"- status={row['status']}",
        "- mode=LOCAL_STATIC_READONLY_CONSOLE",
        "",
        "## Generated Files",
        "",
        f"- {DASHBOARD_INDEX}",
        f"- {DASHBOARD_CSS}",
        f"- {DASHBOARD_SNAPSHOT}",
        f"- {OUTPUT_CSV}",
        f"- {OUTPUT_REPORT}",
        f"- {OUTPUT_PACK}",
        "",
        "## Console Boundary",
        "",
        "- local static HTML, local static CSS, and local static JSON only",
        "- no external URL or CDN dependency",
        "- no IBKR connection",
        "- no market data request",
        "- no historical data request",
        "- no account or position read",
        "- no contract qualification",
        "- no trading, order, cancel, or rebalance",
        "- no Telegram real send",
        "- no secrets, token, account id, or chat id read",
        "",
        "## Current Block",
        "",
        f"- market_data_status={row['market_data_status']}",
        f"- market_data_classification={row['market_data_classification']}",
        f"- ibkr_error_code={row['ibkr_error_code']}",
        "- GLD / SLV only",
        "",
        "## Frozen Scope",
        "",
        f"- jp_status={row['jp_status']}",
        f"- cn_status={row['cn_status']}",
        f"- generated_at_utc={row['generated_at_utc']}",
    ]
    return "\n".join(lines) + "\n"


def write_dashboard_pack(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.write_text(build_dashboard_pack(row), encoding="utf-8")


def generate_dashboard_ui_enhancement_pack(
    *,
    output_index: PathLike = DASHBOARD_INDEX,
    output_css: PathLike = DASHBOARD_CSS,
    output_snapshot: PathLike = DASHBOARD_SNAPSHOT,
    output_csv: PathLike = OUTPUT_CSV,
    output_report: PathLike = OUTPUT_REPORT,
    output_pack: PathLike = OUTPUT_PACK,
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    snapshot = build_status_snapshot(generated_at=generated_at)
    row = _snapshot_to_row(snapshot)
    write_status_snapshot(output_snapshot, snapshot)
    write_dashboard_css(output_css)
    write_dashboard_html(output_index, snapshot)
    write_dashboard_csv(output_csv, row)
    write_dashboard_report(output_report, row)
    write_dashboard_pack(output_pack, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 633-640 dashboard UI enhancement pack.")
    parser.add_argument("--output-index", default=DASHBOARD_INDEX)
    parser.add_argument("--output-css", default=DASHBOARD_CSS)
    parser.add_argument("--output-snapshot", default=DASHBOARD_SNAPSHOT)
    parser.add_argument("--output-csv", default=OUTPUT_CSV)
    parser.add_argument("--output-report", default=OUTPUT_REPORT)
    parser.add_argument("--output-pack", default=OUTPUT_PACK)
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generate_dashboard_ui_enhancement_pack(
        output_index=args.output_index,
        output_css=args.output_css,
        output_snapshot=args.output_snapshot,
        output_csv=args.output_csv,
        output_report=args.output_report,
        output_pack=args.output_pack,
        generated_at=args.generated_at,
    )
    print("[DASHBOARD_UI_ENHANCEMENT_PACK] generated")
    print(f"status={STATUS}")
    print(f"final_mvp_status={FINAL_MVP_STATUS}")
    print(f"archive_handoff_status={ARCHIVE_HANDOFF_STATUS}")
    print("dashboard_index=dashboard/index.html")
    print("dashboard_css=dashboard/assets/style.css")
    print("status_snapshot=dashboard/data/status_snapshot.json")
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
