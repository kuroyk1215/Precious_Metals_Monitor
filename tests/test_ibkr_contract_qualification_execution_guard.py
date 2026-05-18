from pathlib import Path

from src.ibkr_contract_mapping_plan import (
    build_ibkr_contract_mapping_plan_rows,
    load_ibkr_contract_mapping_config,
)
from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
from src.ibkr_contract_qualification_execution_guard import (
    build_ibkr_contract_qualification_execution_guard_rows,
    load_ibkr_contract_qualification_dry_run_rows_by_target,
    write_ibkr_contract_qualification_execution_guard_csv,
    write_ibkr_contract_qualification_execution_guard_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def _dry_run_rows():
    config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
    mapping_rows = build_ibkr_contract_mapping_plan_rows(config, TZ)
    return build_ibkr_contract_qualification_dry_run_rows(mapping_rows, TZ)


def test_execution_guard_blocks_default_without_explicit_flag():
    rows = build_ibkr_contract_qualification_execution_guard_rows(_dry_run_rows(), TZ)

    assert len(rows) == 7

    by_target = {row.target_id: row for row in rows}

    assert by_target["USDJPY"].execution_guard_status == "blocked_missing_explicit_execution_flag"
    assert by_target["1540.T"].future_qualification_candidate == "true"
    assert by_target["XAUUSD"].execution_guard_status == "blocked_not_future_qualification_candidate"
    assert by_target["518880.SH"].future_qualification_candidate == "false"

    for row in rows:
        assert row.explicit_execution_flag == "false"
        assert row.qualification_allowed == "false"
        assert row.tws_connection_allowed == "false"
        assert row.contract_qualification_allowed == "false"
        assert row.market_data_request_allowed == "false"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_contract_qualification" in row.warning_flags


def test_execution_guard_still_blocks_with_explicit_flag_in_phase10j():
    rows = build_ibkr_contract_qualification_execution_guard_rows(
        _dry_run_rows(),
        TZ,
        explicit_execution_flag=True,
    )

    by_target = {row.target_id: row for row in rows}

    assert by_target["USDJPY"].explicit_execution_flag == "true"
    assert by_target["USDJPY"].execution_guard_status == "blocked_phase10j_guard_only"
    assert by_target["USDJPY"].qualification_allowed == "false"
    assert by_target["XAUUSD"].execution_guard_status == "blocked_not_future_qualification_candidate"


def test_execution_guard_loader_and_writers(tmp_path: Path):
    csv_input = tmp_path / "ibkr_contract_qualification_dry_run.csv"
    csv_input.write_text(
        "target_id,symbol,currency,exchange,sec_type,qualification_dry_run_status,future_qualification_candidate,timestamp_jst,timestamp_et\n"
        "USDJPY,USD,JPY,IDEALPRO,CASH,dry_run_ready_for_future_qualification,true,2026-05-18T13:00:00+09:00,2026-05-18T00:00:00-04:00\n",
        encoding="utf-8",
    )

    loaded = load_ibkr_contract_qualification_dry_run_rows_by_target(str(csv_input))
    rows = build_ibkr_contract_qualification_execution_guard_rows(list(loaded.values()), TZ)

    csv_path = tmp_path / "ibkr_contract_qualification_execution_guard.csv"
    md_path = tmp_path / "ibkr_contract_qualification_execution_guard_report.md"

    write_ibkr_contract_qualification_execution_guard_csv(csv_path, rows)
    write_ibkr_contract_qualification_execution_guard_report(md_path, rows, str(csv_input))

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "execution_guard_status" in csv_text
    assert "blocked_missing_explicit_execution_flag" in csv_text
    assert "Phase 10J IBKR Contract Qualification Execution Guard Report" in md_text
    assert "qualification_allowed_count: 0" in md_text
    assert "no real contract qualification" in md_text
    assert "no auto trade" in md_text
