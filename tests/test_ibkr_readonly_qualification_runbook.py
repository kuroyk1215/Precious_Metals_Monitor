from pathlib import Path

from src.ibkr_readonly_qualification_precheck import build_ibkr_readonly_qualification_precheck_rows
from src.ibkr_readonly_qualification_runbook import (
    build_ibkr_readonly_qualification_runbook_rows,
    write_ibkr_readonly_qualification_runbook_csv,
    write_ibkr_readonly_qualification_runbook_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_runbook_default_precheck_blocks_environment_steps():
    precheck_rows = build_ibkr_readonly_qualification_precheck_rows({}, TZ)
    rows = build_ibkr_readonly_qualification_runbook_rows(precheck_rows, TZ)

    assert len(rows) == 10

    by_step = {row.step_id: row for row in rows}

    assert by_step["open_tws_gateway"].runbook_status == "blocked_by_precheck"
    assert by_step["confirm_read_only"].runbook_status == "blocked_by_precheck"
    assert by_step["confirm_request_gate"].runbook_status == "ready_for_manual_review_only"
    assert by_step["confirm_trading_blocked"].runbook_status == "ready_for_manual_review_only"

    for row in rows:
        assert row.qualification_allowed == "false"
        assert row.tws_connection_allowed == "false"
        assert row.contract_qualification_allowed == "false"
        assert row.market_data_request_allowed == "false"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_ibkr_connection" in row.warning_flags


def test_runbook_with_configured_precheck_still_blocks_tws_runtime_and_signoff():
    config = {
        "runtime": {
            "ibkr": {
                "host": "127.0.0.1",
                "port": 7496,
                "client_id": 1,
                "account_mode": "live",
                "read_only_required": True,
            }
        }
    }
    precheck_rows = build_ibkr_readonly_qualification_precheck_rows(config, TZ)
    rows = build_ibkr_readonly_qualification_runbook_rows(precheck_rows, TZ)

    by_step = {row.step_id: row for row in rows}

    assert by_step["confirm_read_only"].runbook_status == "ready_for_manual_review_only"
    assert by_step["confirm_connection_fields"].runbook_status == "ready_for_manual_review_only"
    assert by_step["open_tws_gateway"].runbook_status == "blocked_by_precheck"
    assert by_step["operator_signoff"].runbook_status == "blocked_by_precheck"
    assert by_step["operator_signoff"].qualification_allowed == "false"


def test_runbook_writers(tmp_path: Path):
    precheck_rows = build_ibkr_readonly_qualification_precheck_rows({}, TZ)
    rows = build_ibkr_readonly_qualification_runbook_rows(precheck_rows, TZ)

    csv_path = tmp_path / "ibkr_readonly_qualification_runbook.csv"
    md_path = tmp_path / "ibkr_readonly_qualification_runbook_report.md"

    write_ibkr_readonly_qualification_runbook_csv(csv_path, rows)
    write_ibkr_readonly_qualification_runbook_report(md_path, rows, "config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "runbook_status" in csv_text
    assert "Phase 10L IBKR Read-Only Qualification Runbook Report" in md_text
    assert "qualification_allowed_count: 0" in md_text
    assert "no TWS connection" in md_text
    assert "no auto trade" in md_text
