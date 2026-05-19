from __future__ import annotations

import csv

from src.ibkr_readonly_preflight_profile_aware_config_plan import (
    ADD_TEXT,
    KEEP_TEXT,
    LIVE_READONLY_PROFILE,
    PAPER_PROFILE,
    PROFILE_PLAN_BLOCKED_TEXT,
    PROFILE_PLAN_READY_TEXT,
    REVIEW_UPDATE_TEXT,
    ProfileAwareConfigPlanRow,
    build_ibkr_readonly_preflight_profile_aware_config_plan_rows,
    profile_aware_safe_config_block,
    write_ibkr_readonly_preflight_profile_aware_config_plan_csv,
    write_ibkr_readonly_preflight_profile_aware_config_plan_report,
)


def test_profile_aware_plan_auto_detects_live_readonly_and_keeps_live_port(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
ibkr:
  read_only_required: true
  account_mode: live
  host: 127.0.0.1
  port: 7496
  client_id: 1
  real_connection_allowed: false
  contract_qualification_allowed: false
  market_data_request_allowed: false
  historical_data_request_allowed: false
  trading_actions_allowed: false
""".strip(),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_preflight_profile_aware_config_plan_rows(config_path)
    non_final_rows = [row for row in rows if row.profile_plan_id != "FINAL"]

    assert len(rows) == 11
    assert all(row.selected_profile == LIVE_READONLY_PROFILE for row in rows)
    assert all(row.planned_action == KEEP_TEXT for row in non_final_rows)
    assert all(row.would_overwrite_existing == "false" for row in rows)
    assert rows[-1].profile_plan_status == PROFILE_PLAN_READY_TEXT


def test_profile_aware_plan_auto_detects_paper_and_keeps_paper_port(tmp_path):
    config_path = tmp_path / "paper.yaml"
    config_path.write_text(
        """
ibkr:
  read_only_required: true
  account_mode: paper
  host: 127.0.0.1
  port: 7497
  client_id: 1
  real_connection_allowed: false
  contract_qualification_allowed: false
  market_data_request_allowed: false
  historical_data_request_allowed: false
  trading_actions_allowed: false
""".strip(),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_preflight_profile_aware_config_plan_rows(config_path)

    assert all(row.selected_profile == PAPER_PROFILE for row in rows)
    assert all(row.planned_action == KEEP_TEXT for row in rows if row.profile_plan_id != "FINAL")
    assert rows[-1].profile_plan_status == PROFILE_PLAN_READY_TEXT


def test_profile_aware_plan_adds_missing_switches_without_changing_live_profile(tmp_path):
    config_path = tmp_path / "live_missing_switches.yaml"
    config_path.write_text(
        """
ibkr:
  read_only_required: true
  account_mode: live
  host: 127.0.0.1
  port: 7496
  client_id: 1
""".strip(),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_preflight_profile_aware_config_plan_rows(config_path)
    changes = {row.profile_plan_id: row.planned_action for row in rows}

    assert rows[-1].selected_profile == LIVE_READONLY_PROFILE
    assert changes["ACCOUNT_MODE"] == KEEP_TEXT
    assert changes["PORT"] == KEEP_TEXT
    assert changes["REAL_CONNECTION"] == ADD_TEXT
    assert changes["CONTRACT_QUALIFICATION"] == ADD_TEXT
    assert changes["MARKET_DATA"] == ADD_TEXT
    assert changes["HISTORICAL_DATA"] == ADD_TEXT
    assert changes["TRADING_ACTIONS"] == ADD_TEXT
    assert rows[-1].planned_action == ADD_TEXT
    assert rows[-1].would_overwrite_existing == "false"


def test_profile_aware_plan_explicit_paper_flags_live_config_for_review(tmp_path):
    config_path = tmp_path / "live.yaml"
    config_path.write_text(
        """
ibkr:
  read_only_required: true
  account_mode: live
  host: 127.0.0.1
  port: 7496
  client_id: 1
  real_connection_allowed: false
  contract_qualification_allowed: false
  market_data_request_allowed: false
  historical_data_request_allowed: false
  trading_actions_allowed: false
""".strip(),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_preflight_profile_aware_config_plan_rows(config_path, "paper")
    changes = {row.profile_plan_id: row.planned_action for row in rows}

    assert rows[-1].selected_profile == PAPER_PROFILE
    assert changes["ACCOUNT_MODE"] == REVIEW_UPDATE_TEXT
    assert changes["PORT"] == REVIEW_UPDATE_TEXT
    assert rows[-1].would_overwrite_existing == "true"


def test_profile_aware_plan_blocks_missing_input_source(tmp_path):
    missing_path = tmp_path / "missing.yaml"

    rows = build_ibkr_readonly_preflight_profile_aware_config_plan_rows(missing_path)

    assert rows[0].profile_plan_id == "INPUT_SOURCE"
    assert rows[0].profile_plan_status == PROFILE_PLAN_BLOCKED_TEXT
    assert rows[-1].profile_plan_status == PROFILE_PLAN_BLOCKED_TEXT
    assert all(row.config_file_modified == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_profile_aware_safe_config_blocks_are_profile_specific():
    live_block = profile_aware_safe_config_block("live-readonly")
    paper_block = profile_aware_safe_config_block("paper")

    assert "account_mode: live" in live_block
    assert "port: 7496" in live_block
    assert "account_mode: paper" in paper_block
    assert "port: 7497" in paper_block
    assert "real_connection_allowed: false" in live_block
    assert "trading_actions_allowed: false" in paper_block


def test_write_profile_aware_config_plan_csv_and_report(tmp_path):
    rows = [
        ProfileAwareConfigPlanRow(
            profile_plan_id="FINAL",
            profile_plan_name="Final profile-aware config plan decision",
            source_layer="Phase 14H",
            input_source="config.yaml",
            requested_profile="auto",
            selected_profile="live-readonly",
            profile_source="auto_detected",
            config_key="phase14h.profile_aware_config_plan_status",
            current_value="add=0;keep=10;review_update=0;overwrite=0",
            safe_value="PROFILE_AWARE_PLAN_ONLY",
            planned_action="KEEP",
            would_overwrite_existing="false",
            safe_config_line="",
            profile_plan_status="PROFILE_PLAN_READY",
            apply_mode="profile_aware_plan_only",
            config_file_modified="false",
            real_connection_allowed="false",
            tws_connection_allowed="false",
            ibkr_api_request_allowed="false",
            contract_qualification_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            order_action_allowed="false",
            cancel_action_allowed="false",
            rebalance_action_allowed="false",
            auto_trade_allowed="false",
            action_allowed="false",
            warning_flags="PREFLIGHT_PROFILE_AWARE_CONFIG_PLAN_DEFINED",
            notes="Profile-aware plan only.",
            timestamp_jst="2026-05-19T23:30:00+09:00",
            timestamp_et="2026-05-19T10:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "profile_plan.csv"
    md_path = tmp_path / "profile_plan.md"

    write_ibkr_readonly_preflight_profile_aware_config_plan_csv(csv_path, rows)
    write_ibkr_readonly_preflight_profile_aware_config_plan_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["profile_plan_id"] == "FINAL"
    assert csv_rows[0]["selected_profile"] == "live-readonly"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 14H IBKR Read-Only Preflight Profile-Aware Config Plan Report" in report
    assert "selected_profile: live-readonly" in report
    assert "account_mode: live" in report
    assert "port: 7496" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report
