from pathlib import Path

from src.rc_manual_execution_rehearsal import (
    build_rc_manual_execution_rehearsal_decision,
    write_command_preview,
    write_rehearsal_report,
)


def test_default_rehearsal_status_ready():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.rehearsal_status == "RC_REHEARSAL_READY"


def test_blocked_when_required_inputs_missing():
    result = build_rc_manual_execution_rehearsal_decision(required_scripts_ok=False)
    assert result.rehearsal_status == "RC_REHEARSAL_BLOCKED"
    assert result.readiness_decision == "BLOCKED_BEFORE_MANUAL_EXECUTION_C"


def test_rehearsal_mode_preview_only():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.rehearsal_mode == "dry_run_preview_only"


def test_universe_policy_status_user_watchlist_only():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.universe_policy_status == "USER_WATCHLIST_ONLY"


def test_ibkr_first_validation_universe_gld_slv():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.ibkr_first_validation_universe == "GLD_SLV"


def test_jp_optional_universe():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.jp_optional_universe == "1540_1542_OPTIONAL"


def test_cn_non_ibkr_policy():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.cn_non_ibkr_policy == "518880_EXCLUDED_FROM_IBKR"


def test_ready_for_manual_execution_c_when_inputs_exist():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.readiness_decision == "READY_FOR_MANUAL_EXECUTION_C"


def test_safety_markers_false_and_manual_review_true():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.action_allowed == "false"
    assert result.broker_execution_triggered == "false"
    assert result.historical_data_request_triggered == "false"
    assert result.account_read_triggered == "false"
    assert result.position_read_triggered == "false"
    assert result.telegram_send_triggered == "false"
    assert result.manual_review_required == "true"


def test_command_preview_contains_execute_market_data_without_running(tmp_path: Path):
    result = build_rc_manual_execution_rehearsal_decision()
    preview = tmp_path / "preview.md"
    write_command_preview(preview, result)
    text = preview.read_text(encoding="utf-8")
    assert "--execute-market-data" in text
    assert "This rehearsal script does not run them" in text
    assert result.rehearsal_mode == "dry_run_preview_only"


def test_report_does_not_include_token_chat_id_or_secret(tmp_path: Path):
    result = build_rc_manual_execution_rehearsal_decision()
    report = tmp_path / "report.md"
    write_rehearsal_report(report, result)
    text = report.read_text(encoding="utf-8").lower()
    assert "token" not in text
    assert "chat_id" not in text
    assert "secret" not in text
