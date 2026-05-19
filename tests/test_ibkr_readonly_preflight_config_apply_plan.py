from __future__ import annotations

import csv

from src.ibkr_readonly_preflight_config_apply_plan import (
    ADD_TEXT,
    NO_CHANGE_TEXT,
    PLAN_BLOCKED_TEXT,
    PLAN_READY_TEXT,
    UPDATE_TEXT,
    PreflightConfigApplyPlanRow,
    build_ibkr_readonly_preflight_config_apply_plan_rows,
    write_ibkr_readonly_preflight_config_apply_plan_csv,
    write_ibkr_readonly_preflight_config_apply_plan_report,
)


def test_preflight_config_apply_plan_no_change_when_config_matches_template(tmp_path):
    config_path = tmp_path / "config.yaml"
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

    rows = build_ibkr_readonly_preflight_config_apply_plan_rows(config_path)

    assert len(rows) == 11
    non_final_rows = [row for row in rows if row.plan_id != "FINAL"]
    assert all(row.planned_change == NO_CHANGE_TEXT for row in non_final_rows)
    assert rows[-1].plan_id == "FINAL"
    assert rows[-1].plan_status == PLAN_READY_TEXT
    assert rows[-1].planned_change == NO_CHANGE_TEXT
    assert all(row.config_file_modified == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_preflight_config_apply_plan_adds_missing_ibkr_keys(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("runtime:\n  report_dir: reports\n", encoding="utf-8")

    rows = build_ibkr_readonly_preflight_config_apply_plan_rows(config_path)
    changes = {row.plan_id: row.planned_change for row in rows}

    assert changes["READ_ONLY_REQUIRED"] == ADD_TEXT
    assert changes["ACCOUNT_MODE"] == ADD_TEXT
    assert changes["HOST"] == ADD_TEXT
    assert changes["PORT"] == ADD_TEXT
    assert changes["CLIENT_ID"] == ADD_TEXT
    assert changes["REAL_CONNECTION"] == ADD_TEXT
    assert changes["CONTRACT_QUALIFICATION"] == ADD_TEXT
    assert changes["MARKET_DATA"] == ADD_TEXT
    assert changes["HISTORICAL_DATA"] == ADD_TEXT
    assert changes["TRADING_ACTIONS"] == ADD_TEXT
    assert rows[-1].plan_status == PLAN_READY_TEXT
    assert rows[-1].planned_change == UPDATE_TEXT


def test_preflight_config_apply_plan_updates_unsafe_values(tmp_path):
    config_path = tmp_path / "unsafe.yaml"
    config_path.write_text(
        """
ibkr:
  read_only_required: false
  account_mode: live
  host: remote.example.com
  port: 4001
  client_id: 99
  real_connection_allowed: true
  contract_qualification_allowed: true
  market_data_request_allowed: true
  historical_data_request_allowed: true
  trading_actions_allowed: true
""".strip(),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_preflight_config_apply_plan_rows(config_path)
    non_final_rows = [row for row in rows if row.plan_id != "FINAL"]

    assert all(row.planned_change == UPDATE_TEXT for row in non_final_rows)
    assert rows[-1].plan_status == PLAN_READY_TEXT
    assert rows[-1].planned_change == UPDATE_TEXT
    assert all(row.config_file_modified == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_preflight_config_apply_plan_blocks_missing_input_source(tmp_path):
    missing_path = tmp_path / "missing.yaml"

    rows = build_ibkr_readonly_preflight_config_apply_plan_rows(missing_path)

    assert rows[0].plan_id == "INPUT_SOURCE"
    assert rows[0].plan_status == PLAN_BLOCKED_TEXT
    assert rows[-1].plan_id == "FINAL"
    assert rows[-1].plan_status == PLAN_BLOCKED_TEXT
    assert all(row.config_file_modified == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_write_preflight_config_apply_plan_csv_and_report(tmp_path):
    rows = [
        PreflightConfigApplyPlanRow(
            plan_id="FINAL",
            plan_name="Final read-only preflight config apply plan decision",
            source_layer="Phase 14E",
            input_source="config.yaml",
            config_key="phase14e.preflight_config_apply_plan_status",
            expected_value="PLAN_ONLY",
            actual_value="add=0;update=0;no_change=10",
            planned_change="NO_CHANGE",
            plan_status="PLAN_READY",
            apply_mode="plan_only",
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
            warning_flags="PREFLIGHT_CONFIG_APPLY_PLAN_DEFINED;NO_CONFIG_FILE_MODIFICATION",
            notes="Apply plan only.",
            timestamp_jst="2026-05-19T23:30:00+09:00",
            timestamp_et="2026-05-19T10:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "apply_plan.csv"
    md_path = tmp_path / "apply_plan.md"

    write_ibkr_readonly_preflight_config_apply_plan_csv(csv_path, rows)
    write_ibkr_readonly_preflight_config_apply_plan_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["plan_id"] == "FINAL"
    assert csv_rows[0]["planned_change"] == "NO_CHANGE"
    assert csv_rows[0]["config_file_modified"] == "false"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 14E IBKR Read-Only Preflight Config Apply Plan Report" in report
    assert "Phase 14E final plan status: PLAN_READY" in report
    assert "no configuration file is modified" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report
