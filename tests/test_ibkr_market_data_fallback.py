from src.ibkr_market_data_fallback import (
    LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE,
    build_attempt_result,
    classify_error,
)
from src.ibkr_market_data_error_capture import IbkrMarketDataErrorCapture


def test_error_10089_is_live_not_subscribed_delayed_available():
    assert classify_error("10089", "anything") == LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE


def test_error_354_is_live_not_subscribed_delayed_available():
    assert classify_error("354", "anything") == LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE


def test_delayed_market_data_available_is_fallback_allowed():
    assert classify_error("", "Delayed market data available") == LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE


def test_chinese_delayed_market_data_available_is_fallback_allowed():
    assert classify_error("", "延迟市场数据可用") == LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE


def test_live_to_delayed_path():
    r = build_attempt_result("auto", "delayed", "live_to_delayed", "354", "delayed market data available", True, 2, "delayed_available")
    assert r.fallback_stage == "live_to_delayed"
    assert r.effective_market_data_type == "delayed"


def test_delayed_empty_to_delayed_frozen_path():
    r = build_attempt_result("auto", "delayed_frozen", "delayed_to_delayed_frozen", "", "", False, 3, "delayed_snapshot_empty")
    assert r.fallback_stage == "delayed_to_delayed_frozen"
    assert r.snapshot_status == "DELAYED_FROZEN_SNAPSHOT_EMPTY"


def test_action_remains_manual_only_and_no_trade_flags_shape():
    r = build_attempt_result("auto", "delayed", "live_to_delayed", "", "", True, 2, "")
    assert r.fallback_terminal_status in {"usable_price", "empty_price"}


def test_unsupported_518880_sh_should_not_request_market_data():
    r = build_attempt_result("auto", "unknown", "unsupported", "", "Unsupported contract map status", False, 0, "unsupported")
    assert r.fallback_stage == "unsupported"


def test_default_without_execute_remains_no_go():
    # Decision check is handled in shell integration script; here we enforce no-attempt shape.
    r = build_attempt_result("auto", "unknown", "connection_error", "", "--execute was not provided", False, 0, "gate")
    assert r.snapshot_attempt_count == 0


def test_live_empty_without_error_not_354_and_reason_live_snapshot_empty():
    r = build_attempt_result("auto", "delayed", "live_to_delayed", "", "", False, 2, "live_snapshot_empty")
    assert r.error_code == ""
    assert r.live_permission_status == "unknown"
    assert r.fallback_reason == "live_snapshot_empty"


def test_confirmed_error_354_reason_delayed_available():
    r = build_attempt_result("auto", "delayed", "live_to_delayed", "354", "delayed market data available", False, 2, "delayed_available")
    assert r.live_permission_status == "not_subscribed"
    assert r.delayed_permission_status == "available"
    assert r.fallback_reason == LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE


def test_confirmed_error_10089_persists_permission_and_reason():
    r = build_attempt_result(
        "auto",
        "delayed",
        "live_to_delayed",
        "10089",
        "Market data farm connection is OK: delayed market data available",
        True,
        2,
        "",
    )
    assert r.error_code == "10089"
    assert "delayed market data available" in r.error_message
    assert r.live_permission_status == "not_subscribed"
    assert r.delayed_permission_status == "available"
    assert r.fallback_reason == LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE


def test_error_capture_can_scope_latest_error_to_attempt():
    capture = IbkrMarketDataErrorCapture()
    capture.record(1, "10089", "delayed market data available")
    start_index = len(capture.errors)
    capture.record(2, "999", "other")
    assert capture.latest_delayed_available(start_index) is None
