from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.public_data_intake_preparation import (
    FIELD_CONTRACT,
    PUBLIC_DATA_FIELD_CONTRACT_SNAPSHOT,
    PUBLIC_DATA_INTAKE_PREPARATION_SNAPSHOT,
    PUBLIC_DATA_SAFETY_GUARD_SNAPSHOT,
    STATUS,
    build_field_contract_snapshot,
    build_safety_guard_snapshot,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_public_data_intake_prep_cli_succeeds() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "main.py"), "--public-data-intake-prep"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert STATUS in result.stdout
    assert "public_data_connection_implemented=NO" in result.stdout
    assert "external_market_data_request_enabled=NO" in result.stdout
    assert "real_price_ingestion_enabled=NO" in result.stdout


def test_public_data_field_contract_contains_required_fields() -> None:
    snapshot = build_field_contract_snapshot("2026-06-01T00:00:00+00:00")

    for field in (
        "symbol",
        "market",
        "source_name",
        "source_type",
        "timestamp_utc",
        "price_status",
        "last_price_status",
        "currency",
        "data_delay_status",
        "terms_review_status",
        "reliability_status",
        "ingestion_status",
    ):
        assert field in snapshot["fields"]
    assert tuple(snapshot["fields"]) == FIELD_CONTRACT


def test_public_data_safety_guard_contains_required_rules() -> None:
    snapshot = build_safety_guard_snapshot("2026-06-01T00:00:00+00:00")

    for rule in (
        "no source -> no price",
        "no price -> no signal",
        "no approved terms -> no automated ingestion",
        "no verified freshness -> framework only",
    ):
        assert rule in snapshot["rules"]


def test_generated_public_data_snapshots_are_safe() -> None:
    prep = json.loads((REPO_ROOT / PUBLIC_DATA_INTAKE_PREPARATION_SNAPSHOT).read_text(encoding="utf-8"))
    contract = json.loads((REPO_ROOT / PUBLIC_DATA_FIELD_CONTRACT_SNAPSHOT).read_text(encoding="utf-8"))
    guard = json.loads((REPO_ROOT / PUBLIC_DATA_SAFETY_GUARD_SNAPSHOT).read_text(encoding="utf-8"))

    assert prep["status"] == STATUS
    assert prep["public_data_connection_implemented"] == "NO"
    assert prep["external_market_data_request_enabled"] == "NO"
    assert prep["real_price_ingestion_enabled"] == "NO"
    assert "last_price_status" in contract["fields"]
    assert "no verified freshness -> framework only" in guard["rules"]
