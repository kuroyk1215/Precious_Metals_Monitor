from pathlib import Path
import subprocess

from src.ibkr_daily_operator_packet import build_operator_packet_row


def _row(**overrides):
    row = {
        "display_symbol": "1540.T",
        "final_review_status": "FINAL_REVIEW_READY",
        "final_decision_label": "REFERENCE_ONLY_REVIEW",
        "final_research_bucket": "reference_only",
        "usable_reference_price": "100",
        "usable_reference_price_field": "market_price",
        "operator_action_required": "true",
        "manual_review_required": "true",
        "action_allowed": "false",
        "broker_execution_triggered": "false",
        "historical_data_request_triggered": "false",
        "account_read_triggered": "false",
        "position_read_triggered": "false",
        "safety_flags": "",
    }
    row.update(overrides)
    return row


def test_final_review_ready_maps_to_operator_review_ready():
    result = build_operator_packet_row(_row())
    assert result.operator_packet_status == "OPERATOR_REVIEW_READY"
    assert result.operator_instruction == "manual_review_reference_only"


def test_final_review_blocked_maps_to_operator_review_blocked():
    result = build_operator_packet_row(_row(final_review_status="FINAL_REVIEW_BLOCKED"))
    assert result.operator_packet_status == "OPERATOR_REVIEW_BLOCKED"
    assert result.operator_instruction == "no_action_review_blocked"


def test_safety_rejected_maps_to_safety_rejected():
    result = build_operator_packet_row(_row(final_review_status="SAFETY_REJECTED"))
    assert result.operator_packet_status == "SAFETY_REJECTED"
    assert result.operator_instruction == "no_action_safety_rejected"


def test_delayed_reference_next_step():
    result = build_operator_packet_row(_row(final_research_bucket="delayed_reference"))
    assert result.next_step == "operator_compare_with_manual_market_context"


def test_stale_reference_next_step():
    result = build_operator_packet_row(_row(final_research_bucket="stale_reference"))
    assert result.next_step == "operator_verify_market_open_or_latest_quote"


def test_unavailable_buckets_have_no_operator_action():
    for bucket in ("no_price", "unsupported", "no_go"):
        result = build_operator_packet_row(_row(final_research_bucket=bucket))
        assert result.next_step == "no_operator_action"


def test_all_outputs_force_action_allowed_false():
    rows = [
        _row(),
        _row(final_review_status="FINAL_REVIEW_BLOCKED"),
        _row(final_review_status="SAFETY_REJECTED"),
        _row(action_allowed="true"),
    ]
    assert all(build_operator_packet_row(row).action_allowed == "false" for row in rows)


def test_safety_fields_are_false():
    result = build_operator_packet_row(_row())
    assert result.broker_execution_triggered == "false"
    assert result.historical_data_request_triggered == "false"
    assert result.account_read_triggered == "false"
    assert result.position_read_triggered == "false"
    assert result.manual_review_required == "true"


def test_missing_input_final_pack_script_generates_no_go(tmp_path: Path):
    missing = tmp_path / "missing_final_pack.csv"
    result = subprocess.run(
        [
            "bash",
            "scripts/ibkr_daily_operator_packet.sh",
            f"--final-pack={missing}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "final_pack_input_status=missing" in result.stdout
    assert "operator_packet_status=NO_GO" in result.stdout
    assert "action_allowed=false" in result.stdout

    csv_text = Path("ibkr_daily_operator_packet.csv").read_text(encoding="utf-8")
    report_text = Path("reports/ibkr_daily_operator_packet_report.md").read_text(encoding="utf-8")
    assert "OPERATOR_REVIEW_BLOCKED" in csv_text
    assert "Operator Packet Decision" in report_text
    assert "Safety Confirmation" in report_text
