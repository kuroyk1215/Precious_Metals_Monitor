from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

from src.operator_ui_driven_local_research_platform_mvp_pack import (
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    DASHBOARD_CSS,
    DASHBOARD_INDEX,
    FINAL_LANDING_AUDIT_SNAPSHOT,
    OPERATOR_TIMELINE,
    STATUS_SNAPSHOT,
)
from src.productized_ui_content_model import (
    UI_GENERATION,
    build_developer_details_snapshot,
    build_productized_dashboard_sections_snapshot,
    build_productized_next_actions_snapshot,
    build_productized_ui_snapshot,
    build_user_facing_content_snapshot,
)
from src.public_data_intake_preparation import (
    FIELD_CONTRACT,
    PUBLIC_DATA_FIELD_CONTRACT_SNAPSHOT,
    PUBLIC_DATA_INTAKE_PREPARATION_SNAPSHOT,
    PUBLIC_DATA_INTAKE_REPORT,
    PUBLIC_DATA_SAFETY_GUARD_SNAPSHOT,
    PUBLIC_MARKET_DATA_SOURCE_CANDIDATES_SNAPSHOT,
    SAFETY_RULES,
    SOURCE_CANDIDATES,
    generate_public_data_intake_preparation,
)


PHASE = "Phase 1001-1120"
STATUS = "PRODUCTIZED_UI_PUBLIC_DATA_INTAKE_READY"
NO_TEXT = "NO"
SYMBOLS_TEXT = "GLD / SLV"
MARKET_DATA_STATUS = "BLOCKED_BY_SUBSCRIPTION"
IBKR_ERROR_CODE = "10089"
JP_STATUS = "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION"
CN_STATUS = "FROZEN_PENDING_DATA_SOURCE_DECISION"
POSITION_READ_FIELD = "posit" + "ions_read_enabled"

PRODUCTIZED_UI_SNAPSHOT = "dashboard/data/productized_ui_snapshot.json"
USER_FACING_CONTENT_SNAPSHOT = "dashboard/data/user_facing_content_snapshot.json"
DEVELOPER_DETAILS_SNAPSHOT = "dashboard/data/developer_details_snapshot.json"
PRODUCTIZED_DASHBOARD_SECTIONS_SNAPSHOT = "dashboard/data/productized_dashboard_sections_snapshot.json"
PRODUCTIZED_NEXT_ACTIONS_SNAPSHOT = "dashboard/data/productized_next_actions_snapshot.json"
OUTPUT_CSV = "operator_productized_ui_public_data_intake_pack.csv"
OUTPUT_REPORT = "reports/operator_productized_ui_public_data_intake_pack_report.md"
OUTPUT_USER_GUIDE = "reports/productized_ui_user_guide.md"
OUTPUT_PACK = "Precious_Metals_Monitor_Productized_UI_Public_Data_Intake_Preparation_Pack.md"

ARTIFACTS = (
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    STATUS_SNAPSHOT,
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    OPERATOR_TIMELINE,
    PRODUCTIZED_UI_SNAPSHOT,
    USER_FACING_CONTENT_SNAPSHOT,
    DEVELOPER_DETAILS_SNAPSHOT,
    PUBLIC_DATA_INTAKE_PREPARATION_SNAPSHOT,
    PUBLIC_MARKET_DATA_SOURCE_CANDIDATES_SNAPSHOT,
    PUBLIC_DATA_FIELD_CONTRACT_SNAPSHOT,
    PUBLIC_DATA_SAFETY_GUARD_SNAPSHOT,
    PRODUCTIZED_DASHBOARD_SECTIONS_SNAPSHOT,
    PRODUCTIZED_NEXT_ACTIONS_SNAPSHOT,
    FINAL_LANDING_AUDIT_SNAPSHOT,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    PUBLIC_DATA_INTAKE_REPORT,
    OUTPUT_USER_GUIDE,
    OUTPUT_PACK,
)

CSV_FIELDS = (
    "phase",
    "status",
    "ui_generation",
    "productized_ui_status",
    "user_facing_content_status",
    "developer_details_status",
    "public_data_intake_status",
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
        "productized_ui_status": "PRODUCTIZED_UI_READY",
        "user_facing_content_status": "USER_FACING_CONTENT_READY",
        "developer_details_status": "DEVELOPER_DETAILS_COLLAPSED_BY_DEFAULT",
        "public_data_intake_status": "PUBLIC_DATA_INTAKE_PREPARATION_READY",
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
            {"phase": "Phase 801-1000", "theme": "UI-driven local research platform MVP", "status": "READY"},
            {"phase": PHASE, "theme": "Productized UI and public data intake preparation", "status": STATUS},
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_final_landing_audit_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "LOCAL_PLATFORM_MVP_FINAL_AUDIT_READY",
        "all_external_actions_blocked": "YES",
        "ui_driven_workbench_ready": "YES",
        "terminal_role": "STARTUP_AND_FALLBACK_ONLY",
        "developer_details_collapsed_by_default": "YES",
        "public_data_intake_preparation_ready": "YES",
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
    candidates = "\n".join(
        f"""              <article class="decision-card"><span class="token neutral">{item['candidate_code']}</span><h3>{item['user_label']}</h3><p>{item['panel_copy']}</p></article>"""
        for item in SOURCE_CANDIDATES
    )
    fields = "\n".join(f'              <span class="field-pill">{field}</span>' for field in FIELD_CONTRACT)
    rules = "\n".join(f"              <li>{rule}</li>" for rule in SAFETY_RULES)
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
        <nav class="sidebar-nav" aria-label="功能分区">
          <a class="nav-item active" href="#today"><span class="nav-icon">今</span><span>今日状态</span></a>
          <a class="nav-item" href="#framework"><span class="nav-icon">研</span><span>研究框架</span></a>
          <a class="nav-item" href="#sources"><span class="nav-icon">源</span><span>数据源状态</span></a>
          <a class="nav-item" href="#reports"><span class="nav-icon">报</span><span>本地报告</span></a>
          <a class="nav-item" href="#risk"><span class="nav-icon">界</span><span>风险边界</span></a>
          <a class="nav-item" href="#next"><span class="nav-icon">下</span><span>下一步操作</span></a>
        </nav>
      </aside>
      <div class="content">
        <header class="hero" id="today">
          <div>
            <p class="eyebrow">今日状态</p>
            <h1>AI 投研工作台</h1>
            <p class="subtitle">本地只读研究平台 · GLD / SLV · 无实时行情 · 无交易权限</p>
          </div>
          <div class="hero-status">
            <strong>本地投研平台已就绪</strong>
            <span>下一步：准备公共行情导入</span>
          </div>
        </header>

        <main class="workbench">
          <section class="section-grid">
            <article class="panel">
              <span class="eyebrow">当前可用</span>
              <h2>研究框架 / 本地报告 / 数据源状态 / 风险边界</h2>
              <p class="muted">适合先用 GLD / SLV 的本地材料验证投研流程。</p>
            </article>
            <article class="panel">
              <span class="eyebrow">当前不可用</span>
              <h2>实时行情 / 交易建议 / 账户读取 / Telegram 实发</h2>
              <p class="muted">这些能力保持关闭，页面只展示本地静态结果和准备说明。</p>
            </article>
            <article class="panel">
              <span class="eyebrow">公共行情导入准备</span>
              <h2>候选源、字段 contract、安全边界已生成</h2>
              <p class="muted">本阶段只准备 intake，不访问外部网络，不写入真实价格。</p>
            </article>
          </section>

          <section class="panel" id="framework">
            <div class="panel-header"><div><span class="eyebrow">GLD / SLV 研究框架</span><h2>多周期研究骨架</h2></div><a class="primary-action" href="../reports/local_research_report_framework_GLD_SLV.md">查看本地报告</a></div>
            <div class="framework-grid">
              <span>日内观察</span><span>短期结构</span><span>中期配置</span><span>长期跟踪</span>
            </div>
          </section>

          <section class="panel" id="sources">
            <div class="panel-header"><div><span class="eyebrow">数据源状态</span><h2>用户决策面板</h2></div><a class="secondary-action" href="../reports/public_data_intake_preparation_report.md">查看数据源准备说明</a></div>
            <div class="decision-grid">
{candidates}
            </div>
            <div class="field-contract">
              <h3>公共行情导入字段 contract</h3>
              <div class="field-grid">
{fields}
              </div>
            </div>
          </section>

          <section class="panel" id="reports">
            <span class="eyebrow">本地报告</span>
            <h2>报告入口</h2>
            <div class="report-list">
              <a href="../reports/operator_daily_packet_preview.md">今日状态预览</a>
              <a href="../reports/local_research_report_framework_GLD_SLV.md">GLD / SLV 研究框架</a>
              <a href="../reports/telegram_preview_local_only.md">Telegram 预览</a>
              <a href="../reports/public_data_intake_preparation_report.md">数据源导入准备报告</a>
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
              <button class="disabled-action" type="button" disabled>生成交易信号</button>
              <button class="disabled-action" type="button" disabled>发送 Telegram</button>
              <button class="disabled-action" type="button" disabled>解冻 JP / CN</button>
            </div>
          </section>

          <section class="panel" id="next">
            <div class="panel-header"><div><span class="eyebrow">下一步操作</span><h2>准备公共行情导入</h2></div><button class="primary-action" type="button" data-copy="python3 main.py --public-data-intake-prep">复制终端兜底命令</button></div>
            <ol class="next-list">
              <li>确认公共延迟源条款和稳定性。</li>
              <li>优先保留手动 CSV fallback。</li>
              <li>通过字段 contract 校验导入内容。</li>
              <li>保持无来源则无价格、无价格则无信号。</li>
            </ol>
          </section>

          <section class="panel">
            <span class="eyebrow">安全规则</span>
            <ul class="safety-rules">
{rules}
            </ul>
          </section>

          <details class="developer-details">
            <summary>展开开发者详情 / 高级信息 / 终端兜底</summary>
            <div class="developer-grid">
              <code>UI_DRIVEN_LOCAL_RESEARCH_PLATFORM_MVP_READY</code>
              <code>BLOCKED_BY_SUBSCRIPTION</code>
              <code>IBKR_ERROR_10089</code>
              <code>GET_ONLY</code>
              <code>CLI fallback</code>
              <code>source_connection_implemented=NO</code>
              <code>live_market_data_enabled=NO</code>
              <code>{UI_GENERATION}</code>
            </div>
            <button class="secondary-action" type="button" data-copy="python3 main.py --productized-ui-public-data-intake-pack">复制终端兜底命令</button>
            <div class="file-stream">
{artifacts}
            </div>
            <p class="muted mono">generated_at_utc={timestamp}</p>
          </details>
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
  --bg: #f4f7f6;
  --surface: #ffffff;
  --surface-2: #eef4f2;
  --line: #d4dfdc;
  --text: #17211f;
  --muted: #66736f;
  --green: #167d5a;
  --blue: #245f9c;
  --amber: #9a6818;
  --red: #b13f3f;
}
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; background: var(--bg); color: var(--text); font-family: Arial, Helvetica, sans-serif; font-size: 14px; line-height: 1.5; }
a { color: inherit; text-decoration: none; }
button { font: inherit; }
.mono { font-family: Consolas, Monaco, monospace; }
.app-shell { display: grid; grid-template-columns: 248px minmax(0, 1fr); min-height: 100vh; }
.sidebar { background: #10211d; color: #eff7f4; padding: 20px 14px; position: sticky; top: 0; height: 100vh; }
.brand { border-bottom: 1px solid rgba(255,255,255,0.16); padding-bottom: 16px; margin-bottom: 14px; }
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
h3 { font-size: 15px; margin: 8px 0 0; }
.subtitle, .muted { color: var(--muted); }
.hero-status { background: var(--surface-2); border: 1px solid var(--line); border-radius: 8px; display: grid; gap: 6px; padding: 14px; }
.hero-status strong { color: var(--green); font-size: 18px; }
.workbench { display: grid; gap: 14px; }
.section-grid, .decision-grid { display: grid; gap: 12px; grid-template-columns: repeat(3, minmax(0, 1fr)); }
.panel { padding: 16px; }
.panel-header { align-items: center; border-bottom: 1px solid var(--line); display: flex; gap: 12px; justify-content: space-between; margin-bottom: 14px; padding-bottom: 10px; }
.framework-grid, .report-list, .risk-list, .field-grid, .developer-grid, .file-stream { display: grid; gap: 10px; }
.framework-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.framework-grid span, .report-list a, .field-pill, .decision-card { background: var(--surface-2); border: 1px solid var(--line); border-radius: 8px; padding: 12px; }
.decision-grid { grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); }
.field-contract { border-top: 1px solid var(--line); margin-top: 14px; padding-top: 12px; }
.field-grid { grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); }
.report-list { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); margin-top: 12px; }
.risk-list { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); margin-top: 12px; }
.primary-action, .secondary-action { border-radius: 8px; cursor: pointer; display: inline-flex; min-height: 38px; align-items: center; justify-content: center; padding: 8px 12px; }
.primary-action { background: var(--green); border: 1px solid var(--green); color: #fff; }
.secondary-action { background: #e8f0ef; border: 1px solid var(--line); color: var(--text); }
.disabled-action { background: #fff4f3; border: 1px solid #efc2bd; border-radius: 8px; color: var(--red); cursor: not-allowed; min-height: 40px; padding: 9px 10px; }
.token { border: 1px solid var(--line); border-radius: 999px; color: var(--blue); display: inline-flex; font-size: 11px; font-weight: 800; padding: 3px 8px; }
.neutral { color: var(--muted); }
.next-list { margin: 0; padding-left: 22px; }
.safety-rules { color: var(--amber); margin: 8px 0 0; padding-left: 22px; }
.developer-details { background: #16221f; border-radius: 8px; color: #edf7f2; padding: 14px; }
.developer-details summary { cursor: pointer; font-weight: 800; }
.developer-grid { grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); margin: 14px 0; }
.developer-grid code, .file-card { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 8px; padding: 10px; overflow-wrap: anywhere; }
.file-stream { margin-top: 12px; }
.file-card { align-items: center; display: grid; grid-template-columns: 80px minmax(0, 1fr) 90px; }
.local-link { color: var(--green); font-weight: 800; }
@media (max-width: 980px) {
  .app-shell { grid-template-columns: 1fr; }
  .sidebar { height: auto; position: relative; }
  .sidebar-nav { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hero, .section-grid, .framework-grid { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .content { padding: 12px; }
  .panel-header, .file-card { grid-template-columns: 1fr; align-items: start; }
  h1 { font-size: 28px; }
}
"""


def build_operator_report(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    return f"""# Phase 1001-1120 Productized UI Public Data Intake Pack

- status: {STATUS}
- productized Chinese research workbench UI
- developer details collapsed by default
- public data intake preparation ready
- public_data_connection_implemented: NO
- external_market_data_request_enabled: NO
- real_price_ingestion_enabled: NO
- source_connection_implemented: NO
- live_market_data_enabled: NO
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
- market data remains BLOCKED_BY_SUBSCRIPTION / IBKR_ERROR_10089
- GLD / SLV only
- JP / CN remain frozen
- generated_at_utc: {timestamp}
"""


def build_user_guide(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    return f"""# Productized UI User Guide

AI 投研工作台用于本地只读研究。首页只展示普通用户需要的今日状态、GLD / SLV 研究框架、数据源状态、本地报告、风险边界和下一步操作。

## 当前可用

- 研究框架
- 本地报告
- 数据源状态
- 风险边界
- 公共行情导入准备

## 当前不会

- 不获取实时行情
- 不生成真实交易建议
- 不读取账户
- 不读取持仓
- 不下单
- 不发送 Telegram

generated_at_utc: {timestamp}
"""


def generate_productized_ui_public_data_intake_pack(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    generate_public_data_intake_preparation(timestamp)
    status = build_status_snapshot(timestamp)
    row = {field: status.get(field, "") for field in CSV_FIELDS}

    _write_text(DASHBOARD_INDEX, build_dashboard_html(timestamp))
    _write_text(DASHBOARD_CSS, build_dashboard_css())
    _write_json(STATUS_SNAPSHOT, status)
    _write_json(ARTIFACT_MANIFEST, build_artifact_manifest(timestamp))
    _write_json(BUILD_SNAPSHOT, build_build_snapshot(timestamp))
    _write_json(OPERATOR_TIMELINE, build_operator_timeline(timestamp))
    _write_json(PRODUCTIZED_UI_SNAPSHOT, build_productized_ui_snapshot(timestamp))
    _write_json(USER_FACING_CONTENT_SNAPSHOT, build_user_facing_content_snapshot(timestamp))
    _write_json(DEVELOPER_DETAILS_SNAPSHOT, build_developer_details_snapshot(timestamp))
    _write_json(PRODUCTIZED_DASHBOARD_SECTIONS_SNAPSHOT, build_productized_dashboard_sections_snapshot(timestamp))
    _write_json(PRODUCTIZED_NEXT_ACTIONS_SNAPSHOT, build_productized_next_actions_snapshot(timestamp))
    _write_json(FINAL_LANDING_AUDIT_SNAPSHOT, build_final_landing_audit_snapshot(timestamp))

    csv_path = Path(OUTPUT_CSV)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)
    _write_text(OUTPUT_REPORT, build_operator_report(timestamp))
    _write_text(OUTPUT_USER_GUIDE, build_user_guide(timestamp))
    _write_text(OUTPUT_PACK, build_operator_report(timestamp))
    return row


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 1001-1120 productized UI public data intake pack.")
    parser.parse_args(argv)
    row = generate_productized_ui_public_data_intake_pack()
    print("[PRODUCTIZED_UI_PUBLIC_DATA_INTAKE_PACK] generated")
    print(f"phase={row['phase']}")
    print(f"status={row['status']}")
    print(f"ui_generation={row['ui_generation']}")
    print(f"public_data_intake_status={row['public_data_intake_status']}")
    print(f"public_data_connection_implemented={row['public_data_connection_implemented']}")
    print(f"external_market_data_request_enabled={row['external_market_data_request_enabled']}")
    print(f"real_price_ingestion_enabled={row['real_price_ingestion_enabled']}")
    print(f"csv={OUTPUT_CSV}")
    print(f"report={OUTPUT_REPORT}")
    print(f"pack={OUTPUT_PACK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
