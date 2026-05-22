from pathlib import Path
import csv
import subprocess

from src.ibkr_telegram_notification_packet import build_notification_row


def _row(**overrides):
    row = {
        "display_symbol": "1540.T",
        "operator_packet_status": "OPERATOR_REVIEW_READY",
        "final_decision_label": "REFERENCE_ONLY_REVIEW",
        "final_research_bucket": "reference_only",
        "usable_reference_price": "100",
        "operator_instruction": "manual_review_reference_only",
        "next_step": "operator_manual_research_review",
        "safety_flags": "",
    }
    row.update(overrides)
    return row


def test_operator_review_ready_maps_to_ready_to_notify_info():
    result = build_notification_row(_row())
    assert result.notification_status == "READY_TO_NOTIFY"
    assert result.notification_severity == "INFO"


def test_operator_review_blocked_maps_to_blocked_notify_warning():
    result = build_notification_row(_row(operator_packet_status="OPERATOR_REVIEW_BLOCKED"))
    assert result.notification_status == "BLOCKED_NOTIFY"
    assert result.notification_severity == "WARNING"


def test_safety_rejected_maps_to_safety_rejected_notify_critical():
    result = build_notification_row(_row(operator_packet_status="SAFETY_REJECTED"))
    assert result.notification_status == "SAFETY_REJECTED_NOTIFY"
    assert result.notification_severity == "CRITICAL"


def test_delayed_reference_message_mentions_reference_only_and_delayed():
    result = build_notification_row(_row(final_research_bucket="delayed_reference"))
    body = result.message_body.lower()
    assert "reference-only" in body
    assert "delayed" in body


def test_stale_reference_message_mentions_stale_or_delayed_frozen_reference_only():
    result = build_notification_row(_row(final_research_bucket="stale_reference"))
    body = result.message_body.lower()
    assert "stale" in body
    assert "delayed_frozen" in body
    assert "reference-only" in body


def test_unavailable_buckets_message_mentions_no_action():
    for bucket in ("no_price", "unsupported", "no_go"):
        result = build_notification_row(_row(final_research_bucket=bucket))
        assert "no action" in result.message_body.lower()


def test_all_outputs_force_safety_fields_false():
    result = build_notification_row(_row())
    assert result.action_allowed == "false"
    assert result.telegram_send_triggered == "false"
    assert result.broker_execution_triggered == "false"
    assert result.historical_data_request_triggered == "false"
    assert result.account_read_triggered == "false"
    assert result.position_read_triggered == "false"
    assert result.manual_review_required == "true"


def test_missing_operator_packet_script_generates_no_go(tmp_path: Path):
    missing = tmp_path / "missing_operator_packet.csv"
    output_csv = tmp_path / "notification.csv"
    output_report = tmp_path / "report.md"
    preview = tmp_path / "preview.md"

    result = subprocess.run(
        [
            "bash",
            "scripts/ibkr_telegram_notification_packet.sh",
            f"--operator-packet={missing}",
            f"--output-csv={output_csv}",
            f"--output-report={output_report}",
            f"--message-preview={preview}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "operator_packet_input_status=missing" in result.stdout
    assert "notification_packet_status=NO_GO" in result.stdout
    assert "telegram_send_triggered=false" in result.stdout
    assert "action_allowed=false" in result.stdout
    assert "NO_GO" in output_csv.read_text(encoding="utf-8")
    assert "Safety Confirmation" in output_report.read_text(encoding="utf-8")
    assert "Telegram Message Preview" in preview.read_text(encoding="utf-8")


def test_local_runner_telegram_dry_run_does_not_trigger_send(tmp_path: Path):
    log_root = tmp_path / "logs"
    result = subprocess.run(
        [
            "bash",
            "scripts/ibkr_local_daily_runner.sh",
            "--telegram-dry-run",
            f"--log-root={log_root}",
            "--retention-days=7",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "telegram_dry_run_enabled=true" in result.stdout
    assert "telegram_send_triggered=false" in result.stdout
    previews = sorted(log_root.glob("*/*/ibkr_telegram_message_preview.md"))
    packets = sorted(log_root.glob("*/*/ibkr_telegram_notification_packet.csv"))
    assert previews
    assert packets
    with packets[-1].open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows
    assert rows[-1]["telegram_send_triggered"] == "false"
