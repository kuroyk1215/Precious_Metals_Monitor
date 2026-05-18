from pathlib import Path
import yaml

from src.ibkr_readonly_qualification_config_template import (
    build_ibkr_readonly_qualification_config_template_rows,
    default_ibkr_readonly_qualification_template,
    write_ibkr_readonly_qualification_config_template_csv,
    write_ibkr_readonly_qualification_config_template_report,
    write_ibkr_readonly_qualification_template_yaml,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_default_template_is_disabled_and_safe():
    template = default_ibkr_readonly_qualification_template()
    cfg = template["runtime"]["ibkr_readonly_qualification"]

    assert cfg["enabled"] is False
    assert cfg["explicit_execution_flag"] is False
    assert cfg["operator_manual_approval"] is False
    assert cfg["read_only_required"] is True
    assert cfg["allow_tws_connection"] is False
    assert cfg["allow_contract_qualification"] is False
    assert cfg["allow_market_data_request"] is False
    assert cfg["allow_historical_data_request"] is False
    assert cfg["allow_order"] is False
    assert cfg["allow_cancel"] is False
    assert cfg["allow_rebalance"] is False
    assert cfg["allow_auto_trade"] is False


def test_config_template_rows_are_blocked():
    rows = build_ibkr_readonly_qualification_config_template_rows(TZ)

    assert len(rows) >= 16

    by_key = {row.config_key: row for row in rows}

    assert by_key["enabled"].template_value == "false"
    assert by_key["read_only_required"].template_value == "true"
    assert by_key["allow_tws_connection"].template_value == "false"
    assert by_key["allow_contract_qualification"].template_value == "false"
    assert by_key["allow_market_data_request"].template_value == "false"
    assert by_key["allow_order"].template_value == "false"

    for row in rows:
        assert row.qualification_allowed == "false"
        assert row.tws_connection_allowed == "false"
        assert row.contract_qualification_allowed == "false"
        assert row.market_data_request_allowed == "false"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_ibkr_connection" in row.warning_flags


def test_config_template_writers(tmp_path: Path):
    rows = build_ibkr_readonly_qualification_config_template_rows(TZ)

    csv_path = tmp_path / "ibkr_readonly_qualification_config_template.csv"
    md_path = tmp_path / "ibkr_readonly_qualification_config_template_report.md"
    yaml_path = tmp_path / "ibkr_readonly_qualification_config_template.yaml"

    write_ibkr_readonly_qualification_config_template_csv(csv_path, rows)
    write_ibkr_readonly_qualification_config_template_report(md_path, rows, str(yaml_path))
    write_ibkr_readonly_qualification_template_yaml(yaml_path)

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")
    loaded_yaml = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    assert "template_status" in csv_text
    assert "Phase 11A IBKR Read-Only Qualification Config Template Report" in md_text
    assert "qualification_allowed_count: 0" in md_text
    assert "no TWS connection" in md_text
    assert "no auto trade" in md_text
    assert loaded_yaml["runtime"]["ibkr_readonly_qualification"]["enabled"] is False
