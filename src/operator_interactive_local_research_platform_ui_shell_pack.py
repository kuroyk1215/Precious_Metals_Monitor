from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

from src.operator_post_ui_freeze_handoff_data_roadmap_pack import (
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    EXTERNAL_EFFECT,
    IBKR_ERROR_CODE,
    JP_STATUS,
    MARKET_DATA_CLASSIFICATION,
    MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
    MARKET_DATA_SOURCE_DECISION_STATUS,
    MARKET_DATA_STATUS,
    MARKET_SCOPE_STATUS_SNAPSHOT,
    NEXT_ROADMAP_SNAPSHOT,
    OPERATOR_NEXT_ACTIONS_SNAPSHOT,
    OPERATOR_TIMELINE,
    POST_UI_FREEZE_HANDOFF_SNAPSHOT,
    STATUS_SNAPSHOT,
    build_market_data_source_decision_snapshot as build_previous_market_data_source_decision_snapshot,
    build_market_scope_status_snapshot as build_previous_market_scope_status_snapshot,
    build_next_roadmap_snapshot as build_previous_next_roadmap_snapshot,
    build_operator_next_actions_snapshot as build_previous_operator_next_actions_snapshot,
    build_post_ui_freeze_handoff_snapshot as build_previous_post_ui_freeze_handoff_snapshot,
    ARTIFACTS as HANDOFF_ARTIFACTS,
)


PHASE = "Phase 721-760"
STATUS = "INTERACTIVE_LOCAL_RESEARCH_PLATFORM_UI_SHELL_READY"
INTERACTIVE_UI_STATUS = "INTERACTIVE_UI_SHELL_READY"
UI_GENERATION = "V8_INTERACTIVE_LOCAL_RESEARCH_PLATFORM_SHELL"
PREVIOUS_UI_GENERATION = "V7_HIGH_TECH_TRADING_VISUAL_FROZEN"
UI_INTERACTION_MODE = "LOCAL_INLINE_JS_ONLY"
LATEST_MAIN_COMMIT = "a2d1dcb"
LATEST_MERGED_PR = 226
NO_TEXT = "NO"
YES_TEXT = "YES"
CN_STATUS = "FROZEN_PENDING_DATA_SOURCE_DECISION"
SYMBOLS_TEXT = "GLD / SLV"

DASHBOARD_INDEX = "dashboard/index.html"
DASHBOARD_CSS = "dashboard/assets/style.css"
INTERACTIVE_UI_SHELL_SNAPSHOT = "dashboard/data/interactive_ui_shell_snapshot.json"
UI_INTERACTION_CONTRACT_SNAPSHOT = "dashboard/data/ui_interaction_contract_snapshot.json"
UI_DISABLED_ACTIONS_SNAPSHOT = "dashboard/data/ui_disabled_actions_snapshot.json"
UI_FILTER_TABS_SNAPSHOT = "dashboard/data/ui_filter_tabs_snapshot.json"
LOCAL_PLATFORM_SHELL_STATUS_SNAPSHOT = "dashboard/data/local_platform_shell_status_snapshot.json"
OUTPUT_CSV = "operator_interactive_local_research_platform_ui_shell_pack.csv"
OUTPUT_REPORT = "reports/operator_interactive_local_research_platform_ui_shell_pack_report.md"
OUTPUT_PACK = "Precious_Metals_Monitor_Interactive_Local_Research_Platform_UI_Shell_Pack.md"

NEW_ARTIFACTS = (
    INTERACTIVE_UI_SHELL_SNAPSHOT,
    UI_INTERACTION_CONTRACT_SNAPSHOT,
    UI_DISABLED_ACTIONS_SNAPSHOT,
    UI_FILTER_TABS_SNAPSHOT,
    LOCAL_PLATFORM_SHELL_STATUS_SNAPSHOT,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)
ARTIFACTS = tuple(dict.fromkeys((*HANDOFF_ARTIFACTS, *NEW_ARTIFACTS)))

CSV_FIELDS = (
    "phase",
    "status",
    "interactive_ui_status",
    "ui_generation",
    "previous_ui_generation",
    "ui_interaction_mode",
    "javascript_required",
    "external_js",
    "remote_assets",
    "local_backend_api",
    "backend_server_required",
    "source_connection_implemented",
    "live_market_data_enabled",
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
        "interactive_ui_status": INTERACTIVE_UI_STATUS,
        "ui_generation": UI_GENERATION,
        "previous_ui_generation": PREVIOUS_UI_GENERATION,
        "ui_interaction_mode": UI_INTERACTION_MODE,
        "javascript_required": "LOCAL_INLINE_ONLY",
        "external_js": NO_TEXT,
        "remote_assets": NO_TEXT,
        "local_backend_api": NO_TEXT,
        "backend_server_required": NO_TEXT,
        "source_connection_implemented": NO_TEXT,
        "live_market_data_enabled": NO_TEXT,
        "market_data_status": MARKET_DATA_STATUS,
        "market_data_classification": MARKET_DATA_CLASSIFICATION,
        "ibkr_error_code": IBKR_ERROR_CODE,
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


def build_interactive_ui_shell_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": INTERACTIVE_UI_STATUS,
        "ui_generation": UI_GENERATION,
        "interaction_features": [
            "TABS",
            "LOCAL_SEARCH",
            "LOCAL_FILTERS",
            "COLLAPSIBLE_CARDS",
            "COPY_COMMAND",
            "DISABLED_ACTION_HINTS",
        ],
        "tabs": ["总览", "市场观察", "数据源", "风险边界", "本地文件", "路线图", "系统状态"],
        "local_backend_api": NO_TEXT,
        "external_js": NO_TEXT,
        "remote_assets": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_ui_interaction_contract_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "status": "UI_INTERACTION_CONTRACT_READY",
        "allowed_interactions": [
            "tab_switch",
            "local_search",
            "local_filter",
            "collapse_expand",
            "copy_text",
            "disabled_button_tooltip",
        ],
        "forbidden_interactions": [
            "network_fetch",
            "websocket",
            "ibkr_connect",
            "market_data_request",
            "historical_data_request",
            "account_read",
            "position_read",
            "order_submit",
            "order_cancel",
            "telegram_real_send",
            "file_write_from_browser",
        ],
        "generated_at_utc": timestamp,
    }


def build_ui_disabled_actions_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "status": "UI_DISABLED_ACTIONS_READY",
        "disabled_actions": [
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
        ],
        "all_disabled": YES_TEXT,
        "generated_at_utc": timestamp,
    }


def build_ui_filter_tabs_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "status": "UI_FILTER_TABS_READY",
        "tabs": ["overview", "watchlist", "data-source", "risk", "artifacts", "roadmap", "system"],
        "filters": ["all", "risk-only", "json", "report", "us-only", "frozen-market", "next-actions"],
        "generated_at_utc": timestamp,
    }


def build_local_platform_shell_status_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "status": "LOCAL_PLATFORM_UI_SHELL_READY",
        "platform_mode": "UI_DRIVEN_LOCAL_RESEARCH_WORKBENCH",
        "terminal_role": "STARTUP_AND_FALLBACK_ONLY",
        "primary_user_interaction": "WEB_UI",
        "backend_api_status": "NOT_IMPLEMENTED",
        "next_backend_phase": "LOCAL_BACKEND_API_SHELL",
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
    return {
        "timeline": [
            {
                "phase": "Phase 697-704",
                "theme": "Dashboard UI Static Visual Freeze",
                "status": "DASHBOARD_UI_STATIC_VISUAL_FREEZE_READY",
                "external_effect": EXTERNAL_EFFECT,
            },
            {
                "phase": "Phase 705-720",
                "theme": "Post-UI Freeze Handoff / 数据源路线图",
                "status": "POST_UI_FREEZE_HANDOFF_DATA_ROADMAP_READY",
                "external_effect": EXTERNAL_EFFECT,
            },
            {
                "phase": PHASE,
                "theme": "Interactive Local Research Platform UI Shell",
                "status": STATUS,
                "external_effect": EXTERNAL_EFFECT,
            },
        ],
        "generated_at_utc": timestamp,
    }


def build_next_roadmap_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    snapshot = build_previous_next_roadmap_snapshot(generated_at)
    snapshot.update(
        {
            "phase": PHASE,
            "status": "NEXT_ROADMAP_READY",
            "current_track_completed": "INTERACTIVE_LOCAL_RESEARCH_PLATFORM_UI_SHELL",
            "next_recommended_track": "LOCAL_BACKEND_API_SHELL",
            "recommended_sequence": [
                "Phase 729-736 Local Backend API Shell",
                "Phase 737-744 US GLD / SLV Data Source Adapter Plan",
                "Phase 745-752 Watchlist Expansion Policy Pack",
                "Phase 753-760 Telegram Manual Packet Enhancement Pack",
            ],
        },
    )
    return snapshot


def build_market_data_source_decision_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    snapshot = build_previous_market_data_source_decision_snapshot(generated_at)
    snapshot.update(
        {
            "phase": PHASE,
            "source_connection_implemented": NO_TEXT,
            "live_market_data_enabled": NO_TEXT,
            "ui_selection_panel_status": "DISPLAY_ONLY_NOT_CONNECTED",
        },
    )
    return snapshot


def build_market_scope_status_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    snapshot = build_previous_market_scope_status_snapshot(generated_at)
    snapshot.update({"phase": PHASE, "status": "MARKET_SCOPE_STATUS_UI_SHELL_READY"})
    return snapshot


def build_operator_next_actions_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    snapshot = build_previous_operator_next_actions_snapshot(generated_at)
    snapshot.update(
        {
            "phase": PHASE,
            "status": "OPERATOR_NEXT_ACTIONS_UI_SHELL_READY",
            "immediate_next_actions": [
                "Market Data Source Decision",
                "Review Phase 729-736 Local Backend API Shell entry",
                "Keep all external runtime actions disabled",
                "Use UI for local research shell navigation",
            ],
            "operator_commands": [
                "python3 main.py --interactive-local-research-platform-ui-shell-pack",
                "python3 -m py_compile main.py src/*.py",
                ".venv/bin/python -m pytest -q",
            ],
        },
    )
    return snapshot


def build_post_ui_freeze_handoff_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    snapshot = build_previous_post_ui_freeze_handoff_snapshot(generated_at)
    snapshot.update(
        {
            "phase": PHASE,
            "status": "POST_UI_FREEZE_HANDOFF_CONSUMED_BY_INTERACTIVE_UI_SHELL",
            "latest_main_commit": LATEST_MAIN_COMMIT,
            "latest_merged_pr": LATEST_MERGED_PR,
            "interactive_ui_status": INTERACTIVE_UI_STATUS,
        },
    )
    return snapshot


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


def build_dashboard_html(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    artifact_cards = "\n".join(
        f'              <article class="file-card" data-search="{path} { _artifact_category(path) } NONE_LOCAL_ARTIFACT_GENERATION_ONLY" data-kind="{_artifact_category(path).lower()}"><span class="token mono">{_artifact_category(path)}_LOCAL</span><span class="mono">{path}</span><span>{_artifact_category(path)}</span><a class="local-link mono" href="{_artifact_local_href(path)}">本地链接</a><span class="mono muted">NONE_LOCAL_ARTIFACT_GENERATION_ONLY</span></article>'
        for path in ARTIFACTS
    )
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI 投研交易驾驶舱 · 本地交互式投研平台</title>
    <link rel="stylesheet" href="assets/style.css">
  </head>
  <body>
    <div class="app-shell">
      <aside class="sidebar" aria-label="左侧导航">
        <div class="brand"><span class="brand-mark">AI</span><span class="brand-title">AI 投研交易驾驶舱</span><span class="brand-subtitle">本地交互式投研平台</span></div>
        <nav class="sidebar-nav" aria-label="功能分区">
          <button class="nav-item active" type="button" data-tab-target="overview"><span class="nav-icon">总</span><span>总览</span></button>
          <button class="nav-item" type="button" data-tab-target="watchlist"><span class="nav-icon">观</span><span>市场观察</span></button>
          <button class="nav-item" type="button" data-tab-target="data-source"><span class="nav-icon">源</span><span>数据源</span></button>
          <button class="nav-item" type="button" data-tab-target="risk"><span class="nav-icon">风</span><span>风险边界</span></button>
          <button class="nav-item" type="button" data-tab-target="artifacts"><span class="nav-icon">文</span><span>本地文件</span></button>
          <button class="nav-item" type="button" data-tab-target="roadmap"><span class="nav-icon">路</span><span>路线图</span></button>
          <button class="nav-item" type="button" data-tab-target="system"><span class="nav-icon">系</span><span>系统状态</span></button>
        </nav>
        <div class="sidebar-note">未连接 IBKR · 未请求行情 · 本地 inline JS</div>
      </aside>
      <div class="content">
        <header class="command-bar">
          <div>
            <h1>AI 投研交易驾驶舱 · 本地交互式投研平台</h1>
            <p class="subtitle">UI 驱动的本地 AI 投研平台壳 · 无本地后端 API · 无外部依赖 · 无行情连接</p>
            <div class="badge-row">
              <span class="badge safe">GLD / SLV</span>
              <span class="badge blocked">BLOCKED_BY_SUBSCRIPTION</span>
              <span class="badge blocked">IBKR_ERROR_10089</span>
              <span class="badge safe">LOCAL_INLINE_JS_ONLY</span>
              <span class="badge secondary mono">V8_INTERACTIVE_LOCAL_RESEARCH_PLATFORM_SHELL</span>
            </div>
          </div>
          <section class="build-chip"><span class="label">generated_at_utc</span><strong class="big-copy mono">{timestamp}</strong></section>
        </header>

        <section class="toolbar" aria-label="本地搜索和筛选">
          <label class="search-box"><span>搜索</span><input id="localSearch" type="search" placeholder="搜索 artifact、状态、GLD / SLV、数据源选项"></label>
          <label class="filter-box"><span>筛选</span><select id="localFilter"><option value="all">全部</option><option value="risk-only">仅风险项</option><option value="json">仅 JSON</option><option value="report">仅 REPORT</option><option value="us-only">仅 US</option><option value="frozen-market">仅冻结市场</option><option value="next-actions">仅下一步动作</option></select></label>
        </section>

        <main class="tab-panels">
          <section class="tab-panel active" id="overview" data-panel data-search="总览 INTERACTIVE_LOCAL_RESEARCH_PLATFORM_UI_SHELL_READY V8 GLD SLV Market Data Source Decision" data-kind="overview next-actions us-only">
            <div class="hero-grid">
              <article class="panel"><div class="panel-header"><div><span class="eyebrow">平台模式</span><h2>本地交互式投研平台</h2></div><span class="token safe">READY</span></div><strong class="big-copy">UI_DRIVEN_LOCAL_RESEARCH_WORKBENCH</strong><p class="muted">未来主要在 UI 中操作，终端仅保留启动与兜底角色。</p></article>
              <article class="panel"><div class="panel-header"><div><span class="eyebrow">下一步建议</span><h2>Operator action panel</h2></div><span class="token warn">NEXT</span></div><strong class="big-copy">Market Data Source Decision</strong><p class="muted">Phase 729-736 入口：Local Backend API Shell。当前只展示本地命令提示，不执行外部动作。</p><button class="copy-btn" type="button" data-copy="python3 main.py --interactive-local-research-platform-ui-shell-pack">复制命令</button></article>
              <article class="panel"><div class="panel-header"><div><span class="eyebrow">安全状态</span><h2>外部动作禁用</h2></div><span class="token disabled">LOCKED</span></div><strong class="big-copy">未连接 IBKR</strong><p class="muted">未请求行情 · 未请求历史数据 · 未读取账户/持仓 · 未交易 · 未 Telegram 实发</p></article>
            </div>
          </section>

          <section class="tab-panel" id="watchlist" data-panel data-search="市场观察 GLD SLV JP CN 冻结 US" data-kind="us-only frozen-market">
            <div class="card-header"><h2>市场观察</h2><button class="disabled-action" type="button" disabled title="规划中，本阶段不新增标的">添加标的 · 规划中</button></div>
            <div class="watch-grid">
              <article class="watch-card"><strong class="mono">GLD</strong><span class="token blocked">订阅阻断</span><dl><div><dt>市场</dt><dd>US</dd></div><div><dt>实时行情</dt><dd>NO</dd></div><div><dt>用途</dt><dd>本地研究观察</dd></div></dl></article>
              <article class="watch-card"><strong class="mono">SLV</strong><span class="token blocked">订阅阻断</span><dl><div><dt>市场</dt><dd>US</dd></div><div><dt>实时行情</dt><dd>NO</dd></div><div><dt>用途</dt><dd>本地研究观察</dd></div></dl></article>
              <article class="watch-card frozen"><strong class="mono">JP</strong><span class="token disabled">FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION</span><p class="muted">冻结，等待市场数据订阅。</p></article>
              <article class="watch-card frozen"><strong class="mono">CN</strong><span class="token disabled">FROZEN_PENDING_DATA_SOURCE_DECISION</span><p class="muted">冻结，等待数据源决策。</p></article>
            </div>
          </section>

          <section class="tab-panel" id="data-source" data-panel data-search="数据源 IBKR Network B ARCA 免费延迟公开源 手动 CSV 付费 API Hybrid Router GLD SLV" data-kind="next-actions us-only">
            <div class="card-header"><h2>数据源选择面板</h2><span class="token disabled">未接入</span></div>
            <div class="source-grid">
              <article class="collapsible source-card"><button class="collapse-toggle" type="button">IBKR Network B / ARCA <span>折叠</span></button><div class="collapse-body"><p>成本：订阅费用 · 可靠性：高 · 条款风险：低 · 更新频率：实时权限后可用 · 覆盖范围：US ETF · 适合 GLD / SLV：YES · 当前状态：未接入</p></div></article>
              <article class="collapsible source-card"><button class="collapse-toggle" type="button">免费延迟公开源 <span>折叠</span></button><div class="collapse-body"><p>成本：低 · 可靠性：中 · 条款风险：中 · 更新频率：延迟 · 覆盖范围：视来源 · 适合 GLD / SLV：待验证 · 当前状态：未接入</p></div></article>
              <article class="collapsible source-card"><button class="collapse-toggle" type="button">手动 CSV <span>折叠</span></button><div class="collapse-body"><p>成本：低 · 可靠性：取决于输入 · 条款风险：低 · 更新频率：手动 · 覆盖范围：GLD / SLV 优先 · 适合 GLD / SLV：YES · 当前状态：未接入</p></div></article>
              <article class="collapsible source-card"><button class="collapse-toggle" type="button">付费 API <span>折叠</span></button><div class="collapse-body"><p>成本：中到高 · 可靠性：中到高 · 条款风险：按合同 · 更新频率：按套餐 · 覆盖范围：可扩展 · 适合 GLD / SLV：YES · 当前状态：未接入</p></div></article>
              <article class="collapsible source-card"><button class="collapse-toggle" type="button">Hybrid Router <span>折叠</span></button><div class="collapse-body"><p>成本：组合 · 可靠性：路由增强 · 条款风险：需治理 · 更新频率：按来源 · 覆盖范围：可扩展 · 适合 GLD / SLV：YES · 当前状态：未接入</p></div></article>
            </div>
          </section>

          <section class="tab-panel" id="risk" data-panel data-search="风险边界 disabled IBKR 请求行情 历史数据 账户 持仓 下单 Telegram" data-kind="risk-only">
            <article class="collapsible card"><button class="collapse-toggle" type="button">风险权限矩阵 <span>折叠</span></button><div class="collapse-body risk-list">
              <button class="disabled-action" type="button" disabled title="本阶段禁止连接 IBKR">连接 IBKR</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止请求行情">请求行情</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止请求历史数据">请求历史数据</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止读取账户">读取账户</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止读取持仓">读取持仓</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止下单">下单</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止 Telegram 实发">Telegram 实发</button>
            </div></article>
          </section>

          <section class="tab-panel" id="artifacts" data-panel data-search="本地文件 artifact JSON REPORT CSV PACK" data-kind="json report">
            <article class="collapsible card"><button class="collapse-toggle" type="button">artifact 文件流 <span>折叠</span></button><div class="collapse-body file-stream">
{artifact_cards}
            </div></article>
          </section>

          <section class="tab-panel" id="roadmap" data-panel data-search="路线图 operator roadmap Phase 729 736 Local Backend API Shell 下一步动作" data-kind="next-actions">
            <article class="collapsible card"><button class="collapse-toggle" type="button">operator roadmap <span>折叠</span></button><div class="collapse-body phase-rail">
              <article class="phase-card"><strong>Phase 721-760</strong><p>Interactive Local Research Platform UI Shell</p><span class="token safe">READY</span></article>
              <article class="phase-card"><strong>Phase 729-736</strong><p>Local Backend API Shell</p><span class="token warn">NEXT</span></article>
              <article class="phase-card"><strong>Market Data Source Decision</strong><p>选择 GLD / SLV 数据源，不连接当前页面。</p><span class="token blocked">BLOCKED</span></article>
            </div></article>
          </section>

          <section class="tab-panel" id="system" data-panel data-search="系统状态 javascript_required LOCAL_INLINE_ONLY external_js NO remote_assets NO backend API NO" data-kind="risk-only next-actions">
            <article class="collapsible card"><button class="collapse-toggle" type="button">market scope status <span>折叠</span></button><div class="collapse-body version-table">
              <div class="version-row"><span>status</span><strong class="mono">{STATUS}</strong></div>
              <div class="version-row"><span>javascript_required</span><strong class="mono">LOCAL_INLINE_ONLY</strong></div>
              <div class="version-row"><span>external_js</span><strong class="mono">NO</strong></div>
              <div class="version-row"><span>remote_assets</span><strong class="mono">NO</strong></div>
              <div class="version-row"><span>local_backend_api</span><strong class="mono">NO</strong></div>
              <div class="version-row"><span>source_connection_implemented</span><strong class="mono">NO</strong></div>
              <div class="version-row"><span>live_market_data_enabled</span><strong class="mono">NO</strong></div>
            </div></article>
          </section>
        </main>
      </div>
    </div>
    <footer class="footer-safety-bar">未连接 IBKR · 未请求行情 · 未请求历史数据 · 未读取账户/持仓 · 未交易 · 未 Telegram 实发</footer>
    <script>
      (function () {{
        var tabs = document.querySelectorAll("[data-tab-target]");
        var panels = document.querySelectorAll("[data-panel]");
        var search = document.getElementById("localSearch");
        var filter = document.getElementById("localFilter");
        function showPanel(id) {{
          tabs.forEach(function (tab) {{ tab.classList.toggle("active", tab.getAttribute("data-tab-target") === id); }});
          panels.forEach(function (panel) {{ panel.classList.toggle("active", panel.id === id); }});
        }}
        function applyLocalFilter() {{
          var query = (search.value || "").toLowerCase();
          var mode = filter.value;
          panels.forEach(function (panel) {{
            var text = (panel.getAttribute("data-search") || panel.textContent).toLowerCase();
            var kind = panel.getAttribute("data-kind") || "";
            var matchText = !query || text.indexOf(query) >= 0;
            var matchKind = mode === "all" || kind.indexOf(mode) >= 0 || text.indexOf(mode) >= 0;
            panel.classList.toggle("filtered-out", !(matchText && matchKind));
          }});
        }}
        tabs.forEach(function (tab) {{
          tab.addEventListener("click", function () {{ showPanel(tab.getAttribute("data-tab-target")); }});
        }});
        document.querySelectorAll(".collapse-toggle").forEach(function (button) {{
          button.addEventListener("click", function () {{
            var card = button.closest(".collapsible");
            card.classList.toggle("collapsed");
            button.querySelector("span").textContent = card.classList.contains("collapsed") ? "展开" : "折叠";
          }});
        }});
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
        search.addEventListener("input", applyLocalFilter);
        filter.addEventListener("change", applyLocalFilter);
      }})();
    </script>
  </body>
</html>
"""


def build_dashboard_css() -> str:
    return """:root {
  color-scheme: dark;
  --bg: #070a10;
  --panel: rgba(14, 21, 31, 0.95);
  --panel-2: rgba(23, 33, 45, 0.92);
  --line: rgba(114, 204, 190, 0.24);
  --line-strong: rgba(148, 163, 184, 0.36);
  --text: #edf3f8;
  --muted: #95a3b3;
  --green: #38d39f;
  --blue: #7bb8ff;
  --amber: #e5ad45;
  --red: #ff7f82;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  background:
    linear-gradient(rgba(114, 204, 190, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(123, 184, 255, 0.06) 1px, transparent 1px),
    var(--bg);
  background-size: 30px 30px, 30px 30px, auto;
  color: var(--text);
  font-family: Arial, Helvetica, sans-serif;
  font-size: 13px;
  line-height: 1.5;
}
a { color: inherit; text-decoration: none; }
button, input, select { font: inherit; }
.mono { font-family: Consolas, Monaco, monospace; }
.app-shell { display: grid; grid-template-columns: 244px minmax(0, 1fr); min-height: 100vh; }
.sidebar { border-right: 1px solid var(--line); background: rgba(7, 10, 16, 0.96); height: 100vh; padding: 18px 14px; position: sticky; top: 0; }
.brand { border: 1px solid var(--line); border-radius: 8px; padding: 12px; margin-bottom: 16px; }
.brand-mark, .nav-icon { align-items: center; border: 1px solid var(--line-strong); border-radius: 7px; color: var(--green); display: inline-flex; font-weight: 800; height: 30px; justify-content: center; margin-right: 8px; width: 30px; }
.brand-title { display: block; font-size: 14px; font-weight: 800; }
.brand-subtitle, .label, .eyebrow { color: var(--muted); font-size: 11px; font-weight: 700; }
.sidebar-nav { display: grid; gap: 7px; }
.nav-item { align-items: center; background: transparent; border: 1px solid transparent; border-radius: 8px; color: #bdcad7; cursor: pointer; display: flex; min-height: 40px; padding: 5px 8px; text-align: left; }
.nav-item.active, .nav-item:hover { background: rgba(56, 211, 159, 0.1); border-color: var(--line); color: #fff; }
.sidebar-note { border: 1px solid rgba(229, 173, 69, 0.35); border-radius: 8px; color: var(--amber); margin-top: 18px; padding: 10px; }
.content { min-width: 0; padding: 18px 22px 72px; }
.command-bar, .toolbar, .panel, .card, .watch-card, .source-card, .file-card, .phase-card {
  background: linear-gradient(180deg, var(--panel), rgba(8, 12, 19, 0.96));
  border: 1px solid var(--line);
  border-radius: 8px;
  min-width: 0;
}
.command-bar { align-items: start; display: grid; gap: 16px; grid-template-columns: minmax(0, 1fr) auto; padding: 16px; }
h1 { font-size: 25px; line-height: 1.15; margin: 0; }
h2 { font-size: 15px; margin: 0; }
.subtitle, .muted { color: var(--muted); }
.badge-row { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 12px; }
.badge, .token { border: 1px solid var(--line); border-radius: 999px; display: inline-flex; font-size: 11px; font-weight: 800; min-height: 24px; padding: 3px 9px; }
.safe { border-color: rgba(56, 211, 159, 0.42); color: var(--green); }
.warn { border-color: rgba(229, 173, 69, 0.48); color: var(--amber); }
.blocked, .disabled { border-color: rgba(255, 127, 130, 0.48); color: var(--red); }
.secondary { color: var(--muted); font-size: 9px; opacity: 0.9; }
.build-chip { border: 1px solid var(--line); border-radius: 8px; min-width: 260px; padding: 10px 12px; }
.big-copy { display: block; font-size: 18px; font-weight: 800; margin-top: 12px; overflow-wrap: anywhere; }
.toolbar { align-items: end; display: grid; gap: 12px; grid-template-columns: minmax(240px, 1fr) 220px; margin: 14px 0; padding: 12px; }
.search-box, .filter-box { display: grid; gap: 6px; }
input, select { background: rgba(23, 33, 45, 0.92); border: 1px solid var(--line-strong); border-radius: 8px; color: var(--text); min-height: 38px; padding: 8px 10px; }
.tab-panel { display: none; }
.tab-panel.active { display: block; }
.tab-panel.filtered-out { opacity: 0.26; }
.hero-grid { display: grid; gap: 12px; grid-template-columns: repeat(3, minmax(0, 1fr)); }
.panel, .card { padding: 14px; }
.panel-header, .card-header { align-items: center; border-bottom: 1px solid rgba(149, 163, 179, 0.16); display: flex; gap: 12px; justify-content: space-between; margin-bottom: 10px; padding-bottom: 8px; }
.copy-btn, .disabled-action, .collapse-toggle { border-radius: 8px; min-height: 36px; padding: 8px 10px; }
.copy-btn, .collapse-toggle { background: rgba(56, 211, 159, 0.12); border: 1px solid rgba(56, 211, 159, 0.36); color: var(--text); cursor: pointer; }
.disabled-action { background: rgba(255, 127, 130, 0.08); border: 1px solid rgba(255, 127, 130, 0.32); color: var(--red); cursor: not-allowed; }
.watch-grid, .source-grid, .file-stream, .phase-rail, .risk-list { display: grid; gap: 10px; }
.watch-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.watch-card, .source-card, .file-card, .phase-card { padding: 12px; }
.watch-card dl, .version-table { display: grid; gap: 6px; margin: 10px 0 0; }
.watch-card div, .version-row { display: flex; gap: 10px; justify-content: space-between; }
.frozen { opacity: 0.78; }
.source-grid { grid-template-columns: repeat(5, minmax(160px, 1fr)); }
.collapse-toggle { align-items: center; display: flex; justify-content: space-between; width: 100%; }
.collapse-body { margin-top: 10px; }
.collapsed .collapse-body { display: none; }
.risk-list { grid-template-columns: repeat(4, minmax(160px, 1fr)); }
.file-card { align-items: center; display: grid; gap: 8px; grid-template-columns: 120px minmax(0, 1fr) 90px 150px minmax(160px, 240px); }
.local-link { color: var(--green); overflow-wrap: anywhere; }
.phase-rail { grid-template-columns: repeat(3, minmax(180px, 1fr)); }
.footer-safety-bar { background: rgba(7, 10, 16, 0.96); border-top: 1px solid var(--line); bottom: 0; color: var(--muted); font-weight: 800; left: 244px; padding: 11px 22px; position: fixed; right: 0; }
@media (max-width: 1180px) {
  .app-shell { grid-template-columns: 1fr; }
  .sidebar { height: auto; position: relative; }
  .sidebar-nav { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .command-bar, .hero-grid, .source-grid { grid-template-columns: 1fr; }
  .footer-safety-bar { left: 0; }
}
@media (max-width: 760px) {
  .content { padding: 14px 12px 92px; }
  .toolbar, .watch-grid, .risk-list, .file-card, .phase-rail { grid-template-columns: 1fr; }
}
"""


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
        "# Phase 721-760 Interactive Local Research Platform UI Shell Pack Report",
        "",
        "## Status",
        "",
        *[f"- {field}={row[field]}" for field in CSV_FIELDS],
        "",
        "## Boundary",
        "",
        "- V8 interactive local research platform UI shell",
        "- UI-driven local research workbench",
        "- local tabs/search/filter/collapse/copy interactions",
        "- local inline JS only",
        "- no external JS",
        "- no external URL/CDN",
        "- no backend API implemented",
        "- no source connection implemented",
        "- no live market data enabled",
        "- no IBKR connection",
        "- no market data request",
        "- no historical data request",
        "- no account/position read",
        "- no contract qualification",
        "- no trading",
        "- no Telegram real send",
        "- no directional signal",
        "- no target/stop/take-profit",
        "- no live price fields",
        "- market data remains BLOCKED_BY_SUBSCRIPTION / IBKR_ERROR_10089",
        "- GLD / SLV only",
        "- JP / CN remain frozen",
        "- next recommended track: Local Backend API Shell",
    ]
    return "\n".join(lines) + "\n"


def build_pack(row: Dict[str, str]) -> str:
    lines = [
        "# Precious Metals Monitor Interactive Local Research Platform UI Shell Pack",
        "",
        f"- phase={row['phase']}",
        f"- status={row['status']}",
        f"- interactive_ui_status={row['interactive_ui_status']}",
        f"- ui_generation={row['ui_generation']}",
        "- local inline JS only",
        "- no remote assets",
        "- no backend API implemented",
        "- no source connection implemented",
        f"- market data remains {row['market_data_status']} / IBKR_ERROR_{row['ibkr_error_code']}",
        "- GLD / SLV only",
        "- JP / CN remain frozen",
    ]
    return "\n".join(lines) + "\n"


def generate_interactive_local_research_platform_ui_shell_pack(
    *,
    output_dashboard_index: PathLike = DASHBOARD_INDEX,
    output_dashboard_css: PathLike = DASHBOARD_CSS,
    output_status_snapshot: PathLike = STATUS_SNAPSHOT,
    output_interactive_ui_shell_snapshot: PathLike = INTERACTIVE_UI_SHELL_SNAPSHOT,
    output_ui_interaction_contract_snapshot: PathLike = UI_INTERACTION_CONTRACT_SNAPSHOT,
    output_ui_disabled_actions_snapshot: PathLike = UI_DISABLED_ACTIONS_SNAPSHOT,
    output_ui_filter_tabs_snapshot: PathLike = UI_FILTER_TABS_SNAPSHOT,
    output_local_platform_shell_status_snapshot: PathLike = LOCAL_PLATFORM_SHELL_STATUS_SNAPSHOT,
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

    _write_text(output_dashboard_index, build_dashboard_html(timestamp))
    _write_text(output_dashboard_css, build_dashboard_css())
    _write_json(output_status_snapshot, status)
    _write_json(output_interactive_ui_shell_snapshot, build_interactive_ui_shell_snapshot(timestamp))
    _write_json(output_ui_interaction_contract_snapshot, build_ui_interaction_contract_snapshot(timestamp))
    _write_json(output_ui_disabled_actions_snapshot, build_ui_disabled_actions_snapshot(timestamp))
    _write_json(output_ui_filter_tabs_snapshot, build_ui_filter_tabs_snapshot(timestamp))
    _write_json(output_local_platform_shell_status_snapshot, build_local_platform_shell_status_snapshot(timestamp))
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
    parser = argparse.ArgumentParser(description="Build Phase 721-760 interactive local research platform UI shell pack.")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_interactive_local_research_platform_ui_shell_pack(generated_at=args.generated_at)
    print("[INTERACTIVE_LOCAL_RESEARCH_PLATFORM_UI_SHELL_PACK] generated")
    print(f"status={row['status']}")
    print(f"interactive_ui_status={row['interactive_ui_status']}")
    print(f"ui_generation={row['ui_generation']}")
    print(f"ui_interaction_mode={row['ui_interaction_mode']}")
    print(f"javascript_required={row['javascript_required']}")
    print(f"external_js={row['external_js']}")
    print(f"remote_assets={row['remote_assets']}")
    print(f"local_backend_api={row['local_backend_api']}")
    print(f"source_connection_implemented={row['source_connection_implemented']}")
    print(f"live_market_data_enabled={row['live_market_data_enabled']}")
    print(f"market_data_status={row['market_data_status']}")
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
