from pathlib import Path

from src.research_trading_plan_generator import (
    build_research_trading_plan_rows,
    load_review_pack_by_symbol,
    write_research_trading_plan_csv,
    write_research_trading_plan_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_research_trading_plan_neutral_jp_lot_and_reference_zones():
    review_rows = {
        "1540.T": {
            "actual_price": "36425.0",
            "theoretical_price": "36425.000000",
            "deviation_pct": "0.000000",
            "currency": "JPY",
            "reference_label": "no_trade",
            "strategy_label": "neutral_range_framework",
            "action_allowed": "false",
            "confidence": "low",
            "source_quality": "low",
            "risk_flag": "none",
            "warning_flags": "manual_review_pack;action_allowed_false",
            "notes": "sample",
        }
    }

    rows = build_research_trading_plan_rows(review_rows, TZ)
    row = rows[0]

    assert row.etf_symbol == "1540.T"
    assert row.plan_status == "neutral_range_trade_reference"
    assert row.action_allowed == "false"
    assert row.lot_size == "100"
    assert "JPY" in row.today_buy_reference_zone
    assert "JPY" in row.today_sell_reference_zone
    assert "JST 12:32-13:00" in row.time_trigger
    assert "JST 15:25-15:30" in row.time_trigger
    assert "no automatic trade signal" in row.long_term_plan


def test_research_trading_plan_lower_side_jp_discount_reference():
    review_rows = {
        "1542.T": {
            "actual_price": "440.00",
            "theoretical_price": "445.00",
            "deviation_pct": "-0.011236",
            "currency": "JPY",
            "reference_label": "undervalued_watch",
            "strategy_label": "lower_side_range_framework",
            "action_allowed": "false",
            "confidence": "medium",
            "source_quality": "medium",
            "risk_flag": "none",
            "warning_flags": "manual_review_pack;action_allowed_false",
            "notes": "discount sample",
        }
    }

    rows = build_research_trading_plan_rows(review_rows, TZ)
    row = rows[0]

    assert row.etf_symbol == "1542.T"
    assert row.plan_status == "lower_side_trade_reference"
    assert row.lot_size == "100"
    assert "JPY" in row.rolling_t_buy_reference_zone
    assert "JPY" in row.rolling_t_sell_reference_zone
    assert "lower-side reference plan" in row.short_term_plan
    assert row.action_allowed == "false"


def test_research_trading_plan_upper_side_cn_premium_reference():
    review_rows = {
        "518880.SH": {
            "actual_price": "5.2500",
            "theoretical_price": "5.2000",
            "deviation_pct": "0.009615",
            "currency": "CNY",
            "reference_label": "overvalued_watch",
            "strategy_label": "upper_side_range_framework",
            "action_allowed": "false",
            "confidence": "medium",
            "source_quality": "medium",
            "risk_flag": "none",
            "warning_flags": "manual_review_pack;action_allowed_false",
            "notes": "premium sample",
        }
    }

    rows = build_research_trading_plan_rows(review_rows, TZ)
    row = rows[0]

    assert row.etf_symbol == "518880.SH"
    assert row.plan_status == "upper_side_trade_reference"
    assert row.lot_size == "100"
    assert "CNY" in row.today_buy_reference_zone
    assert "CNY" in row.today_sell_reference_zone
    assert "avoid new rolling-T entry" in row.rolling_t_buy_reference_zone
    assert "CST 14:50-15:00" in row.time_trigger
    assert row.action_allowed == "false"


def test_research_trading_plan_closed_when_data_invalid():
    review_rows = {
        "1540.T": {
            "actual_price": "unavailable",
            "theoretical_price": "36425.000000",
            "deviation_pct": "unavailable",
            "currency": "JPY",
            "reference_label": "data_invalid",
            "strategy_label": "no_strategy_data_invalid",
            "action_allowed": "false",
            "confidence": "low",
            "source_quality": "low",
            "risk_flag": "none",
            "warning_flags": "unavailable",
            "notes": "invalid sample",
        }
    }

    rows = build_research_trading_plan_rows(review_rows, TZ)
    row = rows[0]

    assert row.plan_status == "closed_data_invalid"
    assert row.today_buy_reference_zone == "closed"
    assert row.today_sell_reference_zone == "closed"
    assert row.rolling_t_buy_reference_zone == "closed"
    assert row.rolling_t_sell_reference_zone == "closed"
    assert row.stop_loss_trigger == "closed until data and risk flags normalize"
    assert row.take_profit_trigger == "closed until data and risk flags normalize"
    assert row.action_allowed == "false"


def test_research_trading_plan_closed_when_risk_flag_active():
    review_rows = {
        "GLD": {
            "actual_price": "250.00",
            "theoretical_price": "249.00",
            "deviation_pct": "0.004016",
            "currency": "USD",
            "reference_label": "risk_off",
            "strategy_label": "risk_review_only",
            "action_allowed": "false",
            "confidence": "low",
            "source_quality": "low",
            "risk_flag": "risk_off",
            "warning_flags": "risk_off",
            "notes": "risk sample",
        }
    }

    rows = build_research_trading_plan_rows(review_rows, TZ)
    row = rows[0]

    assert row.plan_status == "closed_data_invalid"
    assert row.lot_size == "1"
    assert row.today_buy_reference_zone == "closed"
    assert row.action_allowed == "false"


def test_research_trading_plan_load_and_writers(tmp_path: Path):
    input_csv = tmp_path / "manual_market_data_review_pack.csv"
    input_csv.write_text(
        "etf_symbol,actual_price,theoretical_price,deviation_pct,currency,reference_label,strategy_label,action_allowed,confidence,source_quality,risk_flag,warning_flags,notes,timestamp_jst,timestamp_et\n"
        "1540.T,36425.0,36425.000000,0.000000,JPY,no_trade,neutral_range_framework,false,low,low,none,manual_review_pack,sample,2026-05-06T16:00:00+09:00,2026-05-06T03:00:00-04:00\n",
        encoding="utf-8",
    )

    review_rows = load_review_pack_by_symbol(str(input_csv))
    rows = build_research_trading_plan_rows(review_rows, TZ)

    csv_path = tmp_path / "research_trading_plan.csv"
    md_path = tmp_path / "research_trading_plan_report.md"

    write_research_trading_plan_csv(csv_path, rows)
    write_research_trading_plan_report(md_path, rows, str(input_csv))

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "today_buy_reference_zone" in csv_text
    assert "rolling_t_sell_reference_zone" in csv_text
    assert "Phase 8A Research Trading Plan Report" in md_text
    assert "action_allowed=false" in md_text
    assert "no IBKR connection" in md_text
    assert "no auto trade" in md_text
