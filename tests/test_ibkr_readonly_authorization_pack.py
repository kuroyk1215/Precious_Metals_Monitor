from __future__ import annotations

import csv

from src.ibkr_readonly_authorization_pack import (
    FALSE_TEXT,
    NOT_AUTHORIZED,
    AuthorizationPackRow,
    build_ibkr_readonly_authorization_pack_rows,
    write_ibkr_readonly_authorization_pack_csv,
    write_ibkr_readonly_authorization_pack_report,
)


def test_authorization_pack_not_authorized_even_when_preflight_ready(tmp_path):
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

    rows = build_ibkr_readonly_authorization_pack_rows(config_path)
    final = rows[-1]

    assert len(rows) == 6
    assert final.selected_profile == "live-readonly"
    assert final.authorization_status == NOT_AUTHORIZED
    assert final.operator_approved == "false"
    assert final.runtime_kill_switch_enabled == "true"
    assert final.current_connection_allowed == "false"
    assert final.next_real_connection_phase_allowed == "false"
    assert all(row.action_allowed == "false" for row in rows)
    assert all(row.real_connection_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)


def test_authorization_pack_blocks_incomplete_config(tmp_path):
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

    rows = build_ibkr_readonly_authorization_pack_rows(config_path)
    final = rows[-1]

    assert final.authorization_status == NOT_AUTHORIZED
    assert final.operator_approved == FALSE_TEXT
    assert final.next_real_connection_phase_allowed == FALSE_TEXT


def test_authorization_pack_blocks_missing_input_source(tmp_path):
    rows = build_ibkr_readonly_authorization_pack_rows(tmp_path / "missing.yaml")
    final = rows[-1]

    assert final.authorization_status == NOT_AUTHORIZED
    assert final.current_connection_allowed == FALSE_TEXT
    assert final.next_real_connection_phase_allowed == FALSE_TEXT
    assert all(row.action_allowed == FALSE_TEXT for row in rows)


def test_write_authorization_pack_csv_and_report(tmp_path):
    rows = [
        AuthorizationPackRow(
            authorization_id="FINAL",
            authorization_name="Final read-only authorization decision",
            source_layer="Phase 16D-16F",
            input_source="config.yaml",
            selected_profile="live-readonly",
            component="Phase 16D-16F",
            upstream_status="NOT_AUTHORIZED",
            authorization_status="NOT_AUTHORIZED",
            operator_approval_required="true",
            operator_approved="false",
            runtime_kill_switch_enabled="true",
            next_real_connection_phase_allowed="false",
            current_connection_allowed="false",
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
            evidence="operator_approved=false",
            warning_flags="AUTHORIZATION_PACK_DEFINED",
            notes="Authorization pack only.",
            timestamp_jst="2026-05-20T10:30:00+09:00",
            timestamp_et="2026-05-19T21:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "authorization.csv"
    md_path = tmp_path / "authorization.md"

    write_ibkr_readonly_authorization_pack_csv(csv_path, rows)
    write_ibkr_readonly_authorization_pack_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["authorization_id"] == "FINAL"
    assert csv_rows[0]["authorization_status"] == "NOT_AUTHORIZED"
    assert csv_rows[0]["operator_approved"] == "false"
    assert csv_rows[0]["next_real_connection_phase_allowed"] == "false"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 16D-16F IBKR Read-Only Authorization Pack Report" in report
    assert "final_authorization_status: NOT_AUTHORIZED" in report
    assert "operator_approved_count: 0" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report
