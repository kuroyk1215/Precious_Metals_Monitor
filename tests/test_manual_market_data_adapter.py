from pathlib import Path

from src.manual_market_data_adapter import (
    build_manual_market_data_template_rows,
    load_manual_market_data_csv,
    normalize_manual_market_data_rows,
    validate_manual_market_data_header,
    write_manual_market_data_adapter_report,
    write_manual_market_data_snapshot_csv,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_validate_manual_market_data_header():
    assert validate_manual_market_data_header(None)
    assert validate_manual_market_data_header(["target_id"]) != []
    assert validate_manual_market_data_header([
        "target_id",
        "target_type",
        "market",
        "data_role",
        "value",
        "currency",
        "source",
        "source_status",
        "source_timestamp",
        "notes",
    ]) == []


def test_template_rows_are_unavailable_and_safe():
    rows = build_manual_market_data_template_rows(TZ)
    by_target = {r.target_id: r for r in rows}

    assert "XAUUSD" in by_target
    assert "1540.T" in by_target
    assert "518880.SH" in by_target

    for row in rows:
        assert row.normalized_status == "unavailable"
        assert "manual_input_required" in row.warning_flags
        assert "no_realtime_source" in row.warning_flags


def test_normalize_manual_market_data_rows_ok_and_invalid():
    raw_rows = [
        {
            "target_id": "XAUUSD",
            "target_type": "upstream_factor",
            "market": "GLOBAL",
            "data_role": "gold_spot_usd",
            "value": "2350.5",
            "currency": "USD",
            "source": "manual_csv",
            "source_status": "manual_csv",
            "source_timestamp": "2026-05-06T09:00:00Z",
            "notes": "manual test",
        },
        {
            "target_id": "1540.T",
            "target_type": "etf_actual_price",
            "market": "JP",
            "data_role": "jp_gold_etf_actual_price",
            "value": "unavailable",
            "currency": "JPY",
            "source": "manual_csv",
            "source_status": "manual_csv",
            "source_timestamp": "unavailable",
            "notes": "missing value",
        },
    ]

    rows = normalize_manual_market_data_rows(raw_rows, [], TZ)
    by_target = {r.target_id: r for r in rows}

    assert by_target["XAUUSD"].normalized_status == "ok"
    assert by_target["XAUUSD"].value == "2350.5"
    assert "manual_csv" in by_target["XAUUSD"].warning_flags

    assert by_target["1540.T"].normalized_status == "unavailable"
    assert "value_unavailable_or_invalid" in by_target["1540.T"].warning_flags
    assert "source_timestamp_missing" in by_target["1540.T"].warning_flags


def test_normalize_missing_header_returns_invalid_file_row():
    rows = normalize_manual_market_data_rows([], ["value"], TZ)
    assert len(rows) == 1
    assert rows[0].target_id == "__file__"
    assert rows[0].normalized_status == "invalid"
    assert "missing_required_fields" in rows[0].warning_flags
    assert "value" in rows[0].notes


def test_manual_market_data_load_and_writers(tmp_path: Path):
    input_csv = tmp_path / "input.csv"
    input_csv.write_text(
        "target_id,target_type,market,data_role,value,currency,source,source_status,source_timestamp,notes\n"
        "USDJPY,upstream_factor,FX,fx_rate,155.1,JPY,manual_csv,manual_csv,2026-05-06T09:00:00Z,manual\n",
        encoding="utf-8",
    )

    raw_rows, missing = load_manual_market_data_csv(str(input_csv))
    rows = normalize_manual_market_data_rows(raw_rows, missing, TZ)

    snapshot_csv = tmp_path / "manual_market_data_snapshot.csv"
    report_md = tmp_path / "manual_market_data_adapter_report.md"

    write_manual_market_data_snapshot_csv(snapshot_csv, rows)
    write_manual_market_data_adapter_report(report_md, rows, str(input_csv))

    assert "target_id" in snapshot_csv.read_text(encoding="utf-8")
    assert "normalized_status" in snapshot_csv.read_text(encoding="utf-8")
    assert "Manual CSV Market Data Adapter Report" in report_md.read_text(encoding="utf-8")
    assert "no IBKR connection" in report_md.read_text(encoding="utf-8")
