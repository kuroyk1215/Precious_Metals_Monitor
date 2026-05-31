from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from src.operator_dashboard_visual_density_card_system_pack import (
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    CARD_SYSTEM_SNAPSHOT,
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
    VISUAL_DENSITY_SNAPSHOT,
    WATCHLIST_SNAPSHOT,
    generate_dashboard_visual_density_card_system_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


TARGET_ARTIFACTS = (
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    STATUS_SNAPSHOT,
    VISUAL_DENSITY_SNAPSHOT,
    CARD_SYSTEM_SNAPSHOT,
    WATCHLIST_SNAPSHOT,
    SIGNAL_SNAPSHOT,
    RISK_SNAPSHOT,
    OPERATOR_TIMELINE,
    ARTIFACT_MANIFEST,
    LAYOUT_SNAPSHOT,
    NAVIGATION_SNAPSHOT,
    BUILD_SNAPSHOT,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)


GENERATED_TEXT_ARTIFACTS = TARGET_ARTIFACTS


def _generate(tmp_path: Path) -> None:
    generate_dashboard_visual_density_card_system_pack(
        output_index=tmp_path / DASHBOARD_INDEX,
        output_css=tmp_path / DASHBOARD_CSS,
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_visual_density_snapshot=tmp_path / VISUAL_DENSITY_SNAPSHOT,
        output_card_system_snapshot=tmp_path / CARD_SYSTEM_SNAPSHOT,
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
    row = generate_dashboard_visual_density_card_system_pack(
        output_index=tmp_path / DASHBOARD_INDEX,
        output_css=tmp_path / DASHBOARD_CSS,
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_visual_density_snapshot=tmp_path / VISUAL_DENSITY_SNAPSHOT,
        output_card_system_snapshot=tmp_path / CARD_SYSTEM_SNAPSHOT,
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
        ["python3", str(REPO_ROOT / "main.py"), "--dashboard-visual-density-card-system-pack"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert "status=DASHBOARD_VISUAL_DENSITY_CARD_SYSTEM_READY" in result.stdout
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


def test_dashboard_index_contains_visual_density_sections_and_local_css(tmp_path: Path) -> None:
    _generate(tmp_path)
    html = (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8")

    assert '<link rel="stylesheet" href="assets/style.css">' in html
    for marker in (
        "DASHBOARD_VISUAL_DENSITY_CARD_SYSTEM_READY",
        "HIGH_DENSITY_CONSOLE_READY",
        "CARD_SYSTEM_READY",
        "Market Data Block",
        "Watchlist",
        "Signal Panel",
        "Risk Boundary",
        "Artifact Reader",
        "Operator Timeline",
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
            VISUAL_DENSITY_SNAPSHOT,
            CARD_SYSTEM_SNAPSHOT,
            WATCHLIST_SNAPSHOT,
            SIGNAL_SNAPSHOT,
            RISK_SNAPSHOT,
            OPERATOR_TIMELINE,
            ARTIFACT_MANIFEST,
            LAYOUT_SNAPSHOT,
            NAVIGATION_SNAPSHOT,
            BUILD_SNAPSHOT,
        )
    )
    for marker in ("http://", "https://", "cdn", "@import", "script src"):
        assert marker not in combined


def test_status_snapshot_preserves_blocked_market_data_and_safety_flags(tmp_path: Path) -> None:
    _generate(tmp_path)
    status = json.loads((tmp_path / STATUS_SNAPSHOT).read_text(encoding="utf-8"))

    assert status["ui_status"] == "DASHBOARD_VISUAL_DENSITY_CARD_SYSTEM_READY"
    assert status["ui_generation"] == "V4_VISUAL_DENSITY"
    assert status["visual_density_status"] == "HIGH_DENSITY_CONSOLE_READY"
    assert status["card_system_status"] == "CARD_SYSTEM_READY"
    assert status["matrix_status"] == "RISK_SIGNAL_MATRIX_READY"
    assert status["artifact_reader_status"] == "DENSE_ARTIFACT_READER_READY"
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


def test_visual_density_and_card_system_snapshots(tmp_path: Path) -> None:
    _generate(tmp_path)
    visual_density = json.loads((tmp_path / VISUAL_DENSITY_SNAPSHOT).read_text(encoding="utf-8"))
    card_system = json.loads((tmp_path / CARD_SYSTEM_SNAPSHOT).read_text(encoding="utf-8"))

    assert visual_density["density_mode"] == "HIGH_INFORMATION_DENSITY_STATIC_CONSOLE"
    assert visual_density["table_density"] == "COMPACT"
    assert visual_density["card_spacing"] == "COMPACT"
    assert visual_density["external_assets"] == "NO"
    assert visual_density["javascript_required"] == "NO"
    assert card_system["status"] == "CARD_SYSTEM_READY"
    assert "MATRIX_CARD" in card_system["card_types"]
    assert "TABLE_CARD" in card_system["card_types"]
    assert "SAFETY_CARD" in card_system["card_types"]
    assert card_system["external_assets"] == "NO"


def test_watchlist_omits_live_price_fields(tmp_path: Path) -> None:
    _generate(tmp_path)
    watchlist_text = (tmp_path / WATCHLIST_SNAPSHOT).read_text(encoding="utf-8")

    for forbidden in ("last_price", "bid", "ask", "open", "high", "low", "close"):
        assert forbidden not in watchlist_text


def test_signal_snapshot_and_html_omit_forbidden_trading_outputs(tmp_path: Path) -> None:
    _generate(tmp_path)
    combined = "\n".join(
        (
            (tmp_path / SIGNAL_SNAPSHOT).read_text(encoding="utf-8"),
            (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8"),
        )
    )

    for forbidden in ("BUY", "SELL", "HOLD", "target_price", "stop_loss", "take_profit"):
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
    assert all(item["status"] == "DISABLED" for item in risk["permissions"])
    assert all(item["allowed"] == "NO" for item in risk["permissions"])
    for action in actions:
        assert action in html


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
