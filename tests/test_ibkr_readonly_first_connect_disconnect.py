from __future__ import annotations

import csv

from src.ibkr_readonly_first_connect_disconnect import (
    DRY_RUN_READY,
    PASS_TEXT,
    FirstConnectDisconnectRow,
    build_ibkr_readonly_first_connect_disconnect_rows,
    write_ibkr_readonly_first_connect_disconnect_csv,
    write_ibkr_readonly_first_connect_disconnect_report,
)


LIVE_CONFIG = """
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
""".strip()


class FakeConnector:
    def __init__(self):
        self.connect_called = False
        self.disconnect_called = False

    def connect(self, host, port, clientId, readonly):
        self.connect_called = True
        assert host == "127.0.0.1"
        assert port == 7496
        assert clientId == 1
        assert readonly is True

    def disconnect(self):
        self.disconnect_called = True

    def serverVersion(self):
        return 123

    def twsConnectionTime(self):
        return "2026-05-20T10:30:00"


def test_first_connect_disconnect_default_is_dry_run(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(LIVE_CONFIG, encoding="utf-8")

    rows = build_ibkr_readonly_first_connect_disconnect_rows(config_path, execute=False)
    final = rows[-1]

    assert final.status == DRY_RUN_READY
    assert final.connection_attempted == "false"
    assert final.current_call_allowed == "false"
    assert all(row.market_data_request_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.contract_qualification_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_first_connect_disconnect_execute_uses_fake_connector(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(LIVE_CONFIG, encoding="utf-8")
    fake = FakeConnector()

    rows = build_ibkr_readonly_first_connect_disconnect_rows(
        config_path,
        execute=True,
        connector_factory=lambda: fake,
    )
    final = rows[-1]

    assert fake.connect_called is True
    assert fake.disconnect_called is True
    assert final.status == PASS_TEXT
    assert final.connection_attempted == "true"
    assert final.connect_succeeded == "true"
    assert final.disconnect_succeeded == "true"
    assert final.server_version == "123"
    assert final.connection_time == "2026-05-20T10:30:00"
    assert all(row.action_allowed == "false" for row in rows)


def test_first_connect_disconnect_blocks_incomplete_config(tmp_path):
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

    rows = build_ibkr_readonly_first_connect_disconnect_rows(config_path, execute=True)
    final = rows[-1]

    assert final.status == "FAIL"
    assert final.connection_attempted == "false"
    assert final.current_call_allowed == "false"


def test_write_first_connect_disconnect_csv_and_report(tmp_path):
    rows = [
        FirstConnectDisconnectRow(
            row_id="FINAL",
            row_name="Final first read-only connect/disconnect decision",
            source_layer="Phase 17A",
            input_source="config.yaml",
            selected_profile="live-readonly",
            execute_requested="false",
            component="final",
            status="DRY_RUN_READY",
            host="127.0.0.1",
            port="7496",
            client_id="1",
            server_version="not_requested",
            connection_time="not_requested",
            connection_attempted="false",
            connect_succeeded="false",
            disconnect_attempted="false",
            disconnect_succeeded="false",
            current_call_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            contract_qualification_allowed="false",
            order_action_allowed="false",
            cancel_action_allowed="false",
            rebalance_action_allowed="false",
            auto_trade_allowed="false",
            action_allowed="false",
            evidence="dry_run",
            warning_flags="FIRST_CONNECT_DISCONNECT_DEFINED",
            notes="Dry-run only.",
            timestamp_jst="2026-05-20T10:30:00+09:00",
            timestamp_et="2026-05-19T21:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "first_connect.csv"
    md_path = tmp_path / "first_connect.md"

    write_ibkr_readonly_first_connect_disconnect_csv(csv_path, rows)
    write_ibkr_readonly_first_connect_disconnect_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["row_id"] == "FINAL"
    assert csv_rows[0]["current_call_allowed"] == "false"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 17A IBKR First Read-Only Connect/Disconnect Report" in report
    assert "Default mode is dry-run" in report
    assert "no market data request" in report
    assert "no auto trade" in report
