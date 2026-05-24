from pathlib import Path
import csv

from src.research_trading_plan import (
    ACTION_FIELDS,
    FORBIDDEN_ACTION_WORDS,
    build_research_trading_plan,
    write_markdown_report,
    write_plan_csv,
)


def _write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _latest_rows():
    return [
        {
            "display_symbol": "GLD",
            "symbol": "GLD",
            "reference_price": "",
            "price_status": "no_price",
            "data_delay_flag": "delayed",
            "effective_market_data_type": "delayed",
            "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE",
            "api_error_codes": "10089",
            "operator_status": "OPERATOR_REVIEW_BLOCKED",
            "recommended_operator_action": "NO_PRICE_REVIEW_BLOCKED",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
            "telegram_send_triggered": "false",
        },
        {
            "display_symbol": "SLV",
            "symbol": "SLV",
            "reference_price": "68.31",
            "price_status": "usable_price",
            "data_delay_flag": "delayed",
            "effective_market_data_type": "delayed",
            "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE",
            "api_error_codes": "10089",
            "operator_status": "OPERATOR_REVIEW_READY",
            "recommended_operator_action": "MANUAL_REFERENCE_REVIEW_ONLY",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
            "telegram_send_triggered": "false",
        },
    ]


def test_gld_no_price_and_slv_delayed_reference_fixture(tmp_path: Path):
    _write_csv(tmp_path / "latest_daily_operator_handoff_summary.csv", _latest_rows())
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "latest_operator_handoff_summary.md").write_text("reference only\n", encoding="utf-8")
    (tmp_path / "latest_run_manifest.csv").write_text("artifact_path,artifact_status\n", encoding="utf-8")

    top_status, rows, source = build_research_trading_plan(tmp_path)

    by_symbol = {row.display_symbol: row for row in rows}
    assert source.startswith("latest_daily_operator_handoff_summary.csv")
    assert top_status == "RESEARCH_PLAN_REFERENCE_READY"
    assert by_symbol["GLD"].research_plan_status == "NO_PRICE_PLAN_BLOCKED"
    assert by_symbol["GLD"].manual_observation_bias == "NO_PRICE_BLOCKED"
    assert by_symbol["SLV"].research_plan_status == "REFERENCE_ONLY_PLAN_READY"
    assert by_symbol["SLV"].manual_observation_bias == "REFERENCE_ONLY"
    assert by_symbol["SLV"].market_context_label == "DELAYED_REFERENCE_ONLY"


def test_delayed_reference_plan_has_no_forbidden_action_wording(tmp_path: Path):
    _write_csv(tmp_path / "latest_daily_operator_handoff_summary.csv", _latest_rows())
    _, rows, _ = build_research_trading_plan(tmp_path)

    for row in rows:
        for field in ACTION_FIELDS:
            value = getattr(row, field).upper()
            assert not any(word in value for word in FORBIDDEN_ACTION_WORDS), (field, value)


def test_all_safety_fields_remain_false_for_fixture(tmp_path: Path):
    _write_csv(tmp_path / "latest_daily_operator_handoff_summary.csv", _latest_rows())
    _, rows, _ = build_research_trading_plan(tmp_path)

    for row in rows:
        assert row.action_allowed == "false"
        assert row.broker_execution_triggered == "false"
        assert row.historical_data_request_triggered == "false"
        assert row.account_read_triggered == "false"
        assert row.position_read_triggered == "false"
        assert row.telegram_send_triggered == "false"


def test_missing_latest_artifacts_fail_gracefully_blocked(tmp_path: Path):
    top_status, rows, source = build_research_trading_plan(tmp_path)

    assert top_status == "RESEARCH_PLAN_BLOCKED"
    assert source == "missing_operator_artifacts:missing"
    assert {row.display_symbol for row in rows} == {"GLD", "SLV"}
    assert all(row.research_plan_status == "NO_PRICE_PLAN_BLOCKED" for row in rows)
    assert all(row.action_allowed == "false" for row in rows)


def test_fallback_daily_handoff_when_latest_missing(tmp_path: Path):
    _write_csv(tmp_path / "daily_operator_handoff_summary.csv", _latest_rows())

    top_status, rows, source = build_research_trading_plan(tmp_path)

    assert source.startswith("daily_operator_handoff_summary.csv")
    assert top_status == "RESEARCH_PLAN_REFERENCE_READY"
    assert {row.display_symbol for row in rows} == {"GLD", "SLV"}


def test_writers_emit_required_outputs(tmp_path: Path):
    _write_csv(tmp_path / "latest_daily_operator_handoff_summary.csv", _latest_rows())
    top_status, rows, source = build_research_trading_plan(tmp_path)
    csv_path = tmp_path / "research_trading_plan.csv"
    report_path = tmp_path / "reports" / "research_trading_plan_report.md"

    write_plan_csv(csv_path, rows)
    write_markdown_report(report_path, top_status, rows, source)

    csv_rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
    report = report_path.read_text(encoding="utf-8")
    assert csv_rows[0]["plan_run_id"]
    assert "top_level_status=RESEARCH_PLAN_REFERENCE_READY" in report
    assert "Safety Summary" in report
