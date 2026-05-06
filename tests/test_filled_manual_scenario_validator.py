from pathlib import Path

from src.filled_manual_scenario_validator import (
    build_filled_manual_scenario_validation_rows,
    load_csv_rows,
    write_filled_manual_scenario_validation_csv,
    write_filled_manual_scenario_validation_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


class Step:
    def __init__(self, step_name: str, status: str):
        self.step_name = step_name
        self.status = status


def test_filled_manual_scenario_validation_pass(tmp_path: Path):
    input_csv = tmp_path / "sample.csv"
    input_csv.write_text("target_id,value\nXAUUSD,2350\n", encoding="utf-8")

    pipeline_steps = [
        Step("manual_market_data_adapter", "ok"),
        Step("manual_market_data_integration", "ok"),
        Step("theoretical_pricing", "ok"),
        Step("deviation_check", "ok"),
        Step("reference_signals", "partial"),
        Step("daily_trade_plan", "partial"),
        Step("strategy_plan", "partial"),
    ]
    deviation_rows = [{"deviation_status": "ok"}]
    reference_rows = [{"reference_label": "no_trade", "action_allowed": "false"}]
    daily_rows = [{"action_allowed": "false"}]
    strategy_rows = [{"action_allowed": "false"}]

    rows = build_filled_manual_scenario_validation_rows(
        str(input_csv),
        pipeline_steps,
        deviation_rows,
        reference_rows,
        daily_rows,
        strategy_rows,
        TZ,
    )

    assert rows
    assert all(r.status == "pass" for r in rows)


def test_filled_manual_scenario_validation_fail_on_risk():
    pipeline_steps = [
        Step("manual_market_data_adapter", "ok"),
        Step("manual_market_data_integration", "ok"),
        Step("theoretical_pricing", "ok"),
        Step("deviation_check", "ok"),
        Step("reference_signals", "risk_off"),
        Step("daily_trade_plan", "partial"),
        Step("strategy_plan", "partial"),
    ]
    rows = build_filled_manual_scenario_validation_rows(
        "missing.csv",
        pipeline_steps,
        [{"deviation_status": "ok"}],
        [{"reference_label": "risk_off", "action_allowed": "false"}],
        [{"action_allowed": "false"}],
        [{"action_allowed": "false"}],
        TZ,
    )

    by_check = {r.check_id: r for r in rows}
    assert by_check["input_csv_exists"].status == "fail"
    assert by_check["reference_signals_safe"].status == "fail"


def test_filled_manual_scenario_validation_writers(tmp_path: Path):
    rows = build_filled_manual_scenario_validation_rows(
        str(tmp_path / "missing.csv"),
        [],
        [],
        [],
        [],
        [],
        TZ,
    )

    csv_path = tmp_path / "filled_manual_scenario_validation.csv"
    md_path = tmp_path / "filled_manual_scenario_validation_report.md"

    write_filled_manual_scenario_validation_csv(csv_path, rows)
    write_filled_manual_scenario_validation_report(md_path, rows, "sample.csv")

    assert "check_id" in csv_path.read_text(encoding="utf-8")
    assert "Filled Manual CSV Scenario Validation Report" in md_path.read_text(encoding="utf-8")
    assert "no IBKR connection" in md_path.read_text(encoding="utf-8")


def test_load_csv_rows(tmp_path: Path):
    p = tmp_path / "rows.csv"
    p.write_text("a,b\n1,2\n", encoding="utf-8")
    rows = load_csv_rows(str(p))
    assert rows == [{"a": "1", "b": "2"}]
