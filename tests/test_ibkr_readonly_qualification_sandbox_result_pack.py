from __future__ import annotations

import csv

from src.ibkr_readonly_qualification_sandbox_result_pack import (
    SandboxResultPackRow,
    build_ibkr_readonly_qualification_sandbox_result_pack_rows,
    write_ibkr_readonly_qualification_sandbox_result_pack_csv,
    write_ibkr_readonly_qualification_sandbox_result_pack_report,
)


def test_build_sandbox_result_pack_default_rows():
    rows = build_ibkr_readonly_qualification_sandbox_result_pack_rows()

    assert len(rows) == 5
    assert all(row.sandbox_result_pack_status == "BUILT" for row in rows)
    assert all(row.simulated_result_only == "true" for row in rows)
    assert sum(1 for row in rows if row.sandbox_qualification_status == "SIMULATED") == 3
    assert sum(1 for row in rows if row.sandbox_qualification_status == "NOT_SIMULATED") == 2
    assert all(row.real_qualification_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.ibkr_api_request_allowed == "false" for row in rows)
    assert all(row.market_data_request_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_sandbox_result_pack_from_simulator_csv(tmp_path):
    path = tmp_path / "simulator.csv"
    path.write_text(
        "\n".join(
            [
                "simulation_id,input_label,sandbox_qualification_status,simulated_symbol,simulated_exchange,simulated_currency,simulated_sec_type,simulated_qualification_result,simulated_contract_id",
                "A,Manual 1540,SIMULATED,1540,TSE,JPY,ETF,QUALIFIED_SIMULATED,SIM-1540",
                "B,Rejected input,NOT_SIMULATED,,,,,NOT_SIMULATED_INPUT_REJECTED,",
            ]
        ),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_qualification_sandbox_result_pack_rows(path)

    assert [row.sandbox_result_pack_status for row in rows] == ["BUILT", "BUILT"]
    assert [row.sandbox_qualification_status for row in rows] == ["SIMULATED", "NOT_SIMULATED"]
    assert rows[0].simulated_result_only == "true"
    assert rows[0].real_qualification_allowed == "false"
    assert all(row.action_allowed == "false" for row in rows)


def test_sandbox_result_pack_warning_flags_are_safety_locked():
    rows = build_ibkr_readonly_qualification_sandbox_result_pack_rows()

    for row in rows:
        assert "phase13e_ibkr_readonly_qualification_sandbox_result_pack" in row.warning_flags
        assert "SANDBOX_RESULT_PACK" in row.warning_flags
        assert "SIMULATED_RESULT_ONLY" in row.warning_flags
        assert "REAL_QUALIFICATION_BLOCKED" in row.warning_flags
        assert "TWS_CONNECTION_BLOCKED" in row.warning_flags
        assert "IBKR_API_REQUEST_BLOCKED" in row.warning_flags
        assert "NO_REQ_MKT_DATA" in row.warning_flags
        assert "NO_REQ_HISTORICAL_DATA" in row.warning_flags
        assert "NO_ORDER" in row.warning_flags
        assert "NO_AUTO_TRADE" in row.warning_flags


def test_write_sandbox_result_pack_csv_and_report(tmp_path):
    rows = [
        SandboxResultPackRow(
            pack_id="SIM_1540_T",
            pack_name="Simulated 1540.T qualification candidate",
            source_layer="Phase 13E",
            sandbox_result_pack_status="BUILT",
            simulated_result_only="true",
            sandbox_qualification_status="SIMULATED",
            simulated_qualification_result="QUALIFIED_SIMULATED",
            simulated_symbol="1540",
            simulated_exchange="TSE",
            simulated_currency="JPY",
            simulated_sec_type="ETF",
            simulated_contract_id="SIM-1540",
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
            result_pack_decision="simulated_qualification_result_included_real_qualification_blocked",
            warning_flags="SANDBOX_RESULT_PACK;SIMULATED_RESULT_ONLY;NO_ORDER;NO_AUTO_TRADE",
            notes="Sandbox result pack only.",
            timestamp_jst="2026-05-19T19:00:00+09:00",
            timestamp_et="2026-05-19T06:00:00-04:00",
        )
    ]

    csv_path = tmp_path / "sandbox_result_pack.csv"
    md_path = tmp_path / "sandbox_result_pack_report.md"

    write_ibkr_readonly_qualification_sandbox_result_pack_csv(csv_path, rows)
    write_ibkr_readonly_qualification_sandbox_result_pack_report(md_path, rows, "simulator.csv")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["pack_id"] == "SIM_1540_T"
    assert csv_rows[0]["sandbox_result_pack_status"] == "BUILT"
    assert csv_rows[0]["simulated_result_only"] == "true"
    assert csv_rows[0]["real_qualification_allowed"] == "false"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 13E IBKR Read-Only Qualification Sandbox Result Pack Report" in report
    assert "Sandbox result pack status: BUILT" in report
    assert "Results are simulated only" in report
    assert "Simulated qualification results are not real IBKR qualification" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report


def test_build_sandbox_result_pack_has_timestamps():
    rows = build_ibkr_readonly_qualification_sandbox_result_pack_rows()

    assert rows[0].timestamp_jst
    assert rows[0].timestamp_et
    assert "+09:00" in rows[0].timestamp_jst
