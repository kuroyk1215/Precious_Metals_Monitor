from __future__ import annotations

import csv

from src.ibkr_readonly_connection_preflight_pack import (
    ALLOWLIST_DEFINED,
    FALSE_TEXT,
    PREFLIGHT_BLOCKED,
    PREFLIGHT_READY,
    ConnectionPreflightPackRow,
    build_ibkr_readonly_connection_preflight_pack_rows,
    write_ibkr_readonly_connection_preflight_pack_csv,
    write_ibkr_readonly_connection_preflight_pack_report,
)


def test_connection_preflight_pack_ready_for_complete_live_readonly_config(tmp_path):
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

    rows = build_ibkr_readonly_connection_preflight_pack_rows(config_path)
    final = rows[-1]

    assert final.preflight_status == PREFLIGHT_READY
    assert final.selected_profile == "live-readonly"
    assert final.current_call_allowed == "false"
    assert final.next_connection_phase_allowed == "false"
    assert all(row.action_allowed == "false" for row in rows)
    assert all(row.real_connection_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)


def test_connection_preflight_pack_blocked_when_config_incomplete(tmp_path):
    config_path = tmp_path / "incomplete.yaml"
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

    rows = build_ibkr_readonly_connection_preflight_pack_rows(config_path)
    final = rows[-1]

    assert final.preflight_status == PREFLIGHT_BLOCKED
    assert final.current_call_allowed == FALSE_TEXT
    assert final.next_connection_phase_allowed == FALSE_TEXT


def test_connection_preflight_pack_defines_allowlist_but_does_not_allow_current_calls(tmp_path):
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

    rows = build_ibkr_readonly_connection_preflight_pack_rows(config_path)
    allowlist_rows = [row for row in rows if row.preflight_status == ALLOWLIST_DEFINED]

    assert {row.future_allowed_call for row in allowlist_rows} == {
        "EClient.connect",
        "EClient.disconnect",
        "client.serverVersion",
        "client.twsConnectionTime",
    }
    assert all(row.current_call_allowed == "false" for row in allowlist_rows)
    assert all(row.next_connection_phase_allowed == "false" for row in allowlist_rows)


def test_connection_preflight_pack_blocks_missing_input_source(tmp_path):
    rows = build_ibkr_readonly_connection_preflight_pack_rows(tmp_path / "missing.yaml")
    final = rows[-1]

    assert rows[0].preflight_id == "INPUT_SOURCE"
    assert rows[0].preflight_status == PREFLIGHT_BLOCKED
    assert final.preflight_status == PREFLIGHT_BLOCKED
    assert all(row.current_call_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_write_connection_preflight_pack_csv_and_report(tmp_path):
    rows = [
        ConnectionPreflightPackRow(
            preflight_id="FINAL",
            preflight_name="Final connection preflight pack decision",
            source_layer="Phase 16A-16C",
            input_source="config.yaml",
            selected_profile="live-readonly",
            component="Phase 16A-16C",
            config_key="phase16.connection_preflight_pack_status",
            config_value="dry_run_ready=true",
            expected_value="preflight_pack_only",
            preflight_status="PREFLIGHT_READY",
            future_allowed_call="future_connect_disconnect_only",
            current_call_allowed="false",
            next_connection_phase_allowed="false",
            operator_approval_required="true",
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
            evidence="selected_profile=live-readonly",
            warning_flags="CONNECTION_PREFLIGHT_PACK_DEFINED",
            notes="Connection preflight only.",
            timestamp_jst="2026-05-20T10:30:00+09:00",
            timestamp_et="2026-05-19T21:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "connection_preflight.csv"
    md_path = tmp_path / "connection_preflight.md"

    write_ibkr_readonly_connection_preflight_pack_csv(csv_path, rows)
    write_ibkr_readonly_connection_preflight_pack_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["preflight_id"] == "FINAL"
    assert csv_rows[0]["current_call_allowed"] == "false"
    assert csv_rows[0]["next_connection_phase_allowed"] == "false"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 16A-16C IBKR Read-Only Connection Preflight Pack Report" in report
    assert "EClient.connect" in report
    assert "reqMktData" in report
    assert "no TWS connection" in report
    assert "no auto trade" in report
