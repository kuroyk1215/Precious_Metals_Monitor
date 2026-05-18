from pathlib import Path

from src.ibkr_readonly_qualification_config_template import default_ibkr_readonly_qualification_template
from src.ibkr_readonly_qualification_config_audit import build_ibkr_readonly_qualification_config_audit_rows
from src.ibkr_readonly_qualification_config_apply_plan import (
    build_ibkr_readonly_qualification_config_apply_plan_rows,
    load_ibkr_readonly_qualification_config_audit_rows_by_key,
    write_ibkr_readonly_qualification_config_apply_plan_csv,
    write_ibkr_readonly_qualification_config_apply_plan_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def _audit_rows():
    config = default_ibkr_readonly_qualification_template()
    return build_ibkr_readonly_qualification_config_audit_rows(config, TZ)


def test_apply_plan_default_audit_rows_are_blocked():
    rows = build_ibkr_readonly_qualification_config_apply_plan_rows(_audit_rows(), TZ)

    assert len(rows) == 16

    by_key = {row.config_key: row for row in rows}

    assert by_key["enabled"].apply_plan_status == "keep_disabled"
    assert by_key["read_only_required"].apply_plan_status == "keep_required_true"
    assert by_key["account_mode"].apply_plan_status == "blocked_manual_config_required"
    assert by_key["host"].apply_plan_status == "manual_review_candidate_value"
    assert by_key["allow_tws_connection"].apply_plan_status == "keep_disabled"
    assert by_key["allow_order"].apply_allowed == "false"

    for row in rows:
        assert row.apply_allowed == "false"
        assert row.qualification_allowed == "false"
        assert row.tws_connection_allowed == "false"
        assert row.contract_qualification_allowed == "false"
        assert row.market_data_request_allowed == "false"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_ibkr_connection" in row.warning_flags


def test_apply_plan_blocks_config_violations():
    audit = [row.__dict__.copy() for row in _audit_rows()]
    audit[0]["config_audit_status"] = "config_violation_blocked"
    audit[0]["violation_detected"] = "true"
    audit[0]["observed_value"] = "true"

    rows = build_ibkr_readonly_qualification_config_apply_plan_rows(audit, TZ)
    by_key = {row.config_key: row for row in rows}

    assert by_key["enabled"].apply_plan_status == "blocked_config_violation"
    assert by_key["enabled"].operator_action_required == "true"
    assert by_key["enabled"].apply_allowed == "false"


def test_apply_plan_loader_and_writers(tmp_path: Path):
    csv_input = tmp_path / "ibkr_readonly_qualification_config_audit.csv"
    csv_input.write_text(
        "config_key,config_group,observed_value,required_safe_value,config_audit_status,violation_detected,timestamp_jst,timestamp_et\n"
        "account_mode,connection_config,paper_or_live_explicit_required,live_or_paper_explicit,manual_config_required,false,2026-05-18T15:00:00+09:00,2026-05-18T02:00:00-04:00\n",
        encoding="utf-8",
    )

    loaded = load_ibkr_readonly_qualification_config_audit_rows_by_key(str(csv_input))
    rows = build_ibkr_readonly_qualification_config_apply_plan_rows(list(loaded.values()), TZ)

    csv_path = tmp_path / "ibkr_readonly_qualification_config_apply_plan.csv"
    md_path = tmp_path / "ibkr_readonly_qualification_config_apply_plan_report.md"

    write_ibkr_readonly_qualification_config_apply_plan_csv(csv_path, rows)
    write_ibkr_readonly_qualification_config_apply_plan_report(md_path, rows, str(csv_input))

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "apply_plan_status" in csv_text
    assert "blocked_manual_config_required" in csv_text
    assert "Phase 11C IBKR Read-Only Qualification Config Apply Plan Report" in md_text
    assert "final_apply_plan_status: blocked_manual_config_required" in md_text
    assert "apply_allowed_count: 0" in md_text
    assert "no TWS connection" in md_text
    assert "no auto trade" in md_text
