from pathlib import Path

from src.ibkr_contract_mapping_plan import (
    build_ibkr_contract_mapping_plan_rows,
    load_ibkr_contract_mapping_config,
)
from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
from src.ibkr_readonly_qualification_safety_summary import IBKRReadOnlyQualificationSafetySummaryRow
from src.ibkr_readonly_qualification_candidate_resolver import (
    build_ibkr_readonly_qualification_candidate_resolver_rows,
    load_ibkr_readonly_qualification_candidate_resolver_rows_by_target,
    write_ibkr_readonly_qualification_candidate_resolver_csv,
    write_ibkr_readonly_qualification_candidate_resolver_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def _safety_rows():
    return [
        IBKRReadOnlyQualificationSafetySummaryRow(
            section_id="FINAL",
            section_name="Final",
            source_layer="Phase 10G-10M + Phase 11A-11D",
            input_row_count="0",
            blocked_or_closed_count="0",
            pass_or_ready_count="0",
            summary_status="BLOCKED",
            overall_status="BLOCKED",
            apply_allowed="false",
            qualification_allowed="false",
            tws_connection_allowed="false",
            contract_qualification_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            api_request_allowed="false",
            action_allowed="false",
            blocking_summary="overall_blocked",
            warning_flags="overall_blocked",
            notes="test",
            timestamp_jst="2026-05-18T16:00:00+09:00",
            timestamp_et="2026-05-18T03:00:00-04:00",
        )
    ]


def _resolver_rows():
    config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
    mapping_rows = build_ibkr_contract_mapping_plan_rows(config, TZ)
    dry_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, TZ)
    guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_rows, TZ)

    return build_ibkr_readonly_qualification_candidate_resolver_rows(
        mapping_rows,
        dry_rows,
        guard_rows,
        _safety_rows(),
        TZ,
    )


def test_candidate_resolver_identifies_future_candidates_but_keeps_blocked():
    rows = _resolver_rows()

    assert len(rows) == 7

    by_target = {row.target_id: row for row in rows}

    assert by_target["USDJPY"].qualification_candidate == "true"
    assert by_target["USDJPY"].candidate_resolver_status == "candidate_resolved_blocked_by_safety_summary"
    assert by_target["1540.T"].qualification_candidate == "true"

    assert by_target["XAUUSD"].qualification_candidate == "false"
    assert by_target["XAUUSD"].candidate_resolver_status == "excluded_mapping_review_required"
    assert by_target["518880.SH"].candidate_resolver_status == "excluded_mapping_review_required"

    for row in rows:
        assert row.safety_overall_status == "BLOCKED"
        assert row.qualification_allowed == "false"
        assert row.tws_connection_allowed == "false"
        assert row.contract_qualification_allowed == "false"
        assert row.market_data_request_allowed == "false"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_ibkr_connection" in row.warning_flags


def test_candidate_resolver_blocks_unexpected_safety_status():
    config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
    mapping_rows = build_ibkr_contract_mapping_plan_rows(config, TZ)
    dry_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, TZ)
    guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_rows, TZ)
    safety_rows = _safety_rows()
    safety_rows[0].overall_status = "UNKNOWN"

    rows = build_ibkr_readonly_qualification_candidate_resolver_rows(
        mapping_rows,
        dry_rows,
        guard_rows,
        safety_rows,
        TZ,
    )

    by_target = {row.target_id: row for row in rows}
    assert by_target["USDJPY"].candidate_resolver_status == "blocked_unexpected_safety_status"
    assert by_target["USDJPY"].qualification_allowed == "false"


def test_candidate_resolver_loader_and_writers(tmp_path: Path):
    rows = _resolver_rows()

    csv_path = tmp_path / "ibkr_readonly_qualification_candidate_resolver.csv"
    md_path = tmp_path / "ibkr_readonly_qualification_candidate_resolver_report.md"

    write_ibkr_readonly_qualification_candidate_resolver_csv(csv_path, rows)
    write_ibkr_readonly_qualification_candidate_resolver_report(md_path, rows, "config.yaml")

    loaded = load_ibkr_readonly_qualification_candidate_resolver_rows_by_target(str(csv_path))
    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "candidate_resolver_status" in csv_text
    assert "candidate_resolved_blocked_by_safety_summary" in csv_text
    assert "USDJPY" in loaded
    assert "Phase 12A IBKR Read-Only Qualification Candidate Resolver Report" in md_text
    assert "qualification_candidate_count: 4" in md_text
    assert "qualification_allowed_count: 0" in md_text
    assert "no TWS connection" in md_text
    assert "no auto trade" in md_text
