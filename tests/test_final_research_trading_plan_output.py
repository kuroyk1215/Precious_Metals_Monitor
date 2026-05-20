from __future__ import annotations

import csv

from src.final_research_trading_plan_output import (
    FINAL_PLAN_PRICE_CONFIRMED_RESEARCH_ONLY,
    FINAL_PLAN_THEORETICAL_ONLY,
    PLAN_DECISION_THEORETICAL_RANGE_ONLY,
    READY,
    build_final_research_trading_plan_rows,
    write_final_research_trading_plan_csv,
    write_final_research_trading_plan_report,
)


def test_final_research_plan_theoretical_only_output_blocks_execution_points(tmp_path):
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

    rows = build_final_research_trading_plan_rows(config_path)
    gold = [row for row in rows if row.metal == "gold"][0]
    silver = [row for row in rows if row.metal == "silver"][0]
    final = rows[-1]

    assert gold.status == FINAL_PLAN_THEORETICAL_ONLY
    assert gold.plan_decision == PLAN_DECISION_THEORETICAL_RANGE_ONLY
    assert gold.final_research_plan_available == "true"
    assert gold.market_direction_summary_allowed == "true"
    assert gold.theoretical_range_allowed == "true"
    assert gold.data_gap_status == "ETF_ACTUAL_PRICE_MISSING"
    assert gold.execution_price_confidence == "LOW"
    assert gold.manual_review_required == "true"
    assert gold.high_confidence_buy_sell_point_allowed == "false"
    assert gold.execution_trigger_allowed == "false"
    assert gold.final_action_allowed == "false"

    assert silver.status == FINAL_PLAN_THEORETICAL_ONLY
    assert silver.final_action_allowed == "false"

    assert final.status == READY
    assert final.final_research_plan_available == "true"
    assert final.manual_review_required == "true"
    assert final.high_confidence_buy_sell_point_allowed == "false"
    assert final.final_action_allowed == "false"


def test_final_research_plan_price_confirmed_remains_research_only(tmp_path):
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

    rows = build_final_research_trading_plan_rows(config_path)
    gold = [row for row in rows if row.metal == "gold"][0]
    silver = [row for row in rows if row.metal == "silver"][0]

    assert gold.status == FINAL_PLAN_PRICE_CONFIRMED_RESEARCH_ONLY
    assert gold.data_gap_status == "ETF_ACTUAL_PRICE_CONFIRMED"
    assert gold.execution_price_confidence == "HIGH"
    assert gold.manual_review_required == "true"
    assert gold.high_confidence_buy_sell_point_allowed == "false"
    assert gold.execution_trigger_allowed == "false"
    assert gold.final_action_allowed == "false"

    assert silver.status == FINAL_PLAN_PRICE_CONFIRMED_RESEARCH_ONLY
    assert silver.final_action_allowed == "false"


def test_final_research_plan_requires_inputs_when_no_market_signal(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("primary_metals: {}\n", encoding="utf-8")

    rows = build_final_research_trading_plan_rows(config_path)
    final = rows[-1]

    assert final.status == "INPUT_REQUIRED"
    assert final.plan_decision == "INPUT_REQUIRED"
    assert final.final_research_plan_available == "false"
    assert final.manual_review_required == "true"
    assert final.final_action_allowed == "false"


def test_write_final_research_trading_plan_csv_and_report(tmp_path):
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

    rows = build_final_research_trading_plan_rows(config_path)
    csv_path = tmp_path / "final_plan.csv"
    md_path = tmp_path / "final_plan.md"

    write_final_research_trading_plan_csv(csv_path, rows)
    write_final_research_trading_plan_report(md_path, rows, config_path)

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["metal"] == "gold"
    assert csv_rows[0]["final_research_plan_available"] == "true"
    assert csv_rows[0]["manual_review_required"] == "true"
    assert csv_rows[0]["final_action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 24A-24C Final Research Trading Plan Output Report" in report
    assert "manual_review_required is true" in report
    assert "final_action_allowed is always false" in report
    assert "no market data request" in report
    assert "no auto trade" in report
