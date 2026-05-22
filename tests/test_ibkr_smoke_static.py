from pathlib import Path
import subprocess


def test_main_supports_ibkr_smoke_flag():
    text = Path("main.py").read_text(encoding="utf-8")
    assert "--ibkr-smoke" in text


def test_no_top_level_ib_insync_import_failure():
    proc = subprocess.run(["python3", "-c", "import src.ibkr_data_client; print('ok')"], check=True, capture_output=True, text=True)
    assert "ok" in proc.stdout


def test_build_contract_missing_fields_status():
    from src.ibkr_data_client import IBKRDataClient

    client = IBKRDataClient({"host": "127.0.0.1", "port": 7497, "client_id": 1, "readonly": True})
    _, status, _ = client.build_contract({"symbol": "DXY_PROXY", "market": "US", "ibkr": {"secType": "", "exchange": "", "currency": ""}})
    assert status in {"invalid_config", "needs_manual_contract_config"}


def test_ibkr_smoke_generates_report_without_ibkr():
    subprocess.run(["python3", "main.py", "--config", "config.yaml", "--watchlist", "watchlist.yaml", "--ibkr-smoke"], check=True)
    assert Path("reports/ibkr_smoke_report.md").exists()


def test_no_trading_api_tokens():
    proc = subprocess.run([
        "rg", "-n", r"placeOrder|reqOpenOrders|cancelOrder|bracketOrder|whatIfOrder|exerciseOptions|Order\(",
        "src", "main.py", "README.md", "config.yaml", "watchlist.yaml"
    ], capture_output=True, text=True)
    assert proc.returncode in {1}



def test_connect_handles_missing_current_event_loop(monkeypatch):
    import types
    import sys
    import asyncio
    from src.ibkr_data_client import IBKRDataClient

    class FakeIB:
        def connect(self, **kwargs):
            raise RuntimeError("simulated_no_tws")

    fake_module = types.SimpleNamespace(IB=FakeIB)
    monkeypatch.setitem(sys.modules, "ib_insync", fake_module)

    called = {"set": False}

    def fake_get_event_loop():
        raise RuntimeError("There is no current event loop in thread 'MainThread'.")

    def fake_set_event_loop(loop):
        called["set"] = True

    monkeypatch.setattr(asyncio, "get_event_loop", fake_get_event_loop)
    monkeypatch.setattr(asyncio, "set_event_loop", fake_set_event_loop)

    client = IBKRDataClient({"host": "127.0.0.1", "port": 7497, "client_id": 1, "readonly": True})
    ok, status = client.connect()

    assert ok is False
    assert status.startswith("failed:")
    assert called["set"] is True
