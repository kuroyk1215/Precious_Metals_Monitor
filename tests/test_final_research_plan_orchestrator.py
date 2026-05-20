from __future__ import annotations

import csv

from src.final_research_plan_orchestrator import (
    DATA_ROUTE_PRIMARY_METALS_THEORETICAL,
    ORCHESTRATOR_THEORETICAL_ROUTE,
    PLAN_DECISION_THEORETICAL_RANGE_ONLY,
    READY,
    build_final_research_plan_orchestrator_rows,
    write_final_research_plan_orchestrator_csv,
    write_final_research_plan_orchestrator_report,
)


def test_orchestrator_theoretical_route_outputs_final_manual_plan(tmp_path):
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

    rows = build_final_research_plan_orchestrator_rows(config_path)
    gold = [row for row in rows if row.metal == "gold"][0]
    silver = [row for row in rows if row.metal == "silver"][0]
    final = rows[-1]

    assert gold.status == ORCHESTRATOR_THEORETICAL_ROUTE
    assert gold.plan_decision == PLAN_DECISION_THEORETICAL_RANGE_ONLY
    assert gold.data_route == DATA_ROUTE_PRIMARY_METALS_THEORETICAL
    assert gold.market_direction_summary_allowed == "true"
    assert gold.theoretical_range_allowed == "true"
    assert gold.execution_price_confidence == "LOW"
    assert gold.manual_review_required == "true"
    assert gold.execution_price_required_before_trade == "true"
    assert gold.high_confidence_buy_sell_point_allowed == "false"
    assert gold.execution_trigger_allowed == "false"
    assert gold.final_action_allowed == "false"
    assert gold.one_command_output_available == "true"

    assert silver.status == ORCHESTRATOR_THEORETICAL_ROUTE
    assert silver.final_action_allowed == "false"

    assert final.status == READY
    assert final.plan_decision == PLAN_DECISION_THEORETICAL_RANGE_ONLY
    assert final.final_action_allowed == "false"
    assert final.action_allowed == "false"


def test_orchestrator_requires_inputs_when_primary_inputs_missing(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("primary_metals: {}\n", encoding="utf-8")

    rows = build_final_research_plan_orchestrator_rows(config_path)
    final = rows[-1]

    assert final.status == "INPUT_REQUIRED"
    assert final.plan_decision == "INPUT_REQUIRED"
    assert final.data_route == "INPUT_REQUIRED"
    assert final.final_research_plan_available == "false"
    assert final.final_action_allowed == "false"
    assert final.action_allowed == "false"


def test_orchestrator_price_confirmed_still_blocks_final_action(tmp_path):
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

    rows = build_final_research_plan_orchestrator_rows(config_path)
    gold = [row for row in rows if row.metal == "gold"][0]

    assert gold.status == "ORCHESTRATOR_PRICE_CONFIRMED_ROUTE"
    assert gold.plan_decision == "PRICE_CONFIRMED_RESEARCH_ONLY"
    assert gold.data_route == "ETF_PRICE_CONFIRMED_ROUTE"
    assert gold.execution_price_confidence == "HIGH"
    assert gold.manual_review_required == "true"
    assert gold.high_confidence_buy_sell_point_allowed == "false"
    assert gold.execution_trigger_allowed == "false"
    assert gold.final_action_allowed == "false"


def test_write_orchestrator_csv_and_report(tmp_path):
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

    rows = build_final_research_plan_orchestrator_rows(config_path)
    csv_path = tmp_path / "orchestrator.csv"
    md_path = tmp_path / "orchestrator.md"

    write_final_research_plan_orchestrator_csv(csv_path, rows)
    write_final_research_plan_orchestrator_report(md_path, rows, config_path)

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["metal"] == "gold"
    assert csv_rows[0]["one_command_output_available"] == "true"
    assert csv_rows[0]["final_action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 25A-27C Final Research Plan Orchestrator Report" in report
    assert "one-command final research plan output" in report
    assert "final_action_allowed is always false" in report
    assert "no market data request" in report
    assert "no auto trade" in report
