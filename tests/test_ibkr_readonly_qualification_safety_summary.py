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
from src.ibkr_readonly_qualification_go_no_go import build_ibkr_readonly_qualification_go_no_go_rows
from src.ibkr_readonly_qualification_config_template import (
    build_ibkr_readonly_qualification_config_template_rows,
    default_ibkr_readonly_qualification_template,
)
from src.ibkr_readonly_qualification_config_audit import build_ibkr_readonly_qualification_config_audit_rows
from src.ibkr_readonly_qualification_config_apply_plan import build_ibkr_readonly_qualification_config_apply_plan_rows
from src.ibkr_readonly_qualification_config_final_gate import build_ibkr_readonly_qualification_config_final_gate_rows
from src.ibkr_readonly_qualification_safety_summary import (
    build_ibkr_readonly_qualification_safety_summary_rows,
    write_ibkr_readonly_qualification_safety_summary_csv,
    write_ibkr_readonly_qualification_safety_summary_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def _go_no_go_rows():
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


def _config_gate_rows():
    template_rows = build_ibkr_readonly_qualification_config_template_rows(TZ)
    config = default_ibkr_readonly_qualification_template()
    audit_rows = build_ibkr_readonly_qualification_config_audit_rows(config, TZ)
    apply_rows = build_ibkr_readonly_qualification_config_apply_plan_rows(audit_rows, TZ)

    return build_ibkr_readonly_qualification_config_final_gate_rows(
        template_rows,
        audit_rows,
        apply_rows,
        TZ,
    )


def test_safety_summary_defaults_to_blocked():
    rows = build_ibkr_readonly_qualification_safety_summary_rows(
        _go_no_go_rows(),
        _config_gate_rows(),
        TZ,
    )

    assert len(rows) == 3

    by_section = {row.section_id: row for row in rows}

    assert by_section["10G_10M"].summary_status == "NO_GO"
    assert by_section["11A_11D"].summary_status == "CLOSED"
    assert by_section["FINAL"].overall_status == "BLOCKED"

    for row in rows:
        assert row.apply_allowed == "false"
        assert row.qualification_allowed == "false"
        assert row.tws_connection_allowed == "false"
        assert row.contract_qualification_allowed == "false"
        assert row.market_data_request_allowed == "false"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_ibkr_connection" in row.warning_flags


def test_safety_summary_detects_unsafe_true_permission():
    go_rows = [row.__dict__.copy() for row in _go_no_go_rows()]
    gate_rows = _config_gate_rows()
    go_rows[0]["api_request_allowed"] = "true"

    rows = build_ibkr_readonly_qualification_safety_summary_rows(go_rows, gate_rows, TZ)
    by_section = {row.section_id: row for row in rows}

    assert by_section["10G_10M"].overall_status == "BLOCKED"
    assert "unsafe_true_permission_detected" in by_section["10G_10M"].blocking_summary


def test_safety_summary_writers(tmp_path: Path):
    rows = build_ibkr_readonly_qualification_safety_summary_rows(
        _go_no_go_rows(),
        _config_gate_rows(),
        TZ,
    )

    csv_path = tmp_path / "ibkr_readonly_qualification_safety_summary.csv"
    md_path = tmp_path / "ibkr_readonly_qualification_safety_summary_report.md"

    write_ibkr_readonly_qualification_safety_summary_csv(csv_path, rows)
    write_ibkr_readonly_qualification_safety_summary_report(md_path, rows, "config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "overall_status" in csv_text
    assert "BLOCKED" in csv_text
    assert "Phase 11E IBKR Read-Only Qualification Full Safety Summary Report" in md_text
    assert "final_overall_status: BLOCKED" in md_text
    assert "qualification_allowed_count: 0" in md_text
    assert "no TWS connection" in md_text
    assert "no auto trade" in md_text
