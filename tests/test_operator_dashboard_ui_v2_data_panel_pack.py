from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from src.operator_dashboard_ui_v2_data_panel_pack import (
    ARTIFACT_MANIFEST,
    BLOCKED_ACTIONS,
    DASHBOARD_CSS,
    DASHBOARD_INDEX,
    OUTPUT_CSV,
    OUTPUT_PACK,
    OUTPUT_REPORT,
    RISK_SNAPSHOT,
    SIGNAL_SNAPSHOT,
    STATUS,
    STATUS_SNAPSHOT,
    WATCHLIST_SNAPSHOT,
    OPERATOR_TIMELINE,
    build_risk_snapshot,
    build_signal_snapshot,
    build_status_snapshot,
    build_watchlist_snapshot,
    generate_dashboard_ui_v2_data_panel_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


TARGET_ARTIFACTS = (
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    STATUS_SNAPSHOT,
    WATCHLIST_SNAPSHOT,
    SIGNAL_SNAPSHOT,
    RISK_SNAPSHOT,
    OPERATOR_TIMELINE,
    ARTIFACT_MANIFEST,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)


def _generate(tmp_path: Path) -> None:
    generate_dashboard_ui_v2_data_panel_pack(
        output_index=tmp_path / DASHBOARD_INDEX,
        output_css=tmp_path / DASHBOARD_CSS,
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_watchlist_snapshot=tmp_path / WATCHLIST_SNAPSHOT,
        output_signal_snapshot=tmp_path / SIGNAL_SNAPSHOT,
        output_risk_snapshot=tmp_path / RISK_SNAPSHOT,
        output_operator_timeline=tmp_path / OPERATOR_TIMELINE,
        output_artifact_manifest=tmp_path / ARTIFACT_MANIFEST,
        output_csv=tmp_path / OUTPUT_CSV,
        output_report=tmp_path / OUTPUT_REPORT,
        output_pack=tmp_path / OUTPUT_PACK,
        generated_at="2026-05-31T00:00:00+00:00",
    )


def test_builder_generates_all_new_target_artifacts(tmp_path: Path) -> None:
    row = generate_dashboard_ui_v2_data_panel_pack(
        output_index=tmp_path / DASHBOARD_INDEX,
        output_css=tmp_path / DASHBOARD_CSS,
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_watchlist_snapshot=tmp_path / WATCHLIST_SNAPSHOT,
        output_signal_snapshot=tmp_path / SIGNAL_SNAPSHOT,
        output_risk_snapshot=tmp_path / RISK_SNAPSHOT,
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


def test_cli_generates_static_pack_without_external_actions(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--dashboard-ui-v2-data-panel-pack"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert "status=DASHBOARD_UI_V2_DATA_PANEL_READY" in result.stdout
    assert "market_data_status=BLOCKED_BY_SUBSCRIPTION" in result.stdout
    assert "realtime_market_data_verified=NO" in result.stdout
    assert "trading_enabled=NO" in result.stdout
    assert "account_read_enabled=NO" in result.stdout
    assert "positions_read_enabled=NO" in result.stdout
    assert "historical_data_enabled=NO" in result.stdout
    assert "telegram_real_send_enabled=NO" in result.stdout

    for relative_path in TARGET_ARTIFACTS:
        assert (tmp_path / relative_path).exists()

    combined = result.stdout + "\n" + "\n".join(
        (tmp_path / relative_path).read_text(encoding="utf-8")
        for relative_path in (
            DASHBOARD_INDEX,
            DASHBOARD_CSS,
            STATUS_SNAPSHOT,
            WATCHLIST_SNAPSHOT,
            SIGNAL_SNAPSHOT,
            RISK_SNAPSHOT,
            OPERATOR_TIMELINE,
            ARTIFACT_MANIFEST,
        )
    )
    for forbidden in (
        "ibkr_connected=YES",
        "market_data_request=YES",
        "historical_data_request=YES",
        "account_read_enabled=YES",
        "positions_read_enabled=YES",
        "telegram_real_send_enabled=YES",
        "trading_enabled=YES",
        "contract_qualification=YES",
        "telegram_real_send=YES",
    ):
        assert forbidden not in combined


def test_dashboard_index_contains_v2_panels_and_local_css(tmp_path: Path) -> None:
    _generate(tmp_path)
    html = (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8")

    assert '<link rel="stylesheet" href="assets/style.css">' in html
    for marker in (
        "UI_V2",
        "Watchlist",
        "Signal Panel",
        "Risk Boundary",
        "Operator Timeline",
        "Artifact Reader",
    ):
        assert marker in html

    for misleading in (
        "ready for live trading",
        "production ready",
        "realtime ready",
        "buy signal",
        "sell signal",
        "trade recommendation",
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
            WATCHLIST_SNAPSHOT,
            SIGNAL_SNAPSHOT,
            RISK_SNAPSHOT,
            OPERATOR_TIMELINE,
            ARTIFACT_MANIFEST,
        )
    )
    for marker in ("http://", "https://", "cdn", "@import", "script src"):
        assert marker not in combined.lower()


def test_status_snapshot_preserves_market_data_block_and_disabled_flags() -> None:
    snapshot = build_status_snapshot(generated_at="2026-05-31T00:00:00+00:00")
    assert snapshot["ui_status"] == "DASHBOARD_UI_V2_DATA_PANEL_READY"
    assert snapshot["market_data_status"] == "BLOCKED_BY_SUBSCRIPTION"
    assert snapshot["market_data_classification"] == "MARKET_DATA_BLOCKED_BY_SUBSCRIPTION"
    assert snapshot["realtime_market_data_verified"] == "NO"
    assert snapshot["production_ready"] == "NO"
    assert snapshot["trading_enabled"] == "NO"
    assert snapshot["account_read_enabled"] == "NO"
    assert snapshot["positions_read_enabled"] == "NO"
    assert snapshot["historical_data_enabled"] == "NO"
    assert snapshot["telegram_real_send_enabled"] == "NO"
    assert snapshot["external_effect"] == "NONE_LOCAL_ARTIFACT_GENERATION_ONLY"
    assert snapshot["ibkr_error_code"] == "10089"
    assert snapshot["panels"] == [
        "MVP_STATUS",
        "MARKET_DATA_BLOCK",
        "WATCHLIST",
        "SIGNAL_PANEL",
        "RISK_PANEL",
        "OPERATOR_TIMELINE",
        "ARTIFACT_READER",
        "JP_CN_FROZEN_SCOPE",
    ]


def test_signal_snapshot_contains_no_trade_signal_terms() -> None:
    signal = build_signal_snapshot(generated_at="2026-05-31T00:00:00+00:00")
    serialized = json.dumps(signal, sort_keys=True)
    for forbidden in ("BUY", "SELL", "target_price", "stop_loss", "take_profit"):
        assert forbidden not in serialized
    assert signal["trading_signal_enabled"] == "NO"
    assert signal["recommendation_enabled"] == "NO"


def test_watchlist_snapshot_contains_no_real_price_fields() -> None:
    watchlist = build_watchlist_snapshot(generated_at="2026-05-31T00:00:00+00:00")
    serialized = json.dumps(watchlist, sort_keys=True)
    for forbidden in ("last_price", "bid", "ask", "open", "high", "low", "close"):
        assert forbidden not in serialized
    assert [item["symbol"] for item in watchlist["symbols"]] == ["GLD", "SLV"]


def test_risk_snapshot_preserves_all_blocked_actions() -> None:
    risk = build_risk_snapshot(generated_at="2026-05-31T00:00:00+00:00")
    assert risk["blocked_actions"] == list(BLOCKED_ACTIONS)
    assert set(risk["enabled_flags"].values()) == {"NO"}


def test_repo_forbidden_local_files_are_not_pack_artifacts() -> None:
    assert "config.yaml" not in TARGET_ARTIFACTS
    assert "ibkr_market_data_api_errors.csv" not in TARGET_ARTIFACTS
