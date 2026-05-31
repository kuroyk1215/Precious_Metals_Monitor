from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from src.operator_dashboard_ui_static_visual_freeze_pack import (
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    CARD_SYSTEM_SNAPSHOT,
    CHINESE_UI_SNAPSHOT,
    DASHBOARD_CSS,
    DASHBOARD_INDEX,
    HIGH_TECH_VISUAL_SNAPSHOT,
    ICON_SYSTEM_SNAPSHOT,
    LAYOUT_SNAPSHOT,
    NAVIGATION_SNAPSHOT,
    OPERATOR_TIMELINE,
    OUTPUT_CSV,
    OUTPUT_PACK,
    OUTPUT_REPORT,
    RISK_SNAPSHOT,
    SIGNAL_SNAPSHOT,
    STATIC_CHART_SNAPSHOT,
    STATIC_VISUAL_FREEZE_SNAPSHOT,
    STATUS,
    STATUS_SNAPSHOT,
    TEMPLATE_REFERENCE_SNAPSHOT,
    TIMELINE_POLISH_SNAPSHOT,
    TRADING_SHELL_SNAPSHOT,
    UI_QA_SNAPSHOT,
    VISUAL_DENSITY_SNAPSHOT,
    VISUAL_REGRESSION_GUARD_SNAPSHOT,
    WATCHLIST_SNAPSHOT,
    generate_dashboard_ui_static_visual_freeze_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[1]

TARGET_ARTIFACTS = (
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    STATUS_SNAPSHOT,
    UI_QA_SNAPSHOT,
    STATIC_VISUAL_FREEZE_SNAPSHOT,
    VISUAL_REGRESSION_GUARD_SNAPSHOT,
    HIGH_TECH_VISUAL_SNAPSHOT,
    TRADING_SHELL_SNAPSHOT,
    STATIC_CHART_SNAPSHOT,
    CHINESE_UI_SNAPSHOT,
    TEMPLATE_REFERENCE_SNAPSHOT,
    VISUAL_DENSITY_SNAPSHOT,
    CARD_SYSTEM_SNAPSHOT,
    ICON_SYSTEM_SNAPSHOT,
    TIMELINE_POLISH_SNAPSHOT,
    WATCHLIST_SNAPSHOT,
    SIGNAL_SNAPSHOT,
    RISK_SNAPSHOT,
    LAYOUT_SNAPSHOT,
    NAVIGATION_SNAPSHOT,
    BUILD_SNAPSHOT,
    OPERATOR_TIMELINE,
    ARTIFACT_MANIFEST,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)


def _generate(tmp_path: Path) -> None:
    generate_dashboard_ui_static_visual_freeze_pack(
        output_index=tmp_path / DASHBOARD_INDEX,
        output_css=tmp_path / DASHBOARD_CSS,
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_ui_qa_snapshot=tmp_path / UI_QA_SNAPSHOT,
        output_static_visual_freeze_snapshot=tmp_path / STATIC_VISUAL_FREEZE_SNAPSHOT,
        output_visual_regression_guard_snapshot=tmp_path / VISUAL_REGRESSION_GUARD_SNAPSHOT,
        output_high_tech_visual_snapshot=tmp_path / HIGH_TECH_VISUAL_SNAPSHOT,
        output_trading_shell_snapshot=tmp_path / TRADING_SHELL_SNAPSHOT,
        output_static_chart_snapshot=tmp_path / STATIC_CHART_SNAPSHOT,
        output_chinese_ui_snapshot=tmp_path / CHINESE_UI_SNAPSHOT,
        output_template_reference_snapshot=tmp_path / TEMPLATE_REFERENCE_SNAPSHOT,
        output_visual_density_snapshot=tmp_path / VISUAL_DENSITY_SNAPSHOT,
        output_card_system_snapshot=tmp_path / CARD_SYSTEM_SNAPSHOT,
        output_icon_system_snapshot=tmp_path / ICON_SYSTEM_SNAPSHOT,
        output_timeline_polish_snapshot=tmp_path / TIMELINE_POLISH_SNAPSHOT,
        output_watchlist_snapshot=tmp_path / WATCHLIST_SNAPSHOT,
        output_signal_snapshot=tmp_path / SIGNAL_SNAPSHOT,
        output_risk_snapshot=tmp_path / RISK_SNAPSHOT,
        output_layout_snapshot=tmp_path / LAYOUT_SNAPSHOT,
        output_navigation_snapshot=tmp_path / NAVIGATION_SNAPSHOT,
        output_build_snapshot=tmp_path / BUILD_SNAPSHOT,
        output_operator_timeline=tmp_path / OPERATOR_TIMELINE,
        output_artifact_manifest=tmp_path / ARTIFACT_MANIFEST,
        output_csv=tmp_path / OUTPUT_CSV,
        output_report=tmp_path / OUTPUT_REPORT,
        output_pack=tmp_path / OUTPUT_PACK,
        generated_at="2026-05-31T00:00:00+00:00",
    )


def test_builder_generates_all_target_artifacts(tmp_path: Path) -> None:
    row = generate_dashboard_ui_static_visual_freeze_pack(
        output_index=tmp_path / DASHBOARD_INDEX,
        output_css=tmp_path / DASHBOARD_CSS,
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_ui_qa_snapshot=tmp_path / UI_QA_SNAPSHOT,
        output_static_visual_freeze_snapshot=tmp_path / STATIC_VISUAL_FREEZE_SNAPSHOT,
        output_visual_regression_guard_snapshot=tmp_path / VISUAL_REGRESSION_GUARD_SNAPSHOT,
        output_high_tech_visual_snapshot=tmp_path / HIGH_TECH_VISUAL_SNAPSHOT,
        output_trading_shell_snapshot=tmp_path / TRADING_SHELL_SNAPSHOT,
        output_static_chart_snapshot=tmp_path / STATIC_CHART_SNAPSHOT,
        output_chinese_ui_snapshot=tmp_path / CHINESE_UI_SNAPSHOT,
        output_template_reference_snapshot=tmp_path / TEMPLATE_REFERENCE_SNAPSHOT,
        output_visual_density_snapshot=tmp_path / VISUAL_DENSITY_SNAPSHOT,
        output_card_system_snapshot=tmp_path / CARD_SYSTEM_SNAPSHOT,
        output_icon_system_snapshot=tmp_path / ICON_SYSTEM_SNAPSHOT,
        output_timeline_polish_snapshot=tmp_path / TIMELINE_POLISH_SNAPSHOT,
        output_watchlist_snapshot=tmp_path / WATCHLIST_SNAPSHOT,
        output_signal_snapshot=tmp_path / SIGNAL_SNAPSHOT,
        output_risk_snapshot=tmp_path / RISK_SNAPSHOT,
        output_layout_snapshot=tmp_path / LAYOUT_SNAPSHOT,
        output_navigation_snapshot=tmp_path / NAVIGATION_SNAPSHOT,
        output_build_snapshot=tmp_path / BUILD_SNAPSHOT,
        output_operator_timeline=tmp_path / OPERATOR_TIMELINE,
        output_artifact_manifest=tmp_path / ARTIFACT_MANIFEST,
        output_csv=tmp_path / OUTPUT_CSV,
        output_report=tmp_path / OUTPUT_REPORT,
        output_pack=tmp_path / OUTPUT_PACK,
        generated_at="2026-05-31T00:00:00+00:00",
    )

    for relative_path in TARGET_ARTIFACTS:
        assert (tmp_path / relative_path).exists()
    assert row["status"] == STATUS


def test_cli_generates_pack_without_external_actions(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--dashboard-ui-static-visual-freeze-pack"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert "status=DASHBOARD_UI_STATIC_VISUAL_FREEZE_READY" in result.stdout
    assert "ui_generation=V7_HIGH_TECH_TRADING_VISUAL_FROZEN" in result.stdout
    assert "market_data_status=BLOCKED_BY_SUBSCRIPTION" in result.stdout
    assert "realtime_market_data_verified=NO" in result.stdout
    assert "production_ready=NO" in result.stdout
    assert "trading_enabled=NO" in result.stdout
    for relative_path in TARGET_ARTIFACTS:
        assert (tmp_path / relative_path).exists()


def test_dashboard_index_keeps_v7_chinese_static_markers(tmp_path: Path) -> None:
    _generate(tmp_path)
    html = (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8")

    for marker in (
        "AI 投研交易驾驶舱",
        "贵金属观察系统",
        "总览",
        "市场观察",
        "图表面板",
        "信号状态",
        "风险边界",
        "本地文件流",
        "项目进度轨道",
        "版本与安全",
        "静态占位",
        "无实时行情",
        "未连接 IBKR",
        "未请求行情",
    ):
        assert marker in html


def test_dashboard_css_keeps_dark_css_only_trading_tokens(tmp_path: Path) -> None:
    _generate(tmp_path)
    css = (tmp_path / DASHBOARD_CSS).read_text(encoding="utf-8")

    for marker in (
        "color-scheme: dark",
        "chart-shell",
        "background-size",
        "risk-red",
        "safe-green",
        "amber",
        "cyan",
    ):
        assert marker in css


def test_html_css_and_runtime_json_do_not_load_external_resources(tmp_path: Path) -> None:
    _generate(tmp_path)
    checked_paths = [
        relative_path
        for relative_path in TARGET_ARTIFACTS
        if relative_path.endswith((".html", ".css", ".json"))
        and relative_path != VISUAL_REGRESSION_GUARD_SNAPSHOT
    ]
    combined = "\n".join((tmp_path / relative_path).read_text(encoding="utf-8") for relative_path in checked_paths)

    for marker in ("http://", "https://", "cdn", "@import", "script src", "TradingView", "iframe"):
        assert marker not in combined


def test_ui_qa_snapshot_records_pass_checks(tmp_path: Path) -> None:
    _generate(tmp_path)
    snapshot = json.loads((tmp_path / UI_QA_SNAPSHOT).read_text(encoding="utf-8"))

    assert snapshot["status"] == "STATIC_UI_QA_PASS"
    assert snapshot["external_resource_check"] == "PASS"
    assert snapshot["forbidden_trading_output_check"] == "PASS"
    assert snapshot["forbidden_price_field_check"] == "PASS"


def test_static_visual_freeze_snapshot_records_visual_contract(tmp_path: Path) -> None:
    _generate(tmp_path)
    snapshot = json.loads((tmp_path / STATIC_VISUAL_FREEZE_SNAPSHOT).read_text(encoding="utf-8"))

    assert snapshot["status"] == "STATIC_VISUAL_BASELINE_FROZEN"
    assert snapshot["frozen_ui_generation"] == "V7_HIGH_TECH_TRADING_VISUAL"
    assert "DARK_FINTECH_TRADING_DASHBOARD" in snapshot["visual_contract"]
    assert "CSS_ONLY_DARK_GRID_SURFACE" in snapshot["visual_contract"]


def test_visual_regression_guard_snapshot_records_markers(tmp_path: Path) -> None:
    _generate(tmp_path)
    snapshot = json.loads((tmp_path / VISUAL_REGRESSION_GUARD_SNAPSHOT).read_text(encoding="utf-8"))

    assert snapshot["status"] == "VISUAL_REGRESSION_GUARD_READY"
    assert snapshot["guard_mode"] == "STATIC_TEXT_AND_STRUCTURE_GUARD"
    assert "protected_markers" in snapshot
    assert "forbidden_markers" in snapshot
    assert "AI 投研交易驾驶舱" in snapshot["protected_markers"]
    assert "http://" in snapshot["forbidden_markers"]


def test_status_snapshot_preserves_freeze_and_safety_flags(tmp_path: Path) -> None:
    _generate(tmp_path)
    status = json.loads((tmp_path / STATUS_SNAPSHOT).read_text(encoding="utf-8"))

    assert status["status"] == "DASHBOARD_UI_STATIC_VISUAL_FREEZE_READY"
    assert status["ui_generation"] == "V7_HIGH_TECH_TRADING_VISUAL_FROZEN"
    assert status["visual_freeze_status"] == "STATIC_VISUAL_BASELINE_FROZEN"
    assert status["ui_qa_status"] == "STATIC_UI_QA_PASS"
    assert status["market_data_status"] == "BLOCKED_BY_SUBSCRIPTION"
    for key in (
        "realtime_market_data_verified",
        "production_ready",
        "trading_enabled",
        "account_read_enabled",
        "positions_read_enabled",
        "historical_data_enabled",
        "telegram_real_send_enabled",
    ):
        assert status[key] == "NO"


def test_watchlist_omits_live_price_fields(tmp_path: Path) -> None:
    _generate(tmp_path)
    watchlist_text = (tmp_path / WATCHLIST_SNAPSHOT).read_text(encoding="utf-8")

    for forbidden in ("last_price", "bid", "ask", "open", "high", "low", "close", "price"):
        assert forbidden not in watchlist_text


def test_signal_snapshot_and_html_omit_forbidden_trading_outputs(tmp_path: Path) -> None:
    _generate(tmp_path)
    combined = "\n".join(
        (
            (tmp_path / SIGNAL_SNAPSHOT).read_text(encoding="utf-8"),
            (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8"),
        )
    )

    for forbidden in (
        "BUY",
        "SELL",
        "HOLD",
        "target_price",
        "stop_loss",
        "take_profit",
        "买入",
        "卖出",
        "持有",
        "目标价",
        "止损",
        "止盈",
    ):
        assert forbidden not in combined


def test_risk_snapshot_contains_all_blocked_actions_with_allowed_no(tmp_path: Path) -> None:
    _generate(tmp_path)
    risk = json.loads((tmp_path / RISK_SNAPSHOT).read_text(encoding="utf-8"))
    html = (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8")
    actions = {
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
    }

    assert {item["action"] for item in risk["permissions"]} == actions
    assert all(item["allowed"] == "NO" for item in risk["permissions"])
    for action in actions:
        assert action in html


def test_artifact_manifest_uses_local_fields_without_file_metadata(tmp_path: Path) -> None:
    _generate(tmp_path)
    manifest = json.loads((tmp_path / ARTIFACT_MANIFEST).read_text(encoding="utf-8"))

    for artifact in manifest["artifacts"]:
        assert artifact["external_effect"] == "NONE_LOCAL_ARTIFACT_GENERATION_ONLY"
        assert "http://" not in artifact["local_href"]
        assert "https://" not in artifact["local_href"]
        assert "icon_token" in artifact
        assert "file_size" not in artifact
        assert "mtime" not in artifact


def test_generated_flow_does_not_touch_forbidden_local_files() -> None:
    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    ).stdout
    unexpected = [
        line
        for line in status.splitlines()
        if line.endswith("config.yaml") or line.endswith("ibkr_market_data_api_errors.csv")
    ]
    assert unexpected in ([" M config.yaml", "?? ibkr_market_data_api_errors.csv"], [" M config.yaml"], [])
