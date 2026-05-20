from __future__ import annotations

import csv

from src.report_template_daily_log_telegram_ready_output import (
    READY,
    build_report_template_daily_log_telegram_rows,
    write_report_template_daily_log_telegram_csv,
    append_report_template_daily_log,
    write_report_template_daily_log_telegram_report,
    write_telegram_ready_text,
)


def test_report_template_daily_log_telegram_ready_output_theoretical_route(tmp_path):
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

    rows = build_report_template_daily_log_telegram_rows(config_path)
    gold = [row for row in rows if row.metal == "gold"][0]
    final = rows[-1]

    assert gold.status == "OUTPUT_READY"
    assert gold.telegram_status == "TELEGRAM_READY"
    assert gold.report_section_available == "true"
    assert gold.daily_log_ready == "true"
    assert gold.telegram_text_ready == "true"
    assert gold.telegram_api_called == "false"
    assert gold.final_action_allowed == "false"
    assert "direction=UP" in gold.telegram_message
    assert "manual_review=true" in gold.telegram_message

    assert final.status == READY
    assert final.telegram_text_ready == "true"
    assert final.telegram_api_called == "false"
    assert final.final_action_allowed == "false"


def test_report_template_daily_log_telegram_ready_output_requires_inputs(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("primary_metals: {}\n", encoding="utf-8")

    rows = build_report_template_daily_log_telegram_rows(config_path)
    final = rows[-1]

    assert final.status == "INPUT_REQUIRED"
    assert final.report_section_available == "false"
    assert final.telegram_text_ready == "false"
    assert final.telegram_api_called == "false"
    assert final.final_action_allowed == "false"


def test_write_report_csv_daily_log_report_and_telegram_text(tmp_path):
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

    rows = build_report_template_daily_log_telegram_rows(config_path)
    csv_path = tmp_path / "output.csv"
    log_path = tmp_path / "daily_log.csv"
    report_path = tmp_path / "report.md"
    telegram_path = tmp_path / "telegram.txt"

    write_report_template_daily_log_telegram_csv(csv_path, rows)
    append_report_template_daily_log(log_path, rows)
    write_report_template_daily_log_telegram_report(report_path, rows, config_path)
    write_telegram_ready_text(telegram_path, rows)

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["metal"] == "gold"
    assert csv_rows[0]["telegram_text_ready"] == "true"
    assert csv_rows[0]["telegram_api_called"] == "false"
    assert csv_rows[0]["final_action_allowed"] == "false"

    with log_path.open("r", encoding="utf-8", newline="") as f:
        log_rows = list(csv.DictReader(f))
    assert len(log_rows) == len(rows)

    report = report_path.read_text(encoding="utf-8")
    assert "Phase 28A-30C Report Template Daily Log Telegram-Ready Output Report" in report
    assert "Telegram API is not called" in report
    assert "final_action_allowed is always false" in report
    assert "no auto trade" in report

    telegram_text = telegram_path.read_text(encoding="utf-8")
    assert "Precious Metals Monitor - Final Research Plan" in telegram_text
    assert "telegram_api_called=false" in telegram_text
    assert "action_allowed=false" in telegram_text


def test_append_daily_log_appends_without_duplicate_header(tmp_path):
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

    rows = build_report_template_daily_log_telegram_rows(config_path)
    log_path = tmp_path / "daily_log.csv"

    append_report_template_daily_log(log_path, rows)
    append_report_template_daily_log(log_path, rows)

    with log_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert len(csv_rows) == len(rows) * 2
