from pathlib import Path

from src.ibkr_live_provider_adapter_check import (
    build_ibkr_live_provider_adapter_check_rows,
    load_ibkr_live_provider_adapter_config,
)
from src.ibkr_contract_mapping_plan import (
    build_ibkr_contract_mapping_plan_rows,
    load_ibkr_contract_mapping_config,
)
from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
from src.ibkr_readonly_qualification_precheck import build_ibkr_readonly_qualification_precheck_rows
from src.ibkr_readonly_qualification_runbook import build_ibkr_readonly_qualification_runbook_rows
from src.ibkr_readonly_qualification_go_no_go import (
    build_ibkr_readonly_qualification_go_no_go_rows,
    write_ibkr_readonly_qualification_go_no_go_csv,
    write_ibkr_readonly_qualification_go_no_go_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def _summary_rows():
    provider_config = load_ibkr_live_provider_adapter_config("data/market_data_provider_config.yaml")
    mapping_config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")

    adapter_rows = build_ibkr_live_provider_adapter_check_rows(provider_config, TZ)
    mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, TZ)
    dry_run_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, TZ)
    guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_run_rows, TZ)
    precheck_rows = build_ibkr_readonly_qualification_precheck_rows({}, TZ)
    runbook_rows = build_ibkr_readonly_qualification_runbook_rows(precheck_rows, TZ)

    return build_ibkr_readonly_qualification_go_no_go_rows(
        adapter_rows,
        mapping_rows,
        dry_run_rows,
        guard_rows,
        precheck_rows,
        runbook_rows,
        TZ,
    )


def test_go_no_go_summary_defaults_to_no_go():
    rows = _summary_rows()

    assert len(rows) == 7

    by_phase = {row.phase_id: row for row in rows}

    assert by_phase["10G"].go_no_go_status == "NO_GO"
    assert by_phase["10H"].pass_or_ready_count == "4"
    assert by_phase["10I"].pass_or_ready_count == "4"
    assert by_phase["10J"].blocked_count == "7"
    assert by_phase["10K"].blocked_count == "6"
    assert by_phase["10L"].blocked_count == "5"
    assert by_phase["FINAL"].go_no_go_status == "NO_GO"

    for row in rows:
        assert row.qualification_allowed == "false"
        assert row.tws_connection_allowed == "false"
        assert row.contract_qualification_allowed == "false"
        assert row.market_data_request_allowed == "false"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_ibkr_connection" in row.warning_flags


def test_go_no_go_summary_detects_unsafe_true_permission():
    rows = _summary_rows()
    modified = [row.__dict__.copy() for row in rows]
    modified[0]["api_request_allowed"] = "true"

    summary = build_ibkr_readonly_qualification_go_no_go_rows(
        modified,
        [],
        [],
        [],
        [],
        [],
        TZ,
    )

    assert "unsafe_true_permission_detected" in summary[0].blocking_summary
    assert summary[0].go_no_go_status == "NO_GO"


def test_go_no_go_writers(tmp_path: Path):
    rows = _summary_rows()

    csv_path = tmp_path / "ibkr_readonly_qualification_go_no_go.csv"
    md_path = tmp_path / "ibkr_readonly_qualification_go_no_go_report.md"

    write_ibkr_readonly_qualification_go_no_go_csv(csv_path, rows)
    write_ibkr_readonly_qualification_go_no_go_report(md_path, rows, "config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "go_no_go_status" in csv_text
    assert "NO_GO" in csv_text
    assert "Phase 10M IBKR Read-Only Qualification Go/No-Go Report" in md_text
    assert "final_go_no_go_status: NO_GO" in md_text
    assert "qualification_allowed_count: 0" in md_text
    assert "no TWS connection" in md_text
    assert "no auto trade" in md_text
