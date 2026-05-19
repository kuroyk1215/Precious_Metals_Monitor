from __future__ import annotations

import csv

from src.ibkr_readonly_qualification_sandbox_input_validator import (
    SandboxInputValidatorRow,
    build_ibkr_readonly_qualification_sandbox_input_validator_rows,
    write_ibkr_readonly_qualification_sandbox_input_validator_csv,
    write_ibkr_readonly_qualification_sandbox_input_validator_report,
)


def test_build_sandbox_input_validator_default_rows():
    rows = build_ibkr_readonly_qualification_sandbox_input_validator_rows()

    assert len(rows) == 11
    assert {row.input_source_type for row in rows} >= {"manual_csv", "mock_snapshot", "real_tws", "real_ibkr_runtime"}
    assert sum(1 for row in rows if row.sandbox_input_validation_status == "VALIDATED") == 2
    assert sum(1 for row in rows if row.sandbox_input_validation_status == "REJECTED") == 9
    assert all(row.sandbox_execution_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.ibkr_api_request_allowed == "false" for row in rows)
    assert all(row.contract_qualification_allowed == "false" for row in rows)
    assert all(row.market_data_request_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_sandbox_input_validator_accepts_only_manual_and_mock_csv(tmp_path):
    path = tmp_path / "sandbox_inputs.csv"
    path.write_text(
        "\n".join(
            [
                "validation_id,input_source_type,input_label",
                "A,manual_csv,Manual input",
                "B,mock_snapshot,Mock input",
                "C,real_tws,Real TWS",
                "D,order,Order input",
            ]
        ),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_qualification_sandbox_input_validator_rows(path)

    assert [row.sandbox_input_validation_status for row in rows] == ["VALIDATED", "VALIDATED", "REJECTED", "REJECTED"]
    assert [row.input_allowed for row in rows] == ["true", "true", "false", "false"]
    assert all(row.action_allowed == "false" for row in rows)


def test_sandbox_input_validator_warning_flags_are_safety_locked():
    rows = build_ibkr_readonly_qualification_sandbox_input_validator_rows()

    for row in rows:
        assert "phase13c_ibkr_readonly_qualification_sandbox_input_validator" in row.warning_flags
        assert "EXPLICIT_SANDBOX_INPUT_REQUIRED" in row.warning_flags
        assert "REAL_TWS_INPUT_REJECTED" in row.warning_flags
        assert "REAL_IBKR_RUNTIME_INPUT_REJECTED" in row.warning_flags
        assert "NO_REQ_MKT_DATA" in row.warning_flags
        assert "NO_REQ_HISTORICAL_DATA" in row.warning_flags
        assert "NO_ORDER" in row.warning_flags
        assert "NO_AUTO_TRADE" in row.warning_flags


def test_write_sandbox_input_validator_csv_and_report(tmp_path):
    rows = [
        SandboxInputValidatorRow(
            validation_id="FINAL",
            input_source_type="validator_summary",
            input_label="Final sandbox input validator summary",
            source_layer="Phase 13C",
            sandbox_input_validation_status="REJECTED",
            input_allowed="false",
            validation_passed="false",
            rejection_required="true",
            requires_explicit_sandbox_input="true",
            accepts_real_tws_input="false",
            accepts_real_ibkr_runtime_input="false",
            sandbox_execution_allowed="false",
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
            validation_decision="validator_summary_only_execution_blocked",
            warning_flags="SANDBOX_INPUT_VALIDATOR;NO_ORDER;NO_AUTO_TRADE",
            notes="Sandbox input validator only.",
            timestamp_jst="2026-05-19T17:00:00+09:00",
            timestamp_et="2026-05-19T04:00:00-04:00",
        )
    ]

    csv_path = tmp_path / "sandbox_input_validator.csv"
    md_path = tmp_path / "sandbox_input_validator_report.md"

    write_ibkr_readonly_qualification_sandbox_input_validator_csv(csv_path, rows)
    write_ibkr_readonly_qualification_sandbox_input_validator_report(md_path, rows, "inputs.csv")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["validation_id"] == "FINAL"
    assert csv_rows[0]["sandbox_input_validation_status"] == "REJECTED"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 13C IBKR Read-Only Qualification Sandbox Input Validator Report" in report
    assert "manual_csv and mock_snapshot are accepted only as sandbox input shapes" in report
    assert "real_tws and real_ibkr_runtime inputs are rejected" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report


def test_build_sandbox_input_validator_has_timestamps():
    rows = build_ibkr_readonly_qualification_sandbox_input_validator_rows()

    assert rows[0].timestamp_jst
    assert rows[0].timestamp_et
    assert "+09:00" in rows[0].timestamp_jst
