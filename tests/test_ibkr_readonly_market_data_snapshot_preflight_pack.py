from __future__ import annotations

import csv

from src.ibkr_readonly_market_data_snapshot_preflight_pack import (
    DRY_RUN_READY,
    PASS_STATUS,
    MarketDataSnapshotPreflightPackRow,
    build_ibkr_readonly_market_data_snapshot_preflight_pack_rows,
    write_ibkr_readonly_market_data_snapshot_preflight_pack_csv,
    write_ibkr_readonly_market_data_snapshot_preflight_pack_report,
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


class FakeTicker:
    bid = 100.0
    ask = 101.0
    last = 100.5
    close = 99.5

    def marketPrice(self):
        return 100.5


class FakeSnapshotConnector:
    def __init__(self):
        self.connect_called = False
        self.disconnect_called = False
        self.snapshot_called = False
        self.sleep_called = False

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

    def reqMktData(self, contract, genericTickList="", snapshot=False, regulatorySnapshot=False):
        self.snapshot_called = True
        assert getattr(contract, "symbol") == "1540"
        assert genericTickList == ""
        assert snapshot is True
        assert regulatorySnapshot is False
        return FakeTicker()

    def sleep(self, seconds):
        self.sleep_called = True
        assert seconds == 2


def test_market_data_snapshot_pack_default_is_dry_run(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(LIVE_CONFIG, encoding="utf-8")

    rows = build_ibkr_readonly_market_data_snapshot_preflight_pack_rows(config_path, execute=False)
    final = rows[-1]

    assert final.status == DRY_RUN_READY
    assert final.connection_attempted == "false"
    assert final.market_data_snapshot_request_attempted == "false"
    assert final.current_call_allowed == "false"
    assert all(row.streaming_market_data_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.contract_qualification_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_market_data_snapshot_pack_execute_uses_fake_connector(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(LIVE_CONFIG, encoding="utf-8")
    fake = FakeSnapshotConnector()

    class FakeIbContract:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    import src.ibkr_readonly_market_data_snapshot_preflight_pack as mod
    monkeypatch.setattr(mod, "_make_contract", lambda spec: FakeIbContract(**{
        "symbol": spec["symbol"],
        "secType": spec["sec_type"],
        "exchange": spec["exchange"],
        "currency": spec["currency"],
        "primaryExchange": spec["primary_exchange"],
    }))

    rows = build_ibkr_readonly_market_data_snapshot_preflight_pack_rows(
        config_path,
        execute=True,
        connector_factory=lambda: fake,
    )
    final = rows[-1]

    assert fake.connect_called is True
    assert fake.disconnect_called is True
    assert fake.snapshot_called is True
    assert fake.sleep_called is True
    assert final.status == PASS_STATUS
    assert final.connection_attempted == "true"
    assert final.connect_succeeded == "true"
    assert final.disconnect_succeeded == "true"
    assert final.market_data_snapshot_request_attempted == "true"
    assert final.market_data_snapshot_read_succeeded == "true"
    assert final.snapshot_last == "100.5"
    assert final.snapshot_market_price == "100.5"
    assert final.price_available == "true"
    assert final.action_allowed == "false"


def test_market_data_snapshot_pack_blocks_incomplete_config(tmp_path):
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

    rows = build_ibkr_readonly_market_data_snapshot_preflight_pack_rows(config_path, execute=True)
    final = rows[-1]

    assert final.status == "FAIL"
    assert final.connection_attempted == "false"
    assert final.market_data_snapshot_read_succeeded == "false"


def test_write_market_data_snapshot_pack_csv_and_report(tmp_path):
    rows = [
        MarketDataSnapshotPreflightPackRow(
            row_id="MARKET_DATA_SNAPSHOT_READ",
            row_name="First real read-only market data snapshot read",
            source_layer="Phase 20A-20C",
            input_source="config.yaml",
            selected_profile="live-readonly",
            execute_requested="true",
            component="Phase 20C",
            status="PASS",
            host="127.0.0.1",
            port="7496",
            client_id="1",
            contract_symbol="1540",
            contract_sec_type="STK",
            contract_exchange="SMART",
            contract_currency="JPY",
            contract_primary_exchange="TSEJ",
            server_version="176",
            connection_time="unavailable",
            snapshot_bid="100.0",
            snapshot_ask="101.0",
            snapshot_last="100.5",
            snapshot_close="99.5",
            snapshot_market_price="100.5",
            price_available="true",
            price_status="PRICE_AVAILABLE",
            connection_attempted="true",
            connect_succeeded="true",
            disconnect_attempted="true",
            disconnect_succeeded="true",
            market_data_snapshot_request_attempted="true",
            market_data_snapshot_read_succeeded="true",
            current_call_allowed="true",
            streaming_market_data_allowed="false",
            historical_data_request_allowed="false",
            contract_qualification_allowed="false",
            order_action_allowed="false",
            cancellation_action_allowed="false",
            rebalance_action_allowed="false",
            auto_trade_allowed="false",
            action_allowed="false",
            evidence="snapshot_only",
            warning_flags="MARKET_DATA_SNAPSHOT_PREFLIGHT_PACK_DEFINED",
            notes="Snapshot only.",
            timestamp_jst="2026-05-20T10:30:00+09:00",
            timestamp_et="2026-05-19T21:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "snapshot.csv"
    md_path = tmp_path / "snapshot.md"

    write_ibkr_readonly_market_data_snapshot_preflight_pack_csv(csv_path, rows)
    write_ibkr_readonly_market_data_snapshot_preflight_pack_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["row_id"] == "MARKET_DATA_SNAPSHOT_READ"
    assert csv_rows[0]["current_call_allowed"] == "true"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 20A-20C IBKR Read-Only Market Data Snapshot Preflight Pack Report" in report
    assert "market_data_snapshot_success_count: 1" in report
    assert "no historical data request" in report
    assert "no streaming market data" in report
    assert "no auto trade" in report
