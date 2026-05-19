from __future__ import annotations

import csv

from src.ibkr_readonly_qualification_phase12_closure_report import (
    Phase12ClosureReportRow,
    build_ibkr_readonly_qualification_phase12_closure_report_rows,
    write_ibkr_readonly_qualification_phase12_closure_report_csv,
    write_ibkr_readonly_qualification_phase12_closure_report_report,
)


def test_build_phase12_closure_report_default_rows_are_locked():
    rows = build_ibkr_readonly_qualification_phase12_closure_report_rows()

    assert len(rows) == 9
    assert {row.phase_id for row in rows} == {"12A", "12B", "12C", "12D", "12E", "12F", "12G", "12H", "FINAL"}
    assert all(row.phase12_closure_status == "COMPLETE" for row in rows)
    assert all(row.final_authorization_status == "BLOCKED" for row in rows)
    assert all(row.final_authorization_allowed == "false" for row in rows)
    assert all(row.effective_approval_gate_status == "CLOSED" for row in rows)
    assert all(row.approval_effective == "false" for row in rows)
    assert all(row.candidate_final_gate_status == "CLOSED" for row in rows)
    assert all(row.candidate_safety_status == "BLOCKED" for row in rows)
    assert all(row.qualification_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.api_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_phase12_closure_report_blocks_attempted_upstream_unlock_csv(tmp_path):
    path = tmp_path / "final_authorization_packet.csv"
    path.write_text(
        "\n".join(
            [
                "section_id,section_name,source_layer,final_authorization_status,final_authorization_allowed,action_allowed",
                "FINAL,Final authorization packet,Phase 12A-12H,AUTHORIZED,true,true",
            ]
        ),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_qualification_phase12_closure_report_rows(path)

    assert len(rows) == 1
    assert rows[0].phase12_closure_status == "COMPLETE"
    assert rows[0].final_authorization_status == "BLOCKED"
    assert rows[0].final_authorization_allowed == "false"
    assert rows[0].effective_approval_gate_status == "CLOSED"
    assert rows[0].qualification_allowed == "false"
    assert rows[0].tws_connection_allowed == "false"
    assert rows[0].api_request_allowed == "false"
    assert rows[0].action_allowed == "false"
    assert rows[0].closure_decision == "upstream_attempted_unlock_but_phase12_closure_remains_blocked"


def test_phase12_closure_report_warning_flags_are_safety_locked():
    rows = build_ibkr_readonly_qualification_phase12_closure_report_rows()

    for row in rows:
        assert "phase12i_ibkr_readonly_qualification_phase12_closure_report" in row.warning_flags
        assert "phase12_closure_report_only" in row.warning_flags
        assert "final_authorization_blocked" in row.warning_flags
        assert "final_authorization_allowed_false" in row.warning_flags
        assert "no_tws_connection" in row.warning_flags
        assert "no_ibkr_connection" in row.warning_flags
        assert "no_reqMktData" in row.warning_flags
        assert "no_reqHistoricalData" in row.warning_flags
        assert "no_order" in row.warning_flags
        assert "no_auto_trade" in row.warning_flags


def test_write_phase12_closure_report_csv_and_report(tmp_path):
    rows = [
        Phase12ClosureReportRow(
            phase_id="FINAL",
            phase_name="Phase 12 final closure",
            source_layer="Phase 12A-12H",
            phase12_closure_status="COMPLETE",
            final_authorization_status="BLOCKED",
            final_authorization_allowed="false",
            effective_approval_gate_status="CLOSED",
            approval_effective="false",
            candidate_final_gate_status="CLOSED",
            candidate_safety_status="BLOCKED",
            qualification_allowed="false",
            tws_connection_allowed="false",
            contract_qualification_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            api_request_allowed="false",
            action_allowed="false",
            closure_decision="phase12_closed_with_final_authorization_blocked",
            warning_flags="PHASE12_COMPLETE;BLOCKED;CLOSED;phase12_closure_report_only;no_tws_connection;no_order;no_auto_trade",
            notes="Phase 12 closure report only.",
            timestamp_jst="2026-05-19T14:00:00+09:00",
            timestamp_et="2026-05-19T01:00:00-04:00",
        )
    ]

    csv_path = tmp_path / "phase12_closure_report.csv"
    md_path = tmp_path / "phase12_closure_report.md"

    write_ibkr_readonly_qualification_phase12_closure_report_csv(csv_path, rows)
    write_ibkr_readonly_qualification_phase12_closure_report_report(md_path, rows, "final_authorization_packet.csv")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["phase_id"] == "FINAL"
    assert csv_rows[0]["phase12_closure_status"] == "COMPLETE"
    assert csv_rows[0]["final_authorization_status"] == "BLOCKED"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 12I IBKR Read-Only Qualification Phase 12 Closure Report" in report
    assert "Phase 12 closure status: COMPLETE" in report
    assert "Final authorization status: BLOCKED" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report


def test_build_phase12_closure_report_has_timestamps():
    rows = build_ibkr_readonly_qualification_phase12_closure_report_rows()

    assert rows[0].timestamp_jst
    assert rows[0].timestamp_et
    assert "+09:00" in rows[0].timestamp_jst
