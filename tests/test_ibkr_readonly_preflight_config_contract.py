from __future__ import annotations

import csv

from src.ibkr_readonly_preflight_config_contract import (
    PreflightConfigContractRow,
    build_ibkr_readonly_preflight_config_contract_rows,
    write_ibkr_readonly_preflight_config_contract_csv,
    write_ibkr_readonly_preflight_config_contract_report,
)


def test_build_preflight_config_contract_default_rows_are_locked():
    rows = build_ibkr_readonly_preflight_config_contract_rows()

    assert len(rows) == 11
    assert {row.contract_id for row in rows} == {
        "READ_ONLY_REQUIRED",
        "ACCOUNT_MODE",
        "HOST",
        "PORT",
        "CLIENT_ID",
        "CONNECTION",
        "QUALIFICATION",
        "MARKET_DATA",
        "HISTORICAL_DATA",
        "TRADING_ACTIONS",
        "FINAL",
    }
    assert all(row.preflight_config_contract_status == "DEFINED" for row in rows)
    assert all(row.read_only_required == "true" for row in rows)
    assert all(row.account_mode_explicit_required == "true" for row in rows)
    assert all(row.trading_permissions_must_be_disabled == "true" for row in rows)
    assert all(row.real_connection_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.ibkr_api_request_allowed == "false" for row in rows)
    assert all(row.contract_qualification_allowed == "false" for row in rows)
    assert all(row.market_data_request_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_preflight_config_contract_required_keys_are_present():
    rows = build_ibkr_readonly_preflight_config_contract_rows()
    keys = {row.required_config_key for row in rows}

    assert "ibkr.read_only_required" in keys
    assert "ibkr.account_mode" in keys
    assert "ibkr.host" in keys
    assert "ibkr.port" in keys
    assert "ibkr.client_id" in keys
    assert "ibkr.real_connection_allowed" in keys
    assert "ibkr.contract_qualification_allowed" in keys
    assert "ibkr.market_data_request_allowed" in keys
    assert "ibkr.historical_data_request_allowed" in keys
    assert "ibkr.trading_actions_allowed" in keys


def test_preflight_config_contract_warning_flags_are_safety_locked():
    rows = build_ibkr_readonly_preflight_config_contract_rows()

    for row in rows:
        assert "phase14b_ibkr_readonly_preflight_config_contract" in row.warning_flags
        assert "PREFLIGHT_CONFIG_CONTRACT_DEFINED" in row.warning_flags
        assert "READ_ONLY_REQUIRED" in row.warning_flags
        assert "ACCOUNT_MODE_EXPLICIT_REQUIRED" in row.warning_flags
        assert "REAL_CONNECTION_BLOCKED" in row.warning_flags
        assert "TWS_CONNECTION_BLOCKED" in row.warning_flags
        assert "IBKR_API_REQUEST_BLOCKED" in row.warning_flags
        assert "CONTRACT_QUALIFICATION_BLOCKED" in row.warning_flags
        assert "MARKET_DATA_REQUEST_BLOCKED" in row.warning_flags
        assert "HISTORICAL_DATA_REQUEST_BLOCKED" in row.warning_flags
        assert "ORDER_BLOCKED" in row.warning_flags
        assert "AUTO_TRADE_BLOCKED" in row.warning_flags


def test_write_preflight_config_contract_csv_and_report(tmp_path):
    rows = [
        PreflightConfigContractRow(
            contract_id="FINAL",
            contract_name="Final preflight config contract",
            source_layer="Phase 14B",
            preflight_config_contract_status="DEFINED",
            required_config_key="phase14b.preflight_config_contract_status",
            required_config_value="DEFINED",
            prohibited_config_values="execution_enabled,connection_enabled,trading_enabled",
            read_only_required="true",
            account_mode_explicit_required="true",
            trading_permissions_must_be_disabled="true",
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
            contract_decision="phase14b_preflight_config_contract_defined_but_execution_blocked",
            warning_flags="PREFLIGHT_CONFIG_CONTRACT_DEFINED;READ_ONLY_REQUIRED;ORDER_BLOCKED;AUTO_TRADE_BLOCKED",
            notes="Preflight config contract only.",
            timestamp_jst="2026-05-19T23:30:00+09:00",
            timestamp_et="2026-05-19T10:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "preflight_config_contract.csv"
    md_path = tmp_path / "preflight_config_contract_report.md"

    write_ibkr_readonly_preflight_config_contract_csv(csv_path, rows)
    write_ibkr_readonly_preflight_config_contract_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["contract_id"] == "FINAL"
    assert csv_rows[0]["preflight_config_contract_status"] == "DEFINED"
    assert csv_rows[0]["read_only_required"] == "true"
    assert csv_rows[0]["real_connection_allowed"] == "false"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 14B IBKR Read-Only Preflight Config Contract Report" in report
    assert "Preflight config contract status: DEFINED" in report
    assert "read_only_required must be true" in report
    assert "account_mode must be explicit" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report


def test_build_preflight_config_contract_has_timestamps():
    rows = build_ibkr_readonly_preflight_config_contract_rows()

    assert rows[0].timestamp_jst
    assert rows[0].timestamp_et
    assert "+09:00" in rows[0].timestamp_jst
