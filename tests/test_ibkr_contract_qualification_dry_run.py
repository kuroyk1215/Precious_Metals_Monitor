from pathlib import Path

from src.ibkr_contract_mapping_plan import (
    build_ibkr_contract_mapping_plan_rows,
    load_ibkr_contract_mapping_config,
)
from src.ibkr_contract_qualification_dry_run import (
    build_ibkr_contract_qualification_dry_run_rows,
    load_ibkr_contract_mapping_rows_by_target,
    write_ibkr_contract_qualification_dry_run_csv,
    write_ibkr_contract_qualification_dry_run_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def _mapping_rows():
    config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
    return build_ibkr_contract_mapping_plan_rows(config, TZ)


def test_qualification_dry_run_default_mapping_rows():
    rows = build_ibkr_contract_qualification_dry_run_rows(_mapping_rows(), TZ)

    assert len(rows) == 7

    by_target = {row.target_id: row for row in rows}

    assert by_target["USDJPY"].qualification_dry_run_status == "dry_run_ready_for_future_qualification"
    assert by_target["1540.T"].future_qualification_candidate == "true"
    assert by_target["XAUUSD"].qualification_dry_run_status == "blocked_mapping_review_required"
    assert by_target["518880.SH"].future_qualification_candidate == "false"

    for row in rows:
        assert row.qualification_allowed == "false"
        assert row.tws_connection_allowed == "false"
        assert row.contract_qualification_allowed == "false"
        assert row.market_data_request_allowed == "false"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_contract_qualification" in row.warning_flags


def test_qualification_dry_run_manual_review_status():
    rows = build_ibkr_contract_qualification_dry_run_rows(
        [
            {
                "target_id": "UNKNOWN",
                "asset_class": "unknown",
                "symbol": "UNKNOWN",
                "currency": "unknown",
                "exchange": "unknown",
                "primary_exchange": "unknown",
                "sec_type": "unknown",
                "mapping_status": "manual_review_required",
                "contract_status": "missing_mapping",
            }
        ],
        TZ,
    )

    row = rows[0]

    assert row.qualification_dry_run_status == "blocked_manual_review_required"
    assert row.future_qualification_candidate == "false"
    assert row.qualification_allowed == "false"


def test_qualification_dry_run_loader_and_writers(tmp_path: Path):
    csv_input = tmp_path / "ibkr_contract_mapping_plan.csv"
    csv_input.write_text(
        "target_id,asset_class,symbol,currency,exchange,primary_exchange,sec_type,mapping_status,contract_status,timestamp_jst,timestamp_et\n"
        "USDJPY,fx,USD,JPY,IDEALPRO,IDEALPRO,CASH,candidate_mapping_ready,candidate_mapping,2026-05-18T13:00:00+09:00,2026-05-18T00:00:00-04:00\n",
        encoding="utf-8",
    )

    loaded = load_ibkr_contract_mapping_rows_by_target(str(csv_input))
    rows = build_ibkr_contract_qualification_dry_run_rows(list(loaded.values()), TZ)

    csv_path = tmp_path / "ibkr_contract_qualification_dry_run.csv"
    md_path = tmp_path / "ibkr_contract_qualification_dry_run_report.md"

    write_ibkr_contract_qualification_dry_run_csv(csv_path, rows)
    write_ibkr_contract_qualification_dry_run_report(md_path, rows, str(csv_input))

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "qualification_dry_run_status" in csv_text
    assert "dry_run_ready_for_future_qualification" in csv_text
    assert "Phase 10I IBKR Contract Qualification Dry Run Report" in md_text
    assert "future_qualification_candidate_count: 1" in md_text
    assert "qualification_allowed_count: 0" in md_text
    assert "no real contract qualification" in md_text
    assert "no auto trade" in md_text
