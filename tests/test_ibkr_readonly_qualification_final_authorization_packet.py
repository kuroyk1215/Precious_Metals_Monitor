from __future__ import annotations

import csv

from src.ibkr_readonly_qualification_final_authorization_packet import (
    FinalAuthorizationPacketRow,
    build_ibkr_readonly_qualification_final_authorization_packet_rows,
    write_ibkr_readonly_qualification_final_authorization_packet_csv,
    write_ibkr_readonly_qualification_final_authorization_packet_report,
)


def test_build_final_authorization_packet_default_rows_are_locked():
    rows = build_ibkr_readonly_qualification_final_authorization_packet_rows()

    assert len(rows) == 8
    assert {row.section_id for row in rows} == {"12A", "12B", "12C", "12D", "12E", "12F", "12G", "FINAL"}
    assert all(row.final_authorization_status == "BLOCKED" for row in rows)
    assert all(row.final_authorization_allowed == "false" for row in rows)
    assert all(row.effective_approval_gate_status == "CLOSED" for row in rows)
    assert all(row.approval_effective == "false" for row in rows)
    assert all(row.effective_approval_allowed == "false" for row in rows)
    assert all(row.candidate_final_gate_status == "CLOSED" for row in rows)
    assert all(row.candidate_safety_status == "BLOCKED" for row in rows)
    assert all(row.qualification_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.api_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_final_authorization_packet_blocks_attempted_upstream_unlock_csv(tmp_path):
    path = tmp_path / "effective_gate.csv"
    path.write_text(
        "\n".join(
            [
                "section_id,section_name,source_layer,effective_approval_gate_status,approval_effective,action_allowed",
                "FINAL,Final effective approval gate,Phase 12A-12G,OPEN,true,true",
            ]
        ),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_qualification_final_authorization_packet_rows(path)

    assert len(rows) == 1
    assert rows[0].final_authorization_status == "BLOCKED"
    assert rows[0].final_authorization_allowed == "false"
    assert rows[0].effective_approval_gate_status == "CLOSED"
    assert rows[0].approval_effective == "false"
    assert rows[0].qualification_allowed == "false"
    assert rows[0].tws_connection_allowed == "false"
    assert rows[0].api_request_allowed == "false"
    assert rows[0].action_allowed == "false"
    assert rows[0].decision_reason == "upstream_attempted_unlock_but_final_authorization_remains_blocked"


def test_final_authorization_packet_warning_flags_are_safety_locked():
    rows = build_ibkr_readonly_qualification_final_authorization_packet_rows()

    for row in rows:
        assert "phase12h_ibkr_readonly_qualification_final_authorization_packet" in row.warning_flags
        assert "final_authorization_blocked" in row.warning_flags
        assert "final_authorization_allowed_false" in row.warning_flags
        assert "effective_approval_gate_closed" in row.warning_flags
        assert "no_tws_connection" in row.warning_flags
        assert "no_ibkr_connection" in row.warning_flags
        assert "no_reqMktData" in row.warning_flags
        assert "no_reqHistoricalData" in row.warning_flags
        assert "no_order" in row.warning_flags
        assert "no_auto_trade" in row.warning_flags


def test_write_final_authorization_packet_csv_and_report(tmp_path):
    rows = [
        FinalAuthorizationPacketRow(
            section_id="FINAL",
            section_name="Final authorization packet",
            source_layer="Phase 12A-12G",
            final_authorization_status="BLOCKED",
            final_authorization_allowed="false",
            effective_approval_gate_status="CLOSED",
            approval_effective="false",
            effective_approval_allowed="false",
            candidate_final_gate_status="CLOSED",
            candidate_safety_status="BLOCKED",
            qualification_allowed="false",
            tws_connection_allowed="false",
            contract_qualification_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            api_request_allowed="false",
            action_allowed="false",
            decision_reason="final_authorization_blocked_by_design",
            warning_flags="BLOCKED;CLOSED;final_authorization_blocked;no_tws_connection;no_order;no_auto_trade",
            notes="Final authorization packet only.",
            timestamp_jst="2026-05-19T13:00:00+09:00",
            timestamp_et="2026-05-19T00:00:00-04:00",
        )
    ]

    csv_path = tmp_path / "final_authorization_packet.csv"
    md_path = tmp_path / "final_authorization_packet_report.md"

    write_ibkr_readonly_qualification_final_authorization_packet_csv(csv_path, rows)
    write_ibkr_readonly_qualification_final_authorization_packet_report(md_path, rows, "effective_gate.csv")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["section_id"] == "FINAL"
    assert csv_rows[0]["final_authorization_status"] == "BLOCKED"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 12H IBKR Read-Only Qualification Final Authorization Packet Report" in report
    assert "Final authorization status: BLOCKED" in report
    assert "Final authorization allowed: false" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report


def test_build_final_authorization_packet_has_timestamps():
    rows = build_ibkr_readonly_qualification_final_authorization_packet_rows()

    assert rows[0].timestamp_jst
    assert rows[0].timestamp_et
    assert "+09:00" in rows[0].timestamp_jst
