from pathlib import Path

from src.ibkr_readonly_qualification_config_template import default_ibkr_readonly_qualification_template
from src.ibkr_readonly_qualification_config_audit import (
    build_ibkr_readonly_qualification_config_audit_rows,
    load_ibkr_readonly_qualification_config_audit_config,
    write_ibkr_readonly_qualification_config_audit_csv,
    write_ibkr_readonly_qualification_config_audit_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_config_audit_default_template_is_blocked_or_disabled():
    config = default_ibkr_readonly_qualification_template()
    rows = build_ibkr_readonly_qualification_config_audit_rows(config, TZ)

    assert len(rows) == 16

    by_key = {row.config_key: row for row in rows}

    assert by_key["enabled"].config_audit_status == "blocked_or_disabled"
    assert by_key["read_only_required"].config_audit_status == "required_true"
    assert by_key["account_mode"].config_audit_status == "manual_config_required"
    assert by_key["allow_tws_connection"].observed_value == "false"
    assert by_key["allow_contract_qualification"].observed_value == "false"
    assert by_key["allow_order"].observed_value == "false"

    for row in rows:
        assert row.qualification_allowed == "false"
        assert row.tws_connection_allowed == "false"
        assert row.contract_qualification_allowed == "false"
        assert row.market_data_request_allowed == "false"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_ibkr_connection" in row.warning_flags


def test_config_audit_detects_unsafe_true_permissions():
    config = default_ibkr_readonly_qualification_template()
    qcfg = config["runtime"]["ibkr_readonly_qualification"]
    qcfg["enabled"] = True
    qcfg["allow_tws_connection"] = True
    qcfg["allow_order"] = True

    rows = build_ibkr_readonly_qualification_config_audit_rows(config, TZ)
    by_key = {row.config_key: row for row in rows}

    assert by_key["enabled"].config_audit_status == "config_violation_blocked"
    assert by_key["allow_tws_connection"].violation_detected == "true"
    assert by_key["allow_order"].violation_detected == "true"
    assert by_key["allow_order"].action_allowed == "false"


def test_config_audit_loader_falls_back_to_default_when_missing(tmp_path: Path):
    missing = tmp_path / "missing.yaml"
    config = load_ibkr_readonly_qualification_config_audit_config(str(missing))
    rows = build_ibkr_readonly_qualification_config_audit_rows(config, TZ)

    assert len(rows) == 16
    assert rows[0].qualification_allowed == "false"


def test_config_audit_writers(tmp_path: Path):
    config = default_ibkr_readonly_qualification_template()
    rows = build_ibkr_readonly_qualification_config_audit_rows(config, TZ)

    csv_path = tmp_path / "ibkr_readonly_qualification_config_audit.csv"
    md_path = tmp_path / "ibkr_readonly_qualification_config_audit_report.md"

    write_ibkr_readonly_qualification_config_audit_csv(csv_path, rows)
    write_ibkr_readonly_qualification_config_audit_report(md_path, rows, "data/ibkr_readonly_qualification_config_template.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "config_audit_status" in csv_text
    assert "Phase 11B IBKR Read-Only Qualification Config Audit Report" in md_text
    assert "final_config_audit_status: blocked_or_disabled" in md_text
    assert "qualification_allowed_count: 0" in md_text
    assert "no TWS connection" in md_text
    assert "no auto trade" in md_text
