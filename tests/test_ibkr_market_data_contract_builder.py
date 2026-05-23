from src.ibkr_market_data_contract_builder import build_market_data_contract_kwargs


def test_conid_present_uses_conid_contract_path():
    kwargs = build_market_data_contract_kwargs(
        {
            "display_symbol": "GLD",
            "symbol": "GLD",
            "conid": "12345",
            "sec_type": "STK",
            "exchange": "SMART",
            "primary_exchange": "ARCA",
            "currency": "USD",
        }
    )

    assert kwargs == {
        "conId": 12345,
        "secType": "STK",
        "exchange": "SMART",
        "currency": "USD",
    }


def test_conid_missing_uses_symbol_contract_path():
    kwargs = build_market_data_contract_kwargs(
        {
            "display_symbol": "SLV",
            "symbol": "SLV",
            "conid": "",
            "sec_type": "STK",
            "exchange": "SMART",
            "primary_exchange": "ARCA",
            "currency": "USD",
            "local_symbol": "",
            "trading_class": "",
        }
    )

    assert kwargs == {
        "symbol": "SLV",
        "secType": "STK",
        "exchange": "SMART",
        "currency": "USD",
        "primaryExchange": "ARCA",
    }


def test_contract_builder_has_no_historical_or_broker_execution_fields():
    kwargs = build_market_data_contract_kwargs({"display_symbol": "GLD", "symbol": "GLD"})

    assert "reqHistoricalData" not in kwargs
    assert "placeOrder" not in kwargs
