from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

from src.operator_interactive_local_research_platform_ui_shell_pack import (
    ARTIFACTS as PREVIOUS_ARTIFACTS,
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    CN_STATUS,
    DASHBOARD_CSS,
    DASHBOARD_INDEX,
    IBKR_ERROR_CODE,
    INTERACTIVE_UI_SHELL_SNAPSHOT,
    JP_STATUS,
    LOCAL_PLATFORM_SHELL_STATUS_SNAPSHOT,
    MARKET_DATA_CLASSIFICATION,
    MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
    MARKET_DATA_STATUS,
    MARKET_SCOPE_STATUS_SNAPSHOT,
    NEXT_ROADMAP_SNAPSHOT,
    OPERATOR_NEXT_ACTIONS_SNAPSHOT,
    OPERATOR_TIMELINE,
    STATUS_SNAPSHOT,
    SYMBOLS_TEXT,
    UI_GENERATION,
    build_dashboard_css as build_previous_dashboard_css,
    build_interactive_ui_shell_snapshot as build_previous_interactive_ui_shell_snapshot,
    build_market_data_source_decision_snapshot as build_previous_market_data_source_decision_snapshot,
    build_market_scope_status_snapshot as build_previous_market_scope_status_snapshot,
)


PHASE = "Phase 761-800"
STATUS = "LOCAL_BACKEND_API_SHELL_READY"
BACKEND_API_STATUS = "LOCAL_READONLY_API_SHELL_READY"
EXTERNAL_EFFECT = "LOCALHOST_READONLY_SERVER_OPTIONAL"
NO_TEXT = "NO"
YES_TEXT = "YES"
LATEST_MAIN_COMMIT = "0d0c7ab"
LATEST_MERGED_PR = 227
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
API_MODE = "READONLY_LOCAL_ARTIFACT_API"
SAFETY_MODE = "READONLY_LOCAL_API_ONLY"

LOCAL_BACKEND_API_SHELL_SNAPSHOT = "dashboard/data/local_backend_api_shell_snapshot.json"
API_ENDPOINT_REGISTRY_SNAPSHOT = "dashboard/data/api_endpoint_registry_snapshot.json"
API_READONLY_GUARD_SNAPSHOT = "dashboard/data/api_readonly_guard_snapshot.json"
API_RUNTIME_CONTRACT_SNAPSHOT = "dashboard/data/api_runtime_contract_snapshot.json"
LOCAL_UI_SERVER_RUNBOOK_SNAPSHOT = "dashboard/data/local_ui_server_runbook_snapshot.json"
OUTPUT_CSV = "operator_local_backend_api_shell_pack.csv"
OUTPUT_REPORT = "reports/operator_local_backend_api_shell_pack_report.md"
OUTPUT_PACK = "Precious_Metals_Monitor_Local_Backend_API_Shell_Pack.md"

NEW_ARTIFACTS = (
    LOCAL_BACKEND_API_SHELL_SNAPSHOT,
    API_ENDPOINT_REGISTRY_SNAPSHOT,
    API_READONLY_GUARD_SNAPSHOT,
    API_RUNTIME_CONTRACT_SNAPSHOT,
    LOCAL_UI_SERVER_RUNBOOK_SNAPSHOT,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)
ARTIFACTS = tuple(dict.fromkeys((*PREVIOUS_ARTIFACTS, *NEW_ARTIFACTS)))

ALLOWED_ENDPOINTS = (
    "GET /",
    "GET /dashboard/index.html",
    "GET /assets/style.css",
    "GET /api/health",
    "GET /api/status",
    "GET /api/artifacts",
    "GET /api/roadmap",
    "GET /api/market-scope",
    "GET /api/data-source",
    "GET /api/operator-actions",
)
FORBIDDEN_ENDPOINTS = (
    "POST /api/*",
    "PUT /api/*",
    "DELETE /api/*",
    "/api/ibkr/connect",
    "/api/market-data/request",
    "/api/historical/request",
    "/api/account/read",
    "/api/positions/read",
    "/api/order/submit",
    "/api/order/cancel",
    "/api/telegram/send",
)
BLOCKED_RUNTIME_ACTIONS = (
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
    "backend_api_status",
    "local_backend_api",
    "backend_server_required",
    "api_mode",
    "allowed_http_methods",
    "write_api_enabled",
    "external_network_enabled",
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
        "ui_generation": UI_GENERATION,
        "backend_api_status": BACKEND_API_STATUS,
        "local_backend_api": "YES_READONLY_SHELL",
        "backend_server_required": "OPTIONAL_LOCALHOST_ONLY",
        "local_ui_server_status": "LOCALHOST_SERVER_SHELL_READY",
        "local_server_host": DEFAULT_HOST,
        "local_server_default_port": DEFAULT_PORT,
        "api_mode": API_MODE,
        "allowed_http_methods": "GET_ONLY",
        "write_api_enabled": NO_TEXT,
        "external_network_enabled": NO_TEXT,
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


def build_local_backend_api_shell_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": STATUS,
        "api_mode": API_MODE,
        "host": DEFAULT_HOST,
        "default_port": DEFAULT_PORT,
        "server_type": "PYTHON_STDLIB_HTTP_SERVER",
        "dependency_added": NO_TEXT,
        "local_backend_api": "YES_READONLY_SHELL",
        "write_api_enabled": NO_TEXT,
        "external_network_enabled": NO_TEXT,
        "ibkr_connection_enabled": NO_TEXT,
        "market_data_request_enabled": NO_TEXT,
        "account_read_enabled": NO_TEXT,
        "positions_read_enabled": NO_TEXT,
        "trading_enabled": NO_TEXT,
        "telegram_real_send_enabled": NO_TEXT,
        "generated_at_utc": timestamp,
    }


def build_api_endpoint_registry_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "API_ENDPOINT_REGISTRY_READY",
        "allowed_endpoints": list(ALLOWED_ENDPOINTS),
        "forbidden_endpoints": list(FORBIDDEN_ENDPOINTS),
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_api_readonly_guard_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "API_READONLY_GUARD_READY",
        "allowed_methods": ["GET"],
        "blocked_methods": ["POST", "PUT", "PATCH", "DELETE"],
        "blocked_runtime_actions": list(BLOCKED_RUNTIME_ACTIONS),
        "all_external_actions_blocked": YES_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_api_runtime_contract_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "API_RUNTIME_CONTRACT_READY",
        "runtime_scope": "LOCALHOST_ONLY",
        "browser_to_backend": "LOCALHOST_GET_ONLY",
        "backend_to_external": NO_TEXT,
        "backend_to_ibkr": NO_TEXT,
        "backend_to_market_data": NO_TEXT,
        "backend_to_account": NO_TEXT,
        "backend_to_trading": NO_TEXT,
        "backend_file_write": NO_TEXT,
        "backend_file_read": "LOCAL_ARTIFACTS_ONLY",
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_local_ui_server_runbook_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "LOCAL_UI_SERVER_RUNBOOK_READY",
        "start_command": "python3 main.py --local-ui-server",
        "default_url": "http://127.0.0.1:8765",
        "stop_method": "CTRL_C",
        "startup_role": "TERMINAL_START_ONLY",
        "primary_user_interaction": "WEB_UI",
        "safety_mode": SAFETY_MODE,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_build_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "latest_main_commit": LATEST_MAIN_COMMIT,
        "latest_merged_pr": LATEST_MERGED_PR,
        "phase": PHASE,
        "status": STATUS,
        "ui_generation": UI_GENERATION,
        "backend_api_status": BACKEND_API_STATUS,
        "production_ready": NO_TEXT,
        "trading_enabled": NO_TEXT,
        "external_effect": EXTERNAL_EFFECT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_operator_timeline(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "timeline": [
            {
                "phase": "Phase 697-704",
                "theme": "Dashboard UI Static Visual Freeze",
                "status": "DASHBOARD_UI_STATIC_VISUAL_FREEZE_READY",
                "external_effect": "NONE_LOCAL_ARTIFACT_GENERATION_ONLY",
            },
            {
                "phase": "Phase 705-720",
                "theme": "Post-UI Freeze Handoff / 数据源路线图",
                "status": "POST_UI_FREEZE_HANDOFF_DATA_ROADMAP_READY",
                "external_effect": "NONE_LOCAL_ARTIFACT_GENERATION_ONLY",
            },
            {
                "phase": "Phase 721-760",
                "theme": "Interactive Local Research Platform UI Shell",
                "status": "INTERACTIVE_LOCAL_RESEARCH_PLATFORM_UI_SHELL_READY",
                "external_effect": "NONE_LOCAL_ARTIFACT_GENERATION_ONLY",
            },
            {
                "phase": PHASE,
                "theme": "Local Backend API Shell",
                "status": STATUS,
                "external_effect": EXTERNAL_EFFECT,
            },
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_next_roadmap_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "NEXT_ROADMAP_READY",
        "current_track_completed": "LOCAL_BACKEND_API_SHELL",
        "next_recommended_track": "LOCAL_WORKFLOW_AUTOMATION_PACK",
        "recommended_sequence": [
            "Phase 801-840 Local Workflow Automation Pack",
            "Market Data Source Decision after subscription unblock",
            "US GLD / SLV Data Source Adapter Plan after source decision",
            "Watchlist Expansion Policy Pack after data source decision",
        ],
        "not_recommended_now": [
            "REALTIME_MONITORING_BEFORE_DATA_SOURCE_DECISION",
            "JP_CN_LIVE_MONITOR_BEFORE_DATA_SOURCE_DECISION",
            "AUTO_TRADING",
            "ACCOUNT_POSITION_READER",
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_operator_next_actions_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "OPERATOR_NEXT_ACTIONS_LOCAL_BACKEND_API_READY",
        "immediate_next_actions": [
            "Start optional local UI server only from terminal",
            "Open local dashboard manually after server start",
            "Keep all API writes and external actions disabled",
            "Continue with Local Workflow Automation Pack",
        ],
        "operator_commands": [
            "python3 main.py --local-backend-api-shell-pack",
            "python3 main.py --local-ui-server",
            "python3 -m py_compile main.py src/*.py",
            ".venv/bin/python -m pytest -q",
        ],
        "blocked_actions": list(BLOCKED_RUNTIME_ACTIONS[:-1]),
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_market_data_source_decision_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    snapshot = build_previous_market_data_source_decision_snapshot(generated_at)
    snapshot.update(
        {
            "phase": PHASE,
            "source_connection_implemented": NO_TEXT,
            "live_market_data_enabled": NO_TEXT,
            "backend_api_status": BACKEND_API_STATUS,
            "api_mode": API_MODE,
        }
    )
    return snapshot


def build_market_scope_status_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    snapshot = build_previous_market_scope_status_snapshot(generated_at)
    snapshot.update({"phase": PHASE, "status": "MARKET_SCOPE_STATUS_LOCAL_BACKEND_API_SHELL_READY"})
    return snapshot


def build_interactive_ui_shell_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    snapshot = build_previous_interactive_ui_shell_snapshot(generated_at)
    snapshot.update(
        {
            "phase": PHASE,
            "local_backend_api": "YES_READONLY_SHELL",
            "backend_api_status": BACKEND_API_STATUS,
            "api_calls_from_static_ui": NO_TEXT,
        }
    )
    return snapshot


def build_local_platform_shell_status_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "LOCAL_PLATFORM_UI_SHELL_READY",
        "platform_mode": "UI_DRIVEN_LOCAL_RESEARCH_WORKBENCH",
        "terminal_role": "STARTUP_AND_FALLBACK_ONLY",
        "primary_user_interaction": "WEB_UI",
        "backend_api_status": BACKEND_API_STATUS,
        "local_ui_server_status": "LOCALHOST_SERVER_SHELL_READY",
        "safety_mode": SAFETY_MODE,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_artifact_manifest(generated_at: Optional[str] = None) -> Dict[str, object]:
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
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_dashboard_html(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    artifact_cards = "\n".join(
        f'              <article class="file-card" data-search="{path} { _artifact_category(path) } {EXTERNAL_EFFECT}" data-kind="{_artifact_category(path).lower()}"><span class="token mono">{_artifact_category(path)}_LOCAL</span><span class="mono">{path}</span><span>{_artifact_category(path)}</span><a class="local-link mono" href="{_artifact_local_href(path)}">本地链接</a><span class="mono muted">{EXTERNAL_EFFECT}</span></article>'
        for path in ARTIFACTS
    )
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI 投研交易驾驶舱 · Local Backend API Shell</title>
    <link rel="stylesheet" href="assets/style.css">
  </head>
  <body>
    <div class="app-shell">
      <aside class="sidebar" aria-label="左侧导航">
        <div class="brand"><span class="brand-mark">AI</span><span class="brand-title">AI 投研交易驾驶舱</span><span class="brand-subtitle">本地只读 API 壳</span></div>
        <nav class="sidebar-nav" aria-label="功能分区">
          <button class="nav-item active" type="button" data-tab-target="overview"><span class="nav-icon">总</span><span>总览</span></button>
          <button class="nav-item" type="button" data-tab-target="local-service"><span class="nav-icon">服</span><span>本地服务</span></button>
          <button class="nav-item" type="button" data-tab-target="data-source"><span class="nav-icon">源</span><span>数据源</span></button>
          <button class="nav-item" type="button" data-tab-target="risk"><span class="nav-icon">风</span><span>风险边界</span></button>
          <button class="nav-item" type="button" data-tab-target="artifacts"><span class="nav-icon">文</span><span>本地文件</span></button>
          <button class="nav-item" type="button" data-tab-target="roadmap"><span class="nav-icon">路</span><span>路线图</span></button>
          <button class="nav-item" type="button" data-tab-target="system"><span class="nav-icon">系</span><span>系统状态</span></button>
        </nav>
        <div class="sidebar-note">GET only · localhost only · 外部动作全部禁用</div>
      </aside>
      <div class="content">
        <header class="command-bar">
          <div>
            <h1>AI 投研交易驾驶舱 · Local Backend API Shell</h1>
            <p class="subtitle">本地 localhost 只读 API 壳 · Python 标准库 server · 静态 UI 不自动调用 API</p>
            <div class="badge-row">
              <span class="badge safe">GLD / SLV</span>
              <span class="badge blocked">BLOCKED_BY_SUBSCRIPTION</span>
              <span class="badge blocked">IBKR_ERROR_10089</span>
              <span class="badge safe">GET_ONLY</span>
              <span class="badge safe">127.0.0.1:8765</span>
              <span class="badge secondary mono">V8_INTERACTIVE_LOCAL_RESEARCH_PLATFORM_SHELL</span>
            </div>
          </div>
          <section class="build-chip"><span class="label">generated_at_utc</span><strong class="big-copy mono">{timestamp}</strong></section>
        </header>

        <section class="toolbar" aria-label="本地搜索和筛选">
          <label class="search-box"><span>搜索</span><input id="localSearch" type="search" placeholder="搜索 artifact、状态、API、GLD / SLV"></label>
          <label class="filter-box"><span>筛选</span><select id="localFilter"><option value="all">全部</option><option value="risk-only">仅风险项</option><option value="json">仅 JSON</option><option value="report">仅 REPORT</option><option value="api">仅 API</option><option value="next-actions">仅下一步动作</option></select></label>
        </section>

        <main class="tab-panels">
          <section class="tab-panel active" id="overview" data-panel data-search="总览 LOCAL_BACKEND_API_SHELL_READY localhost GET only" data-kind="overview api next-actions">
            <div class="hero-grid">
              <article class="panel"><div class="panel-header"><div><span class="eyebrow">当前阶段</span><h2>Local Backend API Shell</h2></div><span class="token safe">READY</span></div><strong class="big-copy">LOCAL_BACKEND_API_SHELL_READY</strong><p class="muted">只读 API 壳已规划并可从终端启动；静态页面不自动访问本地服务。</p></article>
              <article class="panel"><div class="panel-header"><div><span class="eyebrow">本地 API 壳</span><h2>已规划 / 只读</h2></div><span class="token safe">GET</span></div><strong class="big-copy">READONLY_LOCAL_ARTIFACT_API</strong><p class="muted">默认地址：127.0.0.1:8765。仅读取 dashboard/data 内允许的 snapshot 和 manifest。</p></article>
              <article class="panel"><div class="panel-header"><div><span class="eyebrow">外部动作</span><h2>全部禁用</h2></div><span class="token disabled">LOCKED</span></div><strong class="big-copy">未连接 IBKR</strong><p class="muted">无行情请求 · 无历史数据请求 · 无账户/持仓读取 · 无交易 · 无 Telegram 实发</p></article>
            </div>
          </section>

          <section class="tab-panel" id="local-service" data-panel data-search="本地服务 local api shell start command 127.0.0.1 8765 READONLY_LOCAL_API_ONLY" data-kind="api next-actions">
            <div class="hero-grid">
              <article class="panel"><div class="panel-header"><div><span class="eyebrow">本地服务</span><h2>本地 API 壳：已规划 / 只读</h2></div><span class="token safe">LOCALHOST</span></div><strong class="big-copy mono">127.0.0.1:8765</strong><p class="muted">默认地址只供手动启动后的浏览器访问；本静态页面不会自动调用 API。</p></article>
              <article class="panel"><div class="panel-header"><div><span class="eyebrow">启动命令</span><h2>terminal only</h2></div><span class="token warn">OPTIONAL</span></div><strong class="big-copy mono">python3 main.py --local-ui-server</strong><button class="copy-btn" type="button" data-copy="python3 main.py --local-ui-server">复制启动命令</button></article>
              <article class="panel"><div class="panel-header"><div><span class="eyebrow">安全模式</span><h2>READONLY_LOCAL_API_ONLY</h2></div><span class="token disabled">NO WRITE</span></div><strong class="big-copy">GET_ONLY</strong><p class="muted">POST / PUT / PATCH / DELETE 均拒绝；禁止 IBKR、行情、账户、持仓、交易、Telegram 和外部 URL。</p></article>
            </div>
          </section>

          <section class="tab-panel" id="data-source" data-panel data-search="数据源 BLOCKED_BY_SUBSCRIPTION IBKR_ERROR_10089 GLD SLV" data-kind="api">
            <div class="card-header"><h2>数据源状态</h2><span class="token disabled">未接入</span></div>
            <div class="source-grid">
              <article class="source-card"><strong>IBKR Network B / ARCA</strong><p class="muted">仍受订阅阻断：IBKR_ERROR_10089。本阶段不连接、不请求行情。</p></article>
              <article class="source-card"><strong>手动 CSV</strong><p class="muted">未来可作为本地 artifact 来源；本阶段不新增导入动作。</p></article>
              <article class="source-card"><strong>Local Artifact API</strong><p class="muted">仅暴露 status、manifest、roadmap、market scope、data source 和 operator actions snapshots。</p></article>
            </div>
          </section>

          <section class="tab-panel" id="risk" data-panel data-search="风险边界 disabled IBKR 请求行情 历史数据 账户 持仓 下单 Telegram 外部 URL" data-kind="risk-only">
            <article class="collapsible card"><button class="collapse-toggle" type="button">只读 API guard <span>折叠</span></button><div class="collapse-body risk-list">
              <button class="disabled-action" type="button" disabled title="本阶段禁止连接 IBKR">连接 IBKR</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止请求行情">请求行情</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止请求历史数据">请求历史数据</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止读取账户">读取账户</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止读取持仓">读取持仓</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止下单">下单</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止 Telegram 实发">Telegram 实发</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止加载外部 URL">外部 URL</button>
            </div></article>
          </section>

          <section class="tab-panel" id="artifacts" data-panel data-search="本地文件 artifact JSON REPORT CSV PACK API" data-kind="json report api">
            <article class="collapsible card"><button class="collapse-toggle" type="button">artifact 文件流 <span>折叠</span></button><div class="collapse-body file-stream">
{artifact_cards}
            </div></article>
          </section>

          <section class="tab-panel" id="roadmap" data-panel data-search="路线图 operator roadmap Local Workflow Automation Pack 下一步动作" data-kind="next-actions">
            <article class="collapsible card"><button class="collapse-toggle" type="button">operator roadmap <span>折叠</span></button><div class="collapse-body phase-rail">
              <article class="phase-card"><strong>Phase 721-760</strong><p>Interactive Local Research Platform UI Shell</p><span class="token safe">READY</span></article>
              <article class="phase-card"><strong>Phase 761-800</strong><p>Local Backend API Shell</p><span class="token safe">READY</span></article>
              <article class="phase-card"><strong>Next</strong><p>Local Workflow Automation Pack</p><span class="token warn">NEXT</span></article>
            </div></article>
          </section>

          <section class="tab-panel" id="system" data-panel data-search="系统状态 LOCAL_BACKEND_API_SHELL_READY backend api localhost only GET" data-kind="risk-only api">
            <article class="collapsible card"><button class="collapse-toggle" type="button">runtime contract <span>折叠</span></button><div class="collapse-body version-table">
              <div class="version-row"><span>status</span><strong class="mono">{STATUS}</strong></div>
              <div class="version-row"><span>backend_api_status</span><strong class="mono">{BACKEND_API_STATUS}</strong></div>
              <div class="version-row"><span>local_backend_api</span><strong class="mono">YES_READONLY_SHELL</strong></div>
              <div class="version-row"><span>backend_server_required</span><strong class="mono">OPTIONAL_LOCALHOST_ONLY</strong></div>
              <div class="version-row"><span>api_mode</span><strong class="mono">{API_MODE}</strong></div>
              <div class="version-row"><span>source_connection_implemented</span><strong class="mono">NO</strong></div>
              <div class="version-row"><span>live_market_data_enabled</span><strong class="mono">NO</strong></div>
              <div class="version-row"><span>production_ready</span><strong class="mono">NO</strong></div>
            </div></article>
          </section>
        </main>
      </div>
    </div>
    <footer class="footer-safety-bar">localhost only · GET only · 未连接 IBKR · 未请求行情 · 未请求历史数据 · 未读取账户/持仓 · 未交易 · 未 Telegram 实发</footer>
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
    return build_previous_dashboard_css() + "\n/* Phase 761-800 local backend API shell additions */\n"


def build_report(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    return f"""# Phase 761-800 Local Backend API Shell Pack

- phase: {PHASE}
- status: {STATUS}
- backend_api_status: {BACKEND_API_STATUS}
- api_mode: {API_MODE}
- local_backend_api: YES_READONLY_SHELL
- server: Python stdlib http.server / socketserver
- host: {DEFAULT_HOST}
- default_port: {DEFAULT_PORT}
- safety_mode: {SAFETY_MODE}
- external_network_enabled: NO
- source_connection_implemented: NO
- live_market_data_enabled: NO
- market_data_status: {MARKET_DATA_STATUS}
- ibkr_error_code: {IBKR_ERROR_CODE}
- production_ready: NO
- trading_enabled: NO
- generated_at_utc: {timestamp}
"""


def build_pack_markdown(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    return f"""# Precious Metals Monitor Local Backend API Shell Pack

status={STATUS}

This pack adds a localhost-only, GET-only, read-only backend API shell for local dashboard artifacts.

- localhost only
- GET only
- Python stdlib server
- no third-party dependency added
- no dashboard external fetch
- no backend external network
- no source connection implemented
- no live market data enabled
- no IBKR connection
- no market data request
- no historical data request
- no account/position read
- no contract qualification
- no trading
- no Telegram real send
- no BUY/SELL/HOLD signal
- no target/stop/take-profit
- no live price fields
- market data remains BLOCKED_BY_SUBSCRIPTION / IBKR_ERROR_10089
- GLD / SLV only
- JP / CN remain frozen
- next recommended track: Local Workflow Automation Pack

generated_at_utc={timestamp}
"""


def generate_local_backend_api_shell_pack(
    output_dashboard_index: PathLike = DASHBOARD_INDEX,
    output_dashboard_css: PathLike = DASHBOARD_CSS,
    output_status_snapshot: PathLike = STATUS_SNAPSHOT,
    output_local_backend_api_shell_snapshot: PathLike = LOCAL_BACKEND_API_SHELL_SNAPSHOT,
    output_api_endpoint_registry_snapshot: PathLike = API_ENDPOINT_REGISTRY_SNAPSHOT,
    output_api_readonly_guard_snapshot: PathLike = API_READONLY_GUARD_SNAPSHOT,
    output_api_runtime_contract_snapshot: PathLike = API_RUNTIME_CONTRACT_SNAPSHOT,
    output_local_ui_server_runbook_snapshot: PathLike = LOCAL_UI_SERVER_RUNBOOK_SNAPSHOT,
    output_build_snapshot: PathLike = BUILD_SNAPSHOT,
    output_operator_timeline: PathLike = OPERATOR_TIMELINE,
    output_interactive_ui_shell_snapshot: PathLike = INTERACTIVE_UI_SHELL_SNAPSHOT,
    output_local_platform_shell_status_snapshot: PathLike = LOCAL_PLATFORM_SHELL_STATUS_SNAPSHOT,
    output_operator_next_actions_snapshot: PathLike = OPERATOR_NEXT_ACTIONS_SNAPSHOT,
    output_next_roadmap_snapshot: PathLike = NEXT_ROADMAP_SNAPSHOT,
    output_market_scope_status_snapshot: PathLike = MARKET_SCOPE_STATUS_SNAPSHOT,
    output_market_data_source_decision_snapshot: PathLike = MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
    output_artifact_manifest: PathLike = ARTIFACT_MANIFEST,
    output_csv: PathLike = OUTPUT_CSV,
    output_report: PathLike = OUTPUT_REPORT,
    output_pack: PathLike = OUTPUT_PACK,
    generated_at: Optional[str] = None,
) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    row = {field: build_status_snapshot(timestamp).get(field, "") for field in CSV_FIELDS}

    _write_text(output_dashboard_index, build_dashboard_html(timestamp))
    _write_text(output_dashboard_css, build_dashboard_css())
    _write_json(output_status_snapshot, build_status_snapshot(timestamp))
    _write_json(output_local_backend_api_shell_snapshot, build_local_backend_api_shell_snapshot(timestamp))
    _write_json(output_api_endpoint_registry_snapshot, build_api_endpoint_registry_snapshot(timestamp))
    _write_json(output_api_readonly_guard_snapshot, build_api_readonly_guard_snapshot(timestamp))
    _write_json(output_api_runtime_contract_snapshot, build_api_runtime_contract_snapshot(timestamp))
    _write_json(output_local_ui_server_runbook_snapshot, build_local_ui_server_runbook_snapshot(timestamp))
    _write_json(output_build_snapshot, build_build_snapshot(timestamp))
    _write_json(output_operator_timeline, build_operator_timeline(timestamp))
    _write_json(output_interactive_ui_shell_snapshot, build_interactive_ui_shell_snapshot(timestamp))
    _write_json(output_local_platform_shell_status_snapshot, build_local_platform_shell_status_snapshot(timestamp))
    _write_json(output_operator_next_actions_snapshot, build_operator_next_actions_snapshot(timestamp))
    _write_json(output_next_roadmap_snapshot, build_next_roadmap_snapshot(timestamp))
    _write_json(output_market_scope_status_snapshot, build_market_scope_status_snapshot(timestamp))
    _write_json(output_market_data_source_decision_snapshot, build_market_data_source_decision_snapshot(timestamp))
    _write_json(output_artifact_manifest, build_artifact_manifest(timestamp))

    csv_path = Path(output_csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerow(row)
    _write_text(output_report, build_report(timestamp))
    _write_text(output_pack, build_pack_markdown(timestamp))
    return row


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 761-800 local backend API shell pack artifacts.")
    parser.parse_args(argv)
    row = generate_local_backend_api_shell_pack()
    print("[LOCAL_BACKEND_API_SHELL_PACK] generated")
    print(f"phase={row['phase']}")
    print(f"status={row['status']}")
    print(f"backend_api_status={row['backend_api_status']}")
    print(f"local_backend_api={row['local_backend_api']}")
    print(f"api_mode={row['api_mode']}")
    print(f"source_connection_implemented={row['source_connection_implemented']}")
    print(f"live_market_data_enabled={row['live_market_data_enabled']}")
    print(f"external_effect={row['external_effect']}")
    print(f"csv={OUTPUT_CSV}")
    print(f"report={OUTPUT_REPORT}")
    print(f"pack={OUTPUT_PACK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
