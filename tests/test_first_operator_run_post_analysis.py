from pathlib import Path
import csv
import subprocess

from src.first_operator_run_post_analysis import (
    build_first_operator_run_post_analysis_decision,
    write_post_analysis_report,
)


def _execution(**overrides):
    row = {
        "execution_c_status": "EXECUTION_C_VALIDATION_READY",
        "validation_decision": "REVIEW_READY_REFERENCE_ONLY",
        "action_allowed": "false",
        "broker_execution_triggered": "false",
        "historical_data_request_triggered": "false",
        "account_read_triggered": "false",
        "position_read_triggered": "false",
        "telegram_send_triggered": "false",
    }
    row.update(overrides)
    return row


def _snapshot(**overrides):
    row = {
        "display_symbol": "GLD",
        "snapshot_status": "DELAYED_SNAPSHOT_RETURNED",
        "effective_market_data_type": "delayed",
        "data_delay_flag": "delayed",
        "error_code": "10089",
        "error_message": "live market data subscription missing; delayed market data is available",
        "action_allowed": "false",
        "broker_execution_triggered": "false",
        "historical_data_request_triggered": "false",
        "account_read_triggered": "false",
        "position_read_triggered": "false",
    }
    row.update(overrides)
    return row


def _operator(**overrides):
    row = {
        "display_symbol": "GLD",
        "operator_packet_status": "OPERATOR_REVIEW_READY",
        "final_research_bucket": "delayed_reference",
        "action_allowed": "false",
        "broker_execution_triggered": "false",
        "historical_data_request_triggered": "false",
        "account_read_triggered": "false",
        "position_read_triggered": "false",
    }
    row.update(overrides)
    return row


def _telegram(**overrides):
    row = {
        "display_symbol": "GLD",
        "notification_status": "READY_TO_NOTIFY",
        "action_allowed": "false",
        "telegram_send_triggered": "false",
        "broker_execution_triggered": "false",
        "historical_data_request_triggered": "false",
        "account_read_triggered": "false",
        "position_read_triggered": "false",
    }
    row.update(overrides)
    return row


def _decision(**overrides):
    params = {
        "execution_c_rows": [_execution()],
        "snapshot_rows": [_snapshot()],
        "operator_rows": [_operator(), _operator(display_symbol="SLV")],
        "telegram_notification_rows": [_telegram(), _telegram(display_symbol="SLV")],
        "execution_c_input_status": "present",
        "snapshot_input_status": "present",
        "operator_packet_input_status": "present",
        "telegram_notification_input_status": "present",
    }
    params.update(overrides)
    return build_first_operator_run_post_analysis_decision(**params)


def test_delayed_execution_c_ready_maps_to_post_run_reference_ready():
    result = _decision()
    assert result.post_run_status == "POST_RUN_REFERENCE_READY"


def test_review_ready_reference_only_maps_to_accept_reference_only_run():
    result = _decision()
    assert result.analysis_decision == "ACCEPT_REFERENCE_ONLY_RUN"


def test_delayed_snapshot_maps_to_delayed_reference_only():
    result = _decision()
    assert result.reference_only_status == "DELAYED_REFERENCE_ONLY"
    assert result.delayed_reference_count == "2"


def test_error_10089_detected_live_subscription_missing_delayed_available():
    result = _decision()
    assert result.error_10089_detected == "true"
    assert result.live_subscription_status == "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE"


def test_error_354_detected_live_subscription_missing_delayed_available():
    result = _decision(snapshot_rows=[_snapshot(error_code="354", error_message="354 delayed market data available")])
    assert result.error_354_detected == "true"
    assert result.live_subscription_status == "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE"


def test_delayed_rows_from_multiple_inputs_count_unique_display_symbols():
    result = _decision(
        snapshot_rows=[
            _snapshot(display_symbol="GLD"),
            _snapshot(display_symbol="SLV"),
        ],
        operator_rows=[
            _operator(display_symbol="GLD"),
            _operator(display_symbol="SLV"),
        ],
    )
    assert result.delayed_reference_count == "2"
    assert result.operator_review_ready_count == "2"


def test_duplicate_gld_delayed_rows_not_counted_twice():
    result = _decision(
        snapshot_rows=[
            _snapshot(display_symbol="GLD"),
            _snapshot(display_symbol="GLD"),
            _snapshot(display_symbol="SLV"),
        ],
        operator_rows=[
            _operator(display_symbol="GLD"),
            _operator(display_symbol="GLD"),
            _operator(display_symbol="SLV"),
        ],
    )
    assert result.delayed_reference_count == "2"
    assert result.operator_review_ready_count == "2"


def test_message_only_delayed_available_sets_live_subscription_status():
    result = _decision(snapshot_rows=[_snapshot(error_code="", error_message="delayed market data available")])
    assert result.error_10089_detected == "false"
    assert result.error_354_detected == "false"
    assert result.live_subscription_status == "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE"


def test_report_text_error_10089_detected():
    result = _decision(snapshot_rows=[{"report_text": "Error 10089: delayed market data available", "action_allowed": "false"}])
    assert result.error_10089_detected == "true"
    assert result.live_subscription_status == "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE"


def test_operator_review_ready_rows_counted():
    result = _decision(operator_rows=[_operator(), _operator(display_symbol="SLV")])
    assert result.operator_review_ready_count == "2"


def test_no_go_global_and_operator_review_ready_semantics():
    result = _decision(operator_rows=[_operator(final_research_bucket="no_go"), _operator(display_symbol="SLV")])
    assert result.semantic_status == "GLOBAL_NO_TRADE_BUT_OPERATOR_REVIEW_READY"
    assert int(result.no_go_count) >= 1


def test_missing_input_blocks_post_run_review():
    result = _decision(execution_c_rows=[], execution_c_input_status="missing")
    assert result.post_run_status == "POST_RUN_BLOCKED"
    assert result.analysis_decision == "BLOCK_POST_RUN_REVIEW"


def test_unsupported_and_no_go_rows_counted():
    result = _decision(
        snapshot_rows=[_snapshot(effective_market_data_type="unsupported", error_code="")],
        operator_rows=[_operator(final_research_bucket="unsupported"), _operator(display_symbol="SLV", final_research_bucket="no_go")],
    )
    assert int(result.unsupported_count) >= 1
    assert int(result.no_go_count) >= 1


def test_all_safety_outputs_forced_false():
    result = _decision()
    assert result.action_allowed == "false"
    assert result.broker_execution_triggered == "false"
    assert result.historical_data_request_triggered == "false"
    assert result.account_read_triggered == "false"
    assert result.position_read_triggered == "false"
    assert result.telegram_send_triggered == "false"


def test_report_does_not_contain_token_chat_id_or_secret_and_warns_reference_only(tmp_path: Path):
    result = _decision()
    report = tmp_path / "report.md"
    write_post_analysis_report(report, result)
    text = report.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "token" not in lowered
    assert "chat_id" not in lowered
    assert "secret" not in lowered
    assert "reference-only data cannot trigger trade" in lowered


def test_script_missing_inputs_generates_blocked_outputs(tmp_path: Path):
    output_csv = tmp_path / "post.csv"
    output_report = tmp_path / "report.md"
    summary = tmp_path / "summary.md"
    result = subprocess.run(
        [
            "bash",
            "scripts/first_operator_run_post_analysis.sh",
            f"--execution-c-packet={tmp_path / 'missing_execution.csv'}",
            f"--snapshot-csv={tmp_path / 'missing_snapshot.csv'}",
            f"--operator-packet={tmp_path / 'missing_operator.csv'}",
            f"--telegram-notification-packet={tmp_path / 'missing_telegram.csv'}",
            f"--output-csv={output_csv}",
            f"--output-report={output_report}",
            f"--summary-md={summary}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "post_run_status=POST_RUN_BLOCKED" in result.stdout
    with output_csv.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["action_allowed"] == "false"
    assert "Safety Confirmation" in output_report.read_text(encoding="utf-8")
    assert "action_allowed=false" in summary.read_text(encoding="utf-8")
