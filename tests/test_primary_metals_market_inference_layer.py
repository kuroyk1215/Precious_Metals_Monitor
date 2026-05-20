from __future__ import annotations

import csv

from src.primary_metals_market_inference_layer import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    INPUT_REQUIRED,
    READY,
    THEORETICAL_ONLY,
    build_primary_metals_market_inference_rows,
    write_primary_metals_market_inference_csv,
    write_primary_metals_market_inference_report,
)


def test_primary_metals_inference_theoretical_only_when_etf_price_missing(tmp_path):
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

    rows = build_primary_metals_market_inference_rows(config_path)
    gold = [row for row in rows if row.metal == "gold"][0]
    silver = [row for row in rows if row.metal == "silver"][0]
    final = rows[-1]

    assert gold.status == THEORETICAL_ONLY
    assert gold.market_direction == "UP"
    assert gold.market_signal_available == "true"
    assert gold.theoretical_value_available == "true"
    assert gold.execution_price_confidence == CONFIDENCE_LOW
    assert gold.high_confidence_buy_sell_point_allowed == "false"

    assert silver.market_direction == "DOWN"
    assert silver.execution_price_confidence == CONFIDENCE_LOW

    assert final.status == READY
    assert final.market_signal_available == "true"
    assert final.execution_price_confidence == CONFIDENCE_LOW
    assert final.action_allowed == "false"


def test_primary_metals_inference_high_confidence_when_etf_price_present(tmp_path):
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

    rows = build_primary_metals_market_inference_rows(config_path)
    gold = [row for row in rows if row.metal == "gold"][0]
    silver = [row for row in rows if row.metal == "silver"][0]

    assert gold.status == "ETF_PRICE_CONFIRMED"
    assert gold.market_direction == "NEUTRAL"
    assert gold.execution_price_confidence == CONFIDENCE_HIGH
    assert gold.high_confidence_buy_sell_point_allowed == "true"

    assert silver.execution_price_confidence == CONFIDENCE_HIGH
    assert silver.high_confidence_buy_sell_point_allowed == "true"


def test_primary_metals_inference_requires_inputs_when_primary_missing(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("primary_metals: {}\n", encoding="utf-8")

    rows = build_primary_metals_market_inference_rows(config_path)
    final = rows[-1]

    assert final.status == INPUT_REQUIRED
    assert final.market_signal_available == "false"
    assert final.execution_price_confidence == "NONE"
    assert final.action_allowed == "false"


def test_write_primary_metals_inference_csv_and_report(tmp_path):
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

    rows = build_primary_metals_market_inference_rows(config_path)
    csv_path = tmp_path / "inference.csv"
    md_path = tmp_path / "inference.md"

    write_primary_metals_market_inference_csv(csv_path, rows)
    write_primary_metals_market_inference_report(md_path, rows, config_path)

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["metal"] == "gold"
    assert csv_rows[0]["market_signal_available"] == "true"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 21A-21C Primary Metals Market Inference Layer Report" in report
    assert "execution_price_confidence remains LOW" in report
    assert "no market data request" in report
    assert "no auto trade" in report
