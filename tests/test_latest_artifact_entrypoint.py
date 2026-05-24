from pathlib import Path
import csv
import subprocess

from src.latest_artifact_entrypoint import (
    FORBIDDEN_ACTION_WORDS,
    build_latest_artifact_entrypoint,
    forbidden_action_words_found,
    read_latest_summary_action_values,
    read_safety_field_values,
)


def _write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _handoff_rows():
    return [
        {
            "top_level_status": "OPERATOR_HANDOFF_REFERENCE_READY",
            "run_id": "fixture_run",
            "run_timestamp": "2026-05-24T12:00:00+00:00",
            "display_symbol": "GLD",
            "symbol": "GLD",
            "asset_route": "ARCA",
            "data_source_route": "SYMBOL_BASED_FIRST_VALIDATION",
            "snapshot_status": "DELAYED_SNAPSHOT_RETURNED",
            "effective_market_data_type": "delayed",
            "data_delay_flag": "delayed",
            "latest_price": "221.10",
            "reference_price": "221.10",
            "price_status": "usable_price",
            "operator_status": "OPERATOR_REVIEW_READY",
            "final_research_bucket": "delayed_reference",
            "api_error_codes": "10089",
            "error_10089_detected": "true",
            "error_354_detected": "false",
            "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE",
            "reference_only_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE_REFERENCE_ONLY",
            "delayed_reference_count": "1",
            "manual_review_required": "true",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
            "telegram_send_triggered": "false",
            "recommended_operator_action": "MANUAL_REFERENCE_REVIEW_ONLY",
        }
    ]


def _write_core_handoff(root: Path):
    _write_csv(root / "daily_operator_handoff_summary.csv", _handoff_rows())
    report = root / "reports" / "daily_operator_handoff_summary.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "# Daily Operator Handoff Summary\n\n- top_level_status=OPERATOR_HANDOFF_REFERENCE_READY\n",
        encoding="utf-8",
    )


def _write_generation_inputs(root: Path):
    _write_csv(
        root / "ibkr_verified_contract_map_gld_slv.csv",
        [{"run_id": "fixture_run", "run_timestamp": "2026-05-24T12:00:00+00:00", "display_symbol": "GLD", "symbol": "GLD", "data_source_route": "SYMBOL_BASED_FIRST_VALIDATION", "action_allowed": "false"}],
    )
    _write_csv(
        root / "ibkr_market_data_snapshot.csv",
        [{"display_symbol": "GLD", "symbol": "GLD", "snapshot_status": "DELAYED_SNAPSHOT_RETURNED", "effective_market_data_type": "delayed", "data_delay_flag": "delayed", "market_price": "221.10", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false"}],
    )
    _write_csv(
        root / "ibkr_market_data_api_errors.csv",
        [{"display_symbol": "GLD", "symbol": "GLD", "error_code": "10089", "raw_error_message": "Delayed market data available.", "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false", "account_read_triggered": "false", "position_read_triggered": "false", "telegram_send_triggered": "false"}],
    )
    _write_csv(
        root / "ibkr_execution_c_validation_packet.csv",
        [{"execution_c_status": "EXECUTION_C_VALIDATION_READY", "validation_decision": "REVIEW_READY_REFERENCE_ONLY", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false", "account_read_triggered": "false", "position_read_triggered": "false", "telegram_send_triggered": "false"}],
    )
    _write_csv(
        root / "ibkr_daily_operator_packet.csv",
        [{"display_symbol": "GLD", "operator_packet_status": "OPERATOR_REVIEW_READY", "final_research_bucket": "delayed_reference", "usable_reference_price": "221.10", "manual_review_required": "true", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false", "account_read_triggered": "false", "position_read_triggered": "false", "telegram_send_triggered": "false"}],
    )
    _write_csv(
        root / "first_operator_run_post_analysis.csv",
        [{"delayed_reference_count": "1", "error_codes_detected": "10089", "error_10089_detected": "true", "error_354_detected": "false", "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false", "account_read_triggered": "false", "position_read_triggered": "false", "telegram_send_triggered": "false"}],
    )
    _write_csv(
        root / "ibkr_telegram_notification_packet.csv",
        [{"display_symbol": "GLD", "notification_status": "READY_TO_NOTIFY", "action_allowed": "false", "telegram_send_triggered": "false"}],
    )


def test_latest_entrypoint_copies_core_handoff_and_generates_manifest(tmp_path: Path):
    _write_core_handoff(tmp_path)

    handoff_status, _ = build_latest_artifact_entrypoint(tmp_path)

    assert handoff_status == "PRESENT"
    assert (tmp_path / "latest_daily_operator_handoff_summary.csv").read_text(encoding="utf-8") == (tmp_path / "daily_operator_handoff_summary.csv").read_text(encoding="utf-8")
    assert (tmp_path / "reports" / "latest_operator_handoff_summary.md").read_text(encoding="utf-8") == (tmp_path / "reports" / "daily_operator_handoff_summary.md").read_text(encoding="utf-8")
    assert (tmp_path / "latest_run_manifest.csv").exists()
    assert (tmp_path / "reports" / "latest_run_manifest.md").exists()


def test_manifest_lists_present_and_missing_artifacts_without_failure(tmp_path: Path):
    _write_core_handoff(tmp_path)

    build_latest_artifact_entrypoint(tmp_path)
    manifest = _read_csv(tmp_path / "latest_run_manifest.csv")
    by_path = {row["artifact_path"]: row for row in manifest}

    assert by_path["daily_operator_handoff_summary.csv"]["artifact_status"] == "PRESENT"
    assert by_path["reports/daily_operator_handoff_summary.md"]["artifact_status"] == "PRESENT"
    assert by_path["latest_daily_operator_handoff_summary.csv"]["artifact_status"] == "COPIED"
    assert by_path["ibkr_execution_c_validation_packet.csv"]["artifact_status"] == "MISSING"
    assert by_path["ibkr_execution_c_validation_packet.csv"]["row_count"] == ""


def test_missing_core_handoff_is_generated_from_offline_fixture_inputs(tmp_path: Path):
    _write_generation_inputs(tmp_path)

    handoff_status, _ = build_latest_artifact_entrypoint(tmp_path)

    assert handoff_status == "GENERATED"
    assert (tmp_path / "daily_operator_handoff_summary.csv").exists()
    assert (tmp_path / "reports" / "daily_operator_handoff_summary.md").exists()
    assert (tmp_path / "latest_daily_operator_handoff_summary.csv").exists()
    assert _read_csv(tmp_path / "latest_daily_operator_handoff_summary.csv")[0]["recommended_operator_action"] == "MANUAL_REFERENCE_REVIEW_ONLY"


def test_safety_flags_stay_false_and_action_values_have_no_forbidden_words(tmp_path: Path):
    _write_core_handoff(tmp_path)

    build_latest_artifact_entrypoint(tmp_path)

    safety_values = read_safety_field_values(tmp_path)
    assert all(value == "false" for value in safety_values.values())
    action_values = read_latest_summary_action_values(tmp_path)
    assert forbidden_action_words_found(action_values) == []
    assert not any(word in " ".join(action_values).upper() for word in FORBIDDEN_ACTION_WORDS)


def test_shell_script_runs_offline_and_reports_expected_markers(tmp_path: Path):
    _write_core_handoff(tmp_path)
    config = tmp_path / "config.yaml"
    config.write_text("ibkr:\n  real_connection_allowed: false\n", encoding="utf-8")

    result = subprocess.run(
        ["bash", "scripts/latest_artifact_entrypoint.sh", "--root", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "latest_entrypoint_status=LATEST_ENTRYPOINT_READY" in result.stdout
    assert "operator_handoff_summary_status=PRESENT" in result.stdout
    assert "manifest_status=READY" in result.stdout
    for field in (
        "action_allowed",
        "broker_execution_triggered",
        "historical_data_request_triggered",
        "account_read_triggered",
        "position_read_triggered",
        "telegram_send_triggered",
    ):
        assert f"{field}=false" in result.stdout
    assert config.read_text(encoding="utf-8") == "ibkr:\n  real_connection_allowed: false\n"
