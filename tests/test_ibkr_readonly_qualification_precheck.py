from pathlib import Path

from src.ibkr_readonly_qualification_precheck import (
    build_ibkr_readonly_qualification_precheck_rows,
    load_ibkr_readonly_qualification_precheck_config,
    write_ibkr_readonly_qualification_precheck_csv,
    write_ibkr_readonly_qualification_precheck_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_precheck_default_config_blocks_tws_runtime_and_execution():
    config = load_ibkr_readonly_qualification_precheck_config("config.yaml")
    rows = build_ibkr_readonly_qualification_precheck_rows(config, TZ)

    assert len(rows) >= 10

    by_check = {row.check_id: row for row in rows}

    assert by_check["tws_runtime_state"].precheck_status == "precheck_blocked"
    assert by_check["explicit_execution_flag"].observed_value == "false"
    assert by_check["qualification_allowed"].observed_value == "false"
    assert by_check["market_data_allowed"].observed_value == "false"
    assert by_check["order_cancel_allowed"].observed_value == "false"

    for row in rows:
        assert row.qualification_allowed == "false"
        assert row.tws_connection_allowed == "false"
        assert row.contract_qualification_allowed == "false"
        assert row.market_data_request_allowed == "false"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_ibkr_connection" in row.warning_flags


def test_precheck_configured_ibkr_fields_can_pass_config_checks():
    config = {
        "runtime": {
            "ibkr": {
                "host": "127.0.0.1",
                "port": 7496,
                "client_id": 1,
                "account_mode": "live",
                "read_only_required": True,
            }
        }
    }

    rows = build_ibkr_readonly_qualification_precheck_rows(config, TZ)
    by_check = {row.check_id: row for row in rows}

    assert by_check["read_only_required"].precheck_status == "precheck_pass"
    assert by_check["account_mode"].precheck_status == "precheck_pass"
    assert by_check["ibkr_port"].precheck_status == "precheck_pass"
    assert by_check["client_id"].precheck_status == "precheck_pass"
    assert by_check["host"].precheck_status == "precheck_pass"

    assert by_check["tws_runtime_state"].precheck_status == "precheck_blocked"
    assert by_check["qualification_allowed"].qualification_allowed == "false"


def test_precheck_writers(tmp_path: Path):
    config = {
        "runtime": {
            "ibkr": {
                "host": "127.0.0.1",
                "port": 7497,
                "client_id": 2,
                "account_mode": "paper",
                "read_only_required": True,
            }
        }
    }
    rows = build_ibkr_readonly_qualification_precheck_rows(config, TZ)

    csv_path = tmp_path / "ibkr_readonly_qualification_precheck.csv"
    md_path = tmp_path / "ibkr_readonly_qualification_precheck_report.md"

    write_ibkr_readonly_qualification_precheck_csv(csv_path, rows)
    write_ibkr_readonly_qualification_precheck_report(md_path, rows, "config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "precheck_status" in csv_text
    assert "Phase 10K IBKR Read-Only Qualification Precheck Report" in md_text
    assert "qualification_allowed_count: 0" in md_text
    assert "tws_connection_allowed_count: 0" in md_text
    assert "no TWS connection" in md_text
    assert "no auto trade" in md_text
