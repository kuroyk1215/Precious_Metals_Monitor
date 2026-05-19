from __future__ import annotations

import csv

from src.ibkr_readonly_preflight_config_validator import (
    PASS_TEXT,
    FAIL_TEXT,
    PreflightConfigValidationRow,
    build_ibkr_readonly_preflight_config_validator_rows,
    write_ibkr_readonly_preflight_config_validator_csv,
    write_ibkr_readonly_preflight_config_validator_report,
)


def test_preflight_config_validator_passes_safe_local_readonly_config(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
ibkr:
  read_only_required: true
  account_mode: paper
  host: 127.0.0.1
  port: 7497
  client_id: 1
  real_connection_allowed: false
  contract_qualification_allowed: false
  market_data_request_allowed: false
  historical_data_request_allowed: false
  trading_actions_allowed: false
""".strip(),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_preflight_config_validator_rows(config_path)

    assert len(rows) == 12
    assert {row.check_id for row in rows} == {
        "INPUT_SOURCE",
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
    assert all(row.validation_status == PASS_TEXT for row in rows)
    assert all(row.action_allowed == "false" for row in rows)
    assert all(row.real_connection_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.ibkr_api_request_allowed == "false" for row in rows)


def test_preflight_config_validator_fails_missing_input_source(tmp_path):
    missing_path = tmp_path / "missing.yaml"

    rows = build_ibkr_readonly_preflight_config_validator_rows(missing_path)

    assert rows[0].check_id == "INPUT_SOURCE"
    assert rows[0].validation_status == FAIL_TEXT
    assert rows[-1].check_id == "FINAL"
    assert rows[-1].validation_status == FAIL_TEXT
    assert all(row.action_allowed == "false" for row in rows)


def test_preflight_config_validator_fails_unsafe_values(tmp_path):
    config_path = tmp_path / "unsafe.yaml"
    config_path.write_text(
        """
ibkr:
  read_only_required: false
  account_mode: unknown
  host: remote.example.com
  port: not_a_port
  client_id: abc
  real_connection_allowed: true
  contract_qualification_allowed: true
  market_data_request_allowed: true
  historical_data_request_allowed: true
  trading_actions_allowed: true
""".strip(),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_preflight_config_validator_rows(config_path)
    failed = {row.check_id for row in rows if row.validation_status == FAIL_TEXT}

    assert "READ_ONLY_REQUIRED" in failed
    assert "ACCOUNT_MODE" in failed
    assert "HOST" in failed
    assert "PORT" in failed
    assert "CLIENT_ID" in failed
    assert "REAL_CONNECTION" in failed
    assert "CONTRACT_QUALIFICATION" in failed
    assert "MARKET_DATA" in failed
    assert "HISTORICAL_DATA" in failed
    assert "TRADING_ACTIONS" in failed
    assert "FINAL" in failed
    assert all(row.action_allowed == "false" for row in rows)


def test_write_preflight_config_validator_csv_and_report(tmp_path):
    rows = [
        PreflightConfigValidationRow(
            check_id="FINAL",
            check_name="Final IBKR read-only preflight config validation decision",
            source_layer="Phase 14C",
            input_source="config.yaml",
            required_config_key="phase14c.preflight_config_validator_status",
            expected_value="PASS",
            actual_value="PASS",
            validation_status="PASS",
            action_allowed="false",
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
            warning_flags="PREFLIGHT_CONFIG_VALIDATOR_DEFINED;PASS",
            notes="Validator only.",
            timestamp_jst="2026-05-19T23:30:00+09:00",
            timestamp_et="2026-05-19T10:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "validator.csv"
    md_path = tmp_path / "validator.md"

    write_ibkr_readonly_preflight_config_validator_csv(csv_path, rows)
    write_ibkr_readonly_preflight_config_validator_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["check_id"] == "FINAL"
    assert csv_rows[0]["validation_status"] == "PASS"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 14C IBKR Read-Only Preflight Config Validator Report" in report
    assert "Phase 14C final validation status: PASS" in report
    assert "no TWS connection" in report
    assert "no IBKR connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report
