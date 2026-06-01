from __future__ import annotations

from src.public_data_source_registry import build_public_data_source_registry


def test_public_data_source_registry_contains_expected_candidates() -> None:
    registry = build_public_data_source_registry("2026-06-01T00:00:00+00:00")
    candidates = {item["source_name"]: item for item in registry["candidates"]}

    assert set(candidates) == {"Stooq", "Alpha Vantage", "Yahoo Finance"}
    assert candidates["Alpha Vantage"]["api_key_required"] == "YES"
    assert candidates["Yahoo Finance"]["enabled"] == "NO"
    assert candidates["Stooq"]["default_status"] == "CANDIDATE_NOT_CONNECTED"
