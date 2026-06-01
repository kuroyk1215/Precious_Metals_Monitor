from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

from src.operator_local_backend_api_shell_pack import (
    API_READONLY_GUARD_SNAPSHOT,
    API_RUNTIME_CONTRACT_SNAPSHOT,
    LOCAL_BACKEND_API_SHELL_SNAPSHOT,
    LOCAL_UI_SERVER_RUNBOOK_SNAPSHOT,
    MARKET_DATA_CLASSIFICATION,
    MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
    MARKET_DATA_STATUS,
    MARKET_SCOPE_STATUS_SNAPSHOT,
    NEXT_ROADMAP_SNAPSHOT,
    OPERATOR_NEXT_ACTIONS_SNAPSHOT,
    OPERATOR_TIMELINE,
    STATUS_SNAPSHOT,
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    DASHBOARD_CSS,
    DASHBOARD_INDEX,
    IBKR_ERROR_CODE,
    build_dashboard_css as build_previous_dashboard_css,
)
from src.local_data_source_dry_run import build_data_source_dry_run_snapshot
from src.local_operator_packet_builder import (
    build_operator_daily_packet_markdown,
    build_operator_daily_packet_snapshot,
    build_telegram_preview_markdown,
    build_telegram_preview_snapshot,
    build_watchlist_policy_snapshot,
)
from src.local_research_report_builder import (
    build_research_report_framework_snapshot,
    build_research_report_markdown,
)
from src.local_workflow_automation import (
    build_local_workflow_automation_snapshot,
    run_local_workflow,
)


PHASE = "Phase 801-1000"
STATUS = "UI_DRIVEN_LOCAL_RESEARCH_PLATFORM_MVP_READY"
UI_GENERATION = "V9_UI_DRIVEN_LOCAL_RESEARCH_PLATFORM_MVP"
BACKEND_API_STATUS = "LOCAL_READONLY_API_SHELL_READY"
API_MODE = "READONLY_LOCAL_ARTIFACT_API"
NO_TEXT = "NO"
YES_TEXT = "YES"
SYMBOLS_TEXT = "GLD / SLV"
JP_STATUS = "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION"
CN_STATUS = "FROZEN_PENDING_DATA_SOURCE_DECISION"
LATEST_MAIN_COMMIT = "022cdc2"
LATEST_MERGED_PR = 228
EXTERNAL_EFFECT = "NONE_LOCAL_ARTIFACT_GENERATION_ONLY"

LOCAL_WORKFLOW_AUTOMATION_SNAPSHOT = "dashboard/data/local_workflow_automation_snapshot.json"
OPERATOR_DAILY_PACKET_SNAPSHOT = "dashboard/data/operator_daily_packet_snapshot.json"
DATA_SOURCE_DRY_RUN_SNAPSHOT = "dashboard/data/us_gld_slv_data_source_dry_run_snapshot.json"
RESEARCH_REPORT_BUILDER_SNAPSHOT = "dashboard/data/research_report_builder_snapshot.json"
RESEARCH_REPORT_FRAMEWORK_SNAPSHOT = "dashboard/data/research_report_framework_snapshot.json"
TELEGRAM_PREVIEW_SNAPSHOT = "dashboard/data/telegram_preview_snapshot.json"
WATCHLIST_POLICY_SNAPSHOT = "dashboard/data/watchlist_policy_snapshot.json"
UI_MVP_ENDPOINT_REGISTRY_SNAPSHOT = "dashboard/data/ui_mvp_endpoint_registry_snapshot.json"
UI_MVP_WORKFLOW_CONTRACT_SNAPSHOT = "dashboard/data/ui_mvp_workflow_contract_snapshot.json"
LOCAL_RESEARCH_PLATFORM_MVP_STATUS_SNAPSHOT = "dashboard/data/local_research_platform_mvp_status_snapshot.json"
FINAL_LANDING_AUDIT_SNAPSHOT = "dashboard/data/final_landing_audit_snapshot.json"
OUTPUT_CSV = "operator_ui_driven_local_research_platform_mvp_pack.csv"
OUTPUT_REPORT = "reports/operator_ui_driven_local_research_platform_mvp_pack_report.md"
OUTPUT_RESEARCH_REPORT = "reports/local_research_report_framework_GLD_SLV.md"
OUTPUT_DAILY_PACKET = "reports/operator_daily_packet_preview.md"
OUTPUT_TELEGRAM_PREVIEW = "reports/telegram_preview_local_only.md"
OUTPUT_PACK = "Precious_Metals_Monitor_UI_Driven_Local_Research_Platform_MVP_Landing_Pack.md"

MVP_ENDPOINTS = (
    "GET /api/workflow/status",
    "GET /api/workflow/run-preview",
    "GET /api/research/report-framework",
    "GET /api/data-source/dry-run",
    "GET /api/operator/daily-packet",
    "GET /api/telegram/preview",
    "GET /api/watchlist/policy",
    "GET /api/mvp/status",
)

BASE_ENDPOINTS = (
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

ARTIFACTS = (
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    STATUS_SNAPSHOT,
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    OPERATOR_TIMELINE,
    LOCAL_BACKEND_API_SHELL_SNAPSHOT,
    "dashboard/data/api_endpoint_registry_snapshot.json",
    API_READONLY_GUARD_SNAPSHOT,
    API_RUNTIME_CONTRACT_SNAPSHOT,
    LOCAL_UI_SERVER_RUNBOOK_SNAPSHOT,
    OPERATOR_NEXT_ACTIONS_SNAPSHOT,
    NEXT_ROADMAP_SNAPSHOT,
    MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
    MARKET_SCOPE_STATUS_SNAPSHOT,
    LOCAL_WORKFLOW_AUTOMATION_SNAPSHOT,
    OPERATOR_DAILY_PACKET_SNAPSHOT,
    DATA_SOURCE_DRY_RUN_SNAPSHOT,
    RESEARCH_REPORT_BUILDER_SNAPSHOT,
    RESEARCH_REPORT_FRAMEWORK_SNAPSHOT,
    TELEGRAM_PREVIEW_SNAPSHOT,
    WATCHLIST_POLICY_SNAPSHOT,
    UI_MVP_ENDPOINT_REGISTRY_SNAPSHOT,
    UI_MVP_WORKFLOW_CONTRACT_SNAPSHOT,
    LOCAL_RESEARCH_PLATFORM_MVP_STATUS_SNAPSHOT,
    FINAL_LANDING_AUDIT_SNAPSHOT,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_RESEARCH_REPORT,
    OUTPUT_DAILY_PACKET,
    OUTPUT_TELEGRAM_PREVIEW,
    OUTPUT_PACK,
)

CSV_FIELDS = (
    "phase",
    "status",
    "local_platform_mvp_status",
    "ui_generation",
    "backend_api_status",
    "local_workflow_status",
    "research_report_builder_status",
    "data_source_dry_run_status",
    "operator_packet_status",
    "telegram_preview_status",
    "watchlist_policy_status",
    "final_landing_audit_status",
    "source_connection_implemented",
    "live_market_data_enabled",
    "market_data_status",
    "ibkr_error_code",
    "production_ready",
    "trading_enabled",
    "telegram_real_send_enabled",
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
        "local_platform_mvp_status": "LOCAL_RESEARCH_PLATFORM_MVP_READY",
        "ui_generation": UI_GENERATION,
        "backend_api_status": BACKEND_API_STATUS,
        "local_backend_api": "YES_READONLY_SHELL",
        "api_mode": API_MODE,
        "allowed_http_methods": "GET_ONLY",
        "local_workflow_status": "LOCAL_WORKFLOW_AUTOMATION_READY",
        "research_report_builder_status": "RESEARCH_REPORT_FRAMEWORK_READY",
        "data_source_dry_run_status": "US_GLD_SLV_DATA_SOURCE_DRY_RUN_READY",
        "operator_packet_status": "OPERATOR_DAILY_PACKET_PREVIEW_READY",
        "telegram_preview_status": "TELEGRAM_PREVIEW_LOCAL_ONLY_READY",
        "watchlist_policy_status": "WATCHLIST_POLICY_READY",
        "final_landing_audit_status": "LOCAL_PLATFORM_MVP_FINAL_AUDIT_READY",
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
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "symbols": SYMBOLS_TEXT,
        "generated_at_utc": timestamp,
    }


def build_research_report_builder_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "RESEARCH_REPORT_FRAMEWORK_READY",
        "symbols": ["GLD", "SLV"],
        "supported_horizons": ["日内", "短期", "中期", "长期"],
        "real_market_data_status": "NO_REAL_MARKET_DATA",
        "directional_signal_enabled": NO_TEXT,
        "price_level_output_enabled": NO_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_ui_mvp_endpoint_registry_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "UI_MVP_ENDPOINT_REGISTRY_READY",
        "allowed_http_methods": ["GET"],
        "allowed_endpoints": [*BASE_ENDPOINTS, *MVP_ENDPOINTS],
        "mvp_endpoints": list(MVP_ENDPOINTS),
        "forbidden_endpoints": list(FORBIDDEN_ENDPOINTS),
        "write_endpoints_enabled": NO_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_api_endpoint_registry_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    snapshot = build_ui_mvp_endpoint_registry_snapshot(generated_at)
    snapshot["status"] = "API_ENDPOINT_REGISTRY_READY"
    return snapshot


def build_api_readonly_guard_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "API_READONLY_GUARD_READY",
        "allowed_methods": ["GET"],
        "blocked_methods": ["POST", "PUT", "PATCH", "DELETE"],
        "all_external_actions_blocked": YES_TEXT,
        "write_api_enabled": NO_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_ui_mvp_workflow_contract_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "UI_MVP_WORKFLOW_CONTRACT_READY",
        "terminal_role": "STARTUP_AND_FALLBACK_ONLY",
        "browser_role": "PRIMARY_LOCAL_WORKBENCH",
        "browser_write_actions_enabled": NO_TEXT,
        "workflow_run_command": "python3 main.py --local-workflow-run",
        "research_build_command": "python3 main.py --local-research-report-build",
        "pack_build_command": "python3 main.py --ui-driven-local-research-platform-mvp-pack",
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_local_research_platform_mvp_status_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "LOCAL_RESEARCH_PLATFORM_MVP_READY",
        "ui_driven_workbench_ready": YES_TEXT,
        "local_workflow_automation_ready": YES_TEXT,
        "research_report_framework_ready": YES_TEXT,
        "data_source_dry_run_ready": YES_TEXT,
        "operator_daily_packet_preview_ready": YES_TEXT,
        "telegram_preview_local_only_ready": YES_TEXT,
        "watchlist_policy_ready": YES_TEXT,
        "terminal_role": "STARTUP_AND_FALLBACK_ONLY",
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_final_landing_audit_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "LOCAL_PLATFORM_MVP_FINAL_AUDIT_READY",
        "all_external_actions_blocked": YES_TEXT,
        "ui_driven_workbench_ready": YES_TEXT,
        "terminal_role": "STARTUP_AND_FALLBACK_ONLY",
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


def build_build_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "latest_main_commit": LATEST_MAIN_COMMIT,
        "latest_merged_pr": LATEST_MERGED_PR,
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
            {"phase": "Phase 721-760", "theme": "Interactive Local Research Platform UI Shell", "status": "READY"},
            {"phase": "Phase 761-800", "theme": "Local Backend API Shell", "status": "READY"},
            {"phase": PHASE, "theme": "UI-Driven Local Research Platform MVP Landing", "status": STATUS},
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_operator_next_actions_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "OPERATOR_NEXT_ACTIONS_MVP_READY",
        "immediate_next_actions": [
            "Start local UI server from terminal only when needed",
            "Use browser UI as the primary workbench",
            "Run local workflow from CLI to refresh local preview artifacts",
            "Keep all external actions disabled",
        ],
        "operator_commands": [
            "python3 main.py --ui-driven-local-research-platform-mvp-pack",
            "python3 main.py --local-workflow-run",
            "python3 main.py --local-research-report-build",
            "python3 main.py --local-ui-server",
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_next_roadmap_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "NEXT_ROADMAP_READY",
        "current_track_completed": "UI_DRIVEN_LOCAL_RESEARCH_PLATFORM_MVP",
        "next_recommended_track": "DATA_SOURCE_DECISION_AFTER_SUBSCRIPTION_UNBLOCK",
        "not_recommended_now": [
            "REALTIME_MONITORING",
            "ACCOUNT_READER",
            "AUTO_TRADING",
            "JP_CN_LIVE_MONITOR",
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_market_data_source_decision_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "MARKET_DATA_SOURCE_DECISION_FROZEN",
        "source_connection_implemented": NO_TEXT,
        "live_market_data_enabled": NO_TEXT,
        "market_data_status": MARKET_DATA_STATUS,
        "ibkr_error_code": IBKR_ERROR_CODE,
        "us_status": "GLD_SLV_DRY_RUN_ONLY",
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_market_scope_status_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "MARKET_SCOPE_STATUS_MVP_READY",
        "us_symbols": ["GLD", "SLV"],
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_local_backend_api_shell_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "LOCAL_BACKEND_API_SHELL_READY",
        "api_mode": API_MODE,
        "local_backend_api": "YES_READONLY_SHELL",
        "allowed_http_methods": ["GET"],
        "write_api_enabled": NO_TEXT,
        "external_network_enabled": NO_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_api_runtime_contract_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "API_RUNTIME_CONTRACT_READY",
        "runtime_scope": "LOCALHOST_ONLY",
        "browser_to_backend": "LOCALHOST_GET_ONLY",
        "backend_to_external": NO_TEXT,
        "backend_file_write": NO_TEXT,
        "backend_file_read": "LOCAL_ARTIFACTS_ONLY",
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_local_ui_server_runbook_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "LOCAL_UI_SERVER_RUNBOOK_READY",
        "start_command": "python3 main.py --local-ui-server",
        "stop_method": "CTRL_C",
        "startup_role": "TERMINAL_START_ONLY",
        "primary_user_interaction": "WEB_UI",
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
                "external_effect": EXTERNAL_EFFECT,
            }
            for path in ARTIFACTS
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_dashboard_html(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    cards = "\n".join(
        f'              <article class="file-card" data-search="{path} {_artifact_category(path)}" data-kind="{_artifact_category(path).lower()}"><span class="token mono">{_artifact_category(path)}_LOCAL</span><span class="mono">{path}</span><a class="local-link mono" href="{_artifact_local_href(path)}">本地路径</a></article>'
        for path in ARTIFACTS
    )
    endpoints = "\n".join(f'<span class="endpoint-pill mono">{endpoint}</span>' for endpoint in MVP_ENDPOINTS)
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI 投研驾驶舱 · UI Driven MVP</title>
    <link rel="stylesheet" href="assets/style.css">
  </head>
  <body>
    <div class="app-shell">
      <aside class="sidebar" aria-label="左侧导航">
        <div class="brand"><span class="brand-mark">AI</span><span class="brand-title">AI 投研驾驶舱</span><span class="brand-subtitle">UI Driven Local MVP</span></div>
        <nav class="sidebar-nav" aria-label="功能分区">
          <button class="nav-item active" type="button" data-tab-target="overview"><span class="nav-icon">总</span><span>总览</span></button>
          <button class="nav-item" type="button" data-tab-target="workbench"><span class="nav-icon">台</span><span>MVP 工作台</span></button>
          <button class="nav-item" type="button" data-tab-target="api"><span class="nav-icon">端</span><span>本地 API</span></button>
          <button class="nav-item" type="button" data-tab-target="reports"><span class="nav-icon">报</span><span>报告</span></button>
          <button class="nav-item" type="button" data-tab-target="risk"><span class="nav-icon">禁</span><span>禁用动作</span></button>
          <button class="nav-item" type="button" data-tab-target="artifacts"><span class="nav-icon">文</span><span>本地文件</span></button>
          <button class="nav-item" type="button" data-tab-target="audit"><span class="nav-icon">审</span><span>Final audit</span></button>
        </nav>
        <div class="sidebar-note">GET only · localhost only · UI 查看与复制命令</div>
      </aside>
      <div class="content">
        <header class="command-bar">
          <div>
            <h1>UI 驱动本地投研平台 MVP</h1>
            <p class="subtitle">终端只负责启动与 CLI fallback；主要操作转移到浏览器 UI。本阶段不连接数据源，不生成交易建议。</p>
            <div class="badge-row">
              <span class="badge safe">GLD / SLV</span>
              <span class="badge safe">LOCAL WORKFLOW READY</span>
              <span class="badge safe">GET ONLY</span>
              <span class="badge blocked">BLOCKED_BY_SUBSCRIPTION</span>
              <span class="badge blocked">IBKR_ERROR_10089</span>
              <span class="badge secondary mono">{UI_GENERATION}</span>
            </div>
          </div>
          <section class="build-chip"><span class="label">generated_at_utc</span><strong class="big-copy mono">{timestamp}</strong></section>
        </header>

        <section class="toolbar" aria-label="本地搜索和筛选">
          <label class="search-box"><span>搜索</span><input id="localSearch" type="search" placeholder="搜索 workflow、报告、API、artifact"></label>
          <label class="filter-box"><span>筛选</span><select id="localFilter"><option value="all">全部</option><option value="json">JSON</option><option value="report">REPORT</option><option value="risk">风险</option><option value="api">API</option><option value="workflow">Workflow</option></select></label>
        </section>

        <main class="tab-panels">
          <section class="tab-panel active" id="overview" data-panel data-search="overview MVP LOCAL_RESEARCH_PLATFORM_MVP_READY workflow report dry run packet telegram watchlist audit" data-kind="workflow api">
            <div class="hero-grid">
              <article class="panel"><div class="panel-header"><div><span class="eyebrow">目标状态</span><h2>Local Research Platform MVP</h2></div><span class="token safe">READY</span></div><strong class="big-copy">{STATUS}</strong><p class="muted">浏览器 UI 是主工作台；终端降级为启动本地服务和执行 CLI fallback。</p></article>
              <article class="panel"><div class="panel-header"><div><span class="eyebrow">本地 workflow</span><h2>只读预览</h2></div><span class="token safe">CLI</span></div><strong class="big-copy mono">python3 main.py --local-workflow-run</strong><button class="copy-btn" type="button" data-copy="python3 main.py --local-workflow-run">复制运行命令</button></article>
              <article class="panel"><div class="panel-header"><div><span class="eyebrow">安全边界</span><h2>外部动作禁用</h2></div><span class="token disabled">LOCKED</span></div><strong class="big-copy">NO REAL MARKET DATA</strong><p class="muted">无 IBKR、无行情、无账户、无持仓、无交易、无 Telegram 实发。</p></article>
            </div>
          </section>

          <section class="tab-panel" id="workbench" data-panel data-search="MVP 工作台 workflow report data source operator telegram watchlist final audit" data-kind="workflow">
            <div class="workbench-grid">
              <article class="workbench-card"><span class="token safe">READY</span><h2>本地 workflow</h2><p class="muted">生成 operator packet、研究框架、Telegram preview 和 watchlist policy。</p><button class="copy-btn" type="button" data-copy="python3 main.py --local-workflow-run">复制运行命令</button></article>
              <article class="workbench-card"><span class="token safe">READY</span><h2>研究报告框架</h2><p class="muted">GLD / SLV，日内 / 短期 / 中期 / 长期，NO_REAL_MARKET_DATA。</p><a class="local-link" href="../reports/local_research_report_framework_GLD_SLV.md">查看本地报告路径</a></article>
              <article class="workbench-card"><span class="token safe">DRY RUN</span><h2>数据源 dry-run</h2><p class="muted">IBKR Network B / ARCA 未订阅且未连接，其他来源仅候选或设计。</p><a class="local-link" href="data/us_gld_slv_data_source_dry_run_snapshot.json">查看预览</a></article>
              <article class="workbench-card"><span class="token safe">PREVIEW</span><h2>Operator packet</h2><p class="muted">本地状态、UI / API / data source / risk / next action。</p><a class="local-link" href="../reports/operator_daily_packet_preview.md">查看本地报告路径</a></article>
              <article class="workbench-card"><span class="token safe">LOCAL ONLY</span><h2>Telegram preview</h2><p class="muted">只生成 markdown preview，不读取 token / chat_id，不发送。</p><a class="local-link" href="../reports/telegram_preview_local_only.md">查看本地报告路径</a></article>
              <article class="workbench-card"><span class="token safe">READY</span><h2>Watchlist policy</h2><p class="muted">US=GLD / SLV first，JP / CN frozen，新增标的需人工确认。</p><a class="local-link" href="data/watchlist_policy_snapshot.json">查看预览</a></article>
              <article class="workbench-card"><span class="token safe">READY</span><h2>Final audit</h2><p class="muted">终端角色：STARTUP_AND_FALLBACK_ONLY。外部动作全部阻断。</p><a class="local-link" href="data/final_landing_audit_snapshot.json">查看预览</a></article>
            </div>
          </section>

          <section class="tab-panel" id="api" data-panel data-search="api endpoints GET only workflow status run preview research report framework data source dry run" data-kind="api">
            <article class="collapsible card"><button class="collapse-toggle" type="button">MVP GET endpoints <span>折叠</span></button><div class="collapse-body endpoint-grid">{endpoints}</div></article>
          </section>

          <section class="tab-panel" id="reports" data-panel data-search="reports GLD SLV NO_REAL_MARKET_DATA operator packet telegram preview" data-kind="report workflow">
            <div class="source-grid">
              <article class="source-card"><strong>reports/local_research_report_framework_GLD_SLV.md</strong><p class="muted">研究框架，不含方向性建议和价格字段。</p></article>
              <article class="source-card"><strong>reports/operator_daily_packet_preview.md</strong><p class="muted">本地 operator packet preview，不含交易指令。</p></article>
              <article class="source-card"><strong>reports/telegram_preview_local_only.md</strong><p class="muted">本地 markdown preview，不实发。</p></article>
            </div>
          </section>

          <section class="tab-panel" id="risk" data-panel data-search="risk disabled 禁用 真实刷新行情 读取账户 发送 Telegram 生成交易信号" data-kind="risk">
            <article class="collapsible card"><button class="collapse-toggle" type="button">危险动作固定禁用 <span>折叠</span></button><div class="collapse-body risk-list">
              <button class="disabled-action" type="button" disabled title="本阶段禁止真实刷新行情">真实刷新行情</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止读取账户">读取账户</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止发送 Telegram">发送 Telegram</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止生成交易信号">生成交易信号</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止连接 IBKR">连接 IBKR</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止请求历史数据">请求历史数据</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止下单">下单</button>
              <button class="disabled-action" type="button" disabled title="本阶段禁止撤单">撤单</button>
            </div></article>
          </section>

          <section class="tab-panel" id="artifacts" data-panel data-search="artifact files json csv reports pack" data-kind="json report">
            <article class="collapsible card"><button class="collapse-toggle" type="button">artifact 文件流 <span>折叠</span></button><div class="collapse-body file-stream">
{cards}
            </div></article>
          </section>

          <section class="tab-panel" id="audit" data-panel data-search="final audit LOCAL_PLATFORM_MVP_FINAL_AUDIT_READY terminal startup fallback only" data-kind="workflow risk">
            <article class="panel"><div class="panel-header"><div><span class="eyebrow">Final landing audit</span><h2>LOCAL_PLATFORM_MVP_FINAL_AUDIT_READY</h2></div><span class="token safe">PASS</span></div><strong class="big-copy">all_external_actions_blocked=YES</strong><p class="muted">ui_driven_workbench_ready=YES · terminal_role=STARTUP_AND_FALLBACK_ONLY · JP / CN remain frozen</p></article>
          </section>
        </main>
      </div>
    </div>
    <footer class="footer-safety-bar">GET only · local artifact preview · no real market data · no source connection · no trading · no Telegram real send</footer>
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
    return (
        build_previous_dashboard_css()
        + """

/* Phase 801-1000 UI-driven local research platform MVP additions */
.workbench-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}
.workbench-card {
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 8px;
  padding: 18px;
  background: rgba(15, 23, 42, 0.78);
  min-height: 190px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.workbench-card h2 {
  margin: 0;
  font-size: 1rem;
}
.endpoint-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 10px;
}
.endpoint-pill {
  display: block;
  padding: 10px 12px;
  border: 1px solid rgba(34, 197, 94, 0.24);
  border-radius: 8px;
  background: rgba(22, 101, 52, 0.18);
  color: #bbf7d0;
  overflow-wrap: anywhere;
}
"""
    )


def build_report(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    return f"""# Phase 801-1000 UI-driven Local Research Platform MVP Pack

- status: {STATUS}
- UI-driven local research platform MVP
- local workflow automation ready
- GLD / SLV research report framework ready
- US GLD / SLV data source dry-run ready
- operator daily packet preview ready
- Telegram preview local-only ready
- watchlist policy ready
- final landing audit ready
- terminal role reduced to startup and fallback only
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
- no price-level guidance
- market data remains BLOCKED_BY_SUBSCRIPTION / IBKR_ERROR_10089
- GLD / SLV only
- JP / CN remain frozen
- generated_at_utc: {timestamp}
"""


def build_pack_markdown(generated_at: Optional[str] = None) -> str:
    return build_report(generated_at)


def generate_ui_driven_local_research_platform_mvp_pack(
    output_dashboard_index: PathLike = DASHBOARD_INDEX,
    output_dashboard_css: PathLike = DASHBOARD_CSS,
    output_status_snapshot: PathLike = STATUS_SNAPSHOT,
    output_artifact_manifest: PathLike = ARTIFACT_MANIFEST,
    output_csv: PathLike = OUTPUT_CSV,
    output_report: PathLike = OUTPUT_REPORT,
    output_pack: PathLike = OUTPUT_PACK,
    generated_at: Optional[str] = None,
) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    status = build_status_snapshot(timestamp)
    row = {field: status.get(field, "") for field in CSV_FIELDS}

    run_local_workflow(generated_at=timestamp)
    _write_json(RESEARCH_REPORT_BUILDER_SNAPSHOT, build_research_report_builder_snapshot(timestamp))
    _write_json(UI_MVP_ENDPOINT_REGISTRY_SNAPSHOT, build_ui_mvp_endpoint_registry_snapshot(timestamp))
    _write_json(UI_MVP_WORKFLOW_CONTRACT_SNAPSHOT, build_ui_mvp_workflow_contract_snapshot(timestamp))
    _write_json(LOCAL_RESEARCH_PLATFORM_MVP_STATUS_SNAPSHOT, build_local_research_platform_mvp_status_snapshot(timestamp))
    _write_json(FINAL_LANDING_AUDIT_SNAPSHOT, build_final_landing_audit_snapshot(timestamp))

    _write_text(output_dashboard_index, build_dashboard_html(timestamp))
    _write_text(output_dashboard_css, build_dashboard_css())
    _write_json(output_status_snapshot, status)
    _write_json(output_artifact_manifest, build_artifact_manifest(timestamp))
    _write_json(BUILD_SNAPSHOT, build_build_snapshot(timestamp))
    _write_json(OPERATOR_TIMELINE, build_operator_timeline(timestamp))
    _write_json(LOCAL_BACKEND_API_SHELL_SNAPSHOT, build_local_backend_api_shell_snapshot(timestamp))
    _write_json("dashboard/data/api_endpoint_registry_snapshot.json", build_api_endpoint_registry_snapshot(timestamp))
    _write_json(API_READONLY_GUARD_SNAPSHOT, build_api_readonly_guard_snapshot(timestamp))
    _write_json(API_RUNTIME_CONTRACT_SNAPSHOT, build_api_runtime_contract_snapshot(timestamp))
    _write_json(LOCAL_UI_SERVER_RUNBOOK_SNAPSHOT, build_local_ui_server_runbook_snapshot(timestamp))
    _write_json(OPERATOR_NEXT_ACTIONS_SNAPSHOT, build_operator_next_actions_snapshot(timestamp))
    _write_json(NEXT_ROADMAP_SNAPSHOT, build_next_roadmap_snapshot(timestamp))
    _write_json(MARKET_DATA_SOURCE_DECISION_SNAPSHOT, build_market_data_source_decision_snapshot(timestamp))
    _write_json(MARKET_SCOPE_STATUS_SNAPSHOT, build_market_scope_status_snapshot(timestamp))
    _write_text(OUTPUT_RESEARCH_REPORT, build_research_report_markdown(timestamp))
    _write_text(OUTPUT_DAILY_PACKET, build_operator_daily_packet_markdown(timestamp))
    _write_text(OUTPUT_TELEGRAM_PREVIEW, build_telegram_preview_markdown(timestamp))

    csv_path = Path(output_csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)
    _write_text(output_report, build_report(timestamp))
    _write_text(output_pack, build_pack_markdown(timestamp))
    return row


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 801-1000 UI-driven local research platform MVP pack.")
    parser.parse_args(argv)
    row = generate_ui_driven_local_research_platform_mvp_pack()
    print("[UI_DRIVEN_LOCAL_RESEARCH_PLATFORM_MVP_PACK] generated")
    print(f"phase={row['phase']}")
    print(f"status={row['status']}")
    print(f"local_platform_mvp_status={row['local_platform_mvp_status']}")
    print(f"local_workflow_status={row['local_workflow_status']}")
    print(f"research_report_builder_status={row['research_report_builder_status']}")
    print(f"data_source_dry_run_status={row['data_source_dry_run_status']}")
    print(f"operator_packet_status={row['operator_packet_status']}")
    print(f"telegram_preview_status={row['telegram_preview_status']}")
    print(f"watchlist_policy_status={row['watchlist_policy_status']}")
    print(f"final_landing_audit_status={row['final_landing_audit_status']}")
    print(f"csv={OUTPUT_CSV}")
    print(f"report={OUTPUT_REPORT}")
    print(f"pack={OUTPUT_PACK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
