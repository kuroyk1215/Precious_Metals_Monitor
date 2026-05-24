from pathlib import Path
import csv
import subprocess

from src.daily_operator_handoff_summary import (
    build_daily_operator_handoff_summary,
    write_markdown_report,
    write_summary_csv,
)


def _map_rows():
    return [
        {"run_id": "fixture_run", "run_timestamp": "2026-05-24T12:00:00+0900", "display_symbol": "GLD", "symbol": "GLD", "data_source_route": "SYMBOL_BASED_FIRST_VALIDATION", "action_allowed": "false"},
        {"run_id": "fixture_run", "run_timestamp": "2026-05-24T12:00:00+0900", "display_symbol": "SLV", "symbol": "SLV", "data_source_route": "SYMBOL_BASED_FIRST_VALIDATION", "action_allowed": "false"},
    ]


def _execution_rows():
    return [
        {
            "execution_c_status": "EXECUTION_C_VALIDATION_READY",
            "validation_decision": "REVIEW_READY_REFERENCE_ONLY",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
            "telegram_send_triggered": "false",
        }
    ]


def _api_error_rows():
    return [
        {
            "display_symbol": "GLD",
            "symbol": "GLD",
            "error_code": "10089",
            "raw_error_message": "Requested market data is not subscribed. Delayed market data available.",
            "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
            "telegram_send_triggered": "false",
        },
        {
            "display_symbol": "GLD",
            "symbol": "GLD",
            "error_code": "10089",
            "raw_error_message": "duplicate persisted 10089 row",
            "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
            "telegram_send_triggered": "false",
        },
        {
            "display_symbol": "GLD",
            "symbol": "GLD",
            "error_code": "300",
            "raw_error_message": "later non-entitlement API row",
            "live_subscription_status": "LIVE_SUBSCRIPTION_STATUS_NOT_DETECTED",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
            "telegram_send_triggered": "false",
        },
        {
            "display_symbol": "SLV",
            "symbol": "SLV",
            "error_code": "10089",
            "raw_error_message": "Requested market data is not subscribed. Delayed market data available.",
            "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
            "telegram_send_triggered": "false",
        },
    ]


def _post_rows(delayed_reference_count="2"):
    return [
        {
            "delayed_reference_count": delayed_reference_count,
            "error_codes_detected": "10089",
            "error_10089_detected": "true",
            "error_354_detected": "false",
            "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
            "telegram_send_triggered": "false",
        }
    ]


def _telegram_rows():
    return [
        {"display_symbol": "GLD", "notification_status": "READY_TO_NOTIFY", "action_allowed": "false", "telegram_send_triggered": "false"},
        {"display_symbol": "SLV", "notification_status": "READY_TO_NOTIFY", "action_allowed": "false", "telegram_send_triggered": "false"},
    ]


def _write_csv(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_gld_slv_persisted_10089_delayed_reference_fixture():
    snapshot_rows = [
        {"display_symbol": "GLD", "symbol": "GLD", "snapshot_status": "DELAYED_SNAPSHOT_RETURNED", "effective_market_data_type": "delayed", "data_delay_flag": "delayed", "market_price": "221.10", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false"},
        {"display_symbol": "SLV", "symbol": "SLV", "snapshot_status": "DELAYED_SNAPSHOT_RETURNED", "effective_market_data_type": "delayed", "data_delay_flag": "delayed", "market_price": "68.31", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false"},
    ]
    operator_rows = [
        {"display_symbol": "GLD", "operator_packet_status": "OPERATOR_REVIEW_READY", "final_research_bucket": "delayed_reference", "usable_reference_price": "221.10", "manual_review_required": "true", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false", "account_read_triggered": "false", "position_read_triggered": "false", "telegram_send_triggered": "false"},
        {"display_symbol": "SLV", "operator_packet_status": "OPERATOR_REVIEW_READY", "final_research_bucket": "delayed_reference", "usable_reference_price": "68.31", "manual_review_required": "true", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false", "account_read_triggered": "false", "position_read_triggered": "false", "telegram_send_triggered": "false"},
    ]

    status, rows = build_daily_operator_handoff_summary(
        contract_map_rows=_map_rows(),
        snapshot_rows=snapshot_rows,
        api_error_rows=_api_error_rows(),
        execution_c_rows=_execution_rows(),
        operator_rows=operator_rows,
        post_analysis_rows=_post_rows(),
        telegram_rows=_telegram_rows(),
    )

    assert status == "OPERATOR_HANDOFF_REFERENCE_READY"
    assert {row.display_symbol for row in rows} == {"GLD", "SLV"}
    assert all(row.error_10089_detected == "true" for row in rows)
    assert all("10089" in row.api_error_codes for row in rows)
    assert all(row.delayed_reference_count == "2" for row in rows)
    assert all(row.recommended_operator_action == "MANUAL_REFERENCE_REVIEW_ONLY" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)
    assert all(row.broker_execution_triggered == "false" for row in rows)
    assert all(row.historical_data_request_triggered == "false" for row in rows)
    assert all(row.account_read_triggered == "false" for row in rows)
    assert all(row.position_read_triggered == "false" for row in rows)
    assert all(row.telegram_send_triggered == "false" for row in rows)


def test_one_delayed_reference_and_one_no_price_fixture():
    snapshot_rows = [
        {"display_symbol": "GLD", "symbol": "GLD", "snapshot_status": "DELAYED_SNAPSHOT_RETURNED", "effective_market_data_type": "delayed", "data_delay_flag": "delayed", "market_price": "221.10", "action_allowed": "false"},
        {"display_symbol": "SLV", "symbol": "SLV", "snapshot_status": "DELAYED_SNAPSHOT_EMPTY", "effective_market_data_type": "delayed", "data_delay_flag": "delayed", "market_price": "", "action_allowed": "false"},
    ]
    operator_rows = [
        {"display_symbol": "GLD", "operator_packet_status": "OPERATOR_REVIEW_READY", "final_research_bucket": "delayed_reference", "usable_reference_price": "221.10", "manual_review_required": "true", "action_allowed": "false"},
        {"display_symbol": "SLV", "operator_packet_status": "OPERATOR_REVIEW_BLOCKED", "final_research_bucket": "no_price", "usable_reference_price": "", "manual_review_required": "true", "action_allowed": "false"},
    ]

    status, rows = build_daily_operator_handoff_summary(
        contract_map_rows=_map_rows(),
        snapshot_rows=snapshot_rows,
        api_error_rows=_api_error_rows(),
        execution_c_rows=_execution_rows(),
        operator_rows=operator_rows,
        post_analysis_rows=_post_rows(delayed_reference_count="2"),
        telegram_rows=_telegram_rows(),
    )

    by_symbol = {row.display_symbol: row for row in rows}
    assert status == "OPERATOR_HANDOFF_REFERENCE_READY"
    assert by_symbol["GLD"].recommended_operator_action == "MANUAL_REFERENCE_REVIEW_ONLY"
    assert by_symbol["SLV"].recommended_operator_action == "NO_PRICE_REVIEW_BLOCKED"
    assert by_symbol["SLV"].price_status == "no_price"


def test_delayed_reference_count_is_not_recalculated_from_api_error_rows():
    status, rows = build_daily_operator_handoff_summary(
        contract_map_rows=_map_rows(),
        snapshot_rows=[{"display_symbol": "GLD", "snapshot_status": "DELAYED_SNAPSHOT_RETURNED", "effective_market_data_type": "delayed", "data_delay_flag": "delayed", "market_price": "221.10", "action_allowed": "false"}],
        api_error_rows=_api_error_rows(),
        execution_c_rows=_execution_rows(),
        operator_rows=[{"display_symbol": "GLD", "operator_packet_status": "OPERATOR_REVIEW_READY", "final_research_bucket": "delayed_reference", "usable_reference_price": "221.10", "action_allowed": "false"}],
        post_analysis_rows=[],
        telegram_rows=[],
    )

    assert status == "OPERATOR_HANDOFF_REFERENCE_READY"
    assert rows[0].delayed_reference_count == "1"


def test_forbidden_action_words_do_not_appear_in_recommendations():
    _, rows = build_daily_operator_handoff_summary(
        contract_map_rows=_map_rows(),
        snapshot_rows=[{"display_symbol": "GLD", "snapshot_status": "DELAYED_SNAPSHOT_RETURNED", "effective_market_data_type": "delayed", "data_delay_flag": "delayed", "market_price": "221.10", "action_allowed": "false"}],
        api_error_rows=_api_error_rows(),
        execution_c_rows=_execution_rows(),
        operator_rows=[{"display_symbol": "GLD", "operator_packet_status": "OPERATOR_REVIEW_READY", "final_research_bucket": "delayed_reference", "usable_reference_price": "221.10", "action_allowed": "false"}],
        post_analysis_rows=_post_rows(),
        telegram_rows=[],
    )

    forbidden = ("TRADE", "BUY", "SELL", "ORDER", "CANCEL", "REBALANCE")
    assert all(not any(word in row.recommended_operator_action.upper() for word in forbidden) for row in rows)


def test_script_runs_offline(tmp_path: Path):
    _write_csv(tmp_path / "map.csv", _map_rows())
    _write_csv(tmp_path / "snapshot.csv", [{"display_symbol": "GLD", "symbol": "GLD", "snapshot_status": "DELAYED_SNAPSHOT_RETURNED", "effective_market_data_type": "delayed", "data_delay_flag": "delayed", "market_price": "221.10", "action_allowed": "false"}])
    _write_csv(tmp_path / "api_errors.csv", _api_error_rows())
    _write_csv(tmp_path / "execution.csv", _execution_rows())
    _write_csv(tmp_path / "operator.csv", [{"display_symbol": "GLD", "operator_packet_status": "OPERATOR_REVIEW_READY", "final_research_bucket": "delayed_reference", "usable_reference_price": "221.10", "manual_review_required": "true", "action_allowed": "false"}])
    _write_csv(tmp_path / "post.csv", _post_rows(delayed_reference_count="1"))
    _write_csv(tmp_path / "telegram.csv", [{"display_symbol": "GLD", "notification_status": "READY_TO_NOTIFY", "action_allowed": "false", "telegram_send_triggered": "false"}])

    result = subprocess.run(
        [
            "bash",
            "scripts/daily_operator_handoff_summary.sh",
            "--contract-map-csv",
            str(tmp_path / "map.csv"),
            "--snapshot-csv",
            str(tmp_path / "snapshot.csv"),
            "--api-errors-csv",
            str(tmp_path / "api_errors.csv"),
            "--execution-c-packet",
            str(tmp_path / "execution.csv"),
            "--operator-packet",
            str(tmp_path / "operator.csv"),
            "--post-analysis-csv",
            str(tmp_path / "post.csv"),
            "--telegram-notification-packet",
            str(tmp_path / "telegram.csv"),
            "--output-csv",
            str(tmp_path / "daily_operator_handoff_summary.csv"),
            "--output-report",
            str(tmp_path / "daily_operator_handoff_summary.md"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "top_level_status=OPERATOR_HANDOFF_REFERENCE_READY" in result.stdout
    assert (tmp_path / "daily_operator_handoff_summary.csv").exists()
    assert (tmp_path / "daily_operator_handoff_summary.md").exists()
