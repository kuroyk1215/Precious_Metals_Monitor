from __future__ import annotations

import csv

from src.ibkr_readonly_connection_log_heartbeat_guard import (
    DRY_RUN_READY,
    PASS_STATUS,
    ConnectionLogHeartbeatGuardRow,
    build_ibkr_readonly_connection_log_heartbeat_guard_rows,
    write_ibkr_readonly_connection_log_heartbeat_guard_csv,
    write_ibkr_readonly_connection_log_heartbeat_guard_report,
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


def test_connection_log_heartbeat_guard_default_is_dry_run(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(LIVE_CONFIG, encoding="utf-8")

    rows = build_ibkr_readonly_connection_log_heartbeat_guard_rows(config_path, execute=False)
    final = rows[-1]

    assert final.status == DRY_RUN_READY
    assert final.connection_attempted == "false"
    assert final.current_call_allowed == "false"
    assert all(row.market_data_request_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.contract_qualification_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_connection_log_heartbeat_guard_execute_uses_fake_connector_metadata(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(LIVE_CONFIG, encoding="utf-8")
    fake = FakeConnector()

    rows = build_ibkr_readonly_connection_log_heartbeat_guard_rows(
        config_path,
        execute=True,
        connector_factory=lambda: fake,
    )
    final = rows[-1]

    assert fake.connect_called is True
    assert fake.disconnect_called is True
    assert final.status == PASS_STATUS
    assert final.connection_attempted == "true"
    assert final.connect_succeeded == "true"
    assert final.disconnect_succeeded == "true"
    assert final.server_version == "123"
    assert final.connection_time == "2026-05-20T10:30:00"
    assert final.heartbeat_metadata_available == "true"


def test_connection_log_heartbeat_guard_blocks_incomplete_config(tmp_path):
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

    rows = build_ibkr_readonly_connection_log_heartbeat_guard_rows(config_path, execute=True)
    final = rows[-1]

    assert final.status == "FAIL"
    assert final.connection_attempted == "false"
    assert final.connect_succeeded == "false"
    assert final.heartbeat_metadata_available == "false"


def test_write_connection_log_heartbeat_guard_csv_and_report(tmp_path):
    rows = [
        ConnectionLogHeartbeatGuardRow(
            row_id="FIRST_CONNECT_SUMMARY",
            row_name="Phase 17A first connect/disconnect summary",
            source_layer="Phase 17C-17D",
            input_source="config.yaml",
            selected_profile="live-readonly",
            execute_requested="true",
            component="connection_log",
            status="PASS",
            first_connect_status="PASS",
            connection_attempted="true",
            connect_succeeded="true",
            disconnect_succeeded="true",
            server_version="123",
            connection_time="2026-05-20T10:30:00",
            heartbeat_metadata_available="true",
            log_retention_required="true",
            current_call_allowed="true",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            contract_qualification_allowed="false",
            order_action_allowed="false",
            cancellation_action_allowed="false",
            rebalance_action_allowed="false",
            auto_trade_allowed="false",
            action_allowed="false",
            evidence="metadata",
            warning_flags="CONNECTION_LOG_HEARTBEAT_GUARD_DEFINED",
            notes="Summary row.",
            timestamp_jst="2026-05-20T10:30:00+09:00",
            timestamp_et="2026-05-19T21:30:00-04:00",
        ),
        ConnectionLogHeartbeatGuardRow(
            row_id="FINAL",
            row_name="Final connection log and heartbeat guard decision",
            source_layer="Phase 17C-17D",
            input_source="config.yaml",
            selected_profile="live-readonly",
            execute_requested="true",
            component="final",
            status="PASS",
            first_connect_status="PASS",
            connection_attempted="true",
            connect_succeeded="true",
            disconnect_succeeded="true",
            server_version="123",
            connection_time="2026-05-20T10:30:00",
            heartbeat_metadata_available="true",
            log_retention_required="true",
            current_call_allowed="true",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            contract_qualification_allowed="false",
            order_action_allowed="false",
            cancellation_action_allowed="false",
            rebalance_action_allowed="false",
            auto_trade_allowed="false",
            action_allowed="false",
            evidence="summary",
            warning_flags="CONNECTION_LOG_HEARTBEAT_GUARD_DEFINED",
            notes="Final row.",
            timestamp_jst="2026-05-20T10:30:00+09:00",
            timestamp_et="2026-05-19T21:30:00-04:00",
        ),
    ]

    csv_path = tmp_path / "guard.csv"
    md_path = tmp_path / "guard.md"

    write_ibkr_readonly_connection_log_heartbeat_guard_csv(csv_path, rows)
    write_ibkr_readonly_connection_log_heartbeat_guard_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["row_id"] == "FIRST_CONNECT_SUMMARY"
    assert csv_rows[0]["current_call_allowed"] == "true"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 17C-17D IBKR Read-Only Connection Log Heartbeat Guard Report" in report
    assert "connection_attempt_count: 1" in report
    assert "current_call_allowed_count: 1" in report
    assert "counter_scope: FIRST_CONNECT_SUMMARY row only" in report
    assert "no market data request" in report
    assert "no auto trade" in report


class FakeConnectorNoConnectionTime:
    def __init__(self):
        self.connect_called = False
        self.disconnect_called = False

    def connect(self, host, port, clientId, readonly):
        self.connect_called = True

    def disconnect(self):
        self.disconnect_called = True

    def serverVersion(self):
        return 176


def test_connection_log_heartbeat_guard_passes_with_server_version_only(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(LIVE_CONFIG, encoding="utf-8")
    fake = FakeConnectorNoConnectionTime()

    rows = build_ibkr_readonly_connection_log_heartbeat_guard_rows(
        config_path,
        execute=True,
        connector_factory=lambda: fake,
    )

    final = rows[-1]
    heartbeat = [row for row in rows if row.row_id == "HEARTBEAT_METADATA_GUARD"][0]

    assert fake.connect_called is True
    assert fake.disconnect_called is True
    assert final.status == "PASS"
    assert heartbeat.status == "HEARTBEAT_READY"
    assert heartbeat.server_version == "176"
    assert heartbeat.connection_time == "unavailable"
    assert heartbeat.heartbeat_metadata_available == "true"
    assert final.action_allowed == "false"
