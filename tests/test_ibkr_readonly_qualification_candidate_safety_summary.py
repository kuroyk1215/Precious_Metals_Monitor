from pathlib import Path

from src.ibkr_contract_mapping_plan import (
    build_ibkr_contract_mapping_plan_rows,
    load_ibkr_contract_mapping_config,
)
from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
from src.ibkr_readonly_qualification_safety_summary import IBKRReadOnlyQualificationSafetySummaryRow
from src.ibkr_readonly_qualification_candidate_resolver import build_ibkr_readonly_qualification_candidate_resolver_rows
from src.ibkr_readonly_qualification_candidate_review_pack import build_ibkr_readonly_qualification_candidate_review_pack_rows
from src.ibkr_readonly_qualification_candidate_final_gate import build_ibkr_readonly_qualification_candidate_final_gate_rows
from src.ibkr_readonly_qualification_candidate_safety_summary import (
    build_ibkr_readonly_qualification_candidate_safety_summary_rows,
    write_ibkr_readonly_qualification_candidate_safety_summary_csv,
    write_ibkr_readonly_qualification_candidate_safety_summary_report,
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


def _all_rows():
    config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
    mapping_rows = build_ibkr_contract_mapping_plan_rows(config, TZ)
    dry_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, TZ)
    guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_rows, TZ)
    resolver_rows = build_ibkr_readonly_qualification_candidate_resolver_rows(
        mapping_rows,
        dry_rows,
        guard_rows,
        _safety_rows(),
        TZ,
    )
    review_rows = build_ibkr_readonly_qualification_candidate_review_pack_rows(resolver_rows, TZ)
    gate_rows = build_ibkr_readonly_qualification_candidate_final_gate_rows(
        resolver_rows,
        review_rows,
        TZ,
    )
    return resolver_rows, review_rows, gate_rows


def _summary_rows():
    resolver_rows, review_rows, gate_rows = _all_rows()
    return build_ibkr_readonly_qualification_candidate_safety_summary_rows(
        resolver_rows,
        review_rows,
        gate_rows,
        TZ,
    )


def test_candidate_safety_summary_defaults_to_blocked():
    rows = _summary_rows()

    assert len(rows) == 4

    by_section = {row.section_id: row for row in rows}

    assert by_section["12A"].candidate_count == "4"
    assert by_section["12A"].excluded_count == "3"
    assert by_section["12B"].review_required_count == "7"
    assert by_section["12C"].candidate_final_gate_status == "CLOSED"
    assert by_section["FINAL"].candidate_safety_status == "BLOCKED"
    assert by_section["FINAL"].candidate_final_gate_status == "CLOSED"
    assert by_section["FINAL"].candidate_count == "4"
    assert by_section["FINAL"].review_required_count == "7"
    assert by_section["FINAL"].excluded_count == "3"

    for row in rows:
        assert row.candidate_safety_status == "BLOCKED"
        assert row.qualification_allowed == "false"
        assert row.tws_connection_allowed == "false"
        assert row.contract_qualification_allowed == "false"
        assert row.market_data_request_allowed == "false"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert "no_ibkr_connection" in row.warning_flags


def test_candidate_safety_summary_detects_unsafe_true_permission():
    resolver_rows, review_rows, gate_rows = _all_rows()
    resolver_rows = [row.__dict__.copy() for row in resolver_rows]
    resolver_rows[0]["api_request_allowed"] = "true"

    rows = build_ibkr_readonly_qualification_candidate_safety_summary_rows(
        resolver_rows,
        review_rows,
        gate_rows,
        TZ,
    )

    by_section = {row.section_id: row for row in rows}
    assert by_section["12A"].candidate_safety_status == "BLOCKED"
    assert "unsafe_true_permission_detected" in by_section["12A"].blocking_summary


def test_candidate_safety_summary_writers(tmp_path: Path):
    rows = _summary_rows()

    csv_path = tmp_path / "ibkr_readonly_qualification_candidate_safety_summary.csv"
    md_path = tmp_path / "ibkr_readonly_qualification_candidate_safety_summary_report.md"

    write_ibkr_readonly_qualification_candidate_safety_summary_csv(csv_path, rows)
    write_ibkr_readonly_qualification_candidate_safety_summary_report(md_path, rows, "config.yaml")

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "candidate_safety_status" in csv_text
    assert "BLOCKED" in csv_text
    assert "Phase 12D IBKR Read-Only Qualification Candidate Safety Summary Report" in md_text
    assert "candidate_safety_status: BLOCKED" in md_text
    assert "candidate_final_gate_status: CLOSED" in md_text
    assert "final_candidate_count: 4" in md_text
    assert "final_review_required_count: 7" in md_text
    assert "qualification_allowed_count: 0" in md_text
    assert "no TWS connection" in md_text
    assert "no auto trade" in md_text
