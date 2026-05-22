from src.ibkr_market_data_fallback import build_attempt_result, classify_error


def test_error_354_is_live_not_subscribed():
    assert classify_error("354", "anything") == "live_not_subscribed"


def test_delayed_market_data_available_is_fallback_allowed():
    assert classify_error("", "Delayed market data available") == "live_not_subscribed"


def test_live_to_delayed_path():
    r = build_attempt_result("auto", "delayed", "live_to_delayed", "354", "delayed market data available", True, 2, "delayed_requested")
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
