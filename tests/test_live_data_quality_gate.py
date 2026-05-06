from pathlib import Path

from src.live_data_quality_gate import (
    EXPECTED_TARGETS,
    build_live_data_quality_gate_rows,
    load_live_provider_adapter_rows_by_target,
    write_live_data_quality_gate_csv,
    write_live_data_quality_gate_report,
)
from src.live_provider_mock_adapter import (
    build_live_provider_mock_adapter_rows,
    load_live_provider_mock_adapter_config,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def _mock_rows_by_target():
    config = load_live_provider_mock_adapter_config("data/market_data_provider_config.yaml")
    rows = build_live_provider_mock_adapter_rows(config, TZ)
    return {row.target_id: row.__dict__ for row in rows}


def test_live_data_quality_gate_passes_default_mock_rows():
    rows = build_live_data_quality_gate_rows(_mock_rows_by_target(), TZ)

    assert len(rows) == len(EXPECTED_TARGETS)

    for row in rows:
        assert row.quality_status == "pass_mock_quality_gate"
        assert row.usable_for_research == "true"
        assert row.api_request_allowed == "false"
        assert row.action_allowed == "false"
        assert row.failure_reasons == "none"


def test_live_data_quality_gate_fails_invalid_value():
    source = _mock_rows_by_target()
    source["XAUUSD"]["mock_value"] = "-1"

    rows = build_live_data_quality_gate_rows(source, TZ)
    by_target = {row.target_id: row for row in rows}

    assert by_target["XAUUSD"].quality_status == "fail_quality_gate"
    assert by_target["XAUUSD"].usable_for_research == "false"
    assert "non_positive_value" in by_target["XAUUSD"].failure_reasons


def test_live_data_quality_gate_fails_missing_target():
    source = _mock_rows_by_target()
    source.pop("518880.SH")

    rows = build_live_data_quality_gate_rows(source, TZ)
    by_target = {row.target_id: row for row in rows}

    assert by_target["518880.SH"].quality_status == "fail_missing_target"
    assert by_target["518880.SH"].usable_for_research == "false"
    assert by_target["518880.SH"].failure_reasons == "missing_target"


def test_live_data_quality_gate_load_and_writers(tmp_path: Path):
    csv_input = tmp_path / "live_provider_mock_adapter.csv"
    csv_input.write_text(
        "target_id,target_type,market,data_role,mock_value,currency,data_status,source_quality,api_request_allowed,action_allowed,timestamp_jst,timestamp_et\n"
        "XAUUSD,upstream_factor,GLOBAL,gold_spot_usd,3400.00,USD,mock_live_adapter,mock_only,false,false,2026-05-06T18:00:00+09:00,2026-05-06T05:00:00-04:00\n",
        encoding="utf-8",
    )

    loaded = load_live_provider_adapter_rows_by_target(str(csv_input))
    rows = build_live_data_quality_gate_rows(loaded, TZ, expected_targets=["XAUUSD"])

    csv_path = tmp_path / "live_data_quality_gate.csv"
    md_path = tmp_path / "live_data_quality_gate_report.md"

    write_live_data_quality_gate_csv(csv_path, rows)
    write_live_data_quality_gate_report(md_path, rows, str(csv_input))

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "quality_status" in csv_text
    assert "pass_mock_quality_gate" in csv_text
    assert "Phase 10D Live Data Quality Gate Report" in md_text
    assert "usable_for_research_count: 1" in md_text
    assert "no API request" in md_text
    assert "no auto trade" in md_text
