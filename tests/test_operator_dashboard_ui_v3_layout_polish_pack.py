from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from src.operator_dashboard_ui_v3_layout_polish_pack import (
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    DASHBOARD_CSS,
    DASHBOARD_INDEX,
    LAYOUT_SNAPSHOT,
    NAVIGATION_SNAPSHOT,
    OPERATOR_TIMELINE,
    OUTPUT_CSV,
    OUTPUT_PACK,
    OUTPUT_REPORT,
    RISK_SNAPSHOT,
    SIGNAL_SNAPSHOT,
    STATUS,
    STATUS_SNAPSHOT,
    WATCHLIST_SNAPSHOT,
    generate_dashboard_ui_v3_layout_polish_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


TARGET_ARTIFACTS = (
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    STATUS_SNAPSHOT,
    LAYOUT_SNAPSHOT,
    NAVIGATION_SNAPSHOT,
    BUILD_SNAPSHOT,
    WATCHLIST_SNAPSHOT,
    SIGNAL_SNAPSHOT,
    RISK_SNAPSHOT,
    OPERATOR_TIMELINE,
    ARTIFACT_MANIFEST,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)


GENERATED_TEXT_ARTIFACTS = TARGET_ARTIFACTS


def _generate(tmp_path: Path) -> None:
    generate_dashboard_ui_v3_layout_polish_pack(
        output_index=tmp_path / DASHBOARD_INDEX,
        output_css=tmp_path / DASHBOARD_CSS,
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_watchlist_snapshot=tmp_path / WATCHLIST_SNAPSHOT,
        output_signal_snapshot=tmp_path / SIGNAL_SNAPSHOT,
        output_risk_snapshot=tmp_path / RISK_SNAPSHOT,
        output_operator_timeline=tmp_path / OPERATOR_TIMELINE,
        output_layout_snapshot=tmp_path / LAYOUT_SNAPSHOT,
        output_navigation_snapshot=tmp_path / NAVIGATION_SNAPSHOT,
        output_build_snapshot=tmp_path / BUILD_SNAPSHOT,
        output_artifact_manifest=tmp_path / ARTIFACT_MANIFEST,
        output_csv=tmp_path / OUTPUT_CSV,
        output_report=tmp_path / OUTPUT_REPORT,
        output_pack=tmp_path / OUTPUT_PACK,
        generated_at="2026-05-31T00:00:00+00:00",
    )


def test_builder_generates_all_target_artifacts(tmp_path: Path) -> None:
    row = generate_dashboard_ui_v3_layout_polish_pack(
        output_index=tmp_path / DASHBOARD_INDEX,
        output_css=tmp_path / DASHBOARD_CSS,
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_watchlist_snapshot=tmp_path / WATCHLIST_SNAPSHOT,
        output_signal_snapshot=tmp_path / SIGNAL_SNAPSHOT,
        output_risk_snapshot=tmp_path / RISK_SNAPSHOT,
        output_operator_timeline=tmp_path / OPERATOR_TIMELINE,
        output_layout_snapshot=tmp_path / LAYOUT_SNAPSHOT,
        output_navigation_snapshot=tmp_path / NAVIGATION_SNAPSHOT,
        output_build_snapshot=tmp_path / BUILD_SNAPSHOT,
        output_artifact_manifest=tmp_path / ARTIFACT_MANIFEST,
        output_csv=tmp_path / OUTPUT_CSV,
        output_report=tmp_path / OUTPUT_REPORT,
        output_pack=tmp_path / OUTPUT_PACK,
        generated_at="2026-05-31T00:00:00+00:00",
    )

    for relative_path in TARGET_ARTIFACTS:
        assert (tmp_path / relative_path).exists()
    assert row["status"] == STATUS


def test_cli_generates_static_pack_without_external_actions(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--dashboard-ui-v3-layout-polish-pack"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert "status=DASHBOARD_UI_V3_LAYOUT_POLISH_READY" in result.stdout
    assert "market_data_status=BLOCKED_BY_SUBSCRIPTION" in result.stdout
    assert "realtime_market_data_verified=NO" in result.stdout
    assert "production_ready=NO" in result.stdout
    assert "trading_enabled=NO" in result.stdout
    assert "account_read_enabled=NO" in result.stdout
    assert "positions_read_enabled=NO" in result.stdout
    assert "historical_data_enabled=NO" in result.stdout
    assert "telegram_real_send_enabled=NO" in result.stdout

    for relative_path in TARGET_ARTIFACTS:
        assert (tmp_path / relative_path).exists()

    combined = result.stdout + "\n" + "\n".join(
        (tmp_path / relative_path).read_text(encoding="utf-8")
        for relative_path in GENERATED_TEXT_ARTIFACTS
    )
    for forbidden in (
        "ibkr_connected=YES",
        "market_data_request=YES",
        "historical_data_request=YES",
        "account_read_enabled=YES",
        "positions_read_enabled=YES",
        "contract_qualification=YES",
        "telegram_real_send=YES",
        "trading_enabled=YES",
    ):
        assert forbidden not in combined


def test_dashboard_index_contains_v3_layout_shell_and_local_css(tmp_path: Path) -> None:
    _generate(tmp_path)
    html = (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8")

    assert '<link rel="stylesheet" href="assets/style.css">' in html
    for marker in (
        "UI_V3",
        "Dashboard",
        "Watchlist",
        "Signals",
        "Risk Boundary",
        "Artifacts",
        "Timeline",
        "System Status",
        "Settings",
        "Console Mode",
        "Build / Version / Safety",
        "No IBKR connection",
        "No market data request",
    ):
        assert marker in html

    for misleading in (
        "ready for live trading",
        "production ready",
        "realtime ready",
        "buy signal",
        "sell signal",
        "trade recommendation",
        "target price",
        "stop loss",
        "take profit",
    ):
        assert misleading not in html.lower()


def test_html_css_and_json_do_not_load_external_resources(tmp_path: Path) -> None:
    _generate(tmp_path)
    combined = "\n".join(
        (tmp_path / relative_path).read_text(encoding="utf-8")
        for relative_path in (
            DASHBOARD_INDEX,
            DASHBOARD_CSS,
            STATUS_SNAPSHOT,
            LAYOUT_SNAPSHOT,
            NAVIGATION_SNAPSHOT,
            BUILD_SNAPSHOT,
            WATCHLIST_SNAPSHOT,
            SIGNAL_SNAPSHOT,
            RISK_SNAPSHOT,
            OPERATOR_TIMELINE,
            ARTIFACT_MANIFEST,
        )
    )
    for marker in ("http://", "https://", "cdn", "@import", "script src"):
        assert marker not in combined


def test_status_snapshot_preserves_blocked_market_data_and_safety_flags(tmp_path: Path) -> None:
    _generate(tmp_path)
    status = json.loads((tmp_path / STATUS_SNAPSHOT).read_text(encoding="utf-8"))

    assert status["ui_status"] == "DASHBOARD_UI_V3_LAYOUT_POLISH_READY"
    assert status["market_data_status"] == "BLOCKED_BY_SUBSCRIPTION"
    assert status["market_data_classification"] == "MARKET_DATA_BLOCKED_BY_SUBSCRIPTION"
    assert status["ibkr_error_code"] == "10089"
    assert status["subscription_required"] == "YES"
    assert status["delayed_available"] == "YES"
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


def test_layout_navigation_and_build_snapshots_preserve_static_boundaries(tmp_path: Path) -> None:
    _generate(tmp_path)
    layout = json.loads((tmp_path / LAYOUT_SNAPSHOT).read_text(encoding="utf-8"))
    navigation = json.loads((tmp_path / NAVIGATION_SNAPSHOT).read_text(encoding="utf-8"))
    build = json.loads((tmp_path / BUILD_SNAPSHOT).read_text(encoding="utf-8"))

    assert layout["layout_mode"] == "DESKTOP_STATIC_APP_SHELL"
    assert "SIDEBAR" in layout["sections"]
    assert "TOP_HEADER" in layout["sections"]
    assert "SAFETY_FOOTER" in layout["sections"]
    assert layout["javascript_required"] == "NO"
    assert layout["external_assets"] == "NO"
    assert all(item["external_url"] == "NO" for item in navigation["items"])
    assert build["production_ready"] == "NO"
    assert build["trading_enabled"] == "NO"


def test_generated_content_omits_forbidden_trading_terms_and_sensitive_files(tmp_path: Path) -> None:
    _generate(tmp_path)
    combined = "\n".join(
        (tmp_path / relative_path).read_text(encoding="utf-8")
        for relative_path in GENERATED_TEXT_ARTIFACTS
    )

    for forbidden in (
        "BUY",
        "SELL",
        "target_price",
        "stop_loss",
        "take_profit",
        "last_price",
        "bid",
        "ask",
    ):
        assert forbidden not in combined

    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    ).stdout
    assert "config.yaml" not in "\n".join(line for line in status.splitlines() if not line.startswith(" M config.yaml"))
    assert "ibkr_market_data_api_errors.csv" not in "\n".join(
        line for line in status.splitlines() if not line.startswith("?? ibkr_market_data_api_errors.csv")
    )
