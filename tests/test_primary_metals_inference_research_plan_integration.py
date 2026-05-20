from __future__ import annotations

import csv

from src.primary_metals_inference_research_plan_integration import (
    READY,
    RESEARCH_PLAN_PRICE_CONFIRMED,
    RESEARCH_PLAN_THEORETICAL_ONLY,
    build_primary_metals_inference_research_plan_rows,
    write_primary_metals_inference_research_plan_csv,
    write_primary_metals_inference_research_plan_report,
)


def test_research_plan_integration_allows_theoretical_plan_but_blocks_execution_points(tmp_path):
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

    rows = build_primary_metals_inference_research_plan_rows(config_path)
    gold = [row for row in rows if row.metal == "gold"][0]
    silver = [row for row in rows if row.metal == "silver"][0]
    final = rows[-1]

    assert gold.status == RESEARCH_PLAN_THEORETICAL_ONLY
    assert gold.market_direction == "UP"
    assert gold.research_plan_available == "true"
    assert gold.theoretical_range_allowed == "true"
    assert gold.execution_price_confidence == "LOW"
    assert gold.high_confidence_buy_sell_point_allowed == "false"
    assert gold.execution_price_required_before_trade == "true"
    assert gold.action_allowed == "false"

    assert silver.status == RESEARCH_PLAN_THEORETICAL_ONLY
    assert silver.market_direction == "DOWN"
    assert silver.high_confidence_buy_sell_point_allowed == "false"

    assert final.status == READY
    assert final.research_plan_available == "true"
    assert final.execution_price_confidence == "LOW"
    assert final.action_allowed == "false"


def test_research_plan_integration_price_confirmed_allows_high_confidence_flag_but_no_action(tmp_path):
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

    rows = build_primary_metals_inference_research_plan_rows(config_path)
    gold = [row for row in rows if row.metal == "gold"][0]
    silver = [row for row in rows if row.metal == "silver"][0]

    assert gold.status == RESEARCH_PLAN_PRICE_CONFIRMED
    assert gold.execution_price_confidence == "HIGH"
    assert gold.high_confidence_buy_sell_point_allowed == "true"
    assert gold.execution_price_required_before_trade == "false"
    assert gold.action_allowed == "false"

    assert silver.status == RESEARCH_PLAN_PRICE_CONFIRMED
    assert silver.high_confidence_buy_sell_point_allowed == "true"
    assert silver.action_allowed == "false"


def test_research_plan_integration_requires_inputs_when_no_market_signal(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("primary_metals: {}\n", encoding="utf-8")

    rows = build_primary_metals_inference_research_plan_rows(config_path)
    final = rows[-1]

    assert final.status == "INPUT_REQUIRED"
    assert final.research_plan_available == "false"
    assert final.action_allowed == "false"


def test_write_research_plan_integration_csv_and_report(tmp_path):
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

    rows = build_primary_metals_inference_research_plan_rows(config_path)
    csv_path = tmp_path / "plan.csv"
    md_path = tmp_path / "plan.md"

    write_primary_metals_inference_research_plan_csv(csv_path, rows)
    write_primary_metals_inference_research_plan_report(md_path, rows, config_path)

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["metal"] == "gold"
    assert csv_rows[0]["research_plan_available"] == "true"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 22A-22C Primary Metals Inference Research Plan Integration Report" in report
    assert "execution_price_confidence is LOW" in report
    assert "no market data request" in report
    assert "no auto trade" in report
