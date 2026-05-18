from __future__ import annotations

import csv

from src.ibkr_readonly_qualification_operator_decision_ledger import (
    OperatorDecisionLedgerRow,
    build_ibkr_readonly_qualification_operator_decision_ledger_rows,
    write_ibkr_readonly_qualification_operator_decision_ledger_csv,
    write_ibkr_readonly_qualification_operator_decision_ledger_report,
)


def _sample_safety_summary_csv(tmp_path):
    path = tmp_path / "candidate_safety_summary.csv"
    path.write_text(
        "\n".join(
            [
                "section_id,section_name,source_layer,candidate_count,review_required_count,excluded_count,candidate_final_gate_status,candidate_safety_status",
                "12A,Candidate resolver safety summary,Phase 12A,4,0,3,CLOSED,BLOCKED",
                "FINAL,Final candidate safety summary,Phase 12A-12C,4,7,3,CLOSED,BLOCKED",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_build_operator_decision_ledger_from_candidate_safety_summary_csv(tmp_path):
    input_path = _sample_safety_summary_csv(tmp_path)

    rows = build_ibkr_readonly_qualification_operator_decision_ledger_rows(input_path)

    assert len(rows) == 2
    assert all(row.operator_decision_status == "PENDING" for row in rows)
    assert all(row.operator_decision_required == "true" for row in rows)
    assert all(row.candidate_final_gate_status == "CLOSED" for row in rows)
    assert all(row.candidate_safety_status == "BLOCKED" for row in rows)
    assert all(row.qualification_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.contract_qualification_allowed == "false" for row in rows)
    assert all(row.market_data_request_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.api_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_operator_decision_ledger_warning_flags_are_safety_locked(tmp_path):
    input_path = _sample_safety_summary_csv(tmp_path)

    rows = build_ibkr_readonly_qualification_operator_decision_ledger_rows(input_path)

    for row in rows:
        assert "phase12e_ibkr_readonly_qualification_operator_decision_ledger" in row.warning_flags
        assert "operator_decision_ledger_only" in row.warning_flags
        assert "no_tws_connection" in row.warning_flags
        assert "no_ibkr_connection" in row.warning_flags
        assert "no_reqMktData" in row.warning_flags
        assert "no_reqHistoricalData" in row.warning_flags
        assert "no_order" in row.warning_flags
        assert "no_auto_trade" in row.warning_flags


def test_write_operator_decision_ledger_csv_and_report(tmp_path):
    rows = [
        OperatorDecisionLedgerRow(
            section_id="FINAL",
            section_name="Final operator decision ledger",
            source_layer="Phase 12A-12D",
            candidate_count=4,
            review_required_count=7,
            excluded_count=3,
            candidate_final_gate_status="CLOSED",
            candidate_safety_status="BLOCKED",
            operator_decision_status="PENDING",
            operator_decision_required="true",
            qualification_allowed="false",
            tws_connection_allowed="false",
            contract_qualification_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            api_request_allowed="false",
            action_allowed="false",
            decision_reason="final_operator_decision_pending_until_explicit_future_phase_design",
            warning_flags="BLOCKED;CLOSED;operator_decision_ledger_only;no_tws_connection;no_ibkr_connection;no_order;no_auto_trade",
            notes="Operator decision ledger only.",
            timestamp_jst="2026-05-18T17:00:00+09:00",
            timestamp_et="2026-05-18T04:00:00-04:00",
        )
    ]

    csv_path = tmp_path / "operator_decision_ledger.csv"
    md_path = tmp_path / "operator_decision_ledger_report.md"

    write_ibkr_readonly_qualification_operator_decision_ledger_csv(csv_path, rows)
    write_ibkr_readonly_qualification_operator_decision_ledger_report(md_path, rows, "candidate_safety_summary.csv")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["section_id"] == "FINAL"
    assert csv_rows[0]["operator_decision_status"] == "PENDING"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 12E IBKR Read-Only Qualification Operator Decision Ledger Report" in report
    assert "Operator decision status: PENDING" in report
    assert "Candidate safety status remains BLOCKED" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report


def test_build_operator_decision_ledger_has_timestamps(tmp_path):
    input_path = _sample_safety_summary_csv(tmp_path)

    rows = build_ibkr_readonly_qualification_operator_decision_ledger_rows(input_path)

    assert rows[0].timestamp_jst
    assert rows[0].timestamp_et
    assert "+09:00" in rows[0].timestamp_jst

def test_build_operator_decision_ledger_from_default_config_path_is_locked():
    rows = build_ibkr_readonly_qualification_operator_decision_ledger_rows(
        "data/market_data_provider_config.yaml"
    )

    assert len(rows) == 4
    assert {row.section_id for row in rows} == {"12A", "12B", "12C", "FINAL"}
    assert all(row.operator_decision_status == "PENDING" for row in rows)
    assert all(row.candidate_final_gate_status == "CLOSED" for row in rows)
    assert all(row.candidate_safety_status == "BLOCKED" for row in rows)
    assert all(row.qualification_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.api_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)
