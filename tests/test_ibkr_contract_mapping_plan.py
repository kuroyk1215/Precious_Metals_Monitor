from pathlib import Path

from src.ibkr_contract_mapping_plan import (
    build_ibkr_contract_mapping_plan_rows,
    load_ibkr_contract_mapping_config,
    write_ibkr_contract_mapping_plan_csv,
    write_ibkr_contract_mapping_plan_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_ibkr_contract_mapping_default_targets():
    config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
    rows = build_ibkr_contract_mapping_plan_rows(config, TZ)

    assert len(rows) == 7

    by_target = {row.target_id: row for row in rows}

    assert by_target["USDJPY"].sec_type == "CASH"
    assert by_target["USDJPY"].exchange == "IDEALPRO"
    assert by_target["1540.T"].sec_type == "STK"
    assert by_target["1540.T"].exchange == "TSEJ"
    assert by_target["1542.T"].currency == "JPY"
    assert by_target["518880.SH"].mapping_status == "candidate_review_required"
    assert by_target["XAUUSD"].mapping_status == "candidate_review_required"

    for row in rows:
        assert row.tws_connection_allowed == "false"
        assert row.market_data_request_allowed == "false"
        assert row.historical_data_request_allowed == "false"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_ibkr_connection" in row.warning_flags


def test_ibkr_contract_mapping_unknown_target_requires_review():
    config = {
        "targets": [
            {
                "target_id": "UNKNOWN",
                "target_type": "unknown",
                "market": "UNKNOWN",
                "data_role": "unknown",
            }
        ]
    }

    rows = build_ibkr_contract_mapping_plan_rows(config, TZ)
    row = rows[0]

    assert row.target_id == "UNKNOWN"
    assert row.contract_status == "missing_mapping"
    assert row.mapping_status == "manual_review_required"
    assert row.action_allowed == "false"


def test_ibkr_contract_mapping_writers(tmp_path: Path):
    config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
    rows = build_ibkr_contract_mapping_plan_rows(config, TZ)

    csv_path = tmp_path / "ibkr_contract_mapping_plan.csv"
    md_path = tmp_path / "ibkr_contract_mapping_plan_report.md"

    write_ibkr_contract_mapping_plan_csv(csv_path, rows)
    write_ibkr_contract_mapping_plan_report(md_path, rows, "data/market_data_provider_config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "mapping_status" in csv_text
    assert "Phase 10H IBKR Contract Mapping Plan Report" in md_text
    assert "candidate_mapping_ready_count: 4" in md_text
    assert "review_required_count: 3" in md_text
    assert "no TWS connection" in md_text
    assert "no auto trade" in md_text
