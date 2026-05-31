from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from src.operator_post_ui_freeze_handoff_data_roadmap_pack import (
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
    MARKET_SCOPE_STATUS_SNAPSHOT,
    NEXT_ROADMAP_SNAPSHOT,
    OPERATOR_NEXT_ACTIONS_SNAPSHOT,
    OPERATOR_TIMELINE,
    OUTPUT_CSV,
    OUTPUT_PACK,
    OUTPUT_REPORT,
    POST_UI_FREEZE_HANDOFF_SNAPSHOT,
    STATUS,
    STATUS_SNAPSHOT,
    generate_post_ui_freeze_handoff_data_roadmap_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_INDEX = "dashboard/index.html"
DASHBOARD_CSS = "dashboard/assets/style.css"
TARGET_ARTIFACTS = (
    STATUS_SNAPSHOT,
    POST_UI_FREEZE_HANDOFF_SNAPSHOT,
    NEXT_ROADMAP_SNAPSHOT,
    MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
    MARKET_SCOPE_STATUS_SNAPSHOT,
    OPERATOR_NEXT_ACTIONS_SNAPSHOT,
    BUILD_SNAPSHOT,
    OPERATOR_TIMELINE,
    ARTIFACT_MANIFEST,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_PACK,
)


def _generate(tmp_path: Path) -> None:
    generate_post_ui_freeze_handoff_data_roadmap_pack(
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_post_ui_freeze_handoff_snapshot=tmp_path / POST_UI_FREEZE_HANDOFF_SNAPSHOT,
        output_next_roadmap_snapshot=tmp_path / NEXT_ROADMAP_SNAPSHOT,
        output_market_data_source_decision_snapshot=tmp_path / MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
        output_market_scope_status_snapshot=tmp_path / MARKET_SCOPE_STATUS_SNAPSHOT,
        output_operator_next_actions_snapshot=tmp_path / OPERATOR_NEXT_ACTIONS_SNAPSHOT,
        output_build_snapshot=tmp_path / BUILD_SNAPSHOT,
        output_operator_timeline=tmp_path / OPERATOR_TIMELINE,
        output_artifact_manifest=tmp_path / ARTIFACT_MANIFEST,
        output_csv=tmp_path / OUTPUT_CSV,
        output_report=tmp_path / OUTPUT_REPORT,
        output_pack=tmp_path / OUTPUT_PACK,
        generated_at="2026-05-31T00:00:00+00:00",
    )


def test_builder_generates_all_target_artifacts(tmp_path: Path) -> None:
    row = generate_post_ui_freeze_handoff_data_roadmap_pack(
        output_status_snapshot=tmp_path / STATUS_SNAPSHOT,
        output_post_ui_freeze_handoff_snapshot=tmp_path / POST_UI_FREEZE_HANDOFF_SNAPSHOT,
        output_next_roadmap_snapshot=tmp_path / NEXT_ROADMAP_SNAPSHOT,
        output_market_data_source_decision_snapshot=tmp_path / MARKET_DATA_SOURCE_DECISION_SNAPSHOT,
        output_market_scope_status_snapshot=tmp_path / MARKET_SCOPE_STATUS_SNAPSHOT,
        output_operator_next_actions_snapshot=tmp_path / OPERATOR_NEXT_ACTIONS_SNAPSHOT,
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


def test_cli_generates_pack_successfully_without_monitor_flow(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--post-ui-freeze-handoff-data-roadmap-pack"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert "status=POST_UI_FREEZE_HANDOFF_DATA_ROADMAP_READY" in result.stdout
    assert "market_data_source_decision_status=MARKET_DATA_SOURCE_DECISION_FRAMEWORK_READY" in result.stdout
    assert "market_data_status=BLOCKED_BY_SUBSCRIPTION" in result.stdout
    assert "realtime_market_data_verified=NO" in result.stdout
    for relative_path in TARGET_ARTIFACTS:
        assert (tmp_path / relative_path).exists()


def test_builder_does_not_generate_dashboard_index_or_css(tmp_path: Path) -> None:
    _generate(tmp_path)

    assert not (tmp_path / DASHBOARD_INDEX).exists()
    assert not (tmp_path / DASHBOARD_CSS).exists()


def test_handoff_snapshot_records_freeze_and_commit_context(tmp_path: Path) -> None:
    _generate(tmp_path)
    snapshot = json.loads((tmp_path / POST_UI_FREEZE_HANDOFF_SNAPSHOT).read_text(encoding="utf-8"))

    assert snapshot["status"] == "POST_UI_FREEZE_OPERATOR_HANDOFF_READY"
    assert snapshot["latest_main_commit"] == "3909b6c"
    assert snapshot["latest_merged_pr"] == 225
    assert snapshot["frozen_ui_generation"] == "V7_HIGH_TECH_TRADING_VISUAL_FROZEN"
    assert "config.yaml" in snapshot["forbidden_commit_files"]
    assert "ibkr_market_data_api_errors.csv" in snapshot["forbidden_commit_files"]


def test_next_roadmap_snapshot_records_priority_and_non_recommended_tracks(tmp_path: Path) -> None:
    _generate(tmp_path)
    snapshot = json.loads((tmp_path / NEXT_ROADMAP_SNAPSHOT).read_text(encoding="utf-8"))

    assert snapshot["status"] == "NEXT_ROADMAP_READY"
    assert "MARKET_DATA_SOURCE_DECISION" in snapshot["priority_tracks"]
    assert "US_GLD_SLV_FIRST" in snapshot["priority_tracks"]
    assert "JP_CN_REMAIN_FROZEN_UNTIL_SOURCE_DECISION" in snapshot["priority_tracks"]
    assert "MORE_UI_REDESIGN" in snapshot["not_recommended_now"]


def test_market_data_source_decision_snapshot_records_blocker_and_options(tmp_path: Path) -> None:
    _generate(tmp_path)
    snapshot = json.loads((tmp_path / MARKET_DATA_SOURCE_DECISION_SNAPSHOT).read_text(encoding="utf-8"))

    assert snapshot["status"] == "MARKET_DATA_SOURCE_DECISION_FRAMEWORK_READY"
    assert snapshot["current_blocker"] == "IBKR_ERROR_10089_SUBSCRIPTION_REQUIRED"
    for option in (
        "IBKR_SUBSCRIBE_NETWORK_B_ARCA",
        "FREE_DELAYED_PUBLIC_SOURCE",
        "MANUAL_CSV_SOURCE",
        "PAID_MARKET_DATA_API",
        "HYBRID_SOURCE_ROUTER",
    ):
        assert option in snapshot["source_options"]
    assert snapshot["live_market_data_enabled"] == "NO"
    assert snapshot["source_connection_implemented"] == "NO"


def test_market_scope_status_snapshot_records_us_jp_cn_state(tmp_path: Path) -> None:
    _generate(tmp_path)
    snapshot = json.loads((tmp_path / MARKET_SCOPE_STATUS_SNAPSHOT).read_text(encoding="utf-8"))

    assert snapshot["markets"]["US"]["scope"] == "GLD_SLV_ONLY"
    assert snapshot["markets"]["JP"]["status"] == "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION"
    assert snapshot["markets"]["CN"]["status"] == "FROZEN_PENDING_DATA_SOURCE_DECISION"


def test_operator_next_actions_snapshot_records_blocked_actions(tmp_path: Path) -> None:
    _generate(tmp_path)
    snapshot = json.loads((tmp_path / OPERATOR_NEXT_ACTIONS_SNAPSHOT).read_text(encoding="utf-8"))

    assert snapshot["status"] == "OPERATOR_NEXT_ACTIONS_READY"
    for action in ("IBKR_CONNECT", "MARKET_DATA_REQUEST", "ORDER_SUBMIT", "TELEGRAM_REAL_SEND"):
        assert action in snapshot["blocked_actions"]


def test_status_snapshot_preserves_blockers_and_disabled_runtime_flags(tmp_path: Path) -> None:
    _generate(tmp_path)
    status = json.loads((tmp_path / STATUS_SNAPSHOT).read_text(encoding="utf-8"))

    assert status["status"] == "POST_UI_FREEZE_HANDOFF_DATA_ROADMAP_READY"
    assert status["market_data_source_decision_status"] == "MARKET_DATA_SOURCE_DECISION_FRAMEWORK_READY"
    assert status["market_data_status"] == "BLOCKED_BY_SUBSCRIPTION"
    assert status["realtime_market_data_verified"] == "NO"
    assert status["production_ready"] == "NO"
    assert status["trading_enabled"] == "NO"
    assert status["account_read_enabled"] == "NO"
    assert status["positions_read_enabled"] == "NO"
    assert status["historical_data_enabled"] == "NO"
    assert status["telegram_real_send_enabled"] == "NO"


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


def test_existing_dashboard_html_and_css_are_not_modified(tmp_path: Path) -> None:
    index_path = tmp_path / DASHBOARD_INDEX
    css_path = tmp_path / DASHBOARD_CSS
    index_path.parent.mkdir(parents=True, exist_ok=True)
    css_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("frozen html\n", encoding="utf-8")
    css_path.write_text("frozen css\n", encoding="utf-8")

    _generate(tmp_path)

    assert index_path.read_text(encoding="utf-8") == "frozen html\n"
    assert css_path.read_text(encoding="utf-8") == "frozen css\n"


def test_generator_does_not_touch_forbidden_local_residue_files(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    error_csv_path = tmp_path / "ibkr_market_data_api_errors.csv"
    config_path.write_text("local: config\n", encoding="utf-8")
    error_csv_path.write_text("code,message\n10089,subscription\n", encoding="utf-8")

    _generate(tmp_path)

    assert config_path.read_text(encoding="utf-8") == "local: config\n"
    assert error_csv_path.read_text(encoding="utf-8") == "code,message\n10089,subscription\n"


def test_generated_artifacts_record_no_external_or_live_runtime_actions(tmp_path: Path) -> None:
    _generate(tmp_path)
    status = json.loads((tmp_path / STATUS_SNAPSHOT).read_text(encoding="utf-8"))
    source = json.loads((tmp_path / MARKET_DATA_SOURCE_DECISION_SNAPSHOT).read_text(encoding="utf-8"))
    actions = json.loads((tmp_path / OPERATOR_NEXT_ACTIONS_SNAPSHOT).read_text(encoding="utf-8"))

    assert status["external_effect"] == "NONE_LOCAL_ARTIFACT_GENERATION_ONLY"
    assert status["historical_data_enabled"] == "NO"
    assert status["account_read_enabled"] == "NO"
    assert status["positions_read_enabled"] == "NO"
    assert status["telegram_real_send_enabled"] == "NO"
    assert source["source_connection_implemented"] == "NO"
    assert source["live_market_data_enabled"] == "NO"
    for action in (
        "IBKR_CONNECT",
        "MARKET_DATA_REQUEST",
        "HISTORICAL_DATA_REQUEST",
        "ACCOUNT_READ",
        "POSITION_READ",
        "CONTRACT_QUALIFICATION",
        "TELEGRAM_REAL_SEND",
    ):
        assert action in actions["blocked_actions"]
