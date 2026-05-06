from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo
import csv


@dataclass
class ResearchTradingPlanRow:
    etf_symbol: str
    plan_status: str
    action_allowed: str
    lot_size: str
    actual_price: str
    theoretical_price: str
    deviation_pct: str
    currency: str
    today_buy_reference_zone: str
    today_sell_reference_zone: str
    rolling_t_buy_reference_zone: str
    rolling_t_sell_reference_zone: str
    short_term_plan: str
    medium_term_plan: str
    long_term_plan: str
    stop_loss_trigger: str
    take_profit_trigger: str
    time_trigger: str
    event_trigger: str
    confidence: str
    source_quality: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


def _now_pair(tz_cfg: dict[str, str]) -> tuple[str, str]:
    now_utc = datetime.now(timezone.utc)
    return (
        now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat(),
        now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat(),
    )


def _parse_float(value: object) -> Optional[float]:
    if value in (None, "", "unavailable", "nan", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_price(value: Optional[float], currency: str) -> str:
    if value is None:
        return "unavailable"
    if currency == "JPY":
        return f"{value:.0f}" if abs(value) >= 1000 else f"{value:.2f}"
    if currency == "CNY":
        return f"{value:.4f}"
    return f"{value:.2f}"


def _zone(low: Optional[float], high: Optional[float], currency: str) -> str:
    if low is None or high is None:
        return "closed"
    if low > high:
        low, high = high, low
    return f"{_format_price(low, currency)}-{_format_price(high, currency)} {currency}"


def _lot_size(symbol: str) -> str:
    if symbol.endswith(".T") or symbol.endswith(".SH") or symbol.endswith(".SZ"):
        return "100"
    return "1"


def _time_trigger(symbol: str) -> str:
    if symbol.endswith(".T"):
        return "JST 09:00 open check; JST 12:32-13:00 lunch-gap check; JST 15:25-15:30 close-auction check"
    if symbol.endswith(".SH") or symbol.endswith(".SZ"):
        return "CST 09:30 open check; CST 13:00 afternoon reopen check; CST 14:50-15:00 close-window check"
    return "ET 10:00 entry check; ET 14:30/15:10/15:50 exit checks; convert to JST before manual execution"


def _has_hard_warning(warning_flags: str) -> bool:
    hard_tokens = {"data_invalid", "invalid", "unavailable", "currency_mismatch", "extreme_deviation", "risk_off"}
    tokens = {t.strip() for t in warning_flags.split(";") if t.strip()}
    return bool(tokens & hard_tokens)


def _plan_status(row: dict[str, str], actual: Optional[float], theoretical: Optional[float], deviation: Optional[float]) -> str:
    reference_label = row.get("reference_label", "")
    strategy_label = row.get("strategy_label", "")
    risk_flag = row.get("risk_flag", "none") or "none"
    warning_flags = row.get("warning_flags", "none") or "none"

    if actual is None or theoretical is None:
        return "closed_data_invalid"
    if reference_label == "data_invalid" or "data_invalid" in strategy_label or _has_hard_warning(warning_flags):
        return "closed_data_invalid"
    if reference_label == "risk_off" or "risk" in strategy_label or risk_flag not in {"", "none", "0"}:
        return "closed_risk_review"
    if "lower_side" in strategy_label or "undervalued" in reference_label or (deviation is not None and deviation <= -0.005):
        return "lower_side_trade_reference"
    if "upper_side" in strategy_label or "overvalued" in reference_label or (deviation is not None and deviation >= 0.005):
        return "upper_side_trade_reference"
    return "neutral_range_trade_reference"


def _daily_zones(status: str, actual: Optional[float], theoretical: Optional[float], currency: str) -> tuple[str, str, str, str]:
    if actual is None or theoretical is None or status.startswith("closed"):
        return "closed", "closed", "closed", "closed"
    if status == "lower_side_trade_reference":
        return (
            _zone(actual * 0.996, min(actual * 0.999, theoretical * 0.999), currency),
            _zone(max(actual * 1.003, theoretical * 0.999), max(actual * 1.006, theoretical * 1.002), currency),
            _zone(actual * 0.995, actual * 0.998, currency),
            _zone(actual * 1.002, actual * 1.005, currency),
        )
    if status == "upper_side_trade_reference":
        return (
            _zone(min(actual * 0.992, theoretical * 0.998), min(actual * 0.996, theoretical), currency),
            _zone(actual * 1.001, actual * 1.004, currency),
            "avoid new rolling-T entry unless price pulls back into buy reference zone",
            _zone(actual * 1.001, actual * 1.004, currency),
        )
    return (
        _zone(actual * 0.997, actual * 0.999, currency),
        _zone(actual * 1.001, actual * 1.004, currency),
        _zone(actual * 0.996, actual * 0.998, currency),
        _zone(actual * 1.002, actual * 1.005, currency),
    )


def _range(actual: Optional[float], low_mult: float, high_mult: float, currency: str) -> str:
    if actual is None:
        return "unavailable"
    return _zone(actual * low_mult, actual * high_mult, currency)


def _plans(status: str, actual: Optional[float], currency: str) -> tuple[str, str, str]:
    if status.startswith("closed"):
        return (
            "short-term: closed until valid review-pack data and risk flags normalize",
            "medium-term: closed; do not infer range from invalid or risk-review data",
            "long-term: keep only observation record; no execution signal",
        )
    if status == "lower_side_trade_reference":
        return (
            "short-term 1-5 sessions: lower-side reference plan; observe whether discount persists and price rebounds toward theoretical band",
            f"medium-term 2-8 weeks: provisional range {_range(actual, 0.97, 1.06, currency)}; refresh after gold, FX, or deviation snapshot changes",
            "long-term: core precious-metals holding framework remains observation-only; use repeated confirmed discounts rather than one snapshot",
        )
    if status == "upper_side_trade_reference":
        return (
            "short-term 1-5 sessions: upper-side reference plan; avoid chasing premium extension and observe normalization risk",
            f"medium-term 2-8 weeks: provisional range {_range(actual, 0.95, 1.03, currency)}; refresh after premium/discount compression",
            "long-term: core precious-metals holding framework remains observation-only; treat premium as execution risk, not structural bullish confirmation",
        )
    return (
        "short-term 1-5 sessions: neutral range plan; only observe edge moves outside reference zones",
        f"medium-term 2-8 weeks: provisional range {_range(actual, 0.98, 1.04, currency)}; wait for repeated deviation break before changing framework",
        "long-term: maintain baseline actual/theoretical/deviation tracking; no automatic trade signal",
    )


def _risk_triggers(status: str, actual: Optional[float], currency: str) -> tuple[str, str]:
    if actual is None or status.startswith("closed"):
        return "closed until data and risk flags normalize", "closed until data and risk flags normalize"
    return (
        f"manual stop reference: price <= {_format_price(actual * 0.985, currency)} {currency}, or warning_flags shift to hard risk, or fresh snapshot contradicts current plan",
        f"manual take-profit reference: rolling-T price >= {_format_price(actual * 1.004, currency)} {currency}, or deviation normalizes back into neutral band",
    )


def load_review_pack_by_symbol(path: str) -> dict[str, dict[str, str]]:
    if not Path(path).exists():
        return {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        return {
            str(row.get("etf_symbol", "")): {k: str(v) if v is not None else "" for k, v in row.items()}
            for row in csv.DictReader(f)
            if row.get("etf_symbol")
        }


def build_research_trading_plan_rows(review_rows: dict[str, dict[str, str]], tz_cfg: dict[str, str]) -> list[ResearchTradingPlanRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    output: list[ResearchTradingPlanRow] = []
    for symbol in sorted(review_rows.keys()):
        row = review_rows[symbol]
        currency = row.get("currency", "unavailable") or "unavailable"
        actual = _parse_float(row.get("actual_price"))
        theoretical = _parse_float(row.get("theoretical_price"))
        deviation = _parse_float(row.get("deviation_pct"))
        status = _plan_status(row, actual, theoretical, deviation)
        today_buy, today_sell, rolling_buy, rolling_sell = _daily_zones(status, actual, theoretical, currency)
        short_plan, medium_plan, long_plan = _plans(status, actual, currency)
        stop_loss, take_profit = _risk_triggers(status, actual, currency)
        flags = row.get("warning_flags", "none") or "none"
        if "phase8a_research_plan" not in flags:
            flags = f"{flags};phase8a_research_plan" if flags != "none" else "phase8a_research_plan"
        output.append(
            ResearchTradingPlanRow(
                etf_symbol=symbol,
                plan_status=status,
                action_allowed="false",
                lot_size=_lot_size(symbol),
                actual_price=row.get("actual_price", "unavailable") or "unavailable",
                theoretical_price=row.get("theoretical_price", "unavailable") or "unavailable",
                deviation_pct=row.get("deviation_pct", "unavailable") or "unavailable",
                currency=currency,
                today_buy_reference_zone=today_buy,
                today_sell_reference_zone=today_sell,
                rolling_t_buy_reference_zone=rolling_buy,
                rolling_t_sell_reference_zone=rolling_sell,
                short_term_plan=short_plan,
                medium_term_plan=medium_plan,
                long_term_plan=long_plan,
                stop_loss_trigger=stop_loss,
                take_profit_trigger=take_profit,
                time_trigger=_time_trigger(symbol),
                event_trigger="rerun after review-pack, actual price, theoretical price, deviation, FX, gold, or silver snapshot changes",
                confidence=row.get("confidence", "low") or "low",
                source_quality=row.get("source_quality", "low") or "low",
                warning_flags=flags,
                notes=row.get("notes", "none") or "none",
                timestamp_jst=row.get("timestamp_jst", ts_jst) or ts_jst,
                timestamp_et=row.get("timestamp_et", ts_et) or ts_et,
            )
        )
    return output


def write_research_trading_plan_csv(path: Path, rows: list[ResearchTradingPlanRow]) -> None:
    fields = list(ResearchTradingPlanRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_research_trading_plan_report(path: Path, rows: list[ResearchTradingPlanRow], review_pack_path: str) -> None:
    statuses = sorted({r.plan_status for r in rows})
    lines = [
        "# Phase 8A Research Trading Plan Report",
        "",
        "- phase: Phase 8A",
        "- scope: final manual research trading plan generator",
        f"- review_pack_input: {review_pack_path}",
        "- action_allowed: false",
        "- execution: manual only; no order / no cancel / no rebalance / no auto trade",
        f"- plan_statuses: {','.join(statuses) if statuses else 'none'}",
        "",
        "## Final Research Plan Rows",
        "",
        "| etf_symbol | plan_status | lot_size | actual_price | theoretical_price | deviation_pct | today_buy_reference_zone | today_sell_reference_zone | action_allowed |",
        "|---|---|---:|---:|---:|---:|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r.etf_symbol} | {r.plan_status} | {r.lot_size} | {r.actual_price} | {r.theoretical_price} | {r.deviation_pct} | {r.today_buy_reference_zone} | {r.today_sell_reference_zone} | {r.action_allowed} |")
    lines.extend(["", "## Rolling-T Reference", ""])
    for r in rows:
        lines.append(f"- {r.etf_symbol}: buy={r.rolling_t_buy_reference_zone}; sell={r.rolling_t_sell_reference_zone}; stop={r.stop_loss_trigger}; take_profit={r.take_profit_trigger}")
    lines.extend(["", "## Safety Statement", "", "- research reference only", "- action_allowed=false for every row", "- no IBKR connection", "- no reqMktData", "- no reqHistoricalData", "- no order", "- no cancel", "- no rebalance", "- no auto trade", "- no automatic execution"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
