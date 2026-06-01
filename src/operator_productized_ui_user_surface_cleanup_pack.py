from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

from src.operator_productized_ui_public_data_intake_pack import (
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    CN_STATUS,
    DASHBOARD_CSS,
    DASHBOARD_INDEX,
    FINAL_LANDING_AUDIT_SNAPSHOT,
    IBKR_ERROR_CODE,
    JP_STATUS,
    MARKET_DATA_STATUS,
    NO_TEXT,
    OPERATOR_TIMELINE,
    POSITION_READ_FIELD,
    STATUS_SNAPSHOT,
    SYMBOLS_TEXT,
)


PHASE = "Phase 1121-1160"
STATUS = "PRODUCTIZED_UI_USER_SURFACE_CLEANUP_READY"
UI_GENERATION = "V11_PRODUCTIZED_USER_SURFACE_CLEANUP"

USER_SURFACE_CLEANUP_SNAPSHOT = "dashboard/data/user_surface_cleanup_snapshot.json"
PRIMARY_NAVIGATION_SNAPSHOT = "dashboard/data/primary_navigation_snapshot.json"
DEVELOPER_MODE_VISIBILITY_SNAPSHOT = "dashboard/data/developer_mode_visibility_snapshot.json"
USER_FACING_SAFETY_COPY_SNAPSHOT = "dashboard/data/user_facing_safety_copy_snapshot.json"
OUTPUT_CSV = "operator_productized_ui_user_surface_cleanup_pack.csv"
OUTPUT_REPORT = "reports/operator_productized_ui_user_surface_cleanup_pack_report.md"
OUTPUT_PACK = "Precious_Metals_Monitor_Productized_UI_User_Surface_Cleanup_Pack.md"

PRIMARY_NAVIGATION = ("总览", "标的观察", "数据源", "本地报告", "风险边界", "设置")
USER_SAFETY_COPY = (
    "未确认数据源前，不显示价格",
    "无有效价格时，不生成分析信号",
    "未确认条款前，不启用自动导入",
    "数据新鲜度未验证前，只生成研究框架",
)
HIDDEN_TECHNICAL_ITEMS = (
    "UI_DRIVEN_LOCAL_RESEARCH_PLATFORM_MVP_READY",
    "PRODUCTIZED_UI_PUBLIC_DATA_INTAKE_READY",
    "BLOCKED_BY_SUBSCRIPTION",
    "IBKR_ERROR_10089",
    "GET_ONLY",
    "CLI fallback",
    "python3 main.py --productized-ui-user-surface-cleanup-pack",
    "python3 main.py --local-ui-server",
    "source_connection_implemented=NO",
    "live_market_data_enabled=NO",
)
ARTIFACTS = (
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    STATUS_SNAPSHOT,
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    OPERATOR_TIMELINE,
    USER_SURFACE_CLEANUP_SNAPSHOT,
    PRIMARY_NAVIGATION_SNAPSHOT,
    DEVELOPER_MODE_VISIBILITY_SNAPSHOT,
    USER_FACING_SAFETY_COPY_SNAPSHOT,
    FINAL_LANDING_AUDIT_SNAPSHOT,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)
CSV_FIELDS = (
    "phase",
    "status",
    "ui_generation",
    "user_surface_cleanup_status",
    "primary_navigation_status",
    "developer_mode_visibility_status",
    "user_facing_safety_copy_status",
    "public_data_connection_implemented",
    "external_market_data_request_enabled",
    "real_price_ingestion_enabled",
    "source_connection_implemented",
    "live_market_data_enabled",
    "market_data_status",
    "ibkr_error_code",
    "realtime_market_data_verified",
    "production_ready",
    "trading_enabled",
    "account_read_enabled",
    POSITION_READ_FIELD,
    "historical_data_enabled",
    "telegram_real_send_enabled",
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
    return {
        "phase": PHASE,
        "status": STATUS,
        "ui_generation": UI_GENERATION,
        "user_surface_cleanup_status": "USER_SURFACE_CLEANUP_READY",
        "primary_navigation_status": "PRIMARY_NAVIGATION_USER_FACING_READY",
        "developer_mode_visibility_status": "DEVELOPER_MODE_COLLAPSED_AND_DEEMPHASIZED",
        "user_facing_safety_copy_status": "USER_FACING_SAFETY_COPY_READY",
        "public_data_connection_implemented": NO_TEXT,
        "external_market_data_request_enabled": NO_TEXT,
        "real_price_ingestion_enabled": NO_TEXT,
        "source_connection_implemented": NO_TEXT,
        "live_market_data_enabled": NO_TEXT,
        "market_data_status": MARKET_DATA_STATUS,
        "ibkr_error_code": IBKR_ERROR_CODE,
        "realtime_market_data_verified": NO_TEXT,
        "production_ready": NO_TEXT,
        "trading_enabled": NO_TEXT,
        "account_read_enabled": NO_TEXT,
        POSITION_READ_FIELD: NO_TEXT,
        "historical_data_enabled": NO_TEXT,
        "telegram_real_send_enabled": NO_TEXT,
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "symbols": SYMBOLS_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_user_surface_cleanup_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "USER_SURFACE_CLEANUP_READY",
        "home_surface": "USER_FACING_RESEARCH_WORKBENCH_ONLY",
        "hidden_by_default": [
            "developer details",
            "advanced information",
            "terminal fallback",
            "CLI commands",
            "engineering status codes",
        ],
        "removed_primary_menu_items": ["下一步操作"],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_primary_navigation_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "PRIMARY_NAVIGATION_USER_FACING_READY",
        "navigation": list(PRIMARY_NAVIGATION),
        "removed": ["下一步操作"],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_developer_mode_visibility_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "DEVELOPER_MODE_COLLAPSED_AND_DEEMPHASIZED",
        "default_visibility": "COLLAPSED",
        "surface_priority": "LOW",
        "allowed_container": "设置页底部高级信息折叠区",
        "technical_items": list(HIDDEN_TECHNICAL_ITEMS),
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_user_facing_safety_copy_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "USER_FACING_SAFETY_COPY_READY",
        "copy": list(USER_SAFETY_COPY),
        "code_like_rule_copy_visible": NO_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_build_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": STATUS,
        "ui_generation": UI_GENERATION,
        "production_ready": NO_TEXT,
        "trading_enabled": NO_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_operator_timeline(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "timeline": [
            {"phase": "Phase 1001-1120", "theme": "Productized UI and public data intake preparation", "status": "READY"},
            {"phase": PHASE, "theme": "Productized UI user surface cleanup", "status": STATUS},
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_final_landing_audit_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "LOCAL_PLATFORM_MVP_FINAL_AUDIT_READY",
        "user_surface_cleanup_ready": "YES",
        "ui_driven_workbench_ready": "YES",
        "terminal_role": "STARTUP_AND_FALLBACK_ONLY",
        "developer_mode_collapsed_by_default": "YES",
        "all_external_actions_blocked": "YES",
        "no_real_market_data": "YES",
        "no_source_connection_implemented": "YES",
        "no_live_market_data_enabled": "YES",
        "no_trading": "YES",
        "no_telegram_real_send": "YES",
        "market_data_status": MARKET_DATA_STATUS,
        "ibkr_error_code": IBKR_ERROR_CODE,
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_artifact_manifest(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": STATUS,
        "artifacts": [
            {
                "artifact_path": path,
                "type": Path(path).suffix.lstrip(".").upper() or "PACK",
                "category": _artifact_category(path),
                "local_href": _artifact_local_href(path),
                "external_effect": "NONE_LOCAL_ARTIFACT_GENERATION_ONLY",
            }
            for path in ARTIFACTS
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_dashboard_html(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    nav = "\n".join(
        f'          <a class="nav-item{" active" if index == 0 else ""}" href="#{anchor}"><span class="nav-icon">{label[0]}</span><span>{label}</span></a>'
        for index, (label, anchor) in enumerate(
            zip(PRIMARY_NAVIGATION, ("overview", "watch", "data-source", "reports", "risk", "settings"))
        )
    )
    safety_copy = "\n".join(f"              <li>{item}</li>" for item in USER_SAFETY_COPY)
    technical_items = "\n".join(f"              <code>{item}</code>" for item in HIDDEN_TECHNICAL_ITEMS)
    artifacts = "\n".join(
        f'              <article class="file-card"><span class="token neutral">{_artifact_category(path)}</span><span class="mono">{path}</span><a class="local-link" href="{_artifact_local_href(path)}">本地路径</a></article>'
        for path in ARTIFACTS
    )
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI 投研工作台</title>
    <link rel="stylesheet" href="assets/style.css">
  </head>
  <body>
    <div class="app-shell">
      <aside class="sidebar" aria-label="左侧导航">
        <div class="brand"><span class="brand-mark">AI</span><span class="brand-title">AI 投研工作台</span><span class="brand-subtitle">本地只读研究平台</span></div>
        <nav class="sidebar-nav" aria-label="投研分区">
{nav}
        </nav>
      </aside>
      <div class="content">
        <header class="hero" id="overview">
          <div>
            <p class="eyebrow">总览</p>
            <h1>AI 投研工作台</h1>
            <p class="subtitle">本地投研工作台已就绪 · GLD / SLV · 当前未启用实时行情</p>
          </div>
          <div class="hero-status">
            <strong>本地投研工作台已就绪</strong>
            <span>数据源状态：准备中</span>
          </div>
        </header>

        <main class="workbench">
          <section class="summary-grid" aria-label="工作台状态">
            <article class="panel">
              <span class="eyebrow">当前支持</span>
              <h2>当前支持 GLD / SLV 研究框架</h2>
              <p class="muted">页面聚焦标的观察、数据源状态、本地报告与风险边界。</p>
            </article>
            <article class="panel">
              <span class="eyebrow">行情状态</span>
              <h2>当前未启用实时行情</h2>
              <p class="muted">未确认数据源前，工作台不显示价格，不生成分析信号。</p>
            </article>
            <article class="panel">
              <span class="eyebrow">权限边界</span>
              <h2>当前不会读取账户、持仓或发送交易指令</h2>
              <p class="muted">账户、持仓、交易、Telegram 实发均保持关闭。</p>
            </article>
          </section>

          <section class="panel" id="watch">
            <div class="panel-header"><div><span class="eyebrow">标的观察</span><h2>GLD / SLV 研究框架</h2></div><a class="primary-action" href="../reports/local_research_report_framework_GLD_SLV.md">查看本地报告</a></div>
            <div class="framework-grid">
              <span>日内观察</span><span>短期结构</span><span>中期配置</span><span>长期跟踪</span>
            </div>
          </section>

          <section class="panel" id="data-source">
            <span class="eyebrow">数据源</span>
            <h2>数据源状态</h2>
            <div class="source-status-grid">
              <article><strong>公共行情源</strong><span>待确认</span></article>
              <article><strong>手动 CSV</strong><span>可作为后续 fallback</span></article>
              <article><strong>IBKR 行情权限</strong><span>未开通</span></article>
            </div>
          </section>

          <section class="panel" id="reports">
            <span class="eyebrow">本地报告</span>
            <h2>报告入口</h2>
            <div class="report-list">
              <a href="../reports/operator_daily_packet_preview.md">今日状态预览</a>
              <a href="../reports/local_research_report_framework_GLD_SLV.md">GLD / SLV 研究框架</a>
              <a href="../reports/telegram_preview_local_only.md">Telegram 预览</a>
              <a href="../reports/productized_ui_user_guide.md">风险边界说明</a>
            </div>
          </section>

          <section class="panel" id="risk">
            <span class="eyebrow">风险边界</span>
            <h2>当前不会</h2>
            <div class="risk-list">
              <button class="disabled-action" type="button" disabled>获取实时行情</button>
              <button class="disabled-action" type="button" disabled>读取账户</button>
              <button class="disabled-action" type="button" disabled>读取持仓</button>
              <button class="disabled-action" type="button" disabled>生成分析信号</button>
              <button class="disabled-action" type="button" disabled>发送 Telegram</button>
              <button class="disabled-action" type="button" disabled>发送交易指令</button>
            </div>
            <ul class="safety-rules">
{safety_copy}
            </ul>
          </section>

          <section class="panel settings-panel" id="settings">
            <span class="eyebrow">设置</span>
            <h2>工作台设置</h2>
            <p class="muted">默认使用普通投研视图。高级信息仅用于本地排查和人工核对。</p>
            <details class="developer-details">
              <summary>高级信息</summary>
              <div class="developer-grid">
{technical_items}
              </div>
              <button class="secondary-action" type="button" data-copy="python3 main.py --productized-ui-user-surface-cleanup-pack">复制终端兜底命令</button>
              <div class="file-stream">
{artifacts}
              </div>
              <p class="muted mono">generated_at_utc={timestamp}</p>
            </details>
          </section>
        </main>
      </div>
    </div>
    <script>
      (function () {{
        document.querySelectorAll("[data-copy]").forEach(function (button) {{
          button.addEventListener("click", function () {{
            var text = button.getAttribute("data-copy");
            var area = document.createElement("textarea");
            area.value = text;
            document.body.appendChild(area);
            area.select();
            document.execCommand("copy");
            document.body.removeChild(area);
            button.textContent = "已复制";
          }});
        }});
      }})();
    </script>
  </body>
</html>
"""


def build_dashboard_css() -> str:
    return """:root {
  color-scheme: light;
  --bg: #f5f7f8;
  --surface: #ffffff;
  --surface-2: #eef4f3;
  --line: #d6e0de;
  --text: #17211f;
  --muted: #65726f;
  --green: #177a58;
  --blue: #285f95;
  --red: #a84545;
}
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; background: var(--bg); color: var(--text); font-family: Arial, Helvetica, sans-serif; font-size: 14px; line-height: 1.5; }
a { color: inherit; text-decoration: none; }
button { font: inherit; }
.mono { font-family: Consolas, Monaco, monospace; }
.app-shell { display: grid; grid-template-columns: 248px minmax(0, 1fr); min-height: 100vh; }
.sidebar { background: #10211d; color: #eff7f4; height: 100vh; padding: 20px 14px; position: sticky; top: 0; }
.brand { border-bottom: 1px solid rgba(255,255,255,0.16); margin-bottom: 14px; padding-bottom: 16px; }
.brand-mark, .nav-icon { align-items: center; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.18); border-radius: 8px; display: inline-flex; font-weight: 800; height: 30px; justify-content: center; margin-right: 8px; width: 30px; }
.brand-title { display: block; font-size: 17px; font-weight: 800; margin-top: 8px; }
.brand-subtitle, .eyebrow { color: var(--muted); font-size: 12px; font-weight: 800; }
.sidebar .brand-subtitle { color: #b8cbc5; }
.sidebar-nav { display: grid; gap: 8px; }
.nav-item { align-items: center; border-radius: 8px; color: #d6e2de; display: flex; min-height: 42px; padding: 7px 8px; }
.nav-item.active, .nav-item:hover { background: rgba(255,255,255,0.1); color: #fff; }
.content { min-width: 0; padding: 22px; }
.hero, .panel { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 10px 24px rgba(22, 35, 31, 0.06); }
.hero { align-items: end; display: grid; gap: 20px; grid-template-columns: minmax(0, 1fr) minmax(220px, 320px); margin-bottom: 16px; padding: 24px; }
h1 { font-size: 34px; line-height: 1.15; margin: 0; }
h2 { font-size: 18px; margin: 4px 0 0; }
.subtitle, .muted { color: var(--muted); }
.hero-status { background: var(--surface-2); border: 1px solid var(--line); border-radius: 8px; display: grid; gap: 6px; padding: 14px; }
.hero-status strong { color: var(--green); font-size: 18px; }
.workbench { display: grid; gap: 14px; }
.summary-grid { display: grid; gap: 12px; grid-template-columns: repeat(3, minmax(0, 1fr)); }
.panel { padding: 16px; }
.panel-header { align-items: center; border-bottom: 1px solid var(--line); display: flex; gap: 12px; justify-content: space-between; margin-bottom: 14px; padding-bottom: 10px; }
.framework-grid, .report-list, .risk-list, .source-status-grid, .developer-grid, .file-stream { display: grid; gap: 10px; }
.framework-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.framework-grid span, .report-list a, .source-status-grid article { background: var(--surface-2); border: 1px solid var(--line); border-radius: 8px; padding: 12px; }
.source-status-grid { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); margin-top: 12px; }
.source-status-grid article { display: grid; gap: 8px; }
.source-status-grid span { color: var(--green); font-weight: 800; }
.report-list { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); margin-top: 12px; }
.risk-list { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); margin-top: 12px; }
.primary-action, .secondary-action { align-items: center; border-radius: 8px; cursor: pointer; display: inline-flex; justify-content: center; min-height: 38px; padding: 8px 12px; }
.primary-action { background: var(--green); border: 1px solid var(--green); color: #fff; }
.secondary-action { background: #e8f0ef; border: 1px solid var(--line); color: var(--text); margin-top: 10px; }
.disabled-action { background: #fff4f3; border: 1px solid #efc2bd; border-radius: 8px; color: var(--red); cursor: not-allowed; min-height: 40px; padding: 9px 10px; }
.safety-rules { background: #fbf7ef; border: 1px solid #ead8b8; border-radius: 8px; color: #71521b; display: grid; gap: 8px; margin: 14px 0 0; padding: 14px 14px 14px 32px; }
.settings-panel { background: #fbfcfc; }
.developer-details { border-top: 1px solid var(--line); color: var(--muted); margin-top: 14px; padding-top: 12px; }
.developer-details summary { cursor: pointer; font-size: 12px; font-weight: 800; }
.developer-grid { grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); margin: 12px 0; }
.developer-grid code, .file-card { background: #f0f3f2; border: 1px solid var(--line); border-radius: 8px; padding: 10px; overflow-wrap: anywhere; }
.token { border: 1px solid var(--line); border-radius: 999px; color: var(--blue); display: inline-flex; font-size: 11px; font-weight: 800; padding: 3px 8px; }
.neutral { color: var(--muted); }
.file-stream { margin-top: 12px; }
.file-card { align-items: center; display: grid; grid-template-columns: 80px minmax(0, 1fr) 90px; }
.local-link { color: var(--green); font-weight: 800; }
@media (max-width: 980px) {
  .app-shell { grid-template-columns: 1fr; }
  .sidebar { height: auto; position: relative; }
  .sidebar-nav { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hero, .summary-grid, .framework-grid { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .content { padding: 12px; }
  .panel-header, .file-card { grid-template-columns: 1fr; align-items: start; }
  h1 { font-size: 28px; }
}
"""


def build_report(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    return f"""# Phase 1121-1160 Productized UI User Surface Cleanup Pack

- status: {STATUS}
- primary navigation is user-facing: 总览 / 标的观察 / 数据源 / 本地报告 / 风险边界 / 设置
- developer details collapsed and visually de-emphasized
- terminal fallback commands hidden inside advanced information
- engineering status codes hidden from the primary surface
- safety rules rewritten as Chinese user-facing business copy
- no IBKR connection
- no market data request
- no historical data request
- no account read
- no holding read
- no contract qualification
- no trading
- no Telegram real send
- no directional signal
- no target, stop, or take-profit levels
- no live price fields
- generated_at_utc: {timestamp}
"""


def generate_productized_ui_user_surface_cleanup_pack(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    status = build_status_snapshot(timestamp)
    row = {field: status.get(field, "") for field in CSV_FIELDS}

    _write_text(DASHBOARD_INDEX, build_dashboard_html(timestamp))
    _write_text(DASHBOARD_CSS, build_dashboard_css())
    _write_json(STATUS_SNAPSHOT, status)
    _write_json(ARTIFACT_MANIFEST, build_artifact_manifest(timestamp))
    _write_json(BUILD_SNAPSHOT, build_build_snapshot(timestamp))
    _write_json(OPERATOR_TIMELINE, build_operator_timeline(timestamp))
    _write_json(USER_SURFACE_CLEANUP_SNAPSHOT, build_user_surface_cleanup_snapshot(timestamp))
    _write_json(PRIMARY_NAVIGATION_SNAPSHOT, build_primary_navigation_snapshot(timestamp))
    _write_json(DEVELOPER_MODE_VISIBILITY_SNAPSHOT, build_developer_mode_visibility_snapshot(timestamp))
    _write_json(USER_FACING_SAFETY_COPY_SNAPSHOT, build_user_facing_safety_copy_snapshot(timestamp))
    _write_json(FINAL_LANDING_AUDIT_SNAPSHOT, build_final_landing_audit_snapshot(timestamp))

    csv_path = Path(OUTPUT_CSV)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)
    _write_text(OUTPUT_REPORT, build_report(timestamp))
    _write_text(OUTPUT_PACK, build_report(timestamp))
    return row


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 1121-1160 productized UI user surface cleanup pack.")
    parser.parse_args(argv)
    row = generate_productized_ui_user_surface_cleanup_pack()
    print("[PRODUCTIZED_UI_USER_SURFACE_CLEANUP_PACK] generated")
    print(f"phase={row['phase']}")
    print(f"status={row['status']}")
    print(f"ui_generation={row['ui_generation']}")
    print(f"user_surface_cleanup_status={row['user_surface_cleanup_status']}")
    print(f"developer_mode_visibility_status={row['developer_mode_visibility_status']}")
    print(f"csv={OUTPUT_CSV}")
    print(f"report={OUTPUT_REPORT}")
    print(f"pack={OUTPUT_PACK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
