from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from src.operator_dashboard_icon_timeline_artifact_polish_pack import (
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    CARD_SYSTEM_SNAPSHOT,
    DASHBOARD_CSS,
    DASHBOARD_INDEX,
    ICON_SYSTEM_SNAPSHOT,
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
    TIMELINE_POLISH_SNAPSHOT,
    VISUAL_DENSITY_SNAPSHOT,
    WATCHLIST_SNAPSHOT,
    generate_dashboard_icon_timeline_artifact_polish_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


TARGET_ARTIFACTS = (
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    STATUS_SNAPSHOT,
    ICON_SYSTEM_SNAPSHOT,
    TIMELINE_POLISH_SNAPSHOT,
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


def _generate(tmp_path: Path) -> None:
    generate_dashboard_icon_timeline_artifact_polish_pack(
        output_index=tmp_path / DASHBOARD_INDEX,
        output_css=tmp_path / DASHBOARD_CSS,
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_icon_system_snapshot=tmp_path / ICON_SYSTEM_SNAPSHOT,
        output_timeline_polish_snapshot=tmp_path / TIMELINE_POLISH_SNAPSHOT,
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
    row = generate_dashboard_icon_timeline_artifact_polish_pack(
        output_index=tmp_path / DASHBOARD_INDEX,
        output_css=tmp_path / DASHBOARD_CSS,
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_icon_system_snapshot=tmp_path / ICON_SYSTEM_SNAPSHOT,
        output_timeline_polish_snapshot=tmp_path / TIMELINE_POLISH_SNAPSHOT,
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
        ["python3", str(REPO_ROOT / "main.py"), "--dashboard-icon-timeline-artifact-polish-pack"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert "status=DASHBOARD_ICON_TIMELINE_ARTIFACT_POLISH_READY" in result.stdout
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


def test_dashboard_index_contains_v5_sections_and_local_css(tmp_path: Path) -> None:
    _generate(tmp_path)
    html = (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8")

    assert '<link rel="stylesheet" href="assets/style.css">' in html
    for marker in (
        "DASHBOARD_ICON_TIMELINE_ARTIFACT_POLISH_READY",
        "V5_ICON_TIMELINE_ARTIFACT_POLISH",
        "LOCAL_ICON_SYSTEM_READY",
        "COMPACT_TIMELINE_POLISHED",
        "FILE_BROWSER_STYLE_READY",
        "Artifact Reader",
        "Operator Timeline",
        "Build / Version / Safety",
        "No IBKR connection",
        "No market data request",
    ):
        assert marker in html


def test_html_css_and_json_do_not_load_external_resources(tmp_path: Path) -> None:
    _generate(tmp_path)
    combined = "\n".join(
        (tmp_path / relative_path).read_text(encoding="utf-8")
        for relative_path in (
            DASHBOARD_INDEX,
            DASHBOARD_CSS,
            STATUS_SNAPSHOT,
            ICON_SYSTEM_SNAPSHOT,
            TIMELINE_POLISH_SNAPSHOT,
            ARTIFACT_MANIFEST,
            BUILD_SNAPSHOT,
        )
    )
    for marker in ("http://", "https://", "cdn", "@import", "script src"):
        assert marker not in combined


def test_icon_system_snapshot_uses_local_text_tokens(tmp_path: Path) -> None:
    _generate(tmp_path)
    icon_system = json.loads((tmp_path / ICON_SYSTEM_SNAPSHOT).read_text(encoding="utf-8"))

    assert icon_system["status"] == "LOCAL_ICON_SYSTEM_READY"
    assert icon_system["icon_mode"] == "TEXT_ONLY_LOCAL_ICON_TOKENS"
    assert icon_system["external_icon_library"] == "NO"
    assert icon_system["remote_icon_assets"] == "NO"
    for token in ("DASHBOARD", "WATCHLIST", "SIGNAL", "RISK", "ARTIFACT", "TIMELINE", "SYSTEM", "SETTINGS", "LOCAL", "READ_ONLY", "BLOCKED", "WARNING", "SAFETY"):
        assert token in icon_system["icon_tokens"]


def test_timeline_polish_snapshot_contains_phase_665_672(tmp_path: Path) -> None:
    _generate(tmp_path)
    timeline_polish = json.loads((tmp_path / TIMELINE_POLISH_SNAPSHOT).read_text(encoding="utf-8"))
    operator_timeline = json.loads((tmp_path / OPERATOR_TIMELINE).read_text(encoding="utf-8"))

    assert timeline_polish["status"] == "COMPACT_TIMELINE_POLISHED"
    assert timeline_polish["timeline_mode"] == "STATIC_OPERATOR_PHASE_TIMELINE"
    assert "Phase 665-672" in timeline_polish["timeline_items"]
    assert len(operator_timeline["timeline"]) == 5
    assert all("visual_tier" in item for item in operator_timeline["timeline"])


def test_artifact_manifest_uses_local_browser_fields_without_metadata(tmp_path: Path) -> None:
    _generate(tmp_path)
    manifest = json.loads((tmp_path / ARTIFACT_MANIFEST).read_text(encoding="utf-8"))

    for artifact in manifest["artifacts"]:
        assert artifact["external_effect"] == "NONE_LOCAL_ARTIFACT_GENERATION_ONLY"
        assert "http://" not in artifact["local_href"]
        assert "https://" not in artifact["local_href"]
        assert "icon_token" in artifact
        assert "file_size" not in artifact
        assert "mtime" not in artifact


def test_build_snapshot_records_phase_665_672_basis_and_disabled_flags(tmp_path: Path) -> None:
    _generate(tmp_path)
    build = json.loads((tmp_path / BUILD_SNAPSHOT).read_text(encoding="utf-8"))

    assert build["latest_main_commit"] == "20fd4fa"
    assert build["latest_merged_pr"] == "221"
    assert build["production_ready"] == "NO"
    assert build["trading_enabled"] == "NO"
    assert build["ui_generation"] == "V5_ICON_TIMELINE_ARTIFACT_POLISH"


def test_status_snapshot_preserves_blocked_market_data_and_safety_flags(tmp_path: Path) -> None:
    _generate(tmp_path)
    status = json.loads((tmp_path / STATUS_SNAPSHOT).read_text(encoding="utf-8"))

    assert status["ui_status"] == "DASHBOARD_ICON_TIMELINE_ARTIFACT_POLISH_READY"
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


def test_watchlist_omits_live_price_fields(tmp_path: Path) -> None:
    _generate(tmp_path)
    watchlist_text = (tmp_path / WATCHLIST_SNAPSHOT).read_text(encoding="utf-8")

    for forbidden in ("last_price", "bid", "ask", "open", "high", "low", "close"):
        assert forbidden not in watchlist_text


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
