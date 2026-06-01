from __future__ import annotations

from datetime import datetime, timezone

from src.market_data_validation import validate_market_data_row


VALID_ROW = {
    "symbol": "GLD",
    "market": "US",
    "timestamp_utc": "2026-06-01T00:00:00Z",
    "price": "220.10",
    "currency": "USD",
    "source_name": "manual_operator_sample",
    "source_type": "manual",
    "data_delay_status": "manual_input",
}


def test_validate_market_data_row_accepts_valid_gld() -> None:
    result = validate_market_data_row(VALID_ROW, now=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc))

    assert result["validation_status"] == "VALID_DATA"
    assert result["errors"] == []
    assert result["normalized"]["symbol"] == "GLD"


def test_validate_market_data_row_rejects_unsupported_symbol() -> None:
    row = {**VALID_ROW, "symbol": "AAPL"}

    result = validate_market_data_row(row, now=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc))

    assert result["validation_status"] == "INVALID_DATA"
    assert "UNSUPPORTED_SYMBOL" in result["errors"]


def test_validate_market_data_row_rejects_missing_fields() -> None:
    row = dict(VALID_ROW)
    row.pop("price")

    result = validate_market_data_row(row, now=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc))

    assert result["validation_status"] == "INVALID_DATA"
    assert "INVALID_DATA" in result["errors"]


def test_validate_market_data_row_rejects_non_usd() -> None:
    row = {**VALID_ROW, "currency": "EUR"}

    result = validate_market_data_row(row, now=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc))

    assert result["validation_status"] == "INVALID_DATA"
    assert "INVALID_CURRENCY" in result["errors"]


def test_validate_market_data_row_marks_stale_data() -> None:
    row = {**VALID_ROW, "timestamp_utc": "2026-05-29T00:00:00Z"}

    result = validate_market_data_row(row, now=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc))

    assert result["validation_status"] == "STALE_DATA"
    assert "STALE_DATA" in result["warnings"]
