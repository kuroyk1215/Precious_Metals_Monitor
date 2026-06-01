from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from src.operator_productized_ui_public_data_intake_pack import STATUS, build_status_snapshot


REPO_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_UI_TERMS = ("fetch(", "XMLHttpRequest", "WebSocket", "http://", "https://", "TradingView", "iframe")
FORBIDDEN_INTEGRATION_TERMS = (
    "ib_insync",
    "reqMktData",
    "reqHistoricalData",
    "placeOrder",
    "accountSummary",
    "positions",
    "telegram send",
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


def test_productized_ui_public_data_intake_pack_cli_succeeds() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "main.py"), "--productized-ui-public-data-intake-pack"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert STATUS in result.stdout
    assert "public_data_intake_status=PUBLIC_DATA_INTAKE_PREPARATION_READY" in result.stdout
    assert "real_price_ingestion_enabled=NO" in result.stdout


def test_dashboard_contains_productized_workbench_sections() -> None:
    html = (REPO_ROOT / "dashboard/index.html").read_text(encoding="utf-8")

    for text in (
        "AI 投研工作台",
        "本地只读研究平台",
        "今日状态",
        "GLD / SLV 研究框架",
        "数据源状态",
        "本地报告",
        "风险边界",
        "下一步操作",
        "公共行情导入准备",
    ):
        assert text in html


def test_technical_status_is_only_in_developer_details() -> None:
    html = (REPO_ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    details_match = re.search(r"<details class=\"developer-details\">(?P<body>.*?)</details>", html, re.S)

    assert details_match is not None
    before_details = html[: details_match.start()]
    details_body = details_match.group("body")
    for text in (
        "UI_DRIVEN_LOCAL_RESEARCH_PLATFORM_MVP_READY",
        "BLOCKED_BY_SUBSCRIPTION",
        "IBKR_ERROR_10089",
        "GET_ONLY",
        "CLI fallback",
        "source_connection_implemented",
        "live_market_data_enabled",
    ):
        assert text not in before_details
        assert text in details_body


def test_dashboard_omits_remote_and_auto_request_patterns() -> None:
    html = (REPO_ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    css = (REPO_ROOT / "dashboard/assets/style.css").read_text(encoding="utf-8")

    for term in FORBIDDEN_UI_TERMS:
        assert term not in html
        assert term not in css


def test_status_snapshot_contains_phase_1001_1120_guardrails() -> None:
    status = json.loads((REPO_ROOT / "dashboard/data/status_snapshot.json").read_text(encoding="utf-8"))
    model = build_status_snapshot("2026-06-01T00:00:00+00:00")

    assert status["status"] == STATUS
    for key in (
        "public_data_connection_implemented",
        "external_market_data_request_enabled",
        "real_price_ingestion_enabled",
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
        assert model[key] == "NO"
    assert status["market_data_status"] == "BLOCKED_BY_SUBSCRIPTION"


def test_generated_outputs_omit_real_price_keys_and_trade_signal_terms() -> None:
    paths = [
        REPO_ROOT / "dashboard/index.html",
        REPO_ROOT / "dashboard/data/productized_ui_snapshot.json",
        REPO_ROOT / "dashboard/data/public_data_intake_preparation_snapshot.json",
        REPO_ROOT / "dashboard/data/public_market_data_source_candidates_snapshot.json",
        REPO_ROOT / "dashboard/data/public_data_safety_guard_snapshot.json",
        REPO_ROOT / "reports/operator_productized_ui_public_data_intake_pack_report.md",
        REPO_ROOT / "reports/public_data_intake_preparation_report.md",
        REPO_ROOT / "reports/productized_ui_user_guide.md",
        REPO_ROOT / "Precious_Metals_Monitor_Productized_UI_Public_Data_Intake_Preparation_Pack.md",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)

    for term in FORBIDDEN_SIGNAL_TERMS:
        assert term not in combined
    for key in FORBIDDEN_PRICE_KEYS:
        assert f'"{key}"' not in combined
        assert f"{key}:" not in combined

    contract = (REPO_ROOT / "dashboard/data/public_data_field_contract_snapshot.json").read_text(encoding="utf-8")
    assert "last_price_status" in contract
    assert '"last_price"' not in contract


def test_productized_runtime_sources_omit_blocked_integrations() -> None:
    for path in (
        REPO_ROOT / "src/local_backend_api_shell.py",
        REPO_ROOT / "src/local_workflow_automation.py",
        REPO_ROOT / "src/operator_productized_ui_public_data_intake_pack.py",
        REPO_ROOT / "src/productized_ui_content_model.py",
        REPO_ROOT / "src/public_data_intake_preparation.py",
    ):
        source = path.read_text(encoding="utf-8")
        for term in FORBIDDEN_INTEGRATION_TERMS:
            assert term not in source
