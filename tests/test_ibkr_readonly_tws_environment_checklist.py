from __future__ import annotations

import csv

from src.ibkr_readonly_tws_environment_checklist import (
    CHECKLIST_BLOCKED_TEXT,
    CHECKLIST_READY_TEXT,
    CONFIG_OK_TEXT,
    LIVE_READONLY_PROFILE,
    MANUAL_REQUIRED_TEXT,
    PAPER_PROFILE,
    TwsEnvironmentChecklistRow,
    build_ibkr_readonly_tws_environment_checklist_rows,
    write_ibkr_readonly_tws_environment_checklist_csv,
    write_ibkr_readonly_tws_environment_checklist_report,
)


def test_tws_environment_checklist_detects_live_readonly_profile(tmp_path):
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

    rows = build_ibkr_readonly_tws_environment_checklist_rows(config_path)

    assert len(rows) == 9
    assert all(row.selected_profile == LIVE_READONLY_PROFILE for row in rows)
    assert rows[-1].checklist_status == CHECKLIST_READY_TEXT
    assert all(row.action_allowed == "false" for row in rows)

    by_id = {row.checklist_id: row for row in rows}
    assert by_id["TWS_LOGIN_MODE"].actual_config_value == "live"
    assert by_id["TWS_LOGIN_MODE"].checklist_status == CONFIG_OK_TEXT
    assert by_id["TWS_SOCKET_PORT"].actual_config_value == "7496"
    assert by_id["TWS_SOCKET_PORT"].checklist_status == CONFIG_OK_TEXT


def test_tws_environment_checklist_detects_paper_profile(tmp_path):
    config_path = tmp_path / "paper.yaml"
    config_path.write_text(
        """
ibkr:
  read_only_required: true
  account_mode: paper
  host: 127.0.0.1
  port: 7497
  client_id: 1
""".strip(),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_tws_environment_checklist_rows(config_path)

    assert all(row.selected_profile == PAPER_PROFILE for row in rows)
    by_id = {row.checklist_id: row for row in rows}
    assert by_id["TWS_LOGIN_MODE"].expected_setting == "paper"
    assert by_id["TWS_SOCKET_PORT"].expected_setting == "7497"
    assert rows[-1].checklist_status == CHECKLIST_READY_TEXT


def test_tws_environment_checklist_blocks_missing_input_source(tmp_path):
    missing_path = tmp_path / "missing.yaml"

    rows = build_ibkr_readonly_tws_environment_checklist_rows(missing_path)

    assert rows[0].checklist_id == "INPUT_SOURCE"
    assert rows[0].checklist_status == CHECKLIST_BLOCKED_TEXT
    assert rows[-1].checklist_status == CHECKLIST_BLOCKED_TEXT
    assert all(row.config_file_modified == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_tws_environment_checklist_manual_items_are_required(tmp_path):
    config_path = tmp_path / "live.yaml"
    config_path.write_text(
        """
ibkr:
  account_mode: live
  host: 127.0.0.1
  port: 7496
  client_id: 1
""".strip(),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_tws_environment_checklist_rows(config_path)
    by_id = {row.checklist_id: row for row in rows}

    assert by_id["TWS_INSTALLATION"].checklist_status == MANUAL_REQUIRED_TEXT
    assert by_id["TWS_API_ENABLED"].checklist_status == MANUAL_REQUIRED_TEXT
    assert by_id["TWS_READ_ONLY_API"].checklist_status == MANUAL_REQUIRED_TEXT
    assert by_id["ORDER_SAFETY_BOUNDARY"].checklist_status == MANUAL_REQUIRED_TEXT


def test_write_tws_environment_checklist_csv_and_report(tmp_path):
    rows = [
        TwsEnvironmentChecklistRow(
            checklist_id="FINAL",
            checklist_name="Final TWS environment checklist decision",
            source_layer="Phase 15A",
            input_source="config.yaml",
            selected_profile="live-readonly",
            external_item="phase15a.tws_environment_checklist_status",
            expected_setting="manual_review_required_before_any_connection_phase",
            actual_config_value="config_review=0;manual_required=8",
            checklist_status="READY_FOR_MANUAL_REVIEW",
            manual_check_required="true",
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
            warning_flags="TWS_ENVIRONMENT_CHECKLIST_DEFINED",
            notes="Checklist only.",
            timestamp_jst="2026-05-20T10:30:00+09:00",
            timestamp_et="2026-05-19T21:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "tws_environment_checklist.csv"
    md_path = tmp_path / "tws_environment_checklist.md"

    write_ibkr_readonly_tws_environment_checklist_csv(csv_path, rows)
    write_ibkr_readonly_tws_environment_checklist_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["checklist_id"] == "FINAL"
    assert csv_rows[0]["selected_profile"] == "live-readonly"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 15A IBKR Read-Only TWS Environment Checklist Report" in report
    assert "selected_profile: live-readonly" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report
