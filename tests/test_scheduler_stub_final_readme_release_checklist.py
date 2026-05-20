from __future__ import annotations

import csv

from src.scheduler_stub_final_readme_release_checklist import (
    MVP_RELEASE_READY,
    READY,
    build_scheduler_stub_final_readme_release_checklist_rows,
    write_final_mvp_readme,
    write_scheduler_stub_final_readme_release_checklist_csv,
    write_scheduler_stub_final_readme_release_checklist_report,
)


def test_scheduler_stub_release_checklist_ready_when_upstream_output_available(tmp_path):
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

    rows = build_scheduler_stub_final_readme_release_checklist_rows(config_path)
    final = rows[-1]

    assert final.status == READY
    assert final.release_decision == MVP_RELEASE_READY
    assert final.scheduler_stub_ready == "true"
    assert final.scheduler_job_started == "false"
    assert final.telegram_stub_ready == "true"
    assert final.telegram_api_called == "false"
    assert final.readme_ready == "true"
    assert final.release_checklist_ready == "true"
    assert final.safety_boundary_ready == "true"
    assert final.final_action_allowed == "false"
    assert final.action_allowed == "false"


def test_scheduler_stub_release_checklist_input_required_without_inputs(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("primary_metals: {}\n", encoding="utf-8")

    rows = build_scheduler_stub_final_readme_release_checklist_rows(config_path)
    final = rows[-1]

    assert final.status == "INPUT_REQUIRED"
    assert final.release_decision == "MVP_INPUT_REQUIRED"
    assert final.scheduler_job_started == "false"
    assert final.telegram_api_called == "false"
    assert final.final_action_allowed == "false"


def test_write_release_checklist_csv_report_and_readme(tmp_path):
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

    rows = build_scheduler_stub_final_readme_release_checklist_rows(config_path)
    csv_path = tmp_path / "release.csv"
    report_path = tmp_path / "release.md"
    readme_path = tmp_path / "mvp_readme.md"

    write_scheduler_stub_final_readme_release_checklist_csv(csv_path, rows)
    write_scheduler_stub_final_readme_release_checklist_report(report_path, rows, config_path)
    write_final_mvp_readme(readme_path, rows)

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["scheduler_job_started"] == "false"
    assert csv_rows[0]["telegram_api_called"] == "false"
    assert csv_rows[0]["final_action_allowed"] == "false"

    report = report_path.read_text(encoding="utf-8")
    assert "Phase 31A-32C Scheduler Stub Final README Release Checklist Report" in report
    assert "No Telegram API call is made" in report
    assert "No background job is started" in report
    assert "no auto trade" in report

    readme = readme_path.read_text(encoding="utf-8")
    assert "贵金属监控系统 MVP 使用说明" in readme
    assert "Telegram API：禁用" in readme
    assert "最终交易动作：禁用" in readme
