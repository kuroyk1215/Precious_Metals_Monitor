from pathlib import Path
import csv
import os
import subprocess

from src.local_dashboard import (
    DASHBOARD_PARTIAL,
    DASHBOARD_READY,
    DASHBOARD_SAFETY_REVIEW_REQUIRED,
    FORBIDDEN_OPERATOR_WORDS,
    build_dashboard_data,
    build_dashboard_html,
    generate_dashboard,
)


def _write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _fixture_artifacts(root: Path, *, optional: bool = True, unsafe: bool = False, safety: bool = False):
    _write_csv(
        root / "latest_daily_operator_handoff_summary.csv",
        [
            {
                "top_level_status": "OPERATOR_HANDOFF_REFERENCE_READY",
                "display_symbol": "GLD",
                "symbol": "GLD",
                "price_status": "<unsafe>",
                "data_delay_flag": "delayed",
                "recommended_operator_action": "MANUAL_REFERENCE_REVIEW_ONLY",
                "manual_review_required": "true",
                "action_allowed": "true" if safety else "false",
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
                "recommended_operator_action": "manual review only",
                "manual_review_required": "true",
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
                "price_status": "no_price",
                "data_delay_flag": "delayed",
                "recommended_operator_action": "BUY now" if unsafe else "manual review only",
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
                "price_status": "usable_price",
                "data_delay_flag": "delayed",
                "recommended_operator_action": "manual review only",
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
                "ibkr_universe_allowed": "true",
                "manual_review_required": "true",
                "universe_status": "ACTIVE_FIRST_VALIDATION",
                "validation_status": "VALID",
                "action_allowed": "false",
            },
            {
                "display_symbol": "SLV",
                "symbol": "SLV",
                "ibkr_universe_allowed": "true",
                "manual_review_required": "true",
                "universe_status": "ACTIVE_FIRST_VALIDATION",
                "validation_status": "VALID",
                "action_allowed": "false",
            },
            {
                "display_symbol": "1540",
                "symbol": "1540",
                "ibkr_universe_allowed": "false",
                "manual_review_required": "true",
                "universe_status": "OPTIONAL_MANUAL_REVIEW",
                "validation_status": "REVIEW_REQUIRED",
                "action_allowed": "false",
            },
            {
                "display_symbol": "1542",
                "symbol": "1542",
                "ibkr_universe_allowed": "false",
                "manual_review_required": "true",
                "universe_status": "OPTIONAL_MANUAL_REVIEW",
                "validation_status": "REVIEW_REQUIRED",
                "action_allowed": "false",
            },
            {
                "display_symbol": "518880",
                "symbol": "518880",
                "ibkr_universe_allowed": "false",
                "manual_review_required": "true",
                "universe_status": "IBKR_EXCLUDED",
                "validation_status": "BLOCKED_FROM_IBKR",
                "action_allowed": "false",
            },
        ],
    )
    _write_csv(
        root / "telegram_notification_gate.csv",
        [
            {
                "top_level_status": "TELEGRAM_GATE_APPROVAL_REQUIRED",
                "telegram_send_status": "READY_FOR_MANUAL_APPROVAL",
                "action_allowed": "false",
                "broker_execution_triggered": "false",
                "historical_data_request_triggered": "false",
                "account_read_triggered": "false",
                "position_read_triggered": "false",
                "telegram_send_triggered": "false",
            }
        ],
    )
    if optional:
        for path in (
            "latest_run_manifest.csv",
            "first_operator_run_post_analysis.csv",
            "ibkr_market_data_api_errors.csv",
        ):
            _write_csv(root / path, [{"status": "present"}])
        for path in (
            "reports/latest_operator_handoff_summary.md",
            "reports/latest_run_manifest.md",
            "reports/research_trading_plan_report.md",
            "reports/watchlist_universe_report.md",
            "reports/telegram_notification_gate_report.md",
            "reports/telegram_notification_approval_preview.md",
        ):
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_text("# report\n", encoding="utf-8")


def test_dashboard_generated_when_all_core_artifacts_exist(tmp_path: Path):
    _fixture_artifacts(tmp_path)

    generate_dashboard(tmp_path)

    assert (tmp_path / "reports/dashboard.html").exists()


def test_dashboard_status_ready_when_all_core_artifacts_exist_and_safety_false(tmp_path: Path):
    _fixture_artifacts(tmp_path, optional=True)

    data = build_dashboard_data(tmp_path)

    assert data.dashboard_status == DASHBOARD_READY


def test_dashboard_status_partial_when_optional_artifacts_missing(tmp_path: Path):
    _fixture_artifacts(tmp_path, optional=False)

    data = build_dashboard_data(tmp_path)

    assert data.dashboard_status == DASHBOARD_PARTIAL


def test_dashboard_status_safety_review_required_when_any_safety_flag_true(tmp_path: Path):
    _fixture_artifacts(tmp_path, safety=True)

    data = build_dashboard_data(tmp_path)

    assert data.dashboard_status == DASHBOARD_SAFETY_REVIEW_REQUIRED


def test_symbol_rows_appear_from_core_artifacts(tmp_path: Path):
    _fixture_artifacts(tmp_path)
    html = build_dashboard_html(build_dashboard_data(tmp_path))

    for symbol in ("GLD", "SLV", "1540", "1542", "518880"):
        assert f"<td>{symbol}</td>" in html


def test_relative_report_links_are_present(tmp_path: Path):
    _fixture_artifacts(tmp_path)
    html = build_dashboard_html(build_dashboard_data(tmp_path))

    for path in (
        "latest_operator_handoff_summary.md",
        "latest_run_manifest.md",
        "research_trading_plan_report.md",
        "watchlist_universe_report.md",
        "telegram_notification_gate_report.md",
        "telegram_notification_approval_preview.md",
    ):
        assert f'href="{path}"' in html


def test_html_escaping_applied_for_unsafe_field_values(tmp_path: Path):
    _fixture_artifacts(tmp_path)
    html = build_dashboard_html(build_dashboard_data(tmp_path))

    assert "&lt;unsafe&gt;" in html
    assert "<unsafe>" not in html


def test_forbidden_execution_words_do_not_appear_as_operator_actions(tmp_path: Path):
    _fixture_artifacts(tmp_path, unsafe=True)
    html = build_dashboard_html(build_dashboard_data(tmp_path))

    assert "BUY now" not in html
    action_values = [row["recommended_operator_action"].upper() for row in build_dashboard_data(tmp_path).symbol_rows]
    for action in action_values:
        assert not any(word in action for word in FORBIDDEN_OPERATOR_WORDS)


def test_script_runs_offline(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    _fixture_artifacts(tmp_path, optional=False)

    result = subprocess.run(
        [
            "bash",
            str(repo_root / "scripts/local_dashboard.sh"),
            "--root",
            str(tmp_path),
            "--output-html",
            "reports/dashboard.html",
        ],
        cwd=repo_root,
        env={**os.environ, "PYTHONPATH": str(repo_root)},
        text=True,
        capture_output=True,
        check=True,
    )

    assert "offline_only=true" in result.stdout
    assert "dashboard path: reports/dashboard.html" in result.stdout
    assert (tmp_path / "reports/dashboard.html").exists()
