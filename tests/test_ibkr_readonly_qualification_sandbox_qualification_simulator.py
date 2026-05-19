from __future__ import annotations

import csv

from src.ibkr_readonly_qualification_sandbox_qualification_simulator import (
    SandboxQualificationSimulatorRow,
    build_ibkr_readonly_qualification_sandbox_qualification_simulator_rows,
    write_ibkr_readonly_qualification_sandbox_qualification_simulator_csv,
    write_ibkr_readonly_qualification_sandbox_qualification_simulator_report,
)


def test_build_sandbox_qualification_simulator_default_rows():
    rows = build_ibkr_readonly_qualification_sandbox_qualification_simulator_rows()

    assert len(rows) == 5
    assert sum(1 for row in rows if row.sandbox_qualification_status == "SIMULATED") == 3
    assert sum(1 for row in rows if row.sandbox_qualification_status == "NOT_SIMULATED") == 2
    assert all(row.real_qualification_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)
    assert all(row.ibkr_api_request_allowed == "false" for row in rows)
    assert all(row.market_data_request_allowed == "false" for row in rows)
    assert all(row.historical_data_request_allowed == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_sandbox_qualification_simulator_from_validator_csv(tmp_path):
    path = tmp_path / "validator.csv"
    path.write_text(
        "\n".join(
            [
                "validation_id,input_source_type,input_label,sandbox_input_validation_status,symbol,exchange,currency,sec_type",
                "A,manual_csv,Manual 1540,VALIDATED,1540,TSE,JPY,ETF",
                "B,mock_snapshot,Mock 1542,VALIDATED,1542,TSE,JPY,ETF",
                "C,real_tws,Real TWS,REJECTED,,,,",
                "D,order,Order Input,REJECTED,,,,",
            ]
        ),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_qualification_sandbox_qualification_simulator_rows(path)

    assert [row.sandbox_qualification_status for row in rows] == ["SIMULATED", "SIMULATED", "NOT_SIMULATED", "NOT_SIMULATED"]
    assert rows[0].simulated_qualification_result == "QUALIFIED_SIMULATED"
    assert rows[1].simulated_contract_id == "SIM-1542"
    assert rows[2].real_qualification_allowed == "false"
    assert all(row.action_allowed == "false" for row in rows)


def test_sandbox_qualification_simulator_warning_flags_are_safety_locked():
    rows = build_ibkr_readonly_qualification_sandbox_qualification_simulator_rows()

    for row in rows:
        assert "phase13d_ibkr_readonly_qualification_sandbox_qualification_simulator" in row.warning_flags
        assert "SIMULATION_ONLY" in row.warning_flags
        assert "REAL_QUALIFICATION_BLOCKED" in row.warning_flags
        assert "TWS_CONNECTION_BLOCKED" in row.warning_flags
        assert "IBKR_API_REQUEST_BLOCKED" in row.warning_flags
        assert "NO_REQ_MKT_DATA" in row.warning_flags
        assert "NO_REQ_HISTORICAL_DATA" in row.warning_flags
        assert "NO_ORDER" in row.warning_flags
        assert "NO_AUTO_TRADE" in row.warning_flags


def test_write_sandbox_qualification_simulator_csv_and_report(tmp_path):
    rows = [
        SandboxQualificationSimulatorRow(
            simulation_id="SIM_1540_T",
            input_source_type="manual_csv",
            input_label="Simulated 1540.T qualification candidate",
            source_layer="Phase 13D",
            sandbox_input_validation_status="VALIDATED",
            sandbox_qualification_status="SIMULATED",
            simulated_symbol="1540",
            simulated_exchange="TSE",
            simulated_currency="JPY",
            simulated_sec_type="ETF",
            simulated_qualification_result="QUALIFIED_SIMULATED",
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
            simulation_decision="sandbox_qualification_simulated_real_qualification_blocked",
            warning_flags="SIMULATION_ONLY;REAL_QUALIFICATION_BLOCKED;NO_ORDER;NO_AUTO_TRADE",
            notes="Sandbox qualification simulator only.",
            timestamp_jst="2026-05-19T18:00:00+09:00",
            timestamp_et="2026-05-19T05:00:00-04:00",
        )
    ]

    csv_path = tmp_path / "sandbox_qualification_simulator.csv"
    md_path = tmp_path / "sandbox_qualification_simulator_report.md"

    write_ibkr_readonly_qualification_sandbox_qualification_simulator_csv(csv_path, rows)
    write_ibkr_readonly_qualification_sandbox_qualification_simulator_report(md_path, rows, "validator.csv")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["simulation_id"] == "SIM_1540_T"
    assert csv_rows[0]["sandbox_qualification_status"] == "SIMULATED"
    assert csv_rows[0]["real_qualification_allowed"] == "false"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 13D IBKR Read-Only Qualification Sandbox Qualification Simulator Report" in report
    assert "Sandbox qualification simulator is simulation-only" in report
    assert "Real qualification remains blocked" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report


def test_build_sandbox_qualification_simulator_has_timestamps():
    rows = build_ibkr_readonly_qualification_sandbox_qualification_simulator_rows()

    assert rows[0].timestamp_jst
    assert rows[0].timestamp_et
    assert "+09:00" in rows[0].timestamp_jst
