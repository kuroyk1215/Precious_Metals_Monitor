from __future__ import annotations

import csv
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from src.batch1_gld_slv_core_research_loop import CSV_FIELDS, generate_batch1_research_loop


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "batch1_gld_slv_core_research_loop.sh"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_quotes(path: Path, body: str) -> None:
    path.write_text(
        "generated_at,symbol,asset_class,market,currency,quote_source,quote_status,data_status,connection_succeeded,market_data_request_triggered,snapshot_rows_detected,last_price,bid,ask,close,quote_time,staleness_status,normalized_status,diagnostic_category,diagnostic_reason,operator_next_step\n"
        + body,
        encoding="utf-8",
    )


def _rating_rank(rating: str) -> int:
    return {"NO_TRADE": 0, "WATCH": 1, "C": 2, "B": 3, "A": 4}[rating]


def test_no_price_blocks_action_and_waits_for_valid_quote(tmp_path: Path):
    quote_csv = tmp_path / "quotes.csv"
    _write_quotes(
        quote_csv,
        "2026-06-03T00:00:00+00:00,GLD,ETF,US,USD,ibkr,UNAVAILABLE,REAL_QUOTE_UNAVAILABLE,false,false,0,,,,,,UNKNOWN_NO_REAL_QUOTE,SAFE_UNAVAILABLE,PERMISSION_OR_CONNECTION_FAILURE,no quote,review\n"
        "2026-06-03T00:00:00+00:00,SLV,ETF,US,USD,ibkr,AVAILABLE,REAL_TIME,true,true,1,27.25,,,,2026-06-02T20:00:00-04:00,FRESH,NORMALIZED,PASS,ok,review\n",
    )

    rows = generate_batch1_research_loop(
        quote_csv=quote_csv,
        output_report=tmp_path / "latest.md",
        output_csv=tmp_path / "research.csv",
        generated_at=datetime(2026, 6, 3, tzinfo=timezone.utc),
    )

    gld = next(row for row in rows if row["symbol"] == "GLD")
    assert gld["data_delay_flag"] == "no_price"
    assert gld["confidence"] == "low"
    assert gld["action_rating"] == "NO_TRADE"
    assert gld["action_allowed"] == "false"
    assert gld["result"] == "不交易，等待有效报价"
    assert "等待有效报价" in gld["signal"]
    assert set(_read_rows(tmp_path / "research.csv")[0]) == set(CSV_FIELDS)


def test_delayed_quote_allows_only_low_confidence_observation(tmp_path: Path):
    quote_csv = tmp_path / "quotes.csv"
    _write_quotes(
        quote_csv,
        "2026-06-03T00:00:00+00:00,GLD,ETF,US,USD,ibkr,AVAILABLE,DELAYED,true,true,1,289.10,,,,2026-06-02T20:00:00-04:00,DELAYED,NORMALIZED,PASS,delayed quote,review\n"
        "2026-06-03T00:00:00+00:00,SLV,ETF,US,USD,ibkr,AVAILABLE,DELAYED,true,true,1,27.25,,,,2026-06-02T20:00:00-04:00,DELAYED,NORMALIZED,PASS,delayed quote,review\n",
    )

    rows = generate_batch1_research_loop(
        quote_csv=quote_csv,
        output_report=tmp_path / "latest.md",
        output_csv=tmp_path / "research.csv",
        generated_at=datetime(2026, 6, 3, tzinfo=timezone.utc),
    )

    assert {row["data_delay_flag"] for row in rows} == {"delayed"}
    assert {row["confidence"] for row in rows} == {"low"}
    assert {row["action_allowed"] for row in rows} == {"true"}
    assert {row["action_rating"] for row in rows}.issubset({"WATCH", "C"})
    assert "A" not in {row["action_rating"] for row in rows}
    assert all("低置信" in row["signal"] for row in rows)
    assert all("delayed 数据只支持观察" in row["position_unit_note"] for row in rows)


def test_frozen_quote_is_reference_only(tmp_path: Path):
    quote_csv = tmp_path / "quotes.csv"
    _write_quotes(
        quote_csv,
        "2026-06-03T00:00:00+00:00,GLD,ETF,US,USD,ibkr,AVAILABLE,FROZEN,true,true,1,289.10,,,,2026-06-02T20:00:00-04:00,FROZEN,NORMALIZED,PASS,frozen quote,review\n"
        "2026-06-03T00:00:00+00:00,SLV,ETF,US,USD,ibkr,AVAILABLE,FROZEN,true,true,1,27.25,,,,2026-06-02T20:00:00-04:00,FROZEN,NORMALIZED,PASS,frozen quote,review\n",
    )

    rows = generate_batch1_research_loop(
        quote_csv=quote_csv,
        output_report=tmp_path / "latest.md",
        output_csv=tmp_path / "research.csv",
        generated_at=datetime(2026, 6, 3, tzinfo=timezone.utc),
    )

    assert {row["data_delay_flag"] for row in rows} == {"frozen"}
    assert {row["action_allowed"] for row in rows} == {"false"}
    assert {row["action_rating"] for row in rows}.issubset({"WATCH", "NO_TRADE"})
    assert all(row["result"] == "仅参考" for row in rows)


def test_source_conflict_downgrades_and_names_conflict_sources(tmp_path: Path):
    quote_csv = tmp_path / "quotes.csv"
    _write_quotes(
        quote_csv,
        "2026-06-03T00:00:00+00:00,GLD,ETF,US,USD,source_a,AVAILABLE,REAL_TIME,true,true,1,289.10,,,,2026-06-02T20:00:00-04:00,FRESH,NORMALIZED,PASS,ok,review\n"
        "2026-06-03T00:01:00+00:00,GLD,ETF,US,USD,source_b,AVAILABLE,DELAYED,true,true,1,291.40,,,,2026-06-02T20:01:00-04:00,DELAYED,NORMALIZED,PASS,other source,review\n"
        "2026-06-03T00:00:00+00:00,SLV,ETF,US,USD,source_a,AVAILABLE,REAL_TIME,true,true,1,27.25,,,,2026-06-02T20:00:00-04:00,FRESH,NORMALIZED,PASS,ok,review\n",
    )

    rows = generate_batch1_research_loop(
        quote_csv=quote_csv,
        output_report=tmp_path / "latest.md",
        output_csv=tmp_path / "research.csv",
        generated_at=datetime(2026, 6, 3, tzinfo=timezone.utc),
    )

    gld = next(row for row in rows if row["symbol"] == "GLD")
    assert gld["data_delay_flag"] == "source_conflict"
    assert gld["confidence"] == "low"
    assert _rating_rank(gld["action_rating"]) <= _rating_rank("WATCH")
    assert gld["action_allowed"] == "false"
    assert "source_a" in gld["notes"]
    assert "source_b" in gld["notes"]
    assert "冲突" in gld["signal"]


def test_report_contains_required_sections_and_cash_account_warnings(tmp_path: Path):
    quote_csv = tmp_path / "quotes.csv"
    _write_quotes(
        quote_csv,
        "2026-06-03T00:00:00+00:00,GLD,ETF,US,USD,ibkr,AVAILABLE,REAL_TIME,true,true,1,289.10,,,,2026-06-02T20:00:00-04:00,FRESH,NORMALIZED,PASS,ok,review\n"
        "2026-06-03T00:00:00+00:00,SLV,ETF,US,USD,ibkr,AVAILABLE,REAL_TIME,true,true,1,27.25,,,,2026-06-02T20:00:00-04:00,FRESH,NORMALIZED,PASS,ok,review\n",
    )
    report = tmp_path / "latest.md"

    rows = generate_batch1_research_loop(
        quote_csv=quote_csv,
        output_report=report,
        output_csv=tmp_path / "research.csv",
        generated_at=datetime(2026, 6, 3, tzinfo=timezone.utc),
    )

    assert {row["data_delay_flag"] for row in rows} == {"real_time"}
    assert {row["confidence"] for row in rows} == {"high"}
    assert {row["action_rating"] for row in rows}.issubset({"A", "B", "C"})
    assert {row["action_allowed"] for row in rows} == {"true"}
    text = report.read_text(encoding="utf-8")
    for section in (
        "今日执行摘要",
        "GLD 策略表",
        "SLV 策略表",
        "数据质量说明",
        "一致预期",
        "实时数据",
        "既有认知",
        "短期策略：1-5 个交易日",
        "中期策略：2-8 周",
        "长期策略：3-12 个月",
        "今日买点",
        "今日卖点",
        "止损/失效位",
        "IBKR现金账户约束",
        "settled cash",
        "GFV / freeriding",
        "US_30mEcho 时间窗口",
        "10:00 ET",
        "14:30 ET",
        "15:10 ET",
        "15:50 ET",
        "JST",
        "风险与退出触发",
        "一致性对账单",
    ):
        assert section in text


def test_wrapper_generates_required_default_outputs(tmp_path: Path):
    quote_csv = tmp_path / "quotes.csv"
    _write_quotes(
        quote_csv,
        "2026-06-03T00:00:00+00:00,GLD,ETF,US,USD,ibkr,AVAILABLE,REAL_TIME,true,true,1,289.10,,,,2026-06-02T20:00:00-04:00,FRESH,NORMALIZED,PASS,ok,review\n"
        "2026-06-03T00:00:00+00:00,SLV,ETF,US,USD,ibkr,AVAILABLE,DELAYED,true,true,1,27.25,,,,2026-06-02T20:00:00-04:00,DELAYED,NORMALIZED,PASS,delayed,review\n",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", "python3")

    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--quote-csv",
            str(quote_csv),
            "--output-report",
            str(tmp_path / "reports/latest_gld_slv_research.md"),
            "--output-csv",
            str(tmp_path / "logs/research_log_US.csv"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert (tmp_path / "reports/latest_gld_slv_research.md").exists()
    assert (tmp_path / "logs/research_log_US.csv").exists()


def test_csv_header_contains_batch2_strategy_risk_fields(tmp_path: Path):
    quote_csv = tmp_path / "quotes.csv"
    _write_quotes(
        quote_csv,
        "2026-06-03T00:00:00+00:00,GLD,ETF,US,USD,ibkr,AVAILABLE,REAL_TIME,true,true,1,289.10,,,,2026-06-02T20:00:00-04:00,FRESH,NORMALIZED,PASS,ok,review\n"
        "2026-06-03T00:00:00+00:00,SLV,ETF,US,USD,ibkr,AVAILABLE,REAL_TIME,true,true,1,27.25,,,,2026-06-02T20:00:00-04:00,FRESH,NORMALIZED,PASS,ok,review\n",
    )

    generate_batch1_research_loop(
        quote_csv=quote_csv,
        output_report=tmp_path / "latest.md",
        output_csv=tmp_path / "research.csv",
        generated_at=datetime(2026, 6, 3, tzinfo=timezone.utc),
    )

    rows = _read_rows(tmp_path / "research.csv")
    assert set(rows[0]) == set(CSV_FIELDS)
    for field in ("action_rating", "invalidation_level", "risk_pct"):
        assert field in rows[0]


def test_no_automatic_trading_api_names_in_batch1_files():
    files = [
        REPO_ROOT / "src" / "batch1_gld_slv_core_research_loop.py",
        REPO_ROOT / "scripts" / "batch1_gld_slv_core_research_loop.sh",
    ]
    forbidden = ["place" + "Order", "cancel" + "Order", "what" + "If" + "Order"]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert not any(term in text for term in forbidden), path
