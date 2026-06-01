from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from src.operator_productized_ui_user_surface_cleanup_pack import (
    PRIMARY_NAVIGATION,
    STATUS,
    USER_SAFETY_COPY,
    build_developer_mode_visibility_snapshot,
    build_primary_navigation_snapshot,
    build_status_snapshot,
    build_user_facing_safety_copy_snapshot,
)


REPO_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_UI_TERMS = ("fetch(", "XMLHttpRequest", "WebSocket", "http://", "https://", "TradingView", "iframe")
TECHNICAL_TERMS = (
    "UI_DRIVEN_LOCAL_RESEARCH_PLATFORM_MVP_READY",
    "PRODUCTIZED_UI_PUBLIC_DATA_INTAKE_READY",
    "BLOCKED_BY_SUBSCRIPTION",
    "IBKR_ERROR_10089",
    "GET_ONLY",
    "CLI fallback",
    "python3 main.py",
    "source_connection_implemented",
    "live_market_data_enabled",
)
CODE_LIKE_SAFETY_COPY = (
    "no source -> no price",
    "no price -> no signal",
    "no approved terms -> no automated ingestion",
    "no verified freshness -> framework only",
)
FORBIDDEN_INTEGRATION_TERMS = (
    "ib_insync",
    "reqMktData",
    "reqHistoricalData",
    "placeOrder",
    "accountSummary",
    "positions",
    "telegram send",
)


def _developer_details(html: str) -> re.Match[str]:
    match = re.search(r"<details class=\"developer-details\">(?P<body>.*?)</details>", html, re.S)
    assert match is not None
    return match


def test_productized_ui_user_surface_cleanup_cli_succeeds() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "main.py"), "--productized-ui-user-surface-cleanup-pack"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert STATUS in result.stdout
    assert "user_surface_cleanup_status=USER_SURFACE_CLEANUP_READY" in result.stdout


def test_dashboard_primary_surface_contains_user_workbench_content() -> None:
    html = (REPO_ROOT / "dashboard/index.html").read_text(encoding="utf-8")

    for text in (
        "AI 投研工作台",
        "本地投研工作台已就绪",
        "标的观察",
        "数据源",
        "本地报告",
        "风险边界",
        "当前支持 GLD / SLV 研究框架",
        "数据源状态：准备中",
        "当前未启用实时行情",
        "当前不会读取账户、持仓或发送交易指令",
    ):
        assert text in html


def test_primary_navigation_is_user_facing_and_omits_next_action_menu() -> None:
    html = (REPO_ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    nav_match = re.search(r"<nav class=\"sidebar-nav\".*?>(?P<body>.*?)</nav>", html, re.S)
    assert nav_match is not None
    nav_body = nav_match.group("body")

    for label in PRIMARY_NAVIGATION:
        assert label in nav_body
    assert "下一步操作" not in nav_body
    assert "下一步操作" not in html


def test_technical_terms_are_only_inside_collapsed_advanced_details() -> None:
    html = (REPO_ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    details = _developer_details(html)
    before_details = html[: details.start()]
    details_body = details.group("body")

    for term in TECHNICAL_TERMS:
        assert term not in before_details
        assert term in details_body
    assert "<summary>高级信息</summary>" in details.group(0)


def test_safety_rules_are_user_facing_chinese_copy() -> None:
    html = (REPO_ROOT / "dashboard/index.html").read_text(encoding="utf-8")

    for text in USER_SAFETY_COPY:
        assert text in html
    for text in CODE_LIKE_SAFETY_COPY:
        assert text not in html


def test_snapshots_record_cleanup_navigation_and_developer_visibility() -> None:
    status = json.loads((REPO_ROOT / "dashboard/data/status_snapshot.json").read_text(encoding="utf-8"))
    nav = json.loads((REPO_ROOT / "dashboard/data/primary_navigation_snapshot.json").read_text(encoding="utf-8"))
    developer = json.loads((REPO_ROOT / "dashboard/data/developer_mode_visibility_snapshot.json").read_text(encoding="utf-8"))
    safety = json.loads((REPO_ROOT / "dashboard/data/user_facing_safety_copy_snapshot.json").read_text(encoding="utf-8"))

    assert status["status"] == STATUS
    assert build_status_snapshot("2026-06-01T00:00:00+00:00")["status"] == STATUS
    assert nav["navigation"] == list(PRIMARY_NAVIGATION)
    assert nav == build_primary_navigation_snapshot(nav["generated_at_utc"])
    assert developer["default_visibility"] == "COLLAPSED"
    assert build_developer_mode_visibility_snapshot(developer["generated_at_utc"])["surface_priority"] == "LOW"
    assert safety["copy"] == list(USER_SAFETY_COPY)
    assert build_user_facing_safety_copy_snapshot(safety["generated_at_utc"])["code_like_rule_copy_visible"] == "NO"


def test_dashboard_omits_remote_request_patterns() -> None:
    html = (REPO_ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    css = (REPO_ROOT / "dashboard/assets/style.css").read_text(encoding="utf-8")

    for term in FORBIDDEN_UI_TERMS:
        assert term not in html
        assert term not in css


def test_cleanup_runtime_source_omits_blocked_integrations() -> None:
    source = (REPO_ROOT / "src/operator_productized_ui_user_surface_cleanup_pack.py").read_text(encoding="utf-8")

    for term in FORBIDDEN_INTEGRATION_TERMS:
        assert term not in source
