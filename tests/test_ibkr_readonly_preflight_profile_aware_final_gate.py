from __future__ import annotations

import csv

from src.ibkr_readonly_preflight_profile_aware_final_gate import (
    GO_TEXT,
    NO_GO_TEXT,
    PASS_GATE_TEXT,
    FAIL_GATE_TEXT,
    ProfileAwareFinalGateRow,
    build_ibkr_readonly_preflight_profile_aware_final_gate_rows,
    write_ibkr_readonly_preflight_profile_aware_final_gate_csv,
    write_ibkr_readonly_preflight_profile_aware_final_gate_report,
)


def test_profile_aware_final_gate_go_for_complete_live_readonly_config(tmp_path):
    config_path = tmp_path / "live.yaml"
    config_path.write_text(
        """
ibkr:
  read_only_required: true
  account_mode: live
  host: 127.0.0.1
  port: 7496
  client_id: 1
  real_connection_allowed: false
  contract_qualification_allowed: false
  market_data_request_allowed: false
  historical_data_request_allowed: false
  trading_actions_allowed: false
""".strip(),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_preflight_profile_aware_final_gate_rows(config_path)
    final = rows[-1]

    assert len(rows) == 4
    assert final.gate_id == "FINAL"
    assert final.selected_profile == "live-readonly"
    assert final.gate_status == PASS_GATE_TEXT
    assert final.final_gate_decision == GO_TEXT
    assert final.go_allowed == "true"
    assert final.config_ready == "true"
    assert final.profile_plan_clear == "true"
    assert all(row.action_allowed == "false" for row in rows)


def test_profile_aware_final_gate_go_for_complete_paper_config(tmp_path):
    config_path = tmp_path / "paper.yaml"
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

    rows = build_ibkr_readonly_preflight_profile_aware_final_gate_rows(config_path)
    final = rows[-1]

    assert final.selected_profile == "paper"
    assert final.gate_status == PASS_GATE_TEXT
    assert final.final_gate_decision == GO_TEXT
    assert final.go_allowed == "true"


def test_profile_aware_final_gate_no_go_when_live_switches_missing(tmp_path):
    config_path = tmp_path / "live_missing_switches.yaml"
    config_path.write_text(
        """
ibkr:
  read_only_required: true
  account_mode: live
  host: 127.0.0.1
  port: 7496
  client_id: 1
""".strip(),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_preflight_profile_aware_final_gate_rows(config_path)
    final = rows[-1]

    assert final.selected_profile == "live-readonly"
    assert final.gate_status == FAIL_GATE_TEXT
    assert final.final_gate_decision == NO_GO_TEXT
    assert final.go_allowed == "false"
    assert final.config_ready == "false"
    assert final.profile_plan_clear == "false"
    assert "add=" in final.evidence


def test_profile_aware_final_gate_no_go_when_explicit_paper_requested_for_live_config(tmp_path):
    config_path = tmp_path / "live.yaml"
    config_path.write_text(
        """
ibkr:
  read_only_required: true
  account_mode: live
  host: 127.0.0.1
  port: 7496
  client_id: 1
  real_connection_allowed: false
  contract_qualification_allowed: false
  market_data_request_allowed: false
  historical_data_request_allowed: false
  trading_actions_allowed: false
""".strip(),
        encoding="utf-8",
    )

    rows = build_ibkr_readonly_preflight_profile_aware_final_gate_rows(config_path, "paper")
    final = rows[-1]

    assert final.selected_profile == "paper"
    assert final.final_gate_decision == NO_GO_TEXT
    assert final.profile_plan_clear == "false"
    assert "review_update=" in final.evidence


def test_profile_aware_final_gate_no_go_when_input_source_missing(tmp_path):
    missing_path = tmp_path / "missing.yaml"

    rows = build_ibkr_readonly_preflight_profile_aware_final_gate_rows(missing_path)
    final = rows[-1]

    assert final.final_gate_decision == NO_GO_TEXT
    assert final.gate_status == FAIL_GATE_TEXT
    assert final.go_allowed == "false"
    assert final.config_ready == "false"
    assert final.profile_plan_clear == "false"


def test_write_profile_aware_final_gate_csv_and_report(tmp_path):
    rows = [
        ProfileAwareFinalGateRow(
            gate_id="FINAL",
            gate_name="Final IBKR read-only profile-aware preflight gate decision",
            source_layer="Phase 14I",
            input_source="config.yaml",
            requested_profile="auto",
            selected_profile="live-readonly",
            profile_source="auto_detected",
            upstream_stage="Phase 14I",
            upstream_status="PASS",
            evidence="selected_profile=live-readonly;config_ready=true;profile_plan_clear=true",
            gate_status="PASS",
            final_gate_decision="GO",
            go_allowed="true",
            config_ready="true",
            profile_plan_clear="true",
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
            warning_flags="PROFILE_AWARE_FINAL_GATE_DEFINED;PHASE14I_PROFILE_AWARE_FINAL_GATE_GO",
            notes="Profile-aware final gate only.",
            timestamp_jst="2026-05-19T23:30:00+09:00",
            timestamp_et="2026-05-19T10:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "profile_final_gate.csv"
    md_path = tmp_path / "profile_final_gate.md"

    write_ibkr_readonly_preflight_profile_aware_final_gate_csv(csv_path, rows)
    write_ibkr_readonly_preflight_profile_aware_final_gate_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["gate_id"] == "FINAL"
    assert csv_rows[0]["selected_profile"] == "live-readonly"
    assert csv_rows[0]["final_gate_decision"] == "GO"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 14I IBKR Read-Only Preflight Profile-Aware Final Gate Report" in report
    assert "selected_profile: live-readonly" in report
    assert "final_gate_decision: GO" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report
