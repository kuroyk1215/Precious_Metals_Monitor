from __future__ import annotations

import csv

from src.ibkr_readonly_market_data_entitlement_diagnostic import (
    DIAGNOSTIC_EXECUTED,
    DIAGNOSTIC_READY,
    NO_MARKET_DATA_SUBSCRIPTION,
    PRICE_AVAILABLE,
    MarketDataEntitlementDiagnosticRow,
    build_ibkr_readonly_market_data_entitlement_diagnostic_rows,
    write_ibkr_readonly_market_data_entitlement_diagnostic_csv,
    write_ibkr_readonly_market_data_entitlement_diagnostic_report,
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


class FakeNoPriceTicker:
    bid = None
    ask = None
    last = None
    close = None

    def marketPrice(self):
        return None


class FakePriceTicker:
    bid = 100.0
    ask = 101.0
    last = 100.5
    close = 99.5

    def marketPrice(self):
        return 100.5


class FakeSnapshotConnector:
    def __init__(self, ticker):
        self.ticker = ticker
        self.connect_called = False
        self.disconnect_called = False
        self.snapshot_called = False

    def connect(self, host, port, clientId, readonly):
        self.connect_called = True
        assert readonly is True

    def disconnect(self):
        self.disconnect_called = True

    def serverVersion(self):
        return 176

    def reqMktData(self, contract, genericTickList="", snapshot=False, regulatorySnapshot=False):
        self.snapshot_called = True
        assert snapshot is True
        assert regulatorySnapshot is False
        return self.ticker

    def sleep(self, seconds):
        return None


def _patch_contract(monkeypatch):
    class FakeIbContract:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    import src.ibkr_readonly_market_data_snapshot_preflight_pack as snapshot_mod
    monkeypatch.setattr(snapshot_mod, "_make_contract", lambda spec: FakeIbContract(**{
        "symbol": spec["symbol"],
        "secType": spec["sec_type"],
        "exchange": spec["exchange"],
        "currency": spec["currency"],
        "primaryExchange": spec["primary_exchange"],
    }))


def test_market_data_entitlement_diagnostic_default_is_dry_run(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(LIVE_CONFIG, encoding="utf-8")

    rows = build_ibkr_readonly_market_data_entitlement_diagnostic_rows(config_path, execute=False)
    final = rows[-1]

    assert final.diagnostic_status == DIAGNOSTIC_READY
    assert final.snapshot_request_succeeded == "false"
    assert final.price_available == "false"
    assert final.action_allowed == "false"


def test_market_data_entitlement_diagnostic_classifies_no_price_as_10168(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(LIVE_CONFIG, encoding="utf-8")
    _patch_contract(monkeypatch)

    fake = FakeSnapshotConnector(FakeNoPriceTicker())

    rows = build_ibkr_readonly_market_data_entitlement_diagnostic_rows(
        config_path,
        execute=True,
        connector_factory=lambda: fake,
    )
    final = rows[-1]

    assert fake.connect_called is True
    assert fake.disconnect_called is True
    assert fake.snapshot_called is True
    assert final.diagnostic_status == DIAGNOSTIC_EXECUTED
    assert final.snapshot_request_succeeded == "true"
    assert final.price_available == "false"
    assert final.market_data_status == NO_MARKET_DATA_SUBSCRIPTION
    assert final.ibkr_error_code == "10168"
    assert final.delayed_data_enabled == "false"
    assert final.action_allowed == "false"


def test_market_data_entitlement_diagnostic_classifies_price_available(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(LIVE_CONFIG, encoding="utf-8")
    _patch_contract(monkeypatch)

    fake = FakeSnapshotConnector(FakePriceTicker())

    rows = build_ibkr_readonly_market_data_entitlement_diagnostic_rows(
        config_path,
        execute=True,
        connector_factory=lambda: fake,
    )
    final = rows[-1]

    assert final.diagnostic_status == DIAGNOSTIC_EXECUTED
    assert final.snapshot_request_succeeded == "true"
    assert final.price_available == "true"
    assert final.market_data_status == PRICE_AVAILABLE
    assert final.ibkr_error_code == "none"
    assert final.action_allowed == "false"


def test_write_market_data_entitlement_diagnostic_csv_and_report(tmp_path):
    rows = [
        MarketDataEntitlementDiagnosticRow(
            row_id="FINAL",
            row_name="Final market data entitlement diagnostic decision",
            source_layer="Phase 20D",
            input_source="config.yaml",
            selected_profile="live-readonly",
            execute_requested="true",
            component="final",
            diagnostic_status="DIAGNOSTIC_EXECUTED",
            market_data_status="NO_MARKET_DATA_SUBSCRIPTION",
            ibkr_error_code="10168",
            ibkr_error_message="requested market data is not subscribed; delayed market data is not enabled",
            delayed_data_enabled="false",
            snapshot_request_succeeded="true",
            price_available="false",
            price_status="PRICE_UNAVAILABLE",
            next_action="Enable delayed market data or subscribe market data.",
            contract_symbol="1540",
            contract_exchange="SMART",
            contract_primary_exchange="TSEJ",
            snapshot_bid="unavailable",
            snapshot_ask="unavailable",
            snapshot_last="unavailable",
            snapshot_close="unavailable",
            snapshot_market_price="unavailable",
            connection_attempted="true",
            connect_succeeded="true",
            disconnect_succeeded="true",
            current_call_allowed="true",
            streaming_market_data_allowed="false",
            historical_data_request_allowed="false",
            contract_qualification_allowed="false",
            order_action_allowed="false",
            cancellation_action_allowed="false",
            rebalance_action_allowed="false",
            auto_trade_allowed="false",
            action_allowed="false",
            evidence="diagnostic",
            warning_flags="MARKET_DATA_ENTITLEMENT_DIAGNOSTIC_DEFINED",
            notes="Diagnostic only.",
            timestamp_jst="2026-05-20T10:30:00+09:00",
            timestamp_et="2026-05-19T21:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "diagnostic.csv"
    md_path = tmp_path / "diagnostic.md"

    write_ibkr_readonly_market_data_entitlement_diagnostic_csv(csv_path, rows)
    write_ibkr_readonly_market_data_entitlement_diagnostic_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["market_data_status"] == "NO_MARKET_DATA_SUBSCRIPTION"
    assert csv_rows[0]["ibkr_error_code"] == "10168"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 20D IBKR Market Data Entitlement Diagnostic Report" in report
    assert "market_data_status: NO_MARKET_DATA_SUBSCRIPTION" in report
    assert "ibkr_error_code: 10168" in report
    assert "no historical data request" in report
    assert "no auto trade" in report
