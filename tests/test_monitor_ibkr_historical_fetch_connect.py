from src.monitor import PreciousMetalsMonitor


class FakeIBKRDataClient:
    should_connect = True
    connect_status = "connected_readonly"
    instances = []

    def __init__(self, _config):
        self.connect_calls = 0
        self.disconnect_calls = 0
        FakeIBKRDataClient.instances.append(self)

    def connect(self):
        self.connect_calls += 1
        return self.should_connect, self.connect_status

    def disconnect(self):
        self.disconnect_calls += 1


def _build_monitor() -> PreciousMetalsMonitor:
    return PreciousMetalsMonitor("config.yaml", "watchlist.yaml", mock_mode=True)


def test_dry_run_does_not_connect(monkeypatch):
    FakeIBKRDataClient.instances = []
    monkeypatch.setattr("src.monitor.IBKRDataClient", FakeIBKRDataClient)

    called = {"fetch": 0}

    def fake_fetch(config, ibkr_client=None):
        called["fetch"] += 1
        assert ibkr_client is None
        return []

    monkeypatch.setattr("src.monitor.fetch_ibkr_historical_bars_readonly", fake_fetch)
    monitor = _build_monitor()
    monitor.run_ibkr_historical_fetch(execute=False)

    assert called["fetch"] == 1
    assert FakeIBKRDataClient.instances == []


def test_execute_connect_fail_no_fetch_and_disconnect(monkeypatch):
    FakeIBKRDataClient.instances = []
    FakeIBKRDataClient.should_connect = False
    FakeIBKRDataClient.connect_status = "socket_refused"
    monkeypatch.setattr("src.monitor.IBKRDataClient", FakeIBKRDataClient)

    called = {"fetch": 0}

    def fake_fetch(config, ibkr_client=None):
        called["fetch"] += 1
        return []

    monkeypatch.setattr("src.monitor.fetch_ibkr_historical_bars_readonly", fake_fetch)
    monitor = _build_monitor()
    rows, *_ = monitor.run_ibkr_historical_fetch(execute=True)

    assert called["fetch"] == 0
    assert [r["symbol"] for r in rows] == ["1540.T", "1542.T"]
    assert all(r["fetch_status"] == "error" for r in rows)
    assert all(r["warning_flags"] == "fetch_error:socket_refused" for r in rows)
    assert FakeIBKRDataClient.instances[0].connect_calls == 1
    assert FakeIBKRDataClient.instances[0].disconnect_calls == 1


def test_execute_connect_success_fetch_and_disconnect(monkeypatch):
    FakeIBKRDataClient.instances = []
    FakeIBKRDataClient.should_connect = True
    FakeIBKRDataClient.connect_status = "connected_readonly"
    monkeypatch.setattr("src.monitor.IBKRDataClient", FakeIBKRDataClient)

    called = {"fetch": 0}

    class Result:
        symbol = "1540.T"
        rows = [{"date": "20260102", "close": 111}]
        fetch_status = "executed_readonly"
        warning_flags = ""

    def fake_fetch(config, ibkr_client=None):
        called["fetch"] += 1
        assert ibkr_client is FakeIBKRDataClient.instances[0]
        return [Result()]

    monkeypatch.setattr("src.monitor.fetch_ibkr_historical_bars_readonly", fake_fetch)
    monitor = _build_monitor()
    rows, *_ = monitor.run_ibkr_historical_fetch(execute=True)

    assert called["fetch"] == 1
    assert rows[0]["symbol"] == "1540.T"
    assert rows[0]["fetch_status"] == "executed_readonly"
    assert FakeIBKRDataClient.instances[0].disconnect_calls == 1
