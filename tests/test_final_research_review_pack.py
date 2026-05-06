from pathlib import Path

from src.final_research_review_pack import (
    build_final_research_review_pack_rows,
    load_csv_by_key,
    write_final_research_review_pack_csv,
    write_final_research_review_pack_report,
)


TZ = {"jst": "Asia/Tokyo", "et": "America/New_York"}


def test_build_final_research_review_pack_rows_neutral():
    trading_rows = {
        "1540.T": {
            "plan_status": "neutral_range_trade_reference",
            "action_allowed": "false",
            "lot_size": "100",
            "actual_price": "36425.0",
            "theoretical_price": "36425.000000",
            "deviation_pct": "0.000000",
            "currency": "JPY",
            "today_buy_reference_zone": "36316-36389 JPY",
            "today_sell_reference_zone": "36461-36571 JPY",
            "rolling_t_buy_reference_zone": "36279-36352 JPY",
            "rolling_t_sell_reference_zone": "36498-36607 JPY",
            "short_term_plan": "short",
            "medium_term_plan": "medium",
            "long_term_plan": "long",
            "stop_loss_trigger": "stop",
            "take_profit_trigger": "take",
            "time_trigger": "JST 15:25-15:30 close-auction check",
            "confidence": "low",
            "source_quality": "low",
            "warning_flags": "phase8a_research_plan",
            "notes": "sample",
        }
    }

    rows = build_final_research_review_pack_rows(trading_rows, TZ)
    row = rows[0]

    assert row.etf_symbol == "1540.T"
    assert row.final_review_label == "neutral_final_reference"
    assert row.action_allowed == "false"
    assert row.lot_size == "100"
    assert "phase8d_final_review_pack" in row.warning_flags


def test_build_final_research_review_pack_rows_closed():
    trading_rows = {
        "1542.T": {
            "plan_status": "closed_data_invalid",
            "actual_price": "unavailable",
            "theoretical_price": "unavailable",
            "deviation_pct": "unavailable",
            "currency": "JPY",
            "warning_flags": "unavailable",
        }
    }

    rows = build_final_research_review_pack_rows(trading_rows, TZ)
    row = rows[0]

    assert row.final_review_label == "closed_review_only"
    assert row.action_allowed == "false"
    assert row.today_buy_reference_zone == "closed"


def test_final_research_review_pack_load_and_writers(tmp_path: Path):
    input_csv = tmp_path / "research_trading_plan.csv"
    input_csv.write_text(
        "etf_symbol,plan_status,action_allowed,lot_size,actual_price,theoretical_price,deviation_pct,currency,today_buy_reference_zone,today_sell_reference_zone,rolling_t_buy_reference_zone,rolling_t_sell_reference_zone,short_term_plan,medium_term_plan,long_term_plan,stop_loss_trigger,take_profit_trigger,time_trigger,confidence,source_quality,warning_flags,notes\n"
        "518880.SH,neutral_range_trade_reference,false,100,5.2,5.200000,0.000000,CNY,5.1844-5.1948 CNY,5.2052-5.2208 CNY,5.1792-5.1896 CNY,5.2104-5.2260 CNY,short,medium,long,stop,take,CST close,low,low,phase8a_research_plan,sample\n",
        encoding="utf-8",
    )

    loaded = load_csv_by_key(str(input_csv), "etf_symbol")
    rows = build_final_research_review_pack_rows(loaded, TZ)

    csv_path = tmp_path / "final_research_review_pack.csv"
    md_path = tmp_path / "final_research_review_pack_report.md"

    write_final_research_review_pack_csv(csv_path, rows)
    write_final_research_review_pack_report(
        md_path,
        rows,
        "data/manual_market_data_sample_valid.csv",
        "manual_research_trading_pipeline_summary.csv",
        str(input_csv),
    )

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "final_review_label" in csv_text
    assert "Phase 8D Final Research Review Pack" in md_text
    assert "action_allowed=false" in md_text
    assert "no IBKR connection" in md_text
    assert "no auto trade" in md_text
