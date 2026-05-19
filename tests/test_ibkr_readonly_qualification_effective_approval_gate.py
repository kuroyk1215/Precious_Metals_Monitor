from __future__ import annotations

import csv

from src.ibkr_readonly_qualification_effective_approval_gate import (
    EffectiveApprovalGateRow,
    build_ibkr_readonly_qualification_effective_approval_gate_rows,
    write_ibkr_readonly_qualification_effective_approval_gate_csv,
    write_ibkr_readonly_qualification_effective_approval_gate_report,
)


def test_build_effective_approval_gate_default_rows_are_locked():
    rows = build_ibkr_readonly_qualification_effective_approval_gate_rows()

    assert len(rows) == 4
    assert {row.section_id for row in rows} == {"12A", "12B", "12C", "FINAL"}
    assert all(row.operator_approval_status == "PENDING" for row in rows)
    assert all(row.effective_approval_gate_status == "CLOSED" for row in rows)
    assert all(row.approval_effective == "false" for row in rows)
    assert all(row.effective_approval_allowed == "false" for row in rows)
    assert all(row.candidate_final_gate_status == "CLOSED" for row in rows)
    assert all(row.candidate_safety_status == "BLOCKED" for row in rows)
    assert all(row.qualification_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.api_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_effective_approval_gate_does_not_unlock_for_approved_csv(tmp_path):
    path = tmp_path / "approval_stub.csv"
    path.write_text(
        "\n".join(
            [
                "section_id,section_name,source_layer,operator_approval_status",
                "FINAL,Final operator approval stub,Phase 12A-12F,APPROVED",
            ]
        ),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_qualification_effective_approval_gate_rows(path)

    assert len(rows) == 1
    assert rows[0].operator_approval_status == "APPROVED"
    assert rows[0].effective_approval_gate_status == "CLOSED"
    assert rows[0].approval_effective == "false"
    assert rows[0].effective_approval_allowed == "false"
    assert rows[0].qualification_allowed == "false"
    assert rows[0].tws_connection_allowed == "false"
    assert rows[0].api_request_allowed == "false"
    assert rows[0].action_allowed == "false"
    assert "operator_approved_but_effective_approval_gate_remains_closed" in rows[0].decision_reason


def test_effective_approval_gate_warning_flags_are_safety_locked():
    rows = build_ibkr_readonly_qualification_effective_approval_gate_rows()

    for row in rows:
        assert "phase12g_ibkr_readonly_qualification_effective_approval_gate" in row.warning_flags
        assert "effective_approval_gate_closed" in row.warning_flags
        assert "effective_approval_allowed_false" in row.warning_flags
        assert "approval_effective_false" in row.warning_flags
        assert "no_tws_connection" in row.warning_flags
        assert "no_ibkr_connection" in row.warning_flags
        assert "no_reqMktData" in row.warning_flags
        assert "no_reqHistoricalData" in row.warning_flags
        assert "no_order" in row.warning_flags
        assert "no_auto_trade" in row.warning_flags


def test_write_effective_approval_gate_csv_and_report(tmp_path):
    rows = [
        EffectiveApprovalGateRow(
            section_id="FINAL",
            section_name="Final effective approval gate",
            source_layer="Phase 12A-12F",
            operator_approval_status="APPROVED",
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
            decision_reason="operator_approved_but_effective_approval_gate_remains_closed",
            warning_flags="BLOCKED;CLOSED;effective_approval_gate_closed;approval_effective_false;no_tws_connection;no_order;no_auto_trade",
            notes="Effective approval gate only.",
            timestamp_jst="2026-05-19T12:00:00+09:00",
            timestamp_et="2026-05-18T23:00:00-04:00",
        )
    ]

    csv_path = tmp_path / "effective_approval_gate.csv"
    md_path = tmp_path / "effective_approval_gate_report.md"

    write_ibkr_readonly_qualification_effective_approval_gate_csv(csv_path, rows)
    write_ibkr_readonly_qualification_effective_approval_gate_report(md_path, rows, "approval_stub.csv")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["section_id"] == "FINAL"
    assert csv_rows[0]["operator_approval_status"] == "APPROVED"
    assert csv_rows[0]["effective_approval_gate_status"] == "CLOSED"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 12G IBKR Read-Only Qualification Effective Approval Gate Report" in report
    assert "Effective approval gate status: CLOSED" in report
    assert "APPROVED upstream status is not executable in Phase 12G" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report


def test_build_effective_approval_gate_has_timestamps():
    rows = build_ibkr_readonly_qualification_effective_approval_gate_rows()

    assert rows[0].timestamp_jst
    assert rows[0].timestamp_et
    assert "+09:00" in rows[0].timestamp_jst
