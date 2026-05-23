from pathlib import Path

from src.release_hardening_audit import (
    build_release_hardening_audit_decision,
    write_release_hardening_audit_report,
)


def test_default_audit_decision_action_allowed_false():
    result = build_release_hardening_audit_decision()
    assert result.audit_status == "RELEASE_AUDIT_PASS"
    assert result.action_allowed == "false"


def test_forbidden_trading_call_status_pass():
    result = build_release_hardening_audit_decision(forbidden_trading_hits=[])
    assert result.forbidden_trading_call_status == "PASS"


def test_account_read_status_pass():
    result = build_release_hardening_audit_decision(forbidden_account_hits=[])
    assert result.forbidden_account_read_status == "PASS"
    assert result.account_read_triggered == "false"
    assert result.position_read_triggered == "false"


def test_historical_request_status_pass():
    result = build_release_hardening_audit_decision(forbidden_historical_hits=[])
    assert result.forbidden_historical_request_status == "PASS"
    assert result.historical_data_request_triggered == "false"


def test_universe_policy_user_watchlist_only():
    result = build_release_hardening_audit_decision()
    assert result.universe_policy_status == "USER_WATCHLIST_ONLY"


def test_ibkr_universe_policy_contains_required_statuses():
    result = build_release_hardening_audit_decision()
    assert "GLD_SLV_FIRST_TEST_UNIVERSE" in result.ibkr_universe_policy_status
    assert "JP_ETF_OPTIONAL" in result.ibkr_universe_policy_status
    assert "CN_ETF_EXCLUDED_FROM_IBKR" in result.ibkr_universe_policy_status


def test_release_candidate_ready_for_manual_execution_c():
    result = build_release_hardening_audit_decision()
    assert result.release_candidate_status == "RC_READY_FOR_MANUAL_EXECUTION_C"


def test_dashboard_ready_status_pass():
    result = build_release_hardening_audit_decision()
    assert result.dashboard_ready_status == "PASS"


def test_telegram_send_triggered_false():
    result = build_release_hardening_audit_decision()
    assert result.telegram_send_triggered == "false"


def test_manual_review_required_true():
    result = build_release_hardening_audit_decision()
    assert result.manual_review_required == "true"


def test_safety_flags_can_output_blocking_hits():
    result = build_release_hardening_audit_decision(forbidden_trading_hits=["src/example.py:10"])
    assert result.audit_status == "RELEASE_AUDIT_BLOCKED"
    assert "forbidden_trading_call" in result.safety_flags
    assert result.release_candidate_status == "RC_BLOCKED"


def test_report_does_not_include_token_chat_id_or_secret(tmp_path: Path):
    result = build_release_hardening_audit_decision()
    report = tmp_path / "release_report.md"
    write_release_hardening_audit_report(report, result)
    text = report.read_text(encoding="utf-8").lower()
    assert "token" not in text
    assert "chat_id" not in text
    assert "secret" not in text
