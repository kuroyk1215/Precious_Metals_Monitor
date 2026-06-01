from __future__ import annotations

from pathlib import Path

from src.local_research_report_builder import (
    build_research_report_framework_snapshot,
    generate_research_report_framework,
)


FORBIDDEN_REPORT_TERMS = (
    "BUY",
    "SELL",
    "HOLD",
    "买入",
    "卖出",
    "持有",
    "target_price",
    "stop_loss",
    "take_profit",
    "目标价",
    "止损",
    "止盈",
)


def test_research_report_framework_is_placeholder_only(tmp_path: Path) -> None:
    output = tmp_path / "reports/local_research_report_framework_GLD_SLV.md"
    snapshot = generate_research_report_framework(output_markdown=output, generated_at="2026-06-01T00:00:00+00:00")
    text = output.read_text(encoding="utf-8")

    assert snapshot["status"] == "RESEARCH_REPORT_FRAMEWORK_READY"
    assert snapshot["real_market_data_status"] == "NO_REAL_MARKET_DATA"
    assert snapshot["symbols"] == ["GLD", "SLV"]
    for term in FORBIDDEN_REPORT_TERMS:
        assert term not in text


def test_research_report_snapshot_supports_required_horizons() -> None:
    snapshot = build_research_report_framework_snapshot("2026-06-01T00:00:00+00:00")

    assert snapshot["horizons"] == ["INTRADAY", "SHORT_TERM", "MID_TERM", "LONG_TERM"]
    assert snapshot["directional_signal_enabled"] == "NO"
    assert snapshot["price_levels_enabled"] == "NO"
