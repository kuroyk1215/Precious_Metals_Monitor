from __future__ import annotations

import csv

from src.ibkr_readonly_preflight_config_template import (
    PreflightConfigTemplateRow,
    build_ibkr_readonly_preflight_config_template_rows,
    write_ibkr_readonly_preflight_config_template_csv,
    write_ibkr_readonly_preflight_config_template_report,
    write_ibkr_readonly_preflight_config_template_yaml,
)


def test_preflight_config_template_default_rows_are_safe():
    rows = build_ibkr_readonly_preflight_config_template_rows("config.yaml")

    assert len(rows) == 11
    assert {row.template_id for row in rows} == {
        "READ_ONLY_REQUIRED",
        "ACCOUNT_MODE",
        "HOST",
        "PORT",
        "CLIENT_ID",
        "REAL_CONNECTION",
        "CONTRACT_QUALIFICATION",
        "MARKET_DATA",
        "HISTORICAL_DATA",
        "TRADING_ACTIONS",
        "FINAL",
    }

    values = {row.config_key: row.template_value for row in rows}
    assert values["ibkr.read_only_required"] == "true"
    assert values["ibkr.account_mode"] == "paper"
    assert values["ibkr.host"] == "127.0.0.1"
    assert values["ibkr.port"] == "7497"
    assert values["ibkr.client_id"] == "1"
    assert values["ibkr.real_connection_allowed"] == "false"
    assert values["ibkr.contract_qualification_allowed"] == "false"
    assert values["ibkr.market_data_request_allowed"] == "false"
    assert values["ibkr.historical_data_request_allowed"] == "false"
    assert values["ibkr.trading_actions_allowed"] == "false"

    assert all(row.template_status == "TEMPLATE" for row in rows)
    assert all(row.apply_mode == "template_only" for row in rows)
    assert all(row.config_file_modified == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)
    assert all(row.real_connection_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.ibkr_api_request_allowed == "false" for row in rows)


def test_preflight_config_template_warning_flags_are_locked():
    rows = build_ibkr_readonly_preflight_config_template_rows()

    for row in rows:
        assert "phase14d_ibkr_readonly_preflight_config_template" in row.warning_flags
        assert "PREFLIGHT_CONFIG_TEMPLATE_DEFINED" in row.warning_flags
        assert "REAL_CONNECTION_BLOCKED" in row.warning_flags
        assert "TWS_CONNECTION_BLOCKED" in row.warning_flags
        assert "IBKR_API_REQUEST_BLOCKED" in row.warning_flags
        assert "ORDER_BLOCKED" in row.warning_flags
        assert "AUTO_TRADE_BLOCKED" in row.warning_flags
        assert "NO_CONFIG_FILE_MODIFICATION" in row.warning_flags


def test_write_preflight_config_template_csv_yaml_and_report(tmp_path):
    rows = [
        PreflightConfigTemplateRow(
            template_id="FINAL",
            template_name="Final preflight config template decision",
            source_layer="Phase 14D",
            input_source="config.yaml",
            config_key="phase14d.preflight_config_template_status",
            template_value="TEMPLATE_ONLY",
            template_status="TEMPLATE",
            apply_mode="template_only",
            config_file_modified="false",
            read_only_required="true",
            account_mode_explicit_required="true",
            real_connection_allowed="false",
            tws_connection_allowed="false",
            ibkr_api_request_allowed="false",
            contract_qualification_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            order_action_allowed="false",
            cancel_action_allowed="false",
            rebalance_action_allowed="false",
            auto_trade_allowed="false",
            action_allowed="false",
            warning_flags="PREFLIGHT_CONFIG_TEMPLATE_DEFINED;NO_CONFIG_FILE_MODIFICATION",
            notes="Template only.",
            timestamp_jst="2026-05-19T23:30:00+09:00",
            timestamp_et="2026-05-19T10:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "template.csv"
    yaml_path = tmp_path / "template.yaml"
    md_path = tmp_path / "template.md"

    write_ibkr_readonly_preflight_config_template_csv(csv_path, rows)
    write_ibkr_readonly_preflight_config_template_yaml(yaml_path, rows)
    write_ibkr_readonly_preflight_config_template_report(md_path, rows, "config.yaml", yaml_path)

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["template_id"] == "FINAL"
    assert csv_rows[0]["template_status"] == "TEMPLATE"
    assert csv_rows[0]["config_file_modified"] == "false"
    assert csv_rows[0]["action_allowed"] == "false"

    yaml_text = yaml_path.read_text(encoding="utf-8")
    assert "ibkr:" in yaml_text
    assert "read_only_required: true" in yaml_text
    assert "account_mode: paper" in yaml_text
    assert "real_connection_allowed: false" in yaml_text
    assert "trading_actions_allowed: false" in yaml_text

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 14D IBKR Read-Only Preflight Config Template Report" in report
    assert "Phase 14D status: TEMPLATE_ONLY" in report
    assert "no configuration file is modified" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report
