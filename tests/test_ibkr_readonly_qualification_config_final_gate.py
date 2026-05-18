from pathlib import Path

from src.ibkr_readonly_qualification_config_template import (
    build_ibkr_readonly_qualification_config_template_rows,
    default_ibkr_readonly_qualification_template,
)
from src.ibkr_readonly_qualification_config_audit import build_ibkr_readonly_qualification_config_audit_rows
from src.ibkr_readonly_qualification_config_apply_plan import build_ibkr_readonly_qualification_config_apply_plan_rows
from src.ibkr_readonly_qualification_config_final_gate import (
    build_ibkr_readonly_qualification_config_final_gate_rows,
    write_ibkr_readonly_qualification_config_final_gate_csv,
    write_ibkr_readonly_qualification_config_final_gate_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def _gate_rows():
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


def test_config_final_gate_defaults_to_closed():
    rows = _gate_rows()

    assert len(rows) == 4

    by_layer = {row.layer_id: row for row in rows}

    assert by_layer["11A"].final_gate_status == "CLOSED"
    assert by_layer["11B"].manual_required_count == "3"
    assert by_layer["11C"].manual_required_count == "4"
    assert by_layer["FINAL"].final_gate_status == "CLOSED"
    assert by_layer["FINAL"].apply_allowed == "false"

    for row in rows:
        assert row.apply_allowed == "false"
        assert row.qualification_allowed == "false"
        assert row.tws_connection_allowed == "false"
        assert row.contract_qualification_allowed == "false"
        assert row.market_data_request_allowed == "false"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_ibkr_connection" in row.warning_flags


def test_config_final_gate_detects_unsafe_true_permission():
    template_rows = build_ibkr_readonly_qualification_config_template_rows(TZ)
    config = default_ibkr_readonly_qualification_template()
    audit_rows = build_ibkr_readonly_qualification_config_audit_rows(config, TZ)
    apply_rows = [row.__dict__.copy() for row in build_ibkr_readonly_qualification_config_apply_plan_rows(audit_rows, TZ)]
    apply_rows[0]["api_request_allowed"] = "true"

    rows = build_ibkr_readonly_qualification_config_final_gate_rows(
        template_rows,
        audit_rows,
        apply_rows,
        TZ,
    )

    by_layer = {row.layer_id: row for row in rows}

    assert by_layer["11C"].final_gate_status == "CLOSED"
    assert "unsafe_true_permission_detected" in by_layer["11C"].blocking_summary


def test_config_final_gate_writers(tmp_path: Path):
    rows = _gate_rows()

    csv_path = tmp_path / "ibkr_readonly_qualification_config_final_gate.csv"
    md_path = tmp_path / "ibkr_readonly_qualification_config_final_gate_report.md"

    write_ibkr_readonly_qualification_config_final_gate_csv(csv_path, rows)
    write_ibkr_readonly_qualification_config_final_gate_report(md_path, rows, "config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "final_gate_status" in csv_text
    assert "CLOSED" in csv_text
    assert "Phase 11D IBKR Read-Only Qualification Config Final Gate Report" in md_text
    assert "final_gate_status: CLOSED" in md_text
    assert "apply_allowed_count: 0" in md_text
    assert "no TWS connection" in md_text
    assert "no auto trade" in md_text
