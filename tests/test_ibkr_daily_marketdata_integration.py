from src.ibkr_daily_marketdata_integration import integrate_snapshot_row, missing_input_row


def _row(**overrides):
    row = {
        "display_symbol": "1540.T",
        "contract_map_status": "MAP_READY",
        "requested_market_data_type": "auto",
        "effective_market_data_type": "live",
        "fallback_stage": "live",
        "data_delay_flag": "real_time",
        "snapshot_status": "SNAPSHOT_RETURNED",
        "fallback_terminal_status": "usable_price",
        "bid": "",
        "ask": "",
        "last": "",
        "close": "",
        "market_price": "",
        "action_allowed": "false",
        "historical_data_request_triggered": "false",
        "broker_execution_triggered": "false",
    }
    row.update(overrides)
    return row


def test_market_price_priority_as_usable_reference_price():
    result = integrate_snapshot_row(_row(market_price="101", last="99", close="98", bid="97", ask="103"))
    assert result["usable_reference_price"] == "101"
    assert result["usable_reference_price_field"] == "market_price"


def test_last_is_second_priority_reference_price():
    result = integrate_snapshot_row(_row(last="99", close="98", bid="97", ask="103"))
    assert result["usable_reference_price"] == "99"
    assert result["usable_reference_price_field"] == "last"


def test_close_is_third_priority_reference_price():
    result = integrate_snapshot_row(_row(close="98", bid="97", ask="103"))
    assert result["usable_reference_price"] == "98"
    assert result["usable_reference_price_field"] == "close"


def test_bid_ask_midpoint_fallback_reference_price():
    result = integrate_snapshot_row(_row(bid="97", ask="103"))
    assert result["usable_reference_price"] == "100"
    assert result["usable_reference_price_field"] == "bid_ask_midpoint"


def test_delayed_maps_to_tier_2_delayed():
    result = integrate_snapshot_row(_row(effective_market_data_type="delayed", data_delay_flag="delayed", market_price="100"))
    assert result["integration_status"] == "READY_DELAYED_REFERENCE_ONLY"
    assert result["data_quality_tier"] == "tier_2_delayed"


def test_delayed_frozen_maps_to_tier_3_delayed_frozen():
    result = integrate_snapshot_row(
        _row(effective_market_data_type="delayed_frozen", data_delay_flag="delayed_frozen", market_price="100")
    )
    assert result["integration_status"] == "READY_DELAYED_FROZEN_REFERENCE_ONLY"
    assert result["data_quality_tier"] == "tier_3_delayed_frozen"


def test_snapshot_empty_maps_to_empty_price():
    result = integrate_snapshot_row(_row(snapshot_status="SNAPSHOT_EMPTY", fallback_terminal_status="empty_price"))
    assert result["integration_status"] == "EMPTY_PRICE"
    assert result["price_availability_status"] == "unavailable"


def test_unsupported_maps_to_unsupported():
    result = integrate_snapshot_row(_row(contract_map_status="IBKR_UNSUPPORTED", fallback_stage="unsupported"))
    assert result["integration_status"] == "UNSUPPORTED"
    assert result["research_usage"] == "unsupported"


def test_action_allowed_non_false_is_safety_rejected():
    result = integrate_snapshot_row(_row(action_allowed="true", market_price="100"))
    assert result["integration_status"] == "SAFETY_REJECTED"
    assert "action_allowed" in result["safety_flags"]


def test_historical_data_request_triggered_non_false_is_safety_rejected():
    result = integrate_snapshot_row(_row(historical_data_request_triggered="true", market_price="100"))
    assert result["integration_status"] == "SAFETY_REJECTED"
    assert "historical_data_request_triggered" in result["safety_flags"]


def test_broker_execution_triggered_non_false_is_safety_rejected():
    result = integrate_snapshot_row(_row(broker_execution_triggered="true", market_price="100"))
    assert result["integration_status"] == "SAFETY_REJECTED"
    assert "broker_execution_triggered" in result["safety_flags"]


def test_missing_input_maps_to_no_go():
    result = missing_input_row("ibkr_market_data_snapshot.csv")
    assert result["integration_status"] == "NO_GO"
    assert result["input_snapshot_status"] == "missing"
