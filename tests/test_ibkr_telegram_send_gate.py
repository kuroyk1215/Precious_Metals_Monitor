from pathlib import Path
import csv
import os
import subprocess

from src.ibkr_telegram_send_gate import evaluate_send_gate, write_send_gate_csv, write_send_gate_report


def _inputs(tmp_path: Path):
    approval = tmp_path / ".telegram_send_approval.local"
    packet = tmp_path / "ibkr_telegram_notification_packet.csv"
    preview = tmp_path / "ibkr_telegram_message_preview.md"
    packet.write_text("display_symbol,telegram_send_triggered\n1540.T,false\n", encoding="utf-8")
    preview.write_text("# Preview\nmessage text\n", encoding="utf-8")
    return approval, packet, preview


def test_default_dry_run_only_not_attempted(tmp_path: Path):
    approval, packet, preview = _inputs(tmp_path)
    result = evaluate_send_gate(
        send_telegram=False,
        approval_file=approval,
        notification_packet=packet,
        message_preview=preview,
    )
    assert result.send_gate_status == "DRY_RUN_ONLY"
    assert result.telegram_send_status == "not_attempted"
    assert result.telegram_send_triggered == "false"


def test_send_telegram_missing_approval_file_blocks(tmp_path: Path):
    approval, packet, preview = _inputs(tmp_path)
    result = evaluate_send_gate(
        send_telegram=True,
        approval_file=approval,
        notification_packet=packet,
        message_preview=preview,
        bot_token="token",
        chat_id="chat",
    )
    assert result.send_gate_status == "SEND_BLOCKED"
    assert result.approval_file_status == "missing"
    assert result.telegram_send_status == "blocked"


def test_send_telegram_missing_token_blocks(tmp_path: Path):
    approval, packet, preview = _inputs(tmp_path)
    approval.write_text("APPROVED_FOR_TELEGRAM_SEND=true\n", encoding="utf-8")
    result = evaluate_send_gate(
        send_telegram=True,
        approval_file=approval,
        notification_packet=packet,
        message_preview=preview,
        chat_id="chat",
    )
    assert result.send_gate_status == "SEND_BLOCKED"
    assert result.token_status == "missing"


def test_send_telegram_missing_chat_id_blocks(tmp_path: Path):
    approval, packet, preview = _inputs(tmp_path)
    approval.write_text("APPROVED_FOR_TELEGRAM_SEND=true\n", encoding="utf-8")
    result = evaluate_send_gate(
        send_telegram=True,
        approval_file=approval,
        notification_packet=packet,
        message_preview=preview,
        bot_token="token",
    )
    assert result.send_gate_status == "SEND_BLOCKED"
    assert result.chat_id_status == "missing"


def test_missing_notification_packet_blocks(tmp_path: Path):
    approval, packet, preview = _inputs(tmp_path)
    approval.write_text("APPROVED_FOR_TELEGRAM_SEND=true\n", encoding="utf-8")
    packet.unlink()
    result = evaluate_send_gate(
        send_telegram=True,
        approval_file=approval,
        notification_packet=packet,
        message_preview=preview,
        bot_token="token",
        chat_id="chat",
    )
    assert result.send_gate_status == "SEND_BLOCKED"
    assert result.notification_packet_status == "missing"


def test_missing_message_preview_blocks(tmp_path: Path):
    approval, packet, preview = _inputs(tmp_path)
    approval.write_text("APPROVED_FOR_TELEGRAM_SEND=true\n", encoding="utf-8")
    preview.unlink()
    result = evaluate_send_gate(
        send_telegram=True,
        approval_file=approval,
        notification_packet=packet,
        message_preview=preview,
        bot_token="token",
        chat_id="chat",
    )
    assert result.send_gate_status == "SEND_BLOCKED"
    assert result.message_preview_status == "missing"


def test_all_requirements_send_allowed_and_sent(tmp_path: Path):
    approval, packet, preview = _inputs(tmp_path)
    approval.write_text("APPROVED_FOR_TELEGRAM_SEND=true\n", encoding="utf-8")
    calls = []

    def fake_sender(token: str, chat_id: str, message: str):
        calls.append((token, chat_id, message))
        return "ok", "http_status=200;ok=true"

    result = evaluate_send_gate(
        send_telegram=True,
        approval_file=approval,
        notification_packet=packet,
        message_preview=preview,
        bot_token="secret-token",
        chat_id="secret-chat",
        sender=fake_sender,
    )
    assert result.send_gate_status == "SEND_ALLOWED"
    assert result.telegram_send_status == "sent"
    assert result.telegram_send_triggered == "true"
    assert calls


def test_send_exception_failed_safe(tmp_path: Path):
    approval, packet, preview = _inputs(tmp_path)
    approval.write_text("APPROVED_FOR_TELEGRAM_SEND=true\n", encoding="utf-8")

    def failing_sender(token: str, chat_id: str, message: str):
        raise RuntimeError("network failed")

    result = evaluate_send_gate(
        send_telegram=True,
        approval_file=approval,
        notification_packet=packet,
        message_preview=preview,
        bot_token="secret-token",
        chat_id="secret-chat",
        sender=failing_sender,
    )
    assert result.send_gate_status == "SEND_FAILED_SAFE"
    assert result.telegram_send_status == "failed"
    assert result.telegram_send_triggered == "true"


def test_outputs_do_not_include_token_or_chat_id(tmp_path: Path):
    approval, packet, preview = _inputs(tmp_path)
    approval.write_text("APPROVED_FOR_TELEGRAM_SEND=true\n", encoding="utf-8")
    result = evaluate_send_gate(
        send_telegram=True,
        approval_file=approval,
        notification_packet=packet,
        message_preview=preview,
        bot_token="dummy-token-for-redaction",
        chat_id="dummy-chat-for-redaction",
        sender=lambda token, chat_id, message: ("ok", "http_status=200;ok=true"),
    )
    csv_path = tmp_path / "decision.csv"
    report_path = tmp_path / "report.md"
    write_send_gate_csv(csv_path, result)
    write_send_gate_report(report_path, result, str(packet), str(preview), str(approval))
    combined = csv_path.read_text(encoding="utf-8") + report_path.read_text(encoding="utf-8")
    assert "dummy-token-for-redaction" not in combined
    assert "dummy-chat-for-redaction" not in combined


def test_safety_fields_are_forced_false(tmp_path: Path):
    approval, packet, preview = _inputs(tmp_path)
    result = evaluate_send_gate(
        send_telegram=False,
        approval_file=approval,
        notification_packet=packet,
        message_preview=preview,
    )
    assert result.action_allowed == "false"
    assert result.broker_execution_triggered == "false"
    assert result.historical_data_request_triggered == "false"
    assert result.account_read_triggered == "false"
    assert result.position_read_triggered == "false"
    assert result.manual_review_required == "true"


def test_script_default_does_not_read_env_or_send(tmp_path: Path):
    env = os.environ.copy()
    env["TELEGRAM_BOT_TOKEN"] = "token-that-must-not-print"
    env["TELEGRAM_CHAT_ID"] = "chat-that-must-not-print"
    output_csv = tmp_path / "decision.csv"
    output_report = tmp_path / "report.md"
    result = subprocess.run(
        [
            "bash",
            "scripts/ibkr_telegram_send_gate.sh",
            f"--output-csv={output_csv}",
            f"--output-report={output_report}",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "send_gate_status=DRY_RUN_ONLY" in result.stdout
    assert "token_status=not_required" in result.stdout
    assert "chat_id_status=not_required" in result.stdout
    assert "token-that-must-not-print" not in result.stdout + output_csv.read_text(encoding="utf-8") + output_report.read_text(encoding="utf-8")
    assert "chat-that-must-not-print" not in result.stdout + output_csv.read_text(encoding="utf-8") + output_report.read_text(encoding="utf-8")


def test_local_runner_default_does_not_trigger_send_gate(tmp_path: Path):
    log_root = tmp_path / "logs"
    result = subprocess.run(
        [
            "bash",
            "scripts/ibkr_local_daily_runner.sh",
            f"--log-root={log_root}",
            "--retention-days=7",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "telegram_send_gate_enabled=false" in result.stdout
    assert not sorted(log_root.glob("*/*/ibkr_telegram_send_gate_decision.csv"))


def test_local_runner_telegram_send_goes_through_gate(tmp_path: Path):
    log_root = tmp_path / "logs"
    result = subprocess.run(
        [
            "bash",
            "scripts/ibkr_local_daily_runner.sh",
            "--telegram-send",
            f"--telegram-approval-file={tmp_path / 'missing_approval.local'}",
            f"--log-root={log_root}",
            "--retention-days=7",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "telegram_send_gate_enabled=true" in result.stdout
    decisions = sorted(log_root.glob("*/*/ibkr_telegram_send_gate_decision.csv"))
    assert decisions
    with decisions[-1].open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[-1]["send_gate_status"] == "SEND_BLOCKED"
    assert rows[-1]["telegram_send_status"] == "blocked"
