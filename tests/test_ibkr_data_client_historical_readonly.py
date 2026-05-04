from pathlib import Path


def _method_block(text: str, method_name: str) -> str:
    start = text.index(f"def {method_name}(")
    tail = text[start:]
    end = tail.find("\n    def ", 1)
    return tail if end < 0 else tail[:end]


def test_readonly_historical_method_exists_and_uses_reqhistoricaldata() -> None:
    text = Path("src/ibkr_data_client.py").read_text(encoding="utf-8")
    assert "class IBKRDataClient" in text
    assert "def request_historical_daily_bars_readonly(" in text
    block = _method_block(text, "request_historical_daily_bars_readonly")
    assert "reqHistoricalData" in block


def test_readonly_historical_method_contains_no_trade_api_calls() -> None:
    text = Path("src/ibkr_data_client.py").read_text(encoding="utf-8")
    block = _method_block(text, "request_historical_daily_bars_readonly")
    banned = ["placeOrder", "cancelOrder", "reqOpenOrders", "bracketOrder", "whatIfOrder", "exerciseOptions", "Order("]
    for token in banned:
        assert token not in block


def test_existing_smoke_and_fallback_methods_still_exist() -> None:
    text = Path("src/ibkr_data_client.py").read_text(encoding="utf-8")
    assert "def request_historical_daily_close(" in text
    assert "def get_quote_snapshot(" in text
    assert "historical_daily_close_fallback" in text
