from __future__ import annotations

from src.local_data_source_dry_run import build_data_source_dry_run_snapshot


def test_data_source_dry_run_keeps_sources_unconnected() -> None:
    snapshot = build_data_source_dry_run_snapshot("2026-06-01T00:00:00+00:00")
    statuses = {entry["name"]: entry["status"] for entry in snapshot["data_sources"]}

    assert snapshot["status"] == "US_GLD_SLV_DATA_SOURCE_DRY_RUN_READY"
    assert statuses["IBKR Network B / ARCA"] == "NOT_SUBSCRIBED_NOT_CONNECTED"
    assert statuses["FREE_DELAYED_PUBLIC_SOURCE"] == "CANDIDATE_NOT_CONNECTED"
    assert statuses["MANUAL_CSV_SOURCE"] == "FALLBACK_READY_AS_DESIGN_ONLY"
    assert statuses["PAID_MARKET_DATA_API"] == "CANDIDATE_NOT_CONNECTED"
    assert statuses["HYBRID_SOURCE_ROUTER"] == "DESIGN_ONLY"
    assert snapshot["source_connection_implemented"] == "NO"
    assert snapshot["live_market_data_enabled"] == "NO"
