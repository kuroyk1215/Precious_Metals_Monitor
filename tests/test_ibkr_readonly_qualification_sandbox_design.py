from __future__ import annotations

import csv

from src.ibkr_readonly_qualification_sandbox_design import (
    SandboxDesignRow,
    build_ibkr_readonly_qualification_sandbox_design_rows,
    write_ibkr_readonly_qualification_sandbox_design_csv,
    write_ibkr_readonly_qualification_sandbox_design_report,
)


def test_build_sandbox_design_rows_are_locked():
    rows = build_ibkr_readonly_qualification_sandbox_design_rows()

    assert len(rows) == 6
    assert {row.component_id for row in rows} == {"ENV", "NETWORK", "CONTRACTS", "DATA", "ACTIONS", "FINAL"}
    assert all(row.sandbox_design_status == "DESIGN_ONLY" for row in rows)
    assert all(row.sandbox_execution_allowed == "false" for row in rows)
    assert all(row.real_ibkr_connection_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.ibkr_api_request_allowed == "false" for row in rows)
    assert all(row.contract_qualification_allowed == "false" for row in rows)
    assert all(row.market_data_request_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_sandbox_design_warning_flags_are_safety_locked():
    rows = build_ibkr_readonly_qualification_sandbox_design_rows()

    for row in rows:
        assert "phase13a_ibkr_readonly_qualification_sandbox_design" in row.warning_flags
        assert "DESIGN_ONLY" in row.warning_flags
        assert "REAL_IBKR_CONNECTION_BLOCKED" in row.warning_flags
        assert "TWS_CONNECTION_BLOCKED" in row.warning_flags
        assert "IBKR_API_REQUEST_BLOCKED" in row.warning_flags
        assert "NO_REQ_MKT_DATA" in row.warning_flags
        assert "NO_REQ_HISTORICAL_DATA" in row.warning_flags
        assert "NO_ORDER" in row.warning_flags
        assert "NO_AUTO_TRADE" in row.warning_flags


def test_write_sandbox_design_csv_and_report(tmp_path):
    rows = [
        SandboxDesignRow(
            component_id="FINAL",
            component_name="Final sandbox design packet",
            source_layer="Phase 13A",
            sandbox_design_status="DESIGN_ONLY",
            sandbox_execution_allowed="false",
            real_ibkr_connection_allowed="false",
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
            design_decision="phase13a_sandbox_design_complete_but_execution_blocked",
            warning_flags="DESIGN_ONLY;REAL_IBKR_CONNECTION_BLOCKED;NO_ORDER;NO_AUTO_TRADE",
            notes="Sandbox design packet only.",
            timestamp_jst="2026-05-19T15:00:00+09:00",
            timestamp_et="2026-05-19T02:00:00-04:00",
        )
    ]

    csv_path = tmp_path / "sandbox_design.csv"
    md_path = tmp_path / "sandbox_design_report.md"

    write_ibkr_readonly_qualification_sandbox_design_csv(csv_path, rows)
    write_ibkr_readonly_qualification_sandbox_design_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["component_id"] == "FINAL"
    assert csv_rows[0]["sandbox_design_status"] == "DESIGN_ONLY"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 13A IBKR Read-Only Qualification Sandbox Design Report" in report
    assert "Sandbox design status: DESIGN_ONLY" in report
    assert "Real IBKR connection allowed: false" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report


def test_build_sandbox_design_has_timestamps():
    rows = build_ibkr_readonly_qualification_sandbox_design_rows()

    assert rows[0].timestamp_jst
    assert rows[0].timestamp_et
    assert "+09:00" in rows[0].timestamp_jst


def test_sandbox_design_blocks_all_action_subtypes():
    rows = build_ibkr_readonly_qualification_sandbox_design_rows()

    for row in rows:
        assert row.order_action_allowed == "false"
        assert row.cancel_action_allowed == "false"
        assert row.rebalance_action_allowed == "false"
        assert row.auto_trade_allowed == "false"
