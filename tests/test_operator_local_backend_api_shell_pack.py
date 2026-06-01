from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from src.operator_local_backend_api_shell_pack import (
    API_ENDPOINT_REGISTRY_SNAPSHOT,
    API_READONLY_GUARD_SNAPSHOT,
    API_RUNTIME_CONTRACT_SNAPSHOT,
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    DASHBOARD_CSS,
    DASHBOARD_INDEX,
    INTERACTIVE_UI_SHELL_SNAPSHOT,
    LOCAL_BACKEND_API_SHELL_SNAPSHOT,
    LOCAL_PLATFORM_SHELL_STATUS_SNAPSHOT,
    LOCAL_UI_SERVER_RUNBOOK_SNAPSHOT,
    MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
    MARKET_SCOPE_STATUS_SNAPSHOT,
    NEXT_ROADMAP_SNAPSHOT,
    OPERATOR_NEXT_ACTIONS_SNAPSHOT,
    OPERATOR_TIMELINE,
    OUTPUT_CSV,
    OUTPUT_PACK,
    OUTPUT_REPORT,
    STATUS,
    STATUS_SNAPSHOT,
    generate_local_backend_api_shell_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_ARTIFACTS = (
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    STATUS_SNAPSHOT,
    LOCAL_BACKEND_API_SHELL_SNAPSHOT,
    API_ENDPOINT_REGISTRY_SNAPSHOT,
    API_READONLY_GUARD_SNAPSHOT,
    API_RUNTIME_CONTRACT_SNAPSHOT,
    LOCAL_UI_SERVER_RUNBOOK_SNAPSHOT,
    BUILD_SNAPSHOT,
    OPERATOR_TIMELINE,
    INTERACTIVE_UI_SHELL_SNAPSHOT,
    LOCAL_PLATFORM_SHELL_STATUS_SNAPSHOT,
    OPERATOR_NEXT_ACTIONS_SNAPSHOT,
    NEXT_ROADMAP_SNAPSHOT,
    MARKET_SCOPE_STATUS_SNAPSHOT,
    MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
    ARTIFACT_MANIFEST,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)


def _generate(tmp_path: Path) -> None:
    generate_local_backend_api_shell_pack(
        output_dashboard_index=tmp_path / DASHBOARD_INDEX,
        output_dashboard_css=tmp_path / DASHBOARD_CSS,
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_local_backend_api_shell_snapshot=tmp_path / LOCAL_BACKEND_API_SHELL_SNAPSHOT,
        output_api_endpoint_registry_snapshot=tmp_path / API_ENDPOINT_REGISTRY_SNAPSHOT,
        output_api_readonly_guard_snapshot=tmp_path / API_READONLY_GUARD_SNAPSHOT,
        output_api_runtime_contract_snapshot=tmp_path / API_RUNTIME_CONTRACT_SNAPSHOT,
        output_local_ui_server_runbook_snapshot=tmp_path / LOCAL_UI_SERVER_RUNBOOK_SNAPSHOT,
        output_build_snapshot=tmp_path / BUILD_SNAPSHOT,
        output_operator_timeline=tmp_path / OPERATOR_TIMELINE,
        output_interactive_ui_shell_snapshot=tmp_path / INTERACTIVE_UI_SHELL_SNAPSHOT,
        output_local_platform_shell_status_snapshot=tmp_path / LOCAL_PLATFORM_SHELL_STATUS_SNAPSHOT,
        output_operator_next_actions_snapshot=tmp_path / OPERATOR_NEXT_ACTIONS_SNAPSHOT,
        output_next_roadmap_snapshot=tmp_path / NEXT_ROADMAP_SNAPSHOT,
        output_market_scope_status_snapshot=tmp_path / MARKET_SCOPE_STATUS_SNAPSHOT,
        output_market_data_source_decision_snapshot=tmp_path / MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
        output_artifact_manifest=tmp_path / ARTIFACT_MANIFEST,
        output_csv=tmp_path / OUTPUT_CSV,
        output_report=tmp_path / OUTPUT_REPORT,
        output_pack=tmp_path / OUTPUT_PACK,
        generated_at="2026-06-01T00:00:00+00:00",
    )


def test_builder_generates_all_target_artifacts(tmp_path: Path) -> None:
    row = generate_local_backend_api_shell_pack(
        output_dashboard_index=tmp_path / DASHBOARD_INDEX,
        output_dashboard_css=tmp_path / DASHBOARD_CSS,
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_local_backend_api_shell_snapshot=tmp_path / LOCAL_BACKEND_API_SHELL_SNAPSHOT,
        output_api_endpoint_registry_snapshot=tmp_path / API_ENDPOINT_REGISTRY_SNAPSHOT,
        output_api_readonly_guard_snapshot=tmp_path / API_READONLY_GUARD_SNAPSHOT,
        output_api_runtime_contract_snapshot=tmp_path / API_RUNTIME_CONTRACT_SNAPSHOT,
        output_local_ui_server_runbook_snapshot=tmp_path / LOCAL_UI_SERVER_RUNBOOK_SNAPSHOT,
        output_build_snapshot=tmp_path / BUILD_SNAPSHOT,
        output_operator_timeline=tmp_path / OPERATOR_TIMELINE,
        output_interactive_ui_shell_snapshot=tmp_path / INTERACTIVE_UI_SHELL_SNAPSHOT,
        output_local_platform_shell_status_snapshot=tmp_path / LOCAL_PLATFORM_SHELL_STATUS_SNAPSHOT,
        output_operator_next_actions_snapshot=tmp_path / OPERATOR_NEXT_ACTIONS_SNAPSHOT,
        output_next_roadmap_snapshot=tmp_path / NEXT_ROADMAP_SNAPSHOT,
        output_market_scope_status_snapshot=tmp_path / MARKET_SCOPE_STATUS_SNAPSHOT,
        output_market_data_source_decision_snapshot=tmp_path / MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
        output_artifact_manifest=tmp_path / ARTIFACT_MANIFEST,
        output_csv=tmp_path / OUTPUT_CSV,
        output_report=tmp_path / OUTPUT_REPORT,
        output_pack=tmp_path / OUTPUT_PACK,
        generated_at="2026-06-01T00:00:00+00:00",
    )

    for relative_path in TARGET_ARTIFACTS:
        assert (tmp_path / relative_path).exists()
    assert row["status"] == STATUS
    assert row["backend_api_status"] == "LOCAL_READONLY_API_SHELL_READY"


def test_cli_generates_pack_successfully_without_monitor_flow(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--local-backend-api-shell-pack"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert "status=LOCAL_BACKEND_API_SHELL_READY" in result.stdout
    assert "backend_api_status=LOCAL_READONLY_API_SHELL_READY" in result.stdout
    assert "local_backend_api=YES_READONLY_SHELL" in result.stdout
    assert "source_connection_implemented=NO" in result.stdout
    assert "live_market_data_enabled=NO" in result.stdout
    for relative_path in TARGET_ARTIFACTS:
        assert (tmp_path / relative_path).exists()


def test_local_ui_server_help_succeeds() -> None:
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--local-ui-server", "--help"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert "--local-ui-server" in result.stdout
    assert "--local-ui-port" in result.stdout


def test_dashboard_contains_local_service_runbook_without_network_calls(tmp_path: Path) -> None:
    _generate(tmp_path)
    html = (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8")

    for text in (
        "本地服务",
        "本地 API 壳：已规划 / 只读",
        "127.0.0.1:8765",
        "python3 main.py --local-ui-server",
        "Local Backend API Shell",
        "外部动作",
        "全部禁用",
        "READONLY_LOCAL_API_ONLY",
    ):
        assert text in html
    for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "http://", "https://", "TradingView", "iframe"):
        assert forbidden not in html


def test_api_snapshots_record_readonly_runtime_contract(tmp_path: Path) -> None:
    _generate(tmp_path)
    shell = json.loads((tmp_path / LOCAL_BACKEND_API_SHELL_SNAPSHOT).read_text(encoding="utf-8"))
    guard = json.loads((tmp_path / API_READONLY_GUARD_SNAPSHOT).read_text(encoding="utf-8"))
    contract = json.loads((tmp_path / API_RUNTIME_CONTRACT_SNAPSHOT).read_text(encoding="utf-8"))
    registry = json.loads((tmp_path / API_ENDPOINT_REGISTRY_SNAPSHOT).read_text(encoding="utf-8"))

    assert shell["status"] == "LOCAL_BACKEND_API_SHELL_READY"
    assert shell["server_type"] == "PYTHON_STDLIB_HTTP_SERVER"
    assert shell["dependency_added"] == "NO"
    assert guard["status"] == "API_READONLY_GUARD_READY"
    assert "GET" in guard["allowed_methods"]
    assert "POST" in guard["blocked_methods"]
    assert "IBKR_CONNECT" in guard["blocked_runtime_actions"]
    assert contract["status"] == "API_RUNTIME_CONTRACT_READY"
    assert contract["backend_to_external"] == "NO"
    assert contract["backend_to_ibkr"] == "NO"
    assert contract["backend_file_write"] == "NO"
    assert "GET /api/health" in registry["allowed_endpoints"]
    assert "/api/order/submit" in registry["forbidden_endpoints"]


def test_status_snapshot_contains_phase_761_safety_flags(tmp_path: Path) -> None:
    _generate(tmp_path)
    status = json.loads((tmp_path / STATUS_SNAPSHOT).read_text(encoding="utf-8"))

    assert status["phase"] == "Phase 761-800"
    assert status["status"] == "LOCAL_BACKEND_API_SHELL_READY"
    assert status["local_backend_api"] == "YES_READONLY_SHELL"
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


def test_artifact_manifest_is_local_and_omits_runtime_metadata(tmp_path: Path) -> None:
    _generate(tmp_path)
    manifest = json.loads((tmp_path / ARTIFACT_MANIFEST).read_text(encoding="utf-8"))

    assert manifest["external_effect"] == "LOCALHOST_READONLY_SERVER_OPTIONAL"
    paths = {artifact["artifact_path"] for artifact in manifest["artifacts"]}
    for relative_path in TARGET_ARTIFACTS:
        assert relative_path in paths
    for artifact in manifest["artifacts"]:
        assert "http://" not in artifact["local_href"]
        assert "https://" not in artifact["local_href"]
        assert "file_size" not in artifact
        assert "mtime" not in artifact


def test_dashboard_html_omits_directional_signals_live_prices_and_remote_widgets(tmp_path: Path) -> None:
    _generate(tmp_path)
    html = (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8")

    for forbidden in (
        "BUY",
        "SELL",
        "HOLD",
        "target_price",
        "stop_loss",
        "take_profit",
        "TradingView",
        "iframe",
    ):
        assert forbidden not in html
    for forbidden in ("last_price", "bid", "ask", "open", "high", "low", "close"):
        assert re.search(rf"(?<![A-Za-z0-9_]){re.escape(forbidden)}(?![A-Za-z0-9_])", html) is None


def test_generator_does_not_touch_forbidden_local_residue_files(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    error_csv_path = tmp_path / "ibkr_market_data_api_errors.csv"
    config_path.write_text("local: config\n", encoding="utf-8")
    error_csv_path.write_text("code,message\n10089,subscription\n", encoding="utf-8")

    _generate(tmp_path)

    assert config_path.read_text(encoding="utf-8") == "local: config\n"
    assert error_csv_path.read_text(encoding="utf-8") == "code,message\n10089,subscription\n"
