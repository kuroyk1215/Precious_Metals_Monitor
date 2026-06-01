from __future__ import annotations

import csv
from pathlib import Path

from src.local_market_data_store import load_manual_csv_to_store
from src.market_data_validation import REQUIRED_FIELDS


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_load_manual_csv_to_store_writes_valid_gld_slv(tmp_path: Path) -> None:
    input_path = tmp_path / "valid.csv"
    store_path = tmp_path / "store.json"
    _write_rows(
        input_path,
        [
            {
                "symbol": "GLD",
                "market": "US",
                "timestamp_utc": "2026-06-01T00:00:00Z",
                "price": "220.10",
                "currency": "USD",
                "source_name": "manual",
                "source_type": "manual",
                "data_delay_status": "manual_input",
            },
            {
                "symbol": "SLV",
                "market": "US",
                "timestamp_utc": "2026-06-01T00:00:00Z",
                "price": "28.40",
                "currency": "USD",
                "source_name": "manual",
                "source_type": "manual",
                "data_delay_status": "manual_input",
            },
        ],
    )

    store = load_manual_csv_to_store(input_path, store_path)

    assert store["status"] == "LOCAL_MARKET_DATA_STORE_READY"
    assert store["symbols"]["GLD"]["source_display"] == "Manual CSV"
    assert store["trade_signal_generated"] == "NO"


def test_load_manual_csv_to_store_rejects_invalid_symbol(tmp_path: Path) -> None:
    input_path = tmp_path / "invalid.csv"
    _write_rows(
        input_path,
        [
            {
                "symbol": "AAPL",
                "market": "US",
                "timestamp_utc": "2026-06-01T00:00:00Z",
                "price": "100",
                "currency": "USD",
                "source_name": "manual",
                "source_type": "manual",
                "data_delay_status": "manual_input",
            }
        ],
    )

    try:
        load_manual_csv_to_store(input_path, tmp_path / "store.json")
    except ValueError as exc:
        assert "validation failed" in str(exc)
    else:
        raise AssertionError("invalid symbol should fail")
