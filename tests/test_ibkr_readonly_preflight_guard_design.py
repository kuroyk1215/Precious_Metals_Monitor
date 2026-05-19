from __future__ import annotations

import csv

from src.ibkr_readonly_preflight_guard_design import (
    PreflightGuardDesignRow,
    build_ibkr_readonly_preflight_guard_design_rows,
    write_ibkr_readonly_preflight_guard_design_csv,
    write_ibkr_readonly_preflight_guard_design_report,
)


def test_build_preflight_guard_design_default_rows_are_locked():
    rows = build_ibkr_readonly_preflight_guard_design_rows()

    assert len(rows) == 11
    assert {row.guard_id for row in rows} == {
        "CONFIG",
        "ENV",
        "TWS",
        "ACCOUNT",
        "READ_ONLY",
        "API_SCOPE",
        "CONTRACTS",
        "MARKET_DATA",
        "HISTORICAL_DATA",
        "ACTIONS",
        "FINAL",
    }
    assert all(row.preflight_guard_status == "DESIGN_ONLY" for row in rows)
    assert all(row.design_only == "true" for row in rows)
    assert all(row.required_before_real_connection == "true" for row in rows)
    assert all(row.real_connection_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.ibkr_api_request_allowed == "false" for row in rows)
    assert all(row.contract_qualification_allowed == "false" for row in rows)
    assert all(row.market_data_request_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_preflight_guard_design_warning_flags_are_safety_locked():
    rows = build_ibkr_readonly_preflight_guard_design_rows()

    for row in rows:
        assert "phase14a_ibkr_readonly_preflight_guard_design" in row.warning_flags
        assert "PREFLIGHT_GUARD_DESIGN_ONLY" in row.warning_flags
        assert "REAL_CONNECTION_BLOCKED" in row.warning_flags
        assert "TWS_CONNECTION_BLOCKED" in row.warning_flags
        assert "IBKR_API_REQUEST_BLOCKED" in row.warning_flags
        assert "CONTRACT_QUALIFICATION_BLOCKED" in row.warning_flags
        assert "MARKET_DATA_REQUEST_BLOCKED" in row.warning_flags
        assert "HISTORICAL_DATA_REQUEST_BLOCKED" in row.warning_flags
        assert "ORDER_BLOCKED" in row.warning_flags
        assert "AUTO_TRADE_BLOCKED" in row.warning_flags


def test_write_preflight_guard_design_csv_and_report(tmp_path):
    rows = [
        PreflightGuardDesignRow(
            guard_id="FINAL",
            guard_name="Final preflight guard design",
            source_layer="Phase 14A",
            preflight_guard_status="DESIGN_ONLY",
            design_only="true",
            required_before_real_connection="true",
            real_connection_allowed="false",
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
            guard_decision="phase14a_preflight_guard_design_complete_but_execution_blocked",
            warning_flags="PREFLIGHT_GUARD_DESIGN_ONLY;REAL_CONNECTION_BLOCKED;NO_ORDER;NO_AUTO_TRADE",
            notes="Preflight guard design only.",
            timestamp_jst="2026-05-19T23:00:00+09:00",
            timestamp_et="2026-05-19T10:00:00-04:00",
        )
    ]

    csv_path = tmp_path / "preflight_guard_design.csv"
    md_path = tmp_path / "preflight_guard_design_report.md"

    write_ibkr_readonly_preflight_guard_design_csv(csv_path, rows)
    write_ibkr_readonly_preflight_guard_design_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["guard_id"] == "FINAL"
    assert csv_rows[0]["preflight_guard_status"] == "DESIGN_ONLY"
    assert csv_rows[0]["real_connection_allowed"] == "false"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 14A IBKR Read-Only Preflight Guard Design Report" in report
    assert "Preflight guard status: DESIGN_ONLY" in report
    assert "Preflight guard is required before any future real read-only connection" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report


def test_build_preflight_guard_design_has_timestamps():
    rows = build_ibkr_readonly_preflight_guard_design_rows()

    assert rows[0].timestamp_jst
    assert rows[0].timestamp_et
    assert "+09:00" in rows[0].timestamp_jst


def test_preflight_guard_design_blocks_all_action_subtypes():
    rows = build_ibkr_readonly_preflight_guard_design_rows()

    for row in rows:
        assert row.order_action_allowed == "false"
        assert row.cancel_action_allowed == "false"
        assert row.rebalance_action_allowed == "false"
        assert row.auto_trade_allowed == "false"
