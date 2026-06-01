from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.operator_ui_driven_local_research_platform_mvp_pack import (
    ARTIFACTS,
    FINAL_LANDING_AUDIT_SNAPSHOT,
    STATUS,
    build_api_endpoint_registry_snapshot,
    build_api_readonly_guard_snapshot,
    generate_ui_driven_local_research_platform_mvp_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_UI_TERMS = ("fetch(", "XMLHttpRequest", "WebSocket", "http://", "https://", "TradingView", "iframe")
FORBIDDEN_SOURCE_TERMS = (
    "ib_insync",
    "reqMktData",
    "reqHistoricalData",
    "placeOrder",
    "accountSummary",
    "positions",
    "telegram send",
)
FORBIDDEN_REPORT_TERMS = (
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
FORBIDDEN_PRICE_FIELDS = ("last_price", "bid", "ask", "open", "high", "low", "close")


def test_builder_generates_all_target_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    row = generate_ui_driven_local_research_platform_mvp_pack(
        output_dashboard_index=tmp_path / "dashboard/index.html",
        output_dashboard_css=tmp_path / "dashboard/assets/style.css",
        output_status_snapshot=tmp_path / "dashboard/data/status_snapshot.json",
        output_artifact_manifest=tmp_path / "dashboard/data/artifact_manifest.json",
        output_csv=tmp_path / "operator_ui_driven_local_research_platform_mvp_pack.csv",
        output_report=tmp_path / "reports/operator_ui_driven_local_research_platform_mvp_pack_report.md",
        output_pack=tmp_path / "Precious_Metals_Monitor_UI_Driven_Local_Research_Platform_MVP_Landing_Pack.md",
        generated_at="2026-06-01T00:00:00+00:00",
    )

    assert row["status"] == STATUS
    assert (tmp_path / "dashboard/index.html").exists()
    assert (tmp_path / "operator_ui_driven_local_research_platform_mvp_pack.csv").exists()
    assert len(ARTIFACTS) >= 30


def test_endpoint_registry_and_readonly_guard_cover_mvp_routes() -> None:
    registry = build_api_endpoint_registry_snapshot("2026-06-01T00:00:00+00:00")
    guard = build_api_readonly_guard_snapshot("2026-06-01T00:00:00+00:00")

    for endpoint in (
        "GET /api/workflow/status",
        "GET /api/workflow/run-preview",
        "GET /api/research/report-framework",
        "GET /api/data-source/dry-run",
        "GET /api/operator/daily-packet",
        "GET /api/telegram/preview",
        "GET /api/watchlist/policy",
        "GET /api/mvp/status",
    ):
        assert endpoint in registry["allowed_endpoints"]
    assert guard["allowed_methods"] == ["GET"]
    assert {"POST", "PUT", "DELETE"}.issubset(set(guard["blocked_methods"]))


def test_ui_omits_external_and_auto_api_patterns() -> None:
    html = (REPO_ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    css = (REPO_ROOT / "dashboard/assets/style.css").read_text(encoding="utf-8")

    for term in FORBIDDEN_UI_TERMS:
        assert term not in html
        assert term not in css


def test_new_runtime_sources_omit_blocked_integrations() -> None:
    for path in (
        REPO_ROOT / "src/local_backend_api_shell.py",
        REPO_ROOT / "src/local_workflow_automation.py",
        REPO_ROOT / "src/local_research_report_builder.py",
    ):
        source = path.read_text(encoding="utf-8")
        for term in FORBIDDEN_SOURCE_TERMS:
            assert term not in source


def test_reports_and_snapshots_keep_research_only_boundary() -> None:
    report = (REPO_ROOT / "reports/local_research_report_framework_GLD_SLV.md").read_text(encoding="utf-8")
    for term in FORBIDDEN_REPORT_TERMS:
        assert term not in report

    paths = [
        REPO_ROOT / "dashboard/data/watchlist_policy_snapshot.json",
        REPO_ROOT / "dashboard/data/research_report_framework_snapshot.json",
        REPO_ROOT / "dashboard/data/us_gld_slv_data_source_dry_run_snapshot.json",
        REPO_ROOT / "reports/operator_daily_packet_preview.md",
        REPO_ROOT / "reports/telegram_preview_local_only.md",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    for field in FORBIDDEN_PRICE_FIELDS:
        assert field not in combined


def test_status_and_final_audit_snapshots_are_ready() -> None:
    status = json.loads((REPO_ROOT / "dashboard/data/status_snapshot.json").read_text(encoding="utf-8"))
    audit = json.loads((REPO_ROOT / FINAL_LANDING_AUDIT_SNAPSHOT).read_text(encoding="utf-8"))

    assert status["status"] in {STATUS, "PRODUCTIZED_UI_PUBLIC_DATA_INTAKE_READY"}
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
    assert status["market_data_status"] == "BLOCKED_BY_SUBSCRIPTION"
    assert audit["status"] == "LOCAL_PLATFORM_MVP_FINAL_AUDIT_READY"
    assert audit["all_external_actions_blocked"] == "YES"
    assert audit["ui_driven_workbench_ready"] == "YES"
    assert audit["terminal_role"] == "STARTUP_AND_FALLBACK_ONLY"


def test_cli_entrypoints_succeed() -> None:
    commands = (
        ["--ui-driven-local-research-platform-mvp-pack"],
        ["--local-workflow-run"],
        ["--local-research-report-build"],
    )
    for args in commands:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "main.py"), *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr


def test_config_and_market_data_error_file_are_not_tracked() -> None:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    tracked_lines = [line for line in result.stdout.splitlines() if "config.yaml" in line or "ibkr_market_data_api_errors.csv" in line]
    assert tracked_lines == [" M config.yaml", "?? ibkr_market_data_api_errors.csv"]
