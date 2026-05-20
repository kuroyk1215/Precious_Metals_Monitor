from __future__ import annotations

import csv

from src.ibkr_readonly_external_readiness_pack import (
    BLOCKED,
    FALSE_TEXT,
    READY_FOR_OPERATOR_REVIEW,
    ExternalReadinessPackRow,
    build_ibkr_readonly_external_readiness_pack_rows,
    write_ibkr_readonly_external_readiness_pack_csv,
    write_ibkr_readonly_external_readiness_pack_report,
)


def test_external_readiness_pack_ready_for_operator_review_with_complete_live_config(tmp_path):
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

    rows = build_ibkr_readonly_external_readiness_pack_rows(config_path)
    final = rows[-1]

    assert len(rows) == 5
    assert final.readiness_status == READY_FOR_OPERATOR_REVIEW
    assert final.selected_profile == "live-readonly"
    assert final.operator_review_required == "true"
    assert final.operator_approved == "false"
    assert final.next_connection_phase_allowed == "false"
    assert all(row.action_allowed == "false" for row in rows)
    assert all(row.real_connection_allowed == "false" for row in rows)
    assert all(row.tws_connection_allowed == "false" for row in rows)


def test_external_readiness_pack_blocked_when_preflight_not_go(tmp_path):
    config_path = tmp_path / "incomplete.yaml"
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

    rows = build_ibkr_readonly_external_readiness_pack_rows(config_path)
    final = rows[-1]

    assert final.readiness_status == BLOCKED
    assert final.operator_approved == "false"
    assert final.next_connection_phase_allowed == "false"


def test_external_readiness_pack_blocked_when_input_missing(tmp_path):
    rows = build_ibkr_readonly_external_readiness_pack_rows(tmp_path / "missing.yaml")
    final = rows[-1]

    assert final.readiness_status == BLOCKED
    assert final.next_connection_phase_allowed == FALSE_TEXT
    assert all(row.action_allowed == FALSE_TEXT for row in rows)


def test_write_external_readiness_pack_csv_and_report(tmp_path):
    rows = [
        ExternalReadinessPackRow(
            readiness_id="FINAL",
            readiness_name="Final external readiness pack decision",
            source_layer="Phase 15B-15D",
            input_source="config.yaml",
            selected_profile="live-readonly",
            upstream_component="Phase 15B-15D",
            upstream_status="READY_FOR_OPERATOR_REVIEW",
            readiness_status="READY_FOR_OPERATOR_REVIEW",
            operator_review_required="true",
            operator_approved="false",
            next_connection_phase_allowed="false",
            evidence="selected_profile=live-readonly;operator_approved=false",
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
            warning_flags="EXTERNAL_READINESS_PACK_DEFINED",
            notes="Readiness pack only.",
            timestamp_jst="2026-05-20T10:30:00+09:00",
            timestamp_et="2026-05-19T21:30:00-04:00",
        )
    ]

    csv_path = tmp_path / "readiness.csv"
    md_path = tmp_path / "readiness.md"

    write_ibkr_readonly_external_readiness_pack_csv(csv_path, rows)
    write_ibkr_readonly_external_readiness_pack_report(md_path, rows, "config.yaml")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    assert csv_rows[0]["readiness_id"] == "FINAL"
    assert csv_rows[0]["operator_approved"] == "false"
    assert csv_rows[0]["next_connection_phase_allowed"] == "false"
    assert csv_rows[0]["action_allowed"] == "false"

    report = md_path.read_text(encoding="utf-8")
    assert "Phase 15B-15D IBKR Read-Only External Readiness Pack Report" in report
    assert "selected_profile: live-readonly" in report
    assert "operator_approved_count: 0" in report
    assert "no TWS connection" in report
    assert "no reqMktData" in report
    assert "no auto trade" in report
