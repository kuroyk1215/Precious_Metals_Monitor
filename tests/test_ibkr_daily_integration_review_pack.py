from pathlib import Path
import subprocess

from src.ibkr_daily_integration_review_pack import (
    build_review_row,
    summarize_data_quality_tiers,
)


def _row(**overrides):
    row = {
        "display_symbol": "1540.T",
        "integration_status": "READY_REFERENCE_ONLY",
        "data_quality_tier": "tier_1_real_time_or_live",
        "research_usage": "reference_only",
        "usable_reference_price": "100",
        "usable_reference_price_field": "market_price",
        "action_allowed": "false",
        "manual_review_required": "true",
        "safety_flags": "",
        "data_delay_flag": "real_time",
        "input_snapshot_status": "SNAPSHOT_RETURNED",
        "reject_reason": "",
    }
    row.update(overrides)
    return row


def test_ready_reference_only_maps_to_review_ready_reference_only():
    result = build_review_row(_row())
    assert result.review_status == "REVIEW_READY"
    assert result.decision_label == "REFERENCE_ONLY"
    assert result.action_allowed == "false"


def test_ready_delayed_reference_only_uses_delayed_next_step():
    result = build_review_row(
        _row(
            integration_status="READY_DELAYED_REFERENCE_ONLY",
            data_quality_tier="tier_2_delayed",
            data_delay_flag="delayed",
        )
    )
    assert result.review_status == "REVIEW_READY"
    assert result.decision_label == "REFERENCE_ONLY"
    assert result.next_step == "manual_review_delayed_reference"


def test_ready_delayed_frozen_reference_only_uses_stale_next_step():
    result = build_review_row(
        _row(
            integration_status="READY_DELAYED_FROZEN_REFERENCE_ONLY",
            data_quality_tier="tier_3_delayed_frozen",
            data_delay_flag="delayed_frozen",
        )
    )
    assert result.review_status == "REVIEW_READY"
    assert result.decision_label == "REFERENCE_ONLY"
    assert result.next_step == "manual_review_stale_reference"


def test_empty_price_maps_to_review_blocked_no_price():
    result = build_review_row(_row(integration_status="EMPTY_PRICE", data_quality_tier="tier_9_unavailable"))
    assert result.review_status == "REVIEW_BLOCKED"
    assert result.decision_label == "NO_PRICE"


def test_unsupported_maps_to_review_blocked_unsupported():
    result = build_review_row(_row(integration_status="UNSUPPORTED", data_quality_tier="tier_9_unavailable"))
    assert result.review_status == "REVIEW_BLOCKED"
    assert result.decision_label == "UNSUPPORTED"


def test_missing_input_maps_to_review_blocked_no_go():
    result = build_review_row(_row(integration_status="MISSING_INPUT", data_quality_tier="tier_9_unavailable"))
    assert result.review_status == "REVIEW_BLOCKED"
    assert result.decision_label == "NO_GO"


def test_action_allowed_non_false_maps_to_safety_rejected():
    result = build_review_row(_row(action_allowed="true"))
    assert result.review_status == "SAFETY_REJECTED"
    assert result.decision_label == "NO_ACTION"
    assert result.action_allowed == "false"


def test_all_outputs_force_action_allowed_false():
    statuses = [
        "READY_REFERENCE_ONLY",
        "READY_DELAYED_REFERENCE_ONLY",
        "READY_DELAYED_FROZEN_REFERENCE_ONLY",
        "EMPTY_PRICE",
        "UNSUPPORTED",
        "MISSING_INPUT",
        "NO_GO",
    ]
    assert all(build_review_row(_row(integration_status=status)).action_allowed == "false" for status in statuses)


def test_data_quality_tier_summary_outputs_counts():
    rows = [
        build_review_row(_row(data_quality_tier="tier_1_real_time_or_live")),
        build_review_row(_row(data_quality_tier="tier_2_delayed")),
        build_review_row(_row(data_quality_tier="tier_2_delayed")),
    ]
    assert summarize_data_quality_tiers(rows) == {
        "tier_1_real_time_or_live": 1,
        "tier_2_delayed": 2,
    }


def test_missing_input_file_script_generates_no_go(tmp_path: Path):
    missing = tmp_path / "missing_daily_integration.csv"
    result = subprocess.run(
        [
            "bash",
            "scripts/ibkr_daily_integration_review_pack.sh",
            f"--daily-integration={missing}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "daily_integration_input_status=missing" in result.stdout
    assert "review_pack_status=NO_GO" in result.stdout
    assert "action_allowed=false" in result.stdout

    csv_text = Path("ibkr_daily_integration_review_pack.csv").read_text(encoding="utf-8")
    report_text = Path("reports/ibkr_daily_integration_review_pack_report.md").read_text(encoding="utf-8")
    assert "MISSING_INPUT" in csv_text
    assert "Review Pack Decision" in report_text
    assert "Data Quality Tier Summary" in report_text
