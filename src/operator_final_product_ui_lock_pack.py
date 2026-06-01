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


PHASE = "Phase 1161-1320"
STATUS = "FINAL_PRODUCT_UI_LOCK_READY"
UI_GENERATION = "V12_FINAL_PRODUCT_UI_LOCK"
YES_TEXT = "YES"

FINAL_PRODUCT_UI_LOCK_SNAPSHOT = "dashboard/data/final_product_ui_lock_snapshot.json"
FINAL_NAVIGATION_SNAPSHOT = "dashboard/data/final_navigation_snapshot.json"
FINAL_DASHBOARD_LAYOUT_SNAPSHOT = "dashboard/data/final_dashboard_layout_snapshot.json"
FINAL_VISUAL_SYSTEM_SNAPSHOT = "dashboard/data/final_visual_system_snapshot.json"
FINAL_USER_WORKFLOW_SNAPSHOT = "dashboard/data/final_user_workflow_snapshot.json"
FINAL_UI_REGRESSION_GUARD_SNAPSHOT = "dashboard/data/final_ui_regression_guard_snapshot.json"
OUTPUT_CSV = "operator_final_product_ui_lock_pack.csv"
OUTPUT_REPORT = "reports/operator_final_product_ui_lock_pack_report.md"
OUTPUT_USER_GUIDE = "reports/final_product_ui_user_guide.md"
OUTPUT_PACK = "Precious_Metals_Monitor_Final_Product_UI_Lock_Pack.md"

NAVIGATION = ("总览", "标的观察", "数据源", "本地报告", "风险边界", "设置")
SOURCE_STATUS_ITEMS = (
    ("IBKR 行情权限", "未开通"),
    ("公共延迟源", "待评估"),
    ("手动 CSV", "可作为后续 fallback"),
    ("付费 API", "暂不优先"),
    ("混合路由", "未来扩展"),
)
RISK_BOUNDARY_COPY = (
    "当前不会获取实时行情",
    "当前不会读取账户",
    "当前不会读取持仓",
    "当前不会生成交易指令",
    "当前不会发送 Telegram",
    "当前不会解冻 JP / CN",
)
REPORT_CENTER_ITEMS = (
    ("今日状态预览", "../reports/operator_daily_packet_preview.md"),
    ("GLD / SLV 研究框架", "../reports/local_research_report_framework_GLD_SLV.md"),
    ("数据源准备说明", "../reports/public_data_intake_preparation_report.md"),
    ("Telegram 预览", "../reports/telegram_preview_local_only.md"),
    ("风险边界说明", "../reports/final_product_ui_user_guide.md"),
)
ADVANCED_ITEMS = (
    "开发者状态",
    "终端兜底命令",
    "本地 API 状态",
    "artifact 调试信息",
    "安全状态码",
    "PRODUCTIZED_UI_USER_SURFACE_CLEANUP_READY",
    "PRODUCTIZED_UI_PUBLIC_DATA_INTAKE_READY",
    "UI_DRIVEN_LOCAL_RESEARCH_PLATFORM_MVP_READY",
    "BLOCKED_BY_SUBSCRIPTION",
    "IBKR_ERROR_10089",
    "GET_ONLY",
    "CLI fallback",
    "python3 main.py --final-product-ui-lock-pack",
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
    FINAL_PRODUCT_UI_LOCK_SNAPSHOT,
    FINAL_NAVIGATION_SNAPSHOT,
    FINAL_DASHBOARD_LAYOUT_SNAPSHOT,
    FINAL_VISUAL_SYSTEM_SNAPSHOT,
    FINAL_USER_WORKFLOW_SNAPSHOT,
    FINAL_UI_REGRESSION_GUARD_SNAPSHOT,
    FINAL_LANDING_AUDIT_SNAPSHOT,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_USER_GUIDE,
    OUTPUT_PACK,
)
CSV_FIELDS = (
    "phase",
    "status",
    "ui_generation",
    "final_product_ui_status",
    "ui_final_locked",
    "product_ui_mode",
    "developer_mode",
    "template_reference_mode",
    "external_assets_used",
    "external_template_code_copied",
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
        "final_product_ui_status": "FINAL_PRODUCT_UI_READY",
        "ui_final_locked": YES_TEXT,
        "product_ui_mode": "USER_FACING_RESEARCH_WORKBENCH",
        "developer_mode": "COLLAPSED_IN_SETTINGS",
        "template_reference_mode": "INSPIRED_ONLY_NO_CODE_COPIED",
        "external_assets_used": NO_TEXT,
        "external_template_code_copied": NO_TEXT,
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


def build_final_product_ui_lock_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": STATUS,
        "ui_final_locked": YES_TEXT,
        "final_product_ui_status": "FINAL_PRODUCT_UI_READY",
        "product_ui_mode": "USER_FACING_RESEARCH_WORKBENCH",
        "developer_mode": "COLLAPSED_IN_SETTINGS",
        "template_reference_mode": "INSPIRED_ONLY_NO_CODE_COPIED",
        "external_assets_used": NO_TEXT,
        "external_template_code_copied": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_final_navigation_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "FINAL_NAVIGATION_READY",
        "navigation": list(NAVIGATION),
        "primary_menu_user_facing": YES_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_final_dashboard_layout_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "FINAL_DASHBOARD_LAYOUT_READY",
        "sections": ["首屏状态", "标的观察", "行情源状态", "报告中心", "风险边界", "设置"],
        "home_cards": ["平台状态", "当前标的", "数据源", "报告", "风险边界"],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_final_visual_system_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "FINAL_VISUAL_SYSTEM_READY",
        "theme": "DARK_FINANCIAL_RESEARCH_WORKBENCH",
        "external_assets_used": NO_TEXT,
        "cdn_used": NO_TEXT,
        "remote_font_used": NO_TEXT,
        "third_party_js_used": NO_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_final_user_workflow_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "FINAL_USER_WORKFLOW_READY",
        "workflow": ["查看总览", "观察 GLD / SLV", "核对数据源状态", "查看本地报告", "确认风险边界"],
        "developer_mode_entry": "设置页高级模式",
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_final_ui_regression_guard_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "FINAL_UI_REGRESSION_GUARD_READY",
        "guard_groups": [
            "remote asset markers",
            "external request APIs",
            "directional trading terms",
            "numeric market value fields",
            "chart-like price visuals",
        ],
        "default_surface_must_hide_technical_status": YES_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_build_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": STATUS,
        "ui_generation": UI_GENERATION,
        "ui_final_locked": YES_TEXT,
        "production_ready": NO_TEXT,
        "trading_enabled": NO_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_operator_timeline(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "timeline": [
            {"phase": "Phase 1121-1160", "theme": "Productized UI user surface cleanup", "status": "READY"},
            {"phase": PHASE, "theme": "Final product UI lock", "status": STATUS},
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_final_landing_audit_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "LOCAL_PLATFORM_MVP_FINAL_AUDIT_READY",
        "ui_final_locked": YES_TEXT,
        "all_external_actions_blocked": YES_TEXT,
        "developer_mode_collapsed_by_default": YES_TEXT,
        "no_real_market_data": YES_TEXT,
        "no_source_connection_implemented": YES_TEXT,
        "no_live_market_data_enabled": YES_TEXT,
        "no_trading": YES_TEXT,
        "no_telegram_real_send": YES_TEXT,
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
        f'          <a class="nav-item{" active" if index == 0 else ""}" href="#{anchor}"><span class="nav-index">0{index + 1}</span><span>{label}</span></a>'
        for index, (label, anchor) in enumerate(
            zip(NAVIGATION, ("overview", "watch", "data-source", "reports", "risk", "settings"))
        )
    )
    source_cards = "\n".join(
        f"              <article><span>{label}</span><strong>{value}</strong></article>" for label, value in SOURCE_STATUS_ITEMS
    )
    risk_copy = "\n".join(f"              <li>{item}</li>" for item in RISK_BOUNDARY_COPY)
    reports = "\n".join(f'              <a href="{href}"><span>{label}</span><small>本地只读</small></a>' for label, href in REPORT_CENTER_ITEMS)
    advanced_items = "\n".join(f"                <code>{item}</code>" for item in ADVANCED_ITEMS)
    advanced_artifacts = "\n".join(
        f'                <article class="debug-row"><span>{_artifact_category(path)}</span><strong>{path}</strong><a href="{_artifact_local_href(path)}">查看</a></article>'
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
        <div class="brand">
          <span class="brand-mark">AI</span>
          <span class="brand-title">AI 投研工作台</span>
          <span class="brand-subtitle">本地只读研究平台</span>
        </div>
        <nav class="sidebar-nav" aria-label="投研导航">
{nav}
        </nav>
        <div class="sidebar-foot">只读模式</div>
      </aside>

      <div class="content">
        <header class="hero" id="overview">
          <div class="hero-copy">
            <span class="eyebrow">总览</span>
            <h1>AI 投研工作台</h1>
            <p>本地只读研究平台 · GLD / SLV · 无实时行情 · 无交易权限</p>
          </div>
          <div class="hero-panel">
            <span>平台状态</span>
            <strong>本地工作台已就绪</strong>
          </div>
        </header>

        <main class="dashboard-grid">
          <section class="status-strip" aria-label="首屏状态">
            <article><span>当前标的</span><strong>GLD / SLV</strong></article>
            <article><span>数据源</span><strong>准备中</strong></article>
            <article><span>报告</span><strong>研究框架可查看</strong></article>
            <article><span>风险边界</span><strong>只读安全模式</strong></article>
          </section>

          <section class="panel" id="watch">
            <div class="section-header">
              <div><span class="eyebrow">标的观察</span><h2>GLD / SLV</h2></div>
              <span class="pill">暂无实时行情：数据源确认后显示</span>
            </div>
            <div class="symbol-grid">
              <article class="symbol-card">
                <div><h3>GLD</h3><span>SPDR Gold Shares</span></div>
                <dl>
                  <div><dt>市场</dt><dd>US ETF</dd></div>
                  <div><dt>数据状态</dt><dd>等待数据源</dd></div>
                  <div><dt>报告状态</dt><dd>研究框架可用</dd></div>
                  <div><dt>风险状态</dt><dd>只读</dd></div>
                </dl>
              </article>
              <article class="symbol-card">
                <div><h3>SLV</h3><span>iShares Silver Trust</span></div>
                <dl>
                  <div><dt>市场</dt><dd>US ETF</dd></div>
                  <div><dt>数据状态</dt><dd>等待数据源</dd></div>
                  <div><dt>报告状态</dt><dd>研究框架可用</dd></div>
                  <div><dt>风险状态</dt><dd>只读</dd></div>
                </dl>
              </article>
            </div>
          </section>

          <section class="panel" id="data-source">
            <div class="section-header">
              <div><span class="eyebrow">数据源</span><h2>行情源状态</h2></div>
              <span class="pill muted-pill">暂不启动真实连接</span>
            </div>
            <div class="source-grid">
{source_cards}
            </div>
          </section>

          <section class="panel" id="reports">
            <div class="section-header">
              <div><span class="eyebrow">本地报告</span><h2>报告中心</h2></div>
              <span class="pill">暂无真实报告：当前仅提供研究框架</span>
            </div>
            <div class="report-grid">
{reports}
            </div>
          </section>

          <section class="panel" id="risk">
            <div class="section-header">
              <div><span class="eyebrow">风险边界</span><h2>只读安全模式</h2></div>
              <span class="pill danger-pill">外部动作关闭</span>
            </div>
            <ul class="risk-copy">
{risk_copy}
            </ul>
          </section>

          <section class="panel settings-panel" id="settings">
            <div class="section-header">
              <div><span class="eyebrow">设置</span><h2>工作台设置</h2></div>
              <span class="pill muted-pill">普通视图默认启用</span>
            </div>
            <p class="muted">高级模式仅用于本地排查。默认折叠，不占用投研操作区。</p>
            <details class="advanced-mode">
              <summary>高级模式</summary>
              <div class="advanced-grid">
{advanced_items}
              </div>
              <button class="secondary-action" type="button" data-copy="python3 main.py --final-product-ui-lock-pack">复制终端兜底命令</button>
              <div class="debug-list">
{advanced_artifacts}
              </div>
              <p class="muted mono">generated_at_utc={timestamp}</p>
            </details>
          </section>
        </main>
      </div>
    </div>
    <footer class="readonly-footer">只读模式 · 本地工作台 · 不连接行情源 · 不执行交易</footer>
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
  color-scheme: dark;
  --bg: #090d12;
  --sidebar: #0d171a;
  --surface: #111a20;
  --surface-2: #17232b;
  --surface-3: #1e2c34;
  --line: #29404a;
  --line-soft: rgba(148, 163, 184, 0.22);
  --text: #edf5f2;
  --muted: #99aaa5;
  --green: #4fd099;
  --blue: #7fb4ff;
  --amber: #d8a64f;
  --red: #e07676;
}
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; background: var(--bg); color: var(--text); font-family: Arial, Helvetica, sans-serif; font-size: 14px; line-height: 1.5; }
a { color: inherit; text-decoration: none; }
button { font: inherit; }
.mono { font-family: Consolas, Monaco, monospace; }
.app-shell { display: grid; grid-template-columns: 260px minmax(0, 1fr); min-height: 100vh; }
.sidebar { background: var(--sidebar); border-right: 1px solid var(--line); color: var(--text); height: 100vh; padding: 22px 16px; position: sticky; top: 0; }
.brand { border-bottom: 1px solid var(--line); display: grid; gap: 7px; margin-bottom: 18px; padding-bottom: 18px; }
.brand-mark { align-items: center; background: rgba(79, 208, 153, 0.14); border: 1px solid rgba(79, 208, 153, 0.35); border-radius: 8px; color: var(--green); display: inline-flex; font-weight: 800; height: 34px; justify-content: center; width: 38px; }
.brand-title { font-size: 18px; font-weight: 800; }
.brand-subtitle, .eyebrow, .muted { color: var(--muted); }
.eyebrow { font-size: 12px; font-weight: 800; }
.sidebar-nav { display: grid; gap: 8px; }
.nav-item { align-items: center; border: 1px solid transparent; border-radius: 8px; color: #cdd9d5; display: flex; gap: 10px; min-height: 42px; padding: 8px 9px; }
.nav-item.active, .nav-item:hover { background: rgba(79, 208, 153, 0.1); border-color: rgba(79, 208, 153, 0.26); color: #fff; }
.nav-index { color: var(--green); font-size: 11px; font-weight: 800; }
.sidebar-foot { border: 1px solid var(--line); border-radius: 8px; color: var(--muted); font-size: 12px; font-weight: 800; margin-top: 18px; padding: 10px; }
.content { min-width: 0; padding: 22px 24px 68px; }
.hero { align-items: stretch; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; display: grid; gap: 16px; grid-template-columns: minmax(0, 1fr) 280px; margin-bottom: 14px; padding: 22px; }
.hero-copy { display: grid; gap: 8px; }
h1 { font-size: 34px; line-height: 1.12; margin: 0; }
h2 { font-size: 18px; margin: 3px 0 0; }
h3 { font-size: 28px; margin: 0; }
p { margin: 0; }
.hero-panel, .status-strip article, .panel { background: var(--surface-2); border: 1px solid var(--line-soft); border-radius: 8px; }
.hero-panel { display: grid; gap: 8px; padding: 16px; }
.hero-panel span, .status-strip span { color: var(--muted); font-size: 12px; font-weight: 800; }
.hero-panel strong { color: var(--green); font-size: 20px; }
.dashboard-grid { display: grid; gap: 14px; }
.status-strip { display: grid; gap: 12px; grid-template-columns: repeat(4, minmax(0, 1fr)); }
.status-strip article { display: grid; gap: 8px; min-height: 92px; padding: 14px; }
.status-strip strong { font-size: 18px; }
.panel { padding: 16px; }
.section-header { align-items: center; border-bottom: 1px solid var(--line-soft); display: flex; gap: 12px; justify-content: space-between; margin-bottom: 14px; padding-bottom: 11px; }
.pill { background: rgba(79, 208, 153, 0.1); border: 1px solid rgba(79, 208, 153, 0.28); border-radius: 999px; color: var(--green); display: inline-flex; font-size: 12px; font-weight: 800; padding: 6px 10px; }
.muted-pill { background: rgba(127, 180, 255, 0.1); border-color: rgba(127, 180, 255, 0.26); color: var(--blue); }
.danger-pill { background: rgba(224, 118, 118, 0.1); border-color: rgba(224, 118, 118, 0.28); color: var(--red); }
.symbol-grid, .source-grid, .report-grid, .advanced-grid, .debug-list { display: grid; gap: 12px; }
.symbol-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.symbol-card, .source-grid article, .report-grid a, .advanced-grid code, .debug-row { background: var(--surface-3); border: 1px solid var(--line-soft); border-radius: 8px; padding: 14px; }
.symbol-card { display: grid; gap: 14px; }
.symbol-card h3 + span { color: var(--muted); }
dl { display: grid; gap: 8px; margin: 0; }
dl div { align-items: center; display: flex; justify-content: space-between; gap: 12px; }
dt { color: var(--muted); }
dd { font-weight: 800; margin: 0; }
.source-grid { grid-template-columns: repeat(5, minmax(0, 1fr)); }
.source-grid article { display: grid; gap: 7px; min-height: 92px; }
.source-grid span { color: var(--muted); font-weight: 800; }
.source-grid strong { color: var(--green); }
.report-grid { grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); }
.report-grid a { display: grid; gap: 7px; }
.report-grid small { color: var(--muted); }
.risk-copy { display: grid; gap: 9px; margin: 0; padding-left: 20px; }
.risk-copy li { color: #f0d8d8; }
.settings-panel { background: #10181d; }
.advanced-mode { border-top: 1px solid var(--line-soft); margin-top: 14px; padding-top: 12px; }
.advanced-mode summary { color: var(--muted); cursor: pointer; font-size: 12px; font-weight: 800; }
.advanced-grid { grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); margin: 12px 0; }
.advanced-grid code, .debug-row { color: #c9d6d2; overflow-wrap: anywhere; }
.secondary-action { background: rgba(127, 180, 255, 0.1); border: 1px solid rgba(127, 180, 255, 0.28); border-radius: 8px; color: var(--text); cursor: pointer; min-height: 38px; padding: 8px 12px; }
.debug-list { margin-top: 12px; }
.debug-row { align-items: center; display: grid; grid-template-columns: 80px minmax(0, 1fr) 80px; }
.debug-row span, .debug-row a { color: var(--green); font-size: 12px; font-weight: 800; }
.readonly-footer { background: rgba(9, 13, 18, 0.96); border-top: 1px solid var(--line); bottom: 0; color: var(--muted); font-size: 12px; font-weight: 800; left: 260px; padding: 10px 24px; position: fixed; right: 0; }
@media (max-width: 1180px) {
  .source-grid, .status-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 920px) {
  .app-shell { grid-template-columns: 1fr; }
  .sidebar { height: auto; position: relative; }
  .sidebar-nav { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hero, .symbol-grid, .source-grid, .status-strip { grid-template-columns: 1fr; }
  .readonly-footer { left: 0; }
}
@media (max-width: 640px) {
  .content { padding: 14px 12px 76px; }
  .section-header, .debug-row { align-items: start; grid-template-columns: 1fr; }
  h1 { font-size: 28px; }
}
"""


def build_report(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    return f"""# Phase 1161-1320 Final Product UI Lock Pack

- status: {STATUS}
- final product UI locked
- user-facing research workbench
- template-inspired only, no copied template code
- no external assets
- no CDN
- developer mode collapsed in settings
- no real market data
- no source connection implemented
- no live market data enabled
- no IBKR connection
- no market data request
- no historical data request
- no account/position read
- no contract qualification
- no trading
- no Telegram real send
- no directional trading signal
- no target, stop, or take-profit levels
- no live price fields
- GLD / SLV only
- JP / CN remain frozen
- generated_at_utc: {timestamp}
"""


def build_user_guide(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    return f"""# Final Product UI User Guide

AI 投研工作台是本地只读研究界面。主导航固定为总览、标的观察、数据源、本地报告、风险边界和设置。

## 可用内容

- GLD / SLV 研究框架
- 行情源状态
- 报告中心
- 只读安全模式说明

## 当前边界

- 当前不会获取实时行情
- 当前不会读取账户
- 当前不会读取持仓
- 当前不会生成交易指令
- 当前不会发送 Telegram
- 当前不会解冻 JP / CN

generated_at_utc: {timestamp}
"""


def generate_final_product_ui_lock_pack(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    status = build_status_snapshot(timestamp)
    row = {field: status.get(field, "") for field in CSV_FIELDS}

    _write_text(DASHBOARD_INDEX, build_dashboard_html(timestamp))
    _write_text(DASHBOARD_CSS, build_dashboard_css())
    _write_json(STATUS_SNAPSHOT, status)
    _write_json(ARTIFACT_MANIFEST, build_artifact_manifest(timestamp))
    _write_json(BUILD_SNAPSHOT, build_build_snapshot(timestamp))
    _write_json(OPERATOR_TIMELINE, build_operator_timeline(timestamp))
    _write_json(FINAL_PRODUCT_UI_LOCK_SNAPSHOT, build_final_product_ui_lock_snapshot(timestamp))
    _write_json(FINAL_NAVIGATION_SNAPSHOT, build_final_navigation_snapshot(timestamp))
    _write_json(FINAL_DASHBOARD_LAYOUT_SNAPSHOT, build_final_dashboard_layout_snapshot(timestamp))
    _write_json(FINAL_VISUAL_SYSTEM_SNAPSHOT, build_final_visual_system_snapshot(timestamp))
    _write_json(FINAL_USER_WORKFLOW_SNAPSHOT, build_final_user_workflow_snapshot(timestamp))
    _write_json(FINAL_UI_REGRESSION_GUARD_SNAPSHOT, build_final_ui_regression_guard_snapshot(timestamp))
    _write_json(FINAL_LANDING_AUDIT_SNAPSHOT, build_final_landing_audit_snapshot(timestamp))

    csv_path = Path(OUTPUT_CSV)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)
    _write_text(OUTPUT_REPORT, build_report(timestamp))
    _write_text(OUTPUT_USER_GUIDE, build_user_guide(timestamp))
    _write_text(OUTPUT_PACK, build_report(timestamp))
    return row


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 1161-1320 final product UI lock pack.")
    parser.parse_args(argv)
    row = generate_final_product_ui_lock_pack()
    print("[FINAL_PRODUCT_UI_LOCK_PACK] generated")
    print(f"phase={row['phase']}")
    print(f"status={row['status']}")
    print(f"ui_generation={row['ui_generation']}")
    print(f"ui_final_locked={row['ui_final_locked']}")
    print(f"product_ui_mode={row['product_ui_mode']}")
    print(f"developer_mode={row['developer_mode']}")
    print(f"csv={OUTPUT_CSV}")
    print(f"report={OUTPUT_REPORT}")
    print(f"pack={OUTPUT_PACK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
