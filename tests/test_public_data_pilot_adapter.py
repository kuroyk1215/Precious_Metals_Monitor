from __future__ import annotations

from src.public_data_pilot_adapter import build_public_data_pilot_dry_run, public_data_pilot_fetch


def test_public_data_pilot_dry_run_has_fetch_disabled() -> None:
    snapshot = build_public_data_pilot_dry_run("2026-06-01T00:00:00+00:00")

    assert snapshot["status"] == "PUBLIC_DATA_PILOT_DRY_RUN_READY"
    assert snapshot["public_data_auto_fetch_enabled"] == "NO"
    assert snapshot["public_data_fetch_requires_explicit_allow"] == "YES"


def test_public_data_pilot_fetch_default_disabled() -> None:
    result = public_data_pilot_fetch()

    assert result["status"] == "PUBLIC_DATA_PILOT_FETCH_DISABLED"
    assert result["network_request_made"] == "NO"
