from __future__ import annotations

import csv

from src.ibkr_readonly_preflight_safe_config_merge_plan import (
    ADD_TEXT,
    KEEP_TEXT,
    MERGE_PLAN_BLOCKED_TEXT,
    MERGE_PLAN_READY_TEXT,
    REVIEW_UPDATE_TEXT,
    SafeConfigMergePlanRow,
    build_ibkr_readonly_preflight_safe_config_merge_plan_rows,
    safe_config_merge_block,
    write_ibkr_readonly_preflight_safe_config_merge_plan_csv,
    write_ibkr_readonly_preflight_safe_config_merge_plan_report,
)


def test_safe_config_merge_plan_keep_when_config_matches(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
ibkr:
  read_only_required: true
  account_mode: paper
  host: 127.0.0.1
  port: 7497
  client_id: 1
  real_connection_allowed: false
  contract_qualification_allowed: false
  market_data_request_allowed: false
  historical_data_request_allowed: false
  trading_actions_allowed: false
""".strip(),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_preflight_safe_config_merge_plan_rows(config_path)
    non_final_rows = [row for row in rows if row.merge_id != "FINAL"]

    assert len(rows) == 11
    assert all(row.merge_action == KEEP_TEXT for row in non_final_rows)
    assert all(row.would_overwrite_existing == "false" for row in rows)
    assert all(row.config_file_modified == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)
    assert rows[-1].merge_plan_status == MERGE_PLAN_READY_TEXT


def test_safe_config_merge_plan_add_when_ibkr_keys_missing(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("runtime:\n  report_dir: reports\n", encoding="utf-8")

    rows = build_ibkr_readonly_preflight_safe_config_merge_plan_rows(config_path)
    non_final_rows = [row for row in rows if row.merge_id != "FINAL"]

    assert all(row.merge_action == ADD_TEXT for row in non_final_rows)
    assert all(row.would_overwrite_existing == "false" for row in non_final_rows)
    assert rows[-1].merge_action == ADD_TEXT
    assert rows[-1].merge_plan_status == MERGE_PLAN_READY_TEXT


def test_safe_config_merge_plan_review_update_when_values_differ(tmp_path):
    config_path = tmp_path / "unsafe.yaml"
    config_path.write_text(
        """
ibkr:
  read_only_required: false
  account_mode: live
  host: remote.example.com
  port: 4001
  client_id: 99
  real_connection_allowed: true
  contract_qualification_allowed: true
  market_data_request_allowed: true
  historical_data_request_allowed: true
  trading_actions_allowed: true
""".strip(),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_preflight_safe_config_merge_plan_rows(config_path)
    non_final_rows = [row for row in rows if row.merge_id != "FINAL"]

    assert all(row.merge_action == REVIEW_UPDATE_TEXT for row in non_final_rows)
    assert all(row.would_overwrite_existing == "true" for row in non_final_rows)
    assert rows[-1].would_overwrite_existing == "true"
    assert rows[-1].merge_plan_status == MERGE_PLAN_READY_TEXT


def test_safe_config_merge_plan_blocks_missing_input_source(tmp_path):
    missing_path = tmp_path / "missing.yaml"

    rows = build_ibkr_readonly_preflight_safe_config_merge_plan_rows(missing_path)

    assert rows[0].merge_id == "INPUT_SOURCE"
    assert rows[0].merge_plan_status == MERGE_PLAN_BLOCKED_TEXT
    assert rows[-1].merge_plan_status == MERGE_PLAN_BLOCKED_TEXT
    assert all(row.config_file_modified == "false" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_safe_config_merge_block_contains_required_ibkr_values():
    block = safe_config_merge_block()

    assert "ibkr:" in block
    assert "read_only_required: true" in block
    assert "account_mode: paper" in block
    assert "host: 127.0.0.1" in block
    assert "port: 7497" in block
    assert "client_id: 1" in block
    assert "real_connection_allowed: false" in block
    assert "trading_actions_allowed: false" in block


def test_write_safe_config_merge_plan_csv_and_report(tmp_path):
    rows = [
        SafeConfigMergePlanRow(
            merge_id="FINAL",
            merge_name="Final safe config manual merge plan decision",
            source_layer="Phase 14G",
            input_source="config.yaml",
            config_key="phase14g.safe_config_merge_plan_status",
            current_value="add=0;keep=10;review_update=0;overwrite=0",
            safe_value="MANUAL_MERGE_PLAN_ONLY",
            merge_action="KEEP",
            would_overwrite_existing="false",
            safe_config_line="",
            merge_plan_status="MERGE_PLAN_READY",
            apply_mode="manual_merge_plan_only",
            config_file_modified="false",
            real_connection_allowed="false",
            tws_connection_allowed="false",
            ibkr_api_request_allowed="false",
            contract_qualification_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            order_action_allowed="false",
            cancel_action_allowed="false",
            rebalance_action_allowed="false",
            auto_trade_allowed="false",
            action_allowed="false",
            warning_flags="PREFLIGHT_SAFE_CONFIG_MERGE_PLAN_DEFINED",
            notes="Safe merge plan only.",
            timestamp_jst="2026-05-19T23:30:00+09:00",
            timestamp_et="2026-05-19T10:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "safe_merge_plan.csv"
    md_path = tmp_path / "safe_merge_plan.md"

    write_ibkr_readonly_preflight_safe_config_merge_plan_csv(csv_path, rows)
    write_ibkr_readonly_preflight_safe_config_merge_plan_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["merge_id"] == "FINAL"
    assert csv_rows[0]["merge_action"] == "KEEP"
    assert csv_rows[0]["config_file_modified"] == "false"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 14G IBKR Read-Only Preflight Safe Config Merge Plan Report" in report
    assert "Safe Config Block" in report
    assert "no configuration file is modified" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report
