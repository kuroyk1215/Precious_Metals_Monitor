from pathlib import Path

from src.ibkr_execution_c_validation import (
    build_execution_c_validation_decision,
    write_validation_report,
)


def _snapshot(**overrides):
    row = {
        "display_symbol": "1540.T",
        "snapshot_status": "DELAYED_SNAPSHOT_RETURNED",
        "effective_market_data_type": "delayed",
        "fallback_stage": "live_to_delayed",
        "data_delay_flag": "delayed",
        "action_allowed": "false",
        "broker_execution_triggered": "false",
        "historical_data_request_triggered": "false",
        "account_read_triggered": "false",
        "position_read_triggered": "false",
    }
    row.update(overrides)
    return row


def test_default_dry_run_ready_no_go():
    result = build_execution_c_validation_decision()
    assert result.execution_c_status == "EXECUTION_C_DRY_RUN_READY"
    assert result.execution_c_mode == "dry_run"
    assert result.validation_decision == "NO_GO"


def test_execute_market_data_requested_sets_mode():
    result = build_execution_c_validation_decision(
        execute_market_data=True,
        runner_rows=[{"pipeline_exit_code": "0", "action_allowed": "false"}],
        snapshot_rows=[_snapshot()],
        snapshot_input_status="present",
    )
    assert result.execution_c_mode == "execute_market_data"
    assert result.market_data_execution_requested == "true"


def test_delayed_reference_only_review_ready():
    result = build_execution_c_validation_decision(
        execute_market_data=True,
        runner_rows=[{"pipeline_exit_code": "0", "action_allowed": "false"}],
        snapshot_rows=[_snapshot(effective_market_data_type="delayed", data_delay_flag="delayed")],
        snapshot_input_status="present",
    )
    assert result.validation_decision == "REVIEW_READY_REFERENCE_ONLY"
    assert "reference-only" in result.validation_reason
    assert "not real-time" in result.validation_reason


def test_delayed_frozen_reference_only_review_ready():
    result = build_execution_c_validation_decision(
        execute_market_data=True,
        runner_rows=[{"pipeline_exit_code": "0", "action_allowed": "false"}],
        snapshot_rows=[_snapshot(effective_market_data_type="delayed_frozen", data_delay_flag="delayed_frozen")],
        snapshot_input_status="present",
    )
    assert result.validation_decision == "REVIEW_READY_REFERENCE_ONLY"


def test_snapshot_missing_blocks_review():
    result = build_execution_c_validation_decision(
        execute_market_data=True,
        runner_rows=[{"pipeline_exit_code": "0", "action_allowed": "false"}],
        snapshot_rows=[],
        snapshot_input_status="missing",
    )
    assert result.execution_c_status == "EXECUTION_C_VALIDATION_BLOCKED"
    assert result.validation_decision == "REVIEW_BLOCKED"


def test_unsupported_blocks_review():
    result = build_execution_c_validation_decision(
        execute_market_data=True,
        runner_rows=[{"pipeline_exit_code": "0", "action_allowed": "false"}],
        snapshot_rows=[_snapshot(effective_market_data_type="unknown", fallback_stage="unsupported")],
        snapshot_input_status="present",
    )
    assert result.execution_c_status == "EXECUTION_C_VALIDATION_BLOCKED"
    assert result.validation_decision == "REVIEW_BLOCKED"


def test_safety_marker_anomaly_failed_safe():
    result = build_execution_c_validation_decision(
        execute_market_data=True,
        runner_rows=[{"pipeline_exit_code": "0", "action_allowed": "false"}],
        snapshot_rows=[_snapshot(action_allowed="true")],
        snapshot_input_status="present",
    )
    assert result.execution_c_status == "EXECUTION_C_FAILED_SAFE"
    assert result.validation_decision == "FAILED_SAFE"


def test_safety_outputs_are_forced_false():
    result = build_execution_c_validation_decision()
    assert result.action_allowed == "false"
    assert result.broker_execution_triggered == "false"
    assert result.historical_data_request_triggered == "false"
    assert result.account_read_triggered == "false"
    assert result.position_read_triggered == "false"
    assert result.manual_review_required == "true"


def test_report_does_not_include_token_chat_id_or_secret(tmp_path: Path):
    result = build_execution_c_validation_decision()
    report = tmp_path / "report.md"
    write_validation_report(report, result)
    text = report.read_text(encoding="utf-8").lower()
    assert "token" not in text
    assert "chat_id" not in text
    assert "secret" not in text
