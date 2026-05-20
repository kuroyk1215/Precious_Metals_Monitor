from __future__ import annotations

import csv

from src.primary_metals_final_review_pack_integration import (
    FINAL_DECISION_RESEARCH_ONLY_THEORETICAL_RANGE,
    FINAL_REVIEW_PRICE_CONFIRMED,
    FINAL_REVIEW_THEORETICAL_ONLY,
    READY,
    build_primary_metals_final_review_pack_rows,
    write_primary_metals_final_review_pack_csv,
    write_primary_metals_final_review_pack_report,
)


def test_final_review_pack_allows_direction_and_theoretical_range_but_blocks_action(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
primary_metals:
  usd_jpy: 155.0
  gold_price: 2400.0
  gold_previous_price: 2380.0
  gold_conversion_factor: 0.01
  gold_etf_data_status: NO_MARKET_DATA_SUBSCRIPTION
  silver_price: 30.0
  silver_previous_price: 31.0
  silver_conversion_factor: 1.0
  silver_etf_data_status: NO_MARKET_DATA_SUBSCRIPTION
""".strip(),
        encoding="utf-8",
    )

    rows = build_primary_metals_final_review_pack_rows(config_path)
    gold = [row for row in rows if row.metal == "gold"][0]
    silver = [row for row in rows if row.metal == "silver"][0]
    final = rows[-1]

    assert gold.status == FINAL_REVIEW_THEORETICAL_ONLY
    assert gold.final_decision == FINAL_DECISION_RESEARCH_ONLY_THEORETICAL_RANGE
    assert gold.final_direction_summary_allowed == "true"
    assert gold.final_theoretical_range_allowed == "true"
    assert gold.execution_price_confidence == "LOW"
    assert gold.final_high_confidence_execution_allowed == "false"
    assert gold.final_action_allowed == "false"

    assert silver.status == FINAL_REVIEW_THEORETICAL_ONLY
    assert silver.final_action_allowed == "false"

    assert final.status == READY
    assert final.final_decision == FINAL_DECISION_RESEARCH_ONLY_THEORETICAL_RANGE
    assert final.final_action_allowed == "false"
    assert final.action_allowed == "false"


def test_final_review_pack_price_confirmed_keeps_research_only_action_block(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
primary_metals:
  usd_jpy: 155.0
  gold_price: 2400.0
  gold_previous_price: 2400.0
  gold_conversion_factor: 0.01
  gold_etf_actual_price: 3720.0
  silver_price: 30.0
  silver_previous_price: 30.0
  silver_conversion_factor: 1.0
  silver_etf_actual_price: 4650.0
""".strip(),
        encoding="utf-8",
    )

    rows = build_primary_metals_final_review_pack_rows(config_path)
    gold = [row for row in rows if row.metal == "gold"][0]
    silver = [row for row in rows if row.metal == "silver"][0]

    assert gold.status == FINAL_REVIEW_PRICE_CONFIRMED
    assert gold.execution_price_confidence == "HIGH"
    assert gold.final_high_confidence_execution_allowed == "true"
    assert gold.final_action_allowed == "false"
    assert gold.action_allowed == "false"

    assert silver.status == FINAL_REVIEW_PRICE_CONFIRMED
    assert silver.final_high_confidence_execution_allowed == "true"
    assert silver.final_action_allowed == "false"


def test_final_review_pack_requires_inputs_when_no_market_signal(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("primary_metals: {}\n", encoding="utf-8")

    rows = build_primary_metals_final_review_pack_rows(config_path)
    final = rows[-1]

    assert final.status == "INPUT_REQUIRED"
    assert final.final_decision == "INPUT_REQUIRED"
    assert final.final_action_allowed == "false"
    assert final.action_allowed == "false"


def test_write_final_review_pack_csv_and_report(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
primary_metals:
  usd_jpy: 155.0
  gold_price: 2400.0
  gold_previous_price: 2380.0
  gold_conversion_factor: 0.01
""".strip(),
        encoding="utf-8",
    )

    rows = build_primary_metals_final_review_pack_rows(config_path)
    csv_path = tmp_path / "final_review.csv"
    md_path = tmp_path / "final_review.md"

    write_primary_metals_final_review_pack_csv(csv_path, rows)
    write_primary_metals_final_review_pack_report(md_path, rows, config_path)

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["metal"] == "gold"
    assert csv_rows[0]["final_direction_summary_allowed"] == "true"
    assert csv_rows[0]["final_action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 23A-23C Primary Metals Final Review Pack Integration Report" in report
    assert "final_action_allowed is always false" in report
    assert "no market data request" in report
    assert "no auto trade" in report
