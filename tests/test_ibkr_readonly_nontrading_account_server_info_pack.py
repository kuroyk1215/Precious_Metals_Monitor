from __future__ import annotations

import csv
from dataclasses import dataclass

from src.ibkr_readonly_nontrading_account_server_info_pack import (
    DRY_RUN_READY,
    PASS_TEXT,
    NonTradingAccountServerInfoRow,
    build_ibkr_readonly_nontrading_account_server_info_pack_rows,
    write_ibkr_readonly_nontrading_account_server_info_pack_csv,
    write_ibkr_readonly_nontrading_account_server_info_pack_report,
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


@dataclass(frozen=True)
class FakeSummaryItem:
    account: str
    tag: str
    value: str
    currency: str


class FakeNonTradingConnector:
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
        return 176

    def managedAccounts(self):
        return ["DU123456"]

    def accountSummary(self):
        return [
            FakeSummaryItem("DU123456", "NetLiquidation", "100000", "USD"),
            FakeSummaryItem("DU123456", "AvailableFunds", "90000", "USD"),
        ]


def test_nontrading_info_pack_default_is_dry_run(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(LIVE_CONFIG, encoding="utf-8")

    rows = build_ibkr_readonly_nontrading_account_server_info_pack_rows(config_path, execute=False)
    final = rows[-1]

    assert final.status == DRY_RUN_READY
    assert final.connection_attempted == "false"
    assert final.nontrading_info_request_attempted == "false"
    assert final.current_call_allowed == "false"
    assert all(row.market_data_request_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.contract_qualification_allowed == "false" for row in rows)
    assert all(row.contract_details_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_nontrading_info_pack_execute_uses_fake_connector(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(LIVE_CONFIG, encoding="utf-8")
    fake = FakeNonTradingConnector()

    rows = build_ibkr_readonly_nontrading_account_server_info_pack_rows(
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
    assert final.nontrading_info_request_attempted == "true"
    assert final.nontrading_info_read_succeeded == "true"
    assert final.server_version == "176"
    assert final.managed_accounts == "DU123456"
    assert "NetLiquidation" in final.account_summary_items
    assert final.action_allowed == "false"


def test_nontrading_info_pack_blocks_incomplete_config(tmp_path):
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

    rows = build_ibkr_readonly_nontrading_account_server_info_pack_rows(config_path, execute=True)
    final = rows[-1]

    assert final.status == "FAIL"
    assert final.connection_attempted == "false"
    assert final.nontrading_info_read_succeeded == "false"


def test_write_nontrading_info_pack_csv_and_report(tmp_path):
    rows = [
        NonTradingAccountServerInfoRow(
            row_id="NONTRADING_INFO_READ",
            row_name="First real non-trading account/server info read",
            source_layer="Phase 18A-18C",
            input_source="config.yaml",
            selected_profile="live-readonly",
            execute_requested="true",
            component="Phase 18C",
            status="PASS",
            host="127.0.0.1",
            port="7496",
            client_id="1",
            server_version="176",
            connection_time="unavailable",
            managed_accounts="DU123456",
            account_summary_items="DU123456:NetLiquidation:100000:USD",
            connection_attempted="true",
            connect_succeeded="true",
            disconnect_attempted="true",
            disconnect_succeeded="true",
            nontrading_info_request_attempted="true",
            nontrading_info_read_succeeded="true",
            current_call_allowed="true",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            contract_qualification_allowed="false",
            contract_details_request_allowed="false",
            order_action_allowed="false",
            cancellation_action_allowed="false",
            rebalance_action_allowed="false",
            auto_trade_allowed="false",
            action_allowed="false",
            evidence="metadata_only",
            warning_flags="NONTRADING_ACCOUNT_SERVER_INFO_PACK_DEFINED",
            notes="Non-trading info only.",
            timestamp_jst="2026-05-20T10:30:00+09:00",
            timestamp_et="2026-05-19T21:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "nontrading.csv"
    md_path = tmp_path / "nontrading.md"

    write_ibkr_readonly_nontrading_account_server_info_pack_csv(csv_path, rows)
    write_ibkr_readonly_nontrading_account_server_info_pack_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["row_id"] == "NONTRADING_INFO_READ"
    assert csv_rows[0]["current_call_allowed"] == "true"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 18A-18C IBKR Read-Only Non-Trading Account/Server Info Pack Report" in report
    assert "nontrading_info_success_count: 1" in report
    assert "no market data request" in report
    assert "no contract details request" in report
    assert "no auto trade" in report
