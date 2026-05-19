from __future__ import annotations

import csv

from src.ibkr_readonly_qualification_sandbox_safety_gate import (
    SandboxSafetyGateRow,
    build_ibkr_readonly_qualification_sandbox_safety_gate_rows,
    write_ibkr_readonly_qualification_sandbox_safety_gate_csv,
    write_ibkr_readonly_qualification_sandbox_safety_gate_report,
)


def test_build_sandbox_safety_gate_default_rows():
    rows = build_ibkr_readonly_qualification_sandbox_safety_gate_rows()

    assert len(rows) == 5
    assert all(row.sandbox_safety_gate_status == "CLOSED" for row in rows)
    assert all(row.sandbox_result_accepted_for_review == "true" for row in rows)
    assert all(row.simulated_result_only == "true" for row in rows)
    assert all(row.real_qualification_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.ibkr_api_request_allowed == "false" for row in rows)
    assert all(row.market_data_request_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_sandbox_safety_gate_blocks_attempted_unlock_csv(tmp_path):
    path = tmp_path / "result_pack.csv"
    path.write_text(
        "\n".join(
            [
                "pack_id,pack_name,sandbox_result_pack_status,simulated_result_only,sandbox_qualification_status,simulated_qualification_result,action_allowed",
                "A,Attempted unlock,BUILT,false,SIMULATED,QUALIFIED_SIMULATED,true",
            ]
        ),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_qualification_sandbox_safety_gate_rows(path)

    assert len(rows) == 1
    assert rows[0].sandbox_safety_gate_status == "CLOSED"
    assert rows[0].sandbox_result_accepted_for_review == "true"
    assert rows[0].simulated_result_only == "true"
    assert rows[0].real_qualification_allowed == "false"
    assert rows[0].action_allowed == "false"
    assert rows[0].safety_decision == "upstream_unlock_attempt_detected_safety_gate_closed"


def test_sandbox_safety_gate_warning_flags_are_safety_locked():
    rows = build_ibkr_readonly_qualification_sandbox_safety_gate_rows()

    for row in rows:
        assert "phase13f_ibkr_readonly_qualification_sandbox_safety_gate" in row.warning_flags
        assert "SANDBOX_SAFETY_GATE" in row.warning_flags
        assert "SAFETY_GATE_CLOSED" in row.warning_flags
        assert "SIMULATED_RESULT_ONLY" in row.warning_flags
        assert "REAL_QUALIFICATION_BLOCKED" in row.warning_flags
        assert "TWS_CONNECTION_BLOCKED" in row.warning_flags
        assert "IBKR_API_REQUEST_BLOCKED" in row.warning_flags
        assert "NO_REQ_MKT_DATA" in row.warning_flags
        assert "NO_REQ_HISTORICAL_DATA" in row.warning_flags
        assert "NO_ORDER" in row.warning_flags
        assert "NO_AUTO_TRADE" in row.warning_flags


def test_write_sandbox_safety_gate_csv_and_report(tmp_path):
    rows = [
        SandboxSafetyGateRow(
            gate_id="FINAL",
            gate_name="Final sandbox safety gate summary",
            source_layer="Phase 13F",
            sandbox_safety_gate_status="CLOSED",
            sandbox_result_pack_status="BUILT",
            sandbox_result_accepted_for_review="true",
            simulated_result_only="true",
            sandbox_qualification_status="NOT_SIMULATED",
            simulated_qualification_result="SAFETY_GATE_SUMMARY_ONLY",
            simulated_symbol="",
            simulated_contract_id="",
            real_qualification_allowed="false",
            tws_connection_allowed="false",
            ibkr_api_request_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            order_action_allowed="false",
            cancel_action_allowed="false",
            rebalance_action_allowed="false",
            auto_trade_allowed="false",
            action_allowed="false",
            safety_decision="sandbox_safety_gate_closed_final_summary",
            warning_flags="SANDBOX_SAFETY_GATE;SAFETY_GATE_CLOSED;NO_ORDER;NO_AUTO_TRADE",
            notes="Sandbox safety gate only.",
            timestamp_jst="2026-05-19T20:00:00+09:00",
            timestamp_et="2026-05-19T07:00:00-04:00",
        )
    ]

    csv_path = tmp_path / "sandbox_safety_gate.csv"
    md_path = tmp_path / "sandbox_safety_gate_report.md"

    write_ibkr_readonly_qualification_sandbox_safety_gate_csv(csv_path, rows)
    write_ibkr_readonly_qualification_sandbox_safety_gate_report(md_path, rows, "result_pack.csv")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["gate_id"] == "FINAL"
    assert csv_rows[0]["sandbox_safety_gate_status"] == "CLOSED"
    assert csv_rows[0]["sandbox_result_accepted_for_review"] == "true"
    assert csv_rows[0]["real_qualification_allowed"] == "false"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 13F IBKR Read-Only Qualification Sandbox Safety Gate Report" in report
    assert "Sandbox safety gate status: CLOSED" in report
    assert "Sandbox results are accepted for review only" in report
    assert "Simulated qualification results are not real IBKR qualification" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report


def test_build_sandbox_safety_gate_has_timestamps():
    rows = build_ibkr_readonly_qualification_sandbox_safety_gate_rows()

    assert rows[0].timestamp_jst
    assert rows[0].timestamp_et
    assert "+09:00" in rows[0].timestamp_jst
