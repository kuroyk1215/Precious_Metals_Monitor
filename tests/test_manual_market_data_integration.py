from pathlib import Path

from src.manual_market_data_integration import (
    build_integrated_market_data_rows,
    load_manual_market_data_snapshot,
    write_integrated_actual_etf_price_csv,
    write_integrated_upstream_factor_csv,
    write_manual_market_data_integration_report,
    write_manual_market_data_integration_summary_csv,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_build_integrated_market_data_rows_ok_and_unavailable():
    snapshot = {
        "XAUUSD": {
            "target_id": "XAUUSD",
            "value": "2350.5",
            "currency": "USD",
            "source": "manual_csv",
            "source_status": "manual_csv",
            "normalized_status": "ok",
            "warning_flags": "manual_csv",
            "notes": "gold",
        },
        "1540.T": {
            "target_id": "1540.T",
            "value": "2912.5",
            "currency": "JPY",
            "source": "manual_csv",
            "source_status": "manual_csv",
            "normalized_status": "ok",
            "warning_flags": "manual_csv",
            "notes": "jp etf",
        },
        "1542.T": {
            "target_id": "1542.T",
            "value": "unavailable",
            "currency": "JPY",
            "source": "manual_csv",
            "source_status": "manual_csv",
            "normalized_status": "unavailable",
            "warning_flags": "value_unavailable_or_invalid",
            "notes": "missing",
        },
    }

    upstream_rows, actual_rows, summary_rows = build_integrated_market_data_rows(snapshot, TZ)
    upstream = {r.factor: r for r in upstream_rows}
    actual = {r.etf_symbol: r for r in actual_rows}
    summary = {r.target_id: r for r in summary_rows}

    assert upstream["XAUUSD"].value == "2350.5"
    assert upstream["XAUUSD"].source_status == "manual_csv"
    assert "no_realtime_source" in upstream["XAUUSD"].warning_flags

    assert upstream["XAGUSD"].value == "unavailable"
    assert "missing_manual_market_data_target" in upstream["XAGUSD"].warning_flags

    assert actual["1540.T"].actual_price == "2912.5"
    assert actual["1542.T"].actual_price == "unavailable"
    assert summary["1540.T"].included == "true"
    assert summary["1542.T"].included == "false"


def test_load_and_write_manual_market_data_integration(tmp_path: Path):
    input_csv = tmp_path / "manual_market_data_snapshot.csv"
    input_csv.write_text(
        "target_id,target_type,market,data_role,value,currency,source,source_status,source_timestamp,normalized_status,warning_flags,notes,timestamp_jst,timestamp_et\n"
        "USDJPY,upstream_factor,FX,fx_rate,155.1,JPY,manual_csv,manual_csv,2026-05-06T09:00:00Z,ok,manual_csv,manual,2026-05-06T18:00:00+09:00,2026-05-06T05:00:00-04:00\n"
        "518880.SH,etf_actual_price,CN,cn_gold_etf_actual_price,5.12,CNY,manual_csv,manual_csv,2026-05-06T09:00:00Z,ok,manual_csv,manual,2026-05-06T18:00:00+09:00,2026-05-06T05:00:00-04:00\n",
        encoding="utf-8",
    )

    snapshot = load_manual_market_data_snapshot(str(input_csv))
    upstream_rows, actual_rows, summary_rows = build_integrated_market_data_rows(snapshot, TZ)

    upstream_csv = tmp_path / "manual_upstream_factor_snapshot.csv"
    actual_csv = tmp_path / "manual_actual_etf_price_snapshot.csv"
    summary_csv = tmp_path / "manual_market_data_integration_summary.csv"
    report_md = tmp_path / "manual_market_data_integration_report.md"

    write_integrated_upstream_factor_csv(upstream_csv, upstream_rows)
    write_integrated_actual_etf_price_csv(actual_csv, actual_rows)
    write_manual_market_data_integration_summary_csv(summary_csv, summary_rows)
    write_manual_market_data_integration_report(report_md, summary_rows, str(input_csv), str(upstream_csv), str(actual_csv))

    assert "factor" in upstream_csv.read_text(encoding="utf-8")
    assert "etf_symbol" in actual_csv.read_text(encoding="utf-8")
    assert "included" in summary_csv.read_text(encoding="utf-8")
    assert "Manual Market Data Snapshot Integration Report" in report_md.read_text(encoding="utf-8")
    assert "no IBKR connection" in report_md.read_text(encoding="utf-8")
