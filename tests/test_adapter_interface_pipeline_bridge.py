from pathlib import Path

from src.adapter_interface_pipeline_bridge import (
    build_adapter_interface_bridge_rows,
    load_adapter_interface_rows,
    write_adapter_interface_bridge_report,
    write_adapter_interface_bridge_snapshot_csv,
    write_adapter_interface_bridge_summary_csv,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_build_adapter_interface_bridge_rows_ok_and_unavailable():
    adapter_rows = [
        {
            "provider_id": "manual_csv",
            "target_id": "XAUUSD",
            "target_type": "upstream_factor",
            "market": "GLOBAL",
            "data_role": "gold_spot_usd",
            "value": "2350.0",
            "currency": "USD",
            "source": "manual_csv",
            "source_status": "manual_csv",
            "adapter_status": "ok",
            "warning_flags": "manual_csv_adapter",
            "notes": "valid",
            "timestamp_jst": "2026-05-06T09:00:00+09:00",
            "timestamp_et": "2026-05-05T20:00:00-04:00",
        },
        {
            "provider_id": "manual_csv",
            "target_id": "1540.T",
            "target_type": "etf_actual_price",
            "market": "JP",
            "data_role": "jp_gold_etf_actual_price",
            "value": "unavailable",
            "currency": "JPY",
            "source": "manual_csv",
            "source_status": "missing_target",
            "adapter_status": "unavailable",
            "warning_flags": "missing_manual_csv_target",
            "notes": "missing",
            "timestamp_jst": "unavailable",
            "timestamp_et": "unavailable",
        },
    ]

    bridge_rows, summary_rows = build_adapter_interface_bridge_rows(adapter_rows, TZ)
    by_target = {r.target_id: r for r in bridge_rows}
    summary = {r.target_id: r for r in summary_rows}

    assert by_target["XAUUSD"].normalized_status == "ok"
    assert by_target["XAUUSD"].value == "2350.0"
    assert by_target["XAUUSD"].source_timestamp == "2026-05-06T09:00:00+09:00"
    assert "adapter_interface_pipeline_bridge" in by_target["XAUUSD"].warning_flags

    assert by_target["1540.T"].normalized_status == "unavailable"
    assert by_target["1540.T"].value == "unavailable"
    assert summary["1540.T"].included == "false"
    assert summary["1540.T"].bridge_status == "unavailable"


def test_load_adapter_interface_rows(tmp_path: Path):
    p = tmp_path / "adapter.csv"
    p.write_text(
        "provider_id,target_id,adapter_status,value\n"
        "manual_csv,XAUUSD,ok,2350.0\n",
        encoding="utf-8",
    )

    rows = load_adapter_interface_rows(str(p))
    assert rows == [{"provider_id": "manual_csv", "target_id": "XAUUSD", "adapter_status": "ok", "value": "2350.0"}]


def test_adapter_interface_bridge_writers(tmp_path: Path):
    adapter_rows = [
        {
            "provider_id": "manual_csv",
            "target_id": "USDJPY",
            "target_type": "upstream_factor",
            "market": "FX",
            "data_role": "fx_rate",
            "value": "155.0",
            "currency": "JPY",
            "source": "manual_csv",
            "source_status": "manual_csv",
            "adapter_status": "ok",
            "warning_flags": "manual_csv_adapter",
            "notes": "valid",
            "timestamp_jst": "2026-05-06T09:00:00+09:00",
            "timestamp_et": "2026-05-05T20:00:00-04:00",
        }
    ]

    bridge_rows, summary_rows = build_adapter_interface_bridge_rows(adapter_rows, TZ)

    snapshot_csv = tmp_path / "adapter_bridge_market_data_snapshot.csv"
    summary_csv = tmp_path / "adapter_bridge_summary.csv"
    report_md = tmp_path / "adapter_bridge_report.md"

    write_adapter_interface_bridge_snapshot_csv(snapshot_csv, bridge_rows)
    write_adapter_interface_bridge_summary_csv(summary_csv, summary_rows)
    write_adapter_interface_bridge_report(report_md, summary_rows, "adapter.csv", str(snapshot_csv))

    assert "normalized_status" in snapshot_csv.read_text(encoding="utf-8")
    assert "bridge_status" in summary_csv.read_text(encoding="utf-8")
    assert "Adapter Interface to Pipeline Bridge Report" in report_md.read_text(encoding="utf-8")
    assert "no API request" in report_md.read_text(encoding="utf-8")
    assert "no IBKR connection" in report_md.read_text(encoding="utf-8")
