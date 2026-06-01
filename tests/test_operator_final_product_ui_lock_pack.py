from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from src.operator_final_product_ui_lock_pack import (
    NAVIGATION,
    STATUS,
    build_final_product_ui_lock_snapshot,
    build_status_snapshot,
)


REPO_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_REMOTE_TERMS = (
    "http://",
    "https://",
    "cdn",
    "@import",
    "script src",
    "fetch(",
    "XMLHttpRequest",
    "WebSocket",
    "TradingView",
    "iframe",
)
HIDDEN_TECHNICAL_TERMS = (
    "PRODUCTIZED_UI_USER_SURFACE_CLEANUP_READY",
    "PRODUCTIZED_UI_PUBLIC_DATA_INTAKE_READY",
    "UI_DRIVEN_LOCAL_RESEARCH_PLATFORM_MVP_READY",
    "BLOCKED_BY_SUBSCRIPTION",
    "IBKR_ERROR_10089",
    "GET_ONLY",
    "python3 main.py",
    "CLI fallback",
    "source_connection_implemented",
    "live_market_data_enabled",
)
FORBIDDEN_SIGNAL_TERMS = (
    "BUY",
    "SELL",
    "HOLD",
    "买入",
    "卖出",
    "持有",
    "target_price",
    "stop_loss",
    "take_profit",
    "目标价",
    "止损",
    "止盈",
)
FORBIDDEN_PRICE_KEYS = ("last_price", "bid", "ask", "open", "high", "low", "close")


def _advanced_details(html: str) -> re.Match[str]:
    match = re.search(r"<details class=\"advanced-mode\">(?P<body>.*?)</details>", html, re.S)
    assert match is not None
    return match


def test_final_product_ui_lock_cli_succeeds() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "main.py"), "--final-product-ui-lock-pack"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert STATUS in result.stdout
    assert "ui_final_locked=YES" in result.stdout
    assert "developer_mode=COLLAPSED_IN_SETTINGS" in result.stdout


def test_dashboard_contains_final_product_surface() -> None:
    html = (REPO_ROOT / "dashboard/index.html").read_text(encoding="utf-8")

    for text in (
        "AI 投研工作台",
        "总览",
        "标的观察",
        "数据源",
        "本地报告",
        "风险边界",
        "设置",
        "本地工作台已就绪",
        "GLD",
        "SLV",
        "等待数据源",
        "只读安全模式",
    ):
        assert text in html


def test_primary_surface_hides_technical_terms() -> None:
    html = (REPO_ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    details = _advanced_details(html)
    primary_surface = html[: details.start()]
    advanced_body = details.group("body")

    assert "下一步操作" not in html
    for term in HIDDEN_TECHNICAL_TERMS:
        assert term not in primary_surface
        assert term in advanced_body


def test_final_navigation_snapshot_is_locked() -> None:
    nav = json.loads((REPO_ROOT / "dashboard/data/final_navigation_snapshot.json").read_text(encoding="utf-8"))

    assert nav["navigation"] == list(NAVIGATION)
    assert "下一步操作" not in nav["navigation"]


def test_final_lock_snapshot_contains_required_flags() -> None:
    snapshot = json.loads((REPO_ROOT / "dashboard/data/final_product_ui_lock_snapshot.json").read_text(encoding="utf-8"))
    model = build_final_product_ui_lock_snapshot(snapshot["generated_at_utc"])
    status = build_status_snapshot(snapshot["generated_at_utc"])

    assert snapshot == model
    assert snapshot["status"] == STATUS
    assert snapshot["ui_final_locked"] == "YES"
    assert snapshot["template_reference_mode"] == "INSPIRED_ONLY_NO_CODE_COPIED"
    assert snapshot["external_assets_used"] == "NO"
    assert status["status"] == STATUS
    assert status["ui_generation"] == "V12_FINAL_PRODUCT_UI_LOCK"


def test_dashboard_and_css_have_no_remote_or_auto_request_patterns() -> None:
    html = (REPO_ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    css = (REPO_ROOT / "dashboard/assets/style.css").read_text(encoding="utf-8")

    for term in FORBIDDEN_REMOTE_TERMS:
        assert term not in html
        assert term not in css


def test_final_outputs_omit_price_value_fields_and_trading_signal_terms() -> None:
    paths = [
        REPO_ROOT / "dashboard/index.html",
        REPO_ROOT / "dashboard/data/final_product_ui_lock_snapshot.json",
        REPO_ROOT / "dashboard/data/final_navigation_snapshot.json",
        REPO_ROOT / "dashboard/data/final_dashboard_layout_snapshot.json",
        REPO_ROOT / "dashboard/data/final_visual_system_snapshot.json",
        REPO_ROOT / "dashboard/data/final_user_workflow_snapshot.json",
        REPO_ROOT / "dashboard/data/final_ui_regression_guard_snapshot.json",
        REPO_ROOT / "reports/operator_final_product_ui_lock_pack_report.md",
        REPO_ROOT / "reports/final_product_ui_user_guide.md",
        REPO_ROOT / "Precious_Metals_Monitor_Final_Product_UI_Lock_Pack.md",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)

    for term in FORBIDDEN_SIGNAL_TERMS:
        assert term not in combined
    for key in FORBIDDEN_PRICE_KEYS:
        assert f'"{key}"' not in combined
        assert f"{key}:" not in combined


def test_status_snapshot_contains_final_guardrails() -> None:
    status = json.loads((REPO_ROOT / "dashboard/data/status_snapshot.json").read_text(encoding="utf-8"))

    assert status["phase"] == "Phase 1161-1320"
    assert status["status"] == STATUS
    assert status["ui_final_locked"] == "YES"
    for key in (
        "source_connection_implemented",
        "live_market_data_enabled",
        "realtime_market_data_verified",
        "production_ready",
        "trading_enabled",
        "account_read_enabled",
        "positions_read_enabled",
        "historical_data_enabled",
        "telegram_real_send_enabled",
    ):
        assert status[key] == "NO"
