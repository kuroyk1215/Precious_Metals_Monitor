from pathlib import Path
import csv
import os
import subprocess

from src.telegram_notification_gate import (
    FORBIDDEN_EXECUTION_WORDS,
    build_approval_preview,
    build_gate,
    validate_gate,
    write_approval_preview,
    write_gate_csv,
    write_gate_report,
    build_gate_report,
)


def _write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _fixture_artifacts(root: Path):
    _write_csv(
        root / "latest_daily_operator_handoff_summary.csv",
        [
            {
                "top_level_status": "OPERATOR_HANDOFF_REFERENCE_READY",
                "display_symbol": "GLD",
                "symbol": "GLD",
                "price_status": "no_price",
                "data_delay_flag": "delayed",
                "reference_price": "",
                "operator_status": "OPERATOR_REVIEW_BLOCKED",
                "action_allowed": "false",
                "broker_execution_triggered": "false",
                "historical_data_request_triggered": "false",
                "account_read_triggered": "false",
                "position_read_triggered": "false",
                "telegram_send_triggered": "false",
            },
            {
                "top_level_status": "OPERATOR_HANDOFF_REFERENCE_READY",
                "display_symbol": "SLV",
                "symbol": "SLV",
                "price_status": "usable_price",
                "data_delay_flag": "delayed",
                "reference_price": "68.31",
                "operator_status": "OPERATOR_REVIEW_READY",
                "action_allowed": "false",
                "broker_execution_triggered": "false",
                "historical_data_request_triggered": "false",
                "account_read_triggered": "false",
                "position_read_triggered": "false",
                "telegram_send_triggered": "false",
            },
        ],
    )
    _write_csv(
        root / "research_trading_plan.csv",
        [
            {
                "display_symbol": "GLD",
                "symbol": "GLD",
                "research_plan_status": "NO_PRICE_PLAN_BLOCKED",
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
                "research_plan_status": "REFERENCE_ONLY_PLAN_READY",
                "action_allowed": "false",
                "broker_execution_triggered": "false",
                "historical_data_request_triggered": "false",
                "account_read_triggered": "false",
                "position_read_triggered": "false",
                "telegram_send_triggered": "false",
            },
        ],
    )
    _write_csv(
        root / "watchlist_universe.csv",
        [
            {
                "display_symbol": "GLD",
                "symbol": "GLD",
                "universe_status": "ACTIVE_FIRST_VALIDATION",
                "validation_status": "VALID",
                "action_allowed": "false",
            },
            {
                "display_symbol": "SLV",
                "symbol": "SLV",
                "universe_status": "ACTIVE_FIRST_VALIDATION",
                "validation_status": "VALID",
                "action_allowed": "false",
            },
        ],
    )
    (root / "reports").mkdir(exist_ok=True)
    (root / "reports/latest_operator_handoff_summary.md").write_text("# latest\n", encoding="utf-8")
    (root / "reports/research_trading_plan_report.md").write_text("# research\n", encoding="utf-8")
    (root / "reports/watchlist_universe_report.md").write_text("# watchlist\n", encoding="utf-8")


def test_default_run_produces_dry_run_only(tmp_path: Path):
    _fixture_artifacts(tmp_path)

    row, operator, research, watchlist = build_gate(root=tmp_path)

    assert row.approval_required == "true"
    assert row.send_approved == "false"
    assert row.telegram_send_triggered == "false"
    assert row.action_allowed == "false"
    assert row.message_preview_status == "PREVIEW_READY"
    assert row.recommended_notification_action == "MANUAL_APPROVAL_REQUIRED"
    assert operator.status == "PRESENT"
    assert research.status == "PRESENT"
    assert watchlist.status == "PRESENT"


def test_dry_run_cli_matches_default_safety_result(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    _fixture_artifacts(tmp_path)

    default = subprocess.run(
        [
            "bash",
            "scripts/telegram_notification_gate.sh",
            "--root",
            str(tmp_path),
            "--output-csv",
            str(tmp_path / "default.csv"),
            "--output-report",
            str(tmp_path / "reports/default.md"),
            "--preview-report",
            str(tmp_path / "reports/default_preview.md"),
        ],
        cwd=repo_root,
        env={**os.environ, "PYTHONPATH": str(repo_root)},
        text=True,
        capture_output=True,
        check=True,
    )
    dry = subprocess.run(
        [
            "bash",
            "scripts/telegram_notification_gate.sh",
            "--root",
            str(tmp_path),
            "--dry-run",
            "--output-csv",
            str(tmp_path / "dry.csv"),
            "--output-report",
            str(tmp_path / "reports/dry.md"),
            "--preview-report",
            str(tmp_path / "reports/dry_preview.md"),
        ],
        cwd=repo_root,
        env={**os.environ, "PYTHONPATH": str(repo_root)},
        text=True,
        capture_output=True,
        check=True,
    )

    assert "telegram_send_triggered=false" in default.stdout
    assert "telegram_send_triggered=false" in dry.stdout
    assert "action_allowed=false" in default.stdout
    assert "action_allowed=false" in dry.stdout


def test_send_approved_never_triggers_send(tmp_path: Path):
    _fixture_artifacts(tmp_path)

    row, _, _, _ = build_gate(root=tmp_path, send_approved=True, approval_note="manual approval smoke test")

    assert row.send_approved == "true"
    assert row.telegram_send_triggered == "false"
    assert row.telegram_send_status == "APPROVED_BUT_SEND_NOT_IMPLEMENTED"
    assert row.top_level_status == "TELEGRAM_GATE_APPROVED_NO_SEND"


def test_missing_optional_telegram_packet_does_not_fail(tmp_path: Path):
    _fixture_artifacts(tmp_path)

    row, _, _, _ = build_gate(root=tmp_path)

    assert row.source_telegram_packet_status == "MISSING"
    assert row.message_preview_status in {"PREVIEW_READY", "PREVIEW_GENERATED"}
    assert row.blocked_reason


def test_existing_latest_artifacts_are_summarized(tmp_path: Path):
    _fixture_artifacts(tmp_path)

    row, operator, research, watchlist = build_gate(root=tmp_path)
    preview = build_approval_preview(gate_row=row, operator=operator, research=research, watchlist=watchlist)

    assert "GLD" in preview
    assert "SLV" in preview
    assert "Research rows:" in preview
    assert "Watchlist universe:" in preview
    assert "no_price" in preview


def test_safety_flag_true_produces_safety_blocked(tmp_path: Path):
    _fixture_artifacts(tmp_path)
    text = (tmp_path / "latest_daily_operator_handoff_summary.csv").read_text(encoding="utf-8")
    (tmp_path / "latest_daily_operator_handoff_summary.csv").write_text(text.replace("false,false,false,false,false,false", "true,false,false,false,false,false", 1), encoding="utf-8")

    row, _, _, _ = build_gate(root=tmp_path)

    assert row.top_level_status == "TELEGRAM_GATE_SAFETY_BLOCKED"
    assert row.telegram_send_status == "SAFETY_BLOCKED"
    assert row.action_allowed == "false"


def test_forbidden_words_do_not_appear_in_action_status_or_preview(tmp_path: Path):
    _fixture_artifacts(tmp_path)

    row, operator, research, watchlist = build_gate(root=tmp_path, send_approved=True)
    preview = build_approval_preview(gate_row=row, operator=operator, research=research, watchlist=watchlist)
    joined = row.recommended_notification_action + " " + row.telegram_send_status + " " + preview

    upper = joined.upper()
    assert not any(word in upper for word in FORBIDDEN_EXECUTION_WORDS)
    assert validate_gate(row, preview) == []


def test_writers_emit_required_outputs(tmp_path: Path):
    _fixture_artifacts(tmp_path)
    row, operator, research, watchlist = build_gate(root=tmp_path)
    preview = build_approval_preview(gate_row=row, operator=operator, research=research, watchlist=watchlist)
    report = build_gate_report(
        row,
        operator=operator,
        research=research,
        watchlist=watchlist,
        output_csv=tmp_path / "telegram_notification_gate.csv",
        preview_report=tmp_path / "reports/telegram_notification_approval_preview.md",
    )

    write_gate_csv(tmp_path / "telegram_notification_gate.csv", row)
    write_gate_report(tmp_path / "reports/telegram_notification_gate_report.md", report)
    write_approval_preview(tmp_path / "reports/telegram_notification_approval_preview.md", preview)

    assert (tmp_path / "telegram_notification_gate.csv").exists()
    assert (tmp_path / "reports/telegram_notification_gate_report.md").exists()
    assert (tmp_path / "reports/telegram_notification_approval_preview.md").exists()
