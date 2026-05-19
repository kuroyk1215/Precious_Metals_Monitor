from __future__ import annotations

import csv

from src.ibkr_readonly_qualification_sandbox_input_contract import (
    SandboxInputContractRow,
    build_ibkr_readonly_qualification_sandbox_input_contract_rows,
    write_ibkr_readonly_qualification_sandbox_input_contract_csv,
    write_ibkr_readonly_qualification_sandbox_input_contract_report,
)


def test_build_sandbox_input_contract_rows_are_locked():
    rows = build_ibkr_readonly_qualification_sandbox_input_contract_rows()

    assert len(rows) == 7
    assert {row.contract_id for row in rows} == {"SCHEMA", "SOURCE", "TWS", "IBKR", "DATA", "ACTIONS", "FINAL"}
    assert all(row.sandbox_input_contract_status == "DEFINED" for row in rows)
    assert all(row.requires_explicit_sandbox_input == "true" for row in rows)
    assert all(row.accepts_manual_csv_input == "true" for row in rows)
    assert all(row.accepts_mock_snapshot_input == "true" for row in rows)
    assert all(row.accepts_real_tws_input == "false" for row in rows)
    assert all(row.accepts_real_ibkr_runtime_input == "false" for row in rows)
    assert all(row.sandbox_execution_allowed == "false" for row in rows)
    assert all(row.ibkr_api_request_allowed == "false" for row in rows)
    assert all(row.contract_qualification_allowed == "false" for row in rows)
    assert all(row.market_data_request_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_sandbox_input_contract_warning_flags_are_safety_locked():
    rows = build_ibkr_readonly_qualification_sandbox_input_contract_rows()

    for row in rows:
        assert "phase13b_ibkr_readonly_qualification_sandbox_input_contract" in row.warning_flags
        assert "INPUT_CONTRACT_DEFINED" in row.warning_flags
        assert "EXPLICIT_SANDBOX_INPUT_REQUIRED" in row.warning_flags
        assert "REAL_TWS_INPUT_REJECTED" in row.warning_flags
        assert "REAL_IBKR_RUNTIME_INPUT_REJECTED" in row.warning_flags
        assert "NO_REQ_MKT_DATA" in row.warning_flags
        assert "NO_REQ_HISTORICAL_DATA" in row.warning_flags
        assert "NO_ORDER" in row.warning_flags
        assert "NO_AUTO_TRADE" in row.warning_flags


def test_write_sandbox_input_contract_csv_and_report(tmp_path):
    rows = [
        SandboxInputContractRow(
            contract_id="FINAL",
            contract_name="Final sandbox input contract",
            source_layer="Phase 13B",
            sandbox_input_contract_status="DEFINED",
            required_input_type="manual_csv_or_mock_snapshot_only",
            requires_explicit_sandbox_input="true",
            accepts_manual_csv_input="true",
            accepts_mock_snapshot_input="true",
            accepts_real_tws_input="false",
            accepts_real_ibkr_runtime_input="false",
            sandbox_execution_allowed="false",
            ibkr_api_request_allowed="false",
            contract_qualification_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            order_action_allowed="false",
            cancel_action_allowed="false",
            rebalance_action_allowed="false",
            auto_trade_allowed="false",
            action_allowed="false",
            contract_decision="phase13b_input_contract_defined_but_execution_blocked",
            warning_flags="INPUT_CONTRACT_DEFINED;REAL_TWS_INPUT_REJECTED;NO_ORDER;NO_AUTO_TRADE",
            notes="Sandbox input contract only.",
            timestamp_jst="2026-05-19T16:00:00+09:00",
            timestamp_et="2026-05-19T03:00:00-04:00",
        )
    ]

    csv_path = tmp_path / "sandbox_input_contract.csv"
    md_path = tmp_path / "sandbox_input_contract_report.md"

    write_ibkr_readonly_qualification_sandbox_input_contract_csv(csv_path, rows)
    write_ibkr_readonly_qualification_sandbox_input_contract_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["contract_id"] == "FINAL"
    assert csv_rows[0]["sandbox_input_contract_status"] == "DEFINED"
    assert csv_rows[0]["accepts_real_tws_input"] == "false"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 13B IBKR Read-Only Qualification Sandbox Input Contract Report" in report
    assert "Sandbox input contract status: DEFINED" in report
    assert "Real TWS input is rejected" in report
    assert "Real IBKR runtime input is rejected" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report


def test_build_sandbox_input_contract_has_timestamps():
    rows = build_ibkr_readonly_qualification_sandbox_input_contract_rows()

    assert rows[0].timestamp_jst
    assert rows[0].timestamp_et
    assert "+09:00" in rows[0].timestamp_jst


def test_sandbox_input_contract_blocks_all_action_subtypes():
    rows = build_ibkr_readonly_qualification_sandbox_input_contract_rows()

    for row in rows:
        assert row.order_action_allowed == "false"
        assert row.cancel_action_allowed == "false"
        assert row.rebalance_action_allowed == "false"
        assert row.auto_trade_allowed == "false"
