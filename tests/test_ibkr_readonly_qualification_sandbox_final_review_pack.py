from __future__ import annotations

import csv

from src.ibkr_readonly_qualification_sandbox_final_review_pack import (
    SandboxFinalReviewPackRow,
    build_ibkr_readonly_qualification_sandbox_final_review_pack_rows,
    write_ibkr_readonly_qualification_sandbox_final_review_pack_csv,
    write_ibkr_readonly_qualification_sandbox_final_review_pack_report,
)


def test_build_sandbox_final_review_pack_default_rows():
    rows = build_ibkr_readonly_qualification_sandbox_final_review_pack_rows()

    assert len(rows) == 7
    assert {row.review_id for row in rows} == {"13A", "13B", "13C", "13D", "13E", "13F", "FINAL"}
    assert all(row.sandbox_final_review_status == "READY_FOR_REVIEW" for row in rows)
    assert all(row.sandbox_safety_gate_status == "CLOSED" for row in rows)
    assert all(row.sandbox_result_accepted_for_review == "true" for row in rows)
    assert all(row.simulated_result_only == "true" for row in rows)
    assert all(row.real_qualification_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.ibkr_api_request_allowed == "false" for row in rows)
    assert all(row.market_data_request_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_sandbox_final_review_pack_blocks_attempted_unlock_csv(tmp_path):
    path = tmp_path / "safety_gate.csv"
    path.write_text(
        "\n".join(
            [
                "gate_id,gate_name,sandbox_safety_gate_status,sandbox_result_accepted_for_review,simulated_result_only,action_allowed",
                "A,Attempted unlock,OPEN,true,false,true",
            ]
        ),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_qualification_sandbox_final_review_pack_rows(path)

    assert len(rows) == 1
    assert rows[0].sandbox_final_review_status == "READY_FOR_REVIEW"
    assert rows[0].sandbox_safety_gate_status == "CLOSED"
    assert rows[0].simulated_result_only == "true"
    assert rows[0].real_qualification_allowed == "false"
    assert rows[0].action_allowed == "false"
    assert rows[0].review_decision == "upstream_unlock_attempt_detected_final_review_kept_locked"


def test_sandbox_final_review_pack_warning_flags_are_safety_locked():
    rows = build_ibkr_readonly_qualification_sandbox_final_review_pack_rows()

    for row in rows:
        assert "phase13g_ibkr_readonly_qualification_sandbox_final_review_pack" in row.warning_flags
        assert "SANDBOX_FINAL_REVIEW_PACK" in row.warning_flags
        assert "READY_FOR_REVIEW" in row.warning_flags
        assert "SAFETY_GATE_CLOSED" in row.warning_flags
        assert "SIMULATED_RESULT_ONLY" in row.warning_flags
        assert "REAL_QUALIFICATION_BLOCKED" in row.warning_flags
        assert "TWS_CONNECTION_BLOCKED" in row.warning_flags
        assert "IBKR_API_REQUEST_BLOCKED" in row.warning_flags
        assert "NO_REQ_MKT_DATA" in row.warning_flags
        assert "NO_REQ_HISTORICAL_DATA" in row.warning_flags
        assert "NO_ORDER" in row.warning_flags
        assert "NO_AUTO_TRADE" in row.warning_flags


def test_write_sandbox_final_review_pack_csv_and_report(tmp_path):
    rows = [
        SandboxFinalReviewPackRow(
            review_id="FINAL",
            review_name="Final sandbox review pack",
            source_layer="Phase 13G",
            sandbox_final_review_status="READY_FOR_REVIEW",
            sandbox_safety_gate_status="CLOSED",
            sandbox_result_accepted_for_review="true",
            simulated_result_only="true",
            sandbox_qualification_status="NOT_SIMULATED",
            simulated_qualification_result="FINAL_REVIEW_PACK_READY",
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
            review_decision="sandbox_final_review_pack_ready_but_execution_blocked",
            warning_flags="SANDBOX_FINAL_REVIEW_PACK;READY_FOR_REVIEW;NO_ORDER;NO_AUTO_TRADE",
            notes="Sandbox final review pack only.",
            timestamp_jst="2026-05-19T21:00:00+09:00",
            timestamp_et="2026-05-19T08:00:00-04:00",
        )
    ]

    csv_path = tmp_path / "sandbox_final_review_pack.csv"
    md_path = tmp_path / "sandbox_final_review_pack_report.md"

    write_ibkr_readonly_qualification_sandbox_final_review_pack_csv(csv_path, rows)
    write_ibkr_readonly_qualification_sandbox_final_review_pack_report(md_path, rows, "safety_gate.csv")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["review_id"] == "FINAL"
    assert csv_rows[0]["sandbox_final_review_status"] == "READY_FOR_REVIEW"
    assert csv_rows[0]["sandbox_safety_gate_status"] == "CLOSED"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 13G IBKR Read-Only Qualification Sandbox Final Review Pack Report" in report
    assert "Sandbox final review status: READY_FOR_REVIEW" in report
    assert "Sandbox outputs are accepted for human review only" in report
    assert "Simulated qualification results are not real IBKR qualification" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report


def test_build_sandbox_final_review_pack_has_timestamps():
    rows = build_ibkr_readonly_qualification_sandbox_final_review_pack_rows()

    assert rows[0].timestamp_jst
    assert rows[0].timestamp_et
    assert "+09:00" in rows[0].timestamp_jst
