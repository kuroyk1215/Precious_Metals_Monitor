from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from src.operator_interactive_local_research_platform_ui_shell_pack import (
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    DASHBOARD_CSS,
    DASHBOARD_INDEX,
    INTERACTIVE_UI_SHELL_SNAPSHOT,
    LOCAL_PLATFORM_SHELL_STATUS_SNAPSHOT,
    OUTPUT_CSV,
    OUTPUT_PACK,
    OUTPUT_REPORT,
    STATUS,
    STATUS_SNAPSHOT,
    UI_DISABLED_ACTIONS_SNAPSHOT,
    UI_FILTER_TABS_SNAPSHOT,
    UI_INTERACTION_CONTRACT_SNAPSHOT,
    generate_interactive_local_research_platform_ui_shell_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_ARTIFACTS = (
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    STATUS_SNAPSHOT,
    INTERACTIVE_UI_SHELL_SNAPSHOT,
    UI_INTERACTION_CONTRACT_SNAPSHOT,
    UI_DISABLED_ACTIONS_SNAPSHOT,
    UI_FILTER_TABS_SNAPSHOT,
    LOCAL_PLATFORM_SHELL_STATUS_SNAPSHOT,
    BUILD_SNAPSHOT,
    ARTIFACT_MANIFEST,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)


def _generate(tmp_path: Path) -> None:
    generate_interactive_local_research_platform_ui_shell_pack(
        output_dashboard_index=tmp_path / DASHBOARD_INDEX,
        output_dashboard_css=tmp_path / DASHBOARD_CSS,
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_interactive_ui_shell_snapshot=tmp_path / INTERACTIVE_UI_SHELL_SNAPSHOT,
        output_ui_interaction_contract_snapshot=tmp_path / UI_INTERACTION_CONTRACT_SNAPSHOT,
        output_ui_disabled_actions_snapshot=tmp_path / UI_DISABLED_ACTIONS_SNAPSHOT,
        output_ui_filter_tabs_snapshot=tmp_path / UI_FILTER_TABS_SNAPSHOT,
        output_local_platform_shell_status_snapshot=tmp_path / LOCAL_PLATFORM_SHELL_STATUS_SNAPSHOT,
        output_build_snapshot=tmp_path / BUILD_SNAPSHOT,
        output_artifact_manifest=tmp_path / ARTIFACT_MANIFEST,
        output_csv=tmp_path / OUTPUT_CSV,
        output_report=tmp_path / OUTPUT_REPORT,
        output_pack=tmp_path / OUTPUT_PACK,
        generated_at="2026-06-01T00:00:00+00:00",
    )


def test_builder_generates_all_target_artifacts(tmp_path: Path) -> None:
    row = generate_interactive_local_research_platform_ui_shell_pack(
        output_dashboard_index=tmp_path / DASHBOARD_INDEX,
        output_dashboard_css=tmp_path / DASHBOARD_CSS,
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_interactive_ui_shell_snapshot=tmp_path / INTERACTIVE_UI_SHELL_SNAPSHOT,
        output_ui_interaction_contract_snapshot=tmp_path / UI_INTERACTION_CONTRACT_SNAPSHOT,
        output_ui_disabled_actions_snapshot=tmp_path / UI_DISABLED_ACTIONS_SNAPSHOT,
        output_ui_filter_tabs_snapshot=tmp_path / UI_FILTER_TABS_SNAPSHOT,
        output_local_platform_shell_status_snapshot=tmp_path / LOCAL_PLATFORM_SHELL_STATUS_SNAPSHOT,
        output_build_snapshot=tmp_path / BUILD_SNAPSHOT,
        output_artifact_manifest=tmp_path / ARTIFACT_MANIFEST,
        output_csv=tmp_path / OUTPUT_CSV,
        output_report=tmp_path / OUTPUT_REPORT,
        output_pack=tmp_path / OUTPUT_PACK,
        generated_at="2026-06-01T00:00:00+00:00",
    )

    for relative_path in TARGET_ARTIFACTS:
        assert (tmp_path / relative_path).exists()
    assert row["status"] == STATUS


def test_cli_generates_pack_successfully_without_monitor_flow(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--interactive-local-research-platform-ui-shell-pack"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert "status=INTERACTIVE_LOCAL_RESEARCH_PLATFORM_UI_SHELL_READY" in result.stdout
    assert "ui_generation=V8_INTERACTIVE_LOCAL_RESEARCH_PLATFORM_SHELL" in result.stdout
    assert "source_connection_implemented=NO" in result.stdout
    assert "live_market_data_enabled=NO" in result.stdout
    for relative_path in TARGET_ARTIFACTS:
        assert (tmp_path / relative_path).exists()


def test_dashboard_html_contains_interactive_platform_shell_copy(tmp_path: Path) -> None:
    _generate(tmp_path)
    html = (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8")

    for text in (
        "AI 投研交易驾驶舱",
        "本地交互式投研平台",
        "总览",
        "市场观察",
        "数据源",
        "风险边界",
        "本地文件",
        "路线图",
        "系统状态",
        "搜索",
        "筛选",
        "折叠",
        "GLD",
        "SLV",
        "IBKR Network B / ARCA",
        "免费延迟公开源",
        "手动 CSV",
        "付费 API",
        "Hybrid Router",
        "未连接 IBKR",
        "未请求行情",
    ):
        assert text in html


def test_dashboard_html_and_css_do_not_load_remote_or_disallowed_runtime_interfaces(tmp_path: Path) -> None:
    _generate(tmp_path)
    text = (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8") + "\n" + (
        tmp_path / DASHBOARD_CSS
    ).read_text(encoding="utf-8")

    for forbidden in (
        "http://",
        "https://",
        "cdn",
        "@import",
        "script src",
        "TradingView",
        "iframe",
        "websocket",
        "fetch(",
        "XMLHttpRequest",
    ):
        assert forbidden not in text


def test_inline_js_only_supports_local_interactions(tmp_path: Path) -> None:
    _generate(tmp_path)
    html = (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8")

    assert "<script>" in html
    assert "addEventListener" in html
    assert "data-tab-target" in html
    assert "data-copy" in html
    for forbidden in ("fetch(", "WebSocket", "XMLHttpRequest", "sendBeacon", "localStorage", "indexedDB"):
        assert forbidden not in html


def test_interactive_ui_shell_snapshot_records_features_and_local_boundaries(tmp_path: Path) -> None:
    _generate(tmp_path)
    snapshot = json.loads((tmp_path / INTERACTIVE_UI_SHELL_SNAPSHOT).read_text(encoding="utf-8"))

    assert snapshot["status"] == "INTERACTIVE_UI_SHELL_READY"
    assert snapshot["ui_generation"] == "V8_INTERACTIVE_LOCAL_RESEARCH_PLATFORM_SHELL"
    assert "LOCAL_SEARCH" in snapshot["interaction_features"]
    assert "LOCAL_FILTERS" in snapshot["interaction_features"]
    assert "COLLAPSIBLE_CARDS" in snapshot["interaction_features"]
    assert snapshot["local_backend_api"] == "NO"
    assert snapshot["external_js"] == "NO"


def test_ui_interaction_contract_records_allowed_and_forbidden_interactions(tmp_path: Path) -> None:
    _generate(tmp_path)
    snapshot = json.loads((tmp_path / UI_INTERACTION_CONTRACT_SNAPSHOT).read_text(encoding="utf-8"))

    assert snapshot["status"] == "UI_INTERACTION_CONTRACT_READY"
    assert "local_search" in snapshot["allowed_interactions"]
    assert "collapse_expand" in snapshot["allowed_interactions"]
    assert "network_fetch" in snapshot["forbidden_interactions"]
    assert "market_data_request" in snapshot["forbidden_interactions"]
    assert "order_submit" in snapshot["forbidden_interactions"]


def test_ui_disabled_actions_snapshot_disables_every_external_action(tmp_path: Path) -> None:
    _generate(tmp_path)
    snapshot = json.loads((tmp_path / UI_DISABLED_ACTIONS_SNAPSHOT).read_text(encoding="utf-8"))

    assert snapshot["status"] == "UI_DISABLED_ACTIONS_READY"
    assert snapshot["all_disabled"] == "YES"
    for action in ("IBKR_CONNECT", "MARKET_DATA_REQUEST", "HISTORICAL_DATA_REQUEST", "ORDER_SUBMIT", "TELEGRAM_REAL_SEND"):
        assert action in snapshot["disabled_actions"]


def test_local_platform_shell_status_records_ui_driven_mode(tmp_path: Path) -> None:
    _generate(tmp_path)
    snapshot = json.loads((tmp_path / LOCAL_PLATFORM_SHELL_STATUS_SNAPSHOT).read_text(encoding="utf-8"))

    assert snapshot["platform_mode"] == "UI_DRIVEN_LOCAL_RESEARCH_WORKBENCH"
    assert snapshot["terminal_role"] == "STARTUP_AND_FALLBACK_ONLY"
    assert snapshot["primary_user_interaction"] == "WEB_UI"
    assert snapshot["backend_api_status"] == "NOT_IMPLEMENTED"


def test_status_snapshot_preserves_blockers_and_disabled_runtime_flags(tmp_path: Path) -> None:
    _generate(tmp_path)
    status = json.loads((tmp_path / STATUS_SNAPSHOT).read_text(encoding="utf-8"))

    assert status["status"] == "INTERACTIVE_LOCAL_RESEARCH_PLATFORM_UI_SHELL_READY"
    assert status["source_connection_implemented"] == "NO"
    assert status["live_market_data_enabled"] == "NO"
    assert status["market_data_status"] == "BLOCKED_BY_SUBSCRIPTION"
    assert status["realtime_market_data_verified"] == "NO"
    assert status["production_ready"] == "NO"
    assert status["trading_enabled"] == "NO"
    assert status["account_read_enabled"] == "NO"
    assert status["positions_read_enabled"] == "NO"
    assert status["historical_data_enabled"] == "NO"
    assert status["telegram_real_send_enabled"] == "NO"


def test_signal_snapshot_and_html_do_not_contain_directional_or_target_terms(tmp_path: Path) -> None:
    _generate(tmp_path)
    html = (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8")
    signal = (REPO_ROOT / "dashboard/data/signal_snapshot.json").read_text(encoding="utf-8")

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
        assert forbidden not in html
        assert forbidden not in signal


def test_watchlist_html_omits_live_price_field_names(tmp_path: Path) -> None:
    _generate(tmp_path)
    html = (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8")

    for forbidden in ("last_price", "bid", "ask", "open", "high", "low", "close"):
        assert re.search(rf"(?<![A-Za-z0-9_]){re.escape(forbidden)}(?![A-Za-z0-9_])", html) is None


def test_artifact_manifest_is_local_static_and_omits_runtime_metadata(tmp_path: Path) -> None:
    _generate(tmp_path)
    manifest = json.loads((tmp_path / ARTIFACT_MANIFEST).read_text(encoding="utf-8"))

    assert manifest["external_effect"] == "NONE_LOCAL_ARTIFACT_GENERATION_ONLY"
    paths = {artifact["artifact_path"] for artifact in manifest["artifacts"]}
    for relative_path in TARGET_ARTIFACTS:
        assert relative_path in paths
    for artifact in manifest["artifacts"]:
        assert artifact["external_effect"] == "NONE_LOCAL_ARTIFACT_GENERATION_ONLY"
        assert "http://" not in artifact["local_href"]
        assert "https://" not in artifact["local_href"]
        assert "icon_token" in artifact
        assert "file_size" not in artifact
        assert "mtime" not in artifact


def test_generator_does_not_touch_forbidden_local_residue_files(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    error_csv_path = tmp_path / "ibkr_market_data_api_errors.csv"
    config_path.write_text("local: config\n", encoding="utf-8")
    error_csv_path.write_text("code,message\n10089,subscription\n", encoding="utf-8")

    _generate(tmp_path)

    assert config_path.read_text(encoding="utf-8") == "local: config\n"
    assert error_csv_path.read_text(encoding="utf-8") == "code,message\n10089,subscription\n"


def test_generation_flow_records_no_external_or_live_runtime_actions(tmp_path: Path) -> None:
    _generate(tmp_path)
    status = json.loads((tmp_path / STATUS_SNAPSHOT).read_text(encoding="utf-8"))
    disabled = json.loads((tmp_path / UI_DISABLED_ACTIONS_SNAPSHOT).read_text(encoding="utf-8"))

    assert status["external_effect"] == "NONE_LOCAL_ARTIFACT_GENERATION_ONLY"
    assert status["source_connection_implemented"] == "NO"
    assert status["live_market_data_enabled"] == "NO"
    assert status["account_read_enabled"] == "NO"
    assert status["positions_read_enabled"] == "NO"
    assert status["historical_data_enabled"] == "NO"
    assert status["telegram_real_send_enabled"] == "NO"
    for action in (
        "IBKR_CONNECT",
        "MARKET_DATA_REQUEST",
        "HISTORICAL_DATA_REQUEST",
        "ACCOUNT_READ",
        "POSITION_READ",
        "CONTRACT_QUALIFICATION",
        "TELEGRAM_REAL_SEND",
    ):
        assert action in disabled["disabled_actions"]
