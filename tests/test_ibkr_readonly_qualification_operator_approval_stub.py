from __future__ import annotations

import csv

from src.ibkr_readonly_qualification_operator_approval_stub import (
    APPROVAL_INPUT_TEMPLATE,
    OperatorApprovalStubRow,
    build_ibkr_readonly_qualification_operator_approval_stub_rows,
    write_ibkr_readonly_qualification_operator_approval_stub_csv,
    write_ibkr_readonly_qualification_operator_approval_stub_report,
)


def test_build_operator_approval_stub_rows_are_locked():
    rows = build_ibkr_readonly_qualification_operator_approval_stub_rows()

    assert len(rows) == 4
    assert {row.section_id for row in rows} == {"12A", "12B", "12C", "FINAL"}
    assert all(row.operator_decision_status == "PENDING" for row in rows)
    assert all(row.operator_approval_status == "PENDING" for row in rows)
    assert all(row.operator_approval_required == "true" for row in rows)
    assert all(row.approval_effective == "false" for row in rows)
    assert all(row.candidate_final_gate_status == "CLOSED" for row in rows)
    assert all(row.candidate_safety_status == "BLOCKED" for row in rows)
    assert all(row.qualification_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.contract_qualification_allowed == "false" for row in rows)
    assert all(row.market_data_request_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.api_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)
    assert all(row.approval_input_template == APPROVAL_INPUT_TEMPLATE for row in rows)


def test_operator_approval_stub_warning_flags_are_safety_locked():
    rows = build_ibkr_readonly_qualification_operator_approval_stub_rows()

    for row in rows:
        assert "phase12f_ibkr_readonly_qualification_operator_approval_stub" in row.warning_flags
        assert "operator_approval_stub_only" in row.warning_flags
        assert "approval_effective_false" in row.warning_flags
        assert "no_tws_connection" in row.warning_flags
        assert "no_ibkr_connection" in row.warning_flags
        assert "no_reqMktData" in row.warning_flags
        assert "no_reqHistoricalData" in row.warning_flags
        assert "no_order" in row.warning_flags
        assert "no_auto_trade" in row.warning_flags


def test_write_operator_approval_stub_csv_and_report(tmp_path):
    rows = [
        OperatorApprovalStubRow(
            section_id="FINAL",
            section_name="Final operator approval stub",
            source_layer="Phase 12A-12E",
            candidate_final_gate_status="CLOSED",
            candidate_safety_status="BLOCKED",
            operator_decision_status="PENDING",
            operator_approval_status="PENDING",
            operator_approval_required="true",
            approval_effective="false",
            qualification_allowed="false",
            tws_connection_allowed="false",
            contract_qualification_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            api_request_allowed="false",
            action_allowed="false",
            approval_input_template="PENDING|APPROVED|REJECTED|NEEDS_REVIEW",
            decision_reason="operator_approval_pending_until_explicit_future_effective_gate",
            warning_flags="BLOCKED;CLOSED;operator_approval_stub_only;approval_effective_false;no_tws_connection;no_order;no_auto_trade",
            notes="Operator approval stub only.",
            timestamp_jst="2026-05-19T09:00:00+09:00",
            timestamp_et="2026-05-18T20:00:00-04:00",
        )
    ]

    csv_path = tmp_path / "operator_approval_stub.csv"
    md_path = tmp_path / "operator_approval_stub_report.md"

    write_ibkr_readonly_qualification_operator_approval_stub_csv(csv_path, rows)
    write_ibkr_readonly_qualification_operator_approval_stub_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["section_id"] == "FINAL"
    assert csv_rows[0]["operator_approval_status"] == "PENDING"
    assert csv_rows[0]["approval_effective"] == "false"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 12F IBKR Read-Only Qualification Operator Approval Stub Report" in report
    assert "Operator approval status: PENDING" in report
    assert "Approval is not effective in Phase 12F" in report
    assert "APPROVED is not executable in Phase 12F" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report


def test_build_operator_approval_stub_has_timestamps():
    rows = build_ibkr_readonly_qualification_operator_approval_stub_rows()

    assert rows[0].timestamp_jst
    assert rows[0].timestamp_et
    assert "+09:00" in rows[0].timestamp_jst
