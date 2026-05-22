from pathlib import Path
import subprocess

from src.ibkr_final_research_review_pack import build_final_review_row


def _row(**overrides):
    row = {
        "display_symbol": "1540.T",
        "review_status": "REVIEW_READY",
        "decision_label": "REFERENCE_ONLY",
        "data_quality_tier": "tier_1_real_time_or_live",
        "research_usage": "reference_only",
        "usable_reference_price": "100",
        "usable_reference_price_field": "market_price",
        "action_allowed": "false",
        "manual_review_required": "true",
        "safety_flags": "",
    }
    row.update(overrides)
    return row


def test_review_ready_reference_only_maps_to_final_review_ready():
    result = build_final_review_row(_row())
    assert result.final_review_status == "FINAL_REVIEW_READY"
    assert result.final_decision_label == "REFERENCE_ONLY_REVIEW"


def test_review_blocked_maps_to_final_review_blocked():
    result = build_final_review_row(_row(review_status="REVIEW_BLOCKED", decision_label="NO_GO"))
    assert result.final_review_status == "FINAL_REVIEW_BLOCKED"
    assert result.final_decision_label == "BLOCKED"


def test_no_price_maps_to_no_price_bucket():
    result = build_final_review_row(_row(review_status="REVIEW_BLOCKED", decision_label="NO_PRICE"))
    assert result.final_research_bucket == "no_price"


def test_unsupported_maps_to_unsupported_bucket():
    result = build_final_review_row(_row(review_status="REVIEW_BLOCKED", decision_label="UNSUPPORTED"))
    assert result.final_research_bucket == "unsupported"


def test_no_go_maps_to_no_go_bucket():
    result = build_final_review_row(_row(review_status="REVIEW_BLOCKED", decision_label="NO_GO"))
    assert result.final_research_bucket == "no_go"


def test_tier_2_delayed_maps_to_delayed_reference_bucket():
    result = build_final_review_row(_row(data_quality_tier="tier_2_delayed"))
    assert result.final_research_bucket == "delayed_reference"
    assert result.next_step == "operator_manual_review_delayed_reference"


def test_tier_3_delayed_frozen_maps_to_stale_reference_bucket():
    result = build_final_review_row(_row(data_quality_tier="tier_3_delayed_frozen"))
    assert result.final_research_bucket == "stale_reference"
    assert result.next_step == "operator_manual_review_stale_reference"


def test_action_allowed_non_false_maps_to_safety_rejected():
    result = build_final_review_row(_row(action_allowed="true"))
    assert result.final_review_status == "SAFETY_REJECTED"
    assert result.final_decision_label == "NO_ACTION"
    assert result.action_allowed == "false"


def test_all_outputs_force_action_allowed_false():
    rows = [
        _row(),
        _row(review_status="REVIEW_BLOCKED", decision_label="NO_PRICE"),
        _row(review_status="REVIEW_BLOCKED", decision_label="UNSUPPORTED"),
        _row(review_status="REVIEW_BLOCKED", decision_label="NO_GO"),
        _row(action_allowed="true"),
    ]
    assert all(build_final_review_row(row).action_allowed == "false" for row in rows)


def test_safety_fields_all_false_and_manual_review_true():
    result = build_final_review_row(_row())
    assert result.broker_execution_triggered == "false"
    assert result.historical_data_request_triggered == "false"
    assert result.account_read_triggered == "false"
    assert result.position_read_triggered == "false"
    assert result.manual_review_required == "true"


def test_missing_input_file_script_generates_no_go(tmp_path: Path):
    missing = tmp_path / "missing_review_pack.csv"
    result = subprocess.run(
        [
            "bash",
            "scripts/ibkr_final_research_review_pack.sh",
            f"--review-pack={missing}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "review_pack_input_status=missing" in result.stdout
    assert "final_research_review_status=NO_GO" in result.stdout
    assert "action_allowed=false" in result.stdout

    csv_text = Path("ibkr_final_research_review_pack.csv").read_text(encoding="utf-8")
    report_text = Path("reports/ibkr_final_research_review_pack_report.md").read_text(encoding="utf-8")
    assert "FINAL_REVIEW_BLOCKED" in csv_text
    assert "Final Research Review Decision" in report_text
    assert "Research Bucket Summary" in report_text
