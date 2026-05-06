from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo
import csv


ETF_TARGETS = ["1540.T", "1542.T", "518880.SH"]


@dataclass
class LiveFinalResearchReviewPackRow:
    etf_symbol: str
    market: str
    actual_price: str
    theoretical_price: str
    deviation_pct: str
    currency: str
    data_status: str
    source_quality: str
    research_pack_status: str
    final_plan_status: str
    lot_size: str
    today_buy_reference_zone: str
    today_sell_reference_zone: str
    rolling_t_buy_reference_zone: str
    rolling_t_sell_reference_zone: str
    short_term_plan: str
    medium_term_plan: str
    long_term_plan: str
    stop_loss_trigger: str
    take_profit_trigger: str
    api_request_allowed: str
    action_allowed: str
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


def _flags(*values: str) -> str:
    flags: set[str] = {
        "phase10f_live_final_research_review_pack",
        "final_research_bridge_only",
        "no_api_request",
        "no_ibkr_connection",
        "no_reqMktData",
        "no_reqHistoricalData",
        "no_order",
        "no_auto_trade",
    }
    for value in values:
        if value and value != "none":
            flags.update(flag.strip() for flag in value.split(";") if flag.strip())
    return ";".join(sorted(flags))


def _as_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _fmt(value: float, currency: str) -> str:
    if currency == "JPY":
        return f"{value:.0f} {currency}"
    return f"{value:.4f} {currency}"


def _zone(center: float, low_pct: float, high_pct: float, currency: str) -> str:
    if center <= 0:
        return "closed"
    return f"{_fmt(center * low_pct, currency)} - {_fmt(center * high_pct, currency)}"


def _market(symbol: str) -> str:
    if symbol.endswith(".T"):
        return "JP"
    if symbol.endswith(".SH"):
        return "CN"
    return "UNKNOWN"


def _lot_size(symbol: str) -> str:
    if symbol.endswith(".T") or symbol.endswith(".SH"):
        return "100"
    return "1"


def _time_plan(symbol: str) -> str:
    if symbol.endswith(".T"):
        return "JP cash ETF reference only; check JST 12:32-13:00 and JST 15:25-15:30 close-auction window"
    if symbol.endswith(".SH"):
        return "CN ETF reference only; check CST 10:30-11:20 and CST 14:30-15:00"
    return "market-specific manual review required"


def _final_status(row: dict[str, str]) -> str:
    if row.get("research_pack_status") == "included_for_research":
        return "live_mock_final_reference"
    if row.get("research_pack_status", "").startswith("excluded"):
        return "closed_quality_gate_failed"
    return "manual_review_required"


def _closed_row(symbol: str, tz_cfg: dict[str, str], reason: str) -> LiveFinalResearchReviewPackRow:
    ts_jst, ts_et = _now_pair(tz_cfg)
    return LiveFinalResearchReviewPackRow(
        etf_symbol=symbol,
        market=_market(symbol),
        actual_price="unavailable",
        theoretical_price="unavailable",
        deviation_pct="unavailable",
        currency="unavailable",
        data_status="unavailable",
        source_quality="unavailable",
        research_pack_status="missing",
        final_plan_status="closed_missing_research_pack",
        lot_size=_lot_size(symbol),
        today_buy_reference_zone="closed",
        today_sell_reference_zone="closed",
        rolling_t_buy_reference_zone="closed",
        rolling_t_sell_reference_zone="closed",
        short_term_plan="closed until live/mock research pack provides usable data",
        medium_term_plan="closed until data quality gate passes",
        long_term_plan="manual review only",
        stop_loss_trigger="closed",
        take_profit_trigger="closed",
        api_request_allowed="false",
        action_allowed="false",
        warning_flags=_flags("closed_missing_research_pack", reason),
        notes=reason,
        timestamp_jst=ts_jst,
        timestamp_et=ts_et,
    )


def build_live_final_research_review_pack_rows(
    research_rows_by_target: dict[str, dict[str, str]],
    tz_cfg: dict[str, str],
    etf_targets: Optional[list[str]] = None,
) -> list[LiveFinalResearchReviewPackRow]:
    targets = etf_targets or ETF_TARGETS
    output: list[LiveFinalResearchReviewPackRow] = []

    for symbol in targets:
        source = research_rows_by_target.get(symbol)
        if source is None:
            output.append(_closed_row(symbol, tz_cfg, "missing live research review pack row"))
            continue

        actual = _as_float(source.get("research_value", "0"))
        currency = source.get("currency", "unavailable")
        status = _final_status(source)

        if status != "live_mock_final_reference" or actual <= 0 or currency == "unavailable":
            ts_jst, ts_et = _now_pair(tz_cfg)
            output.append(
                LiveFinalResearchReviewPackRow(
                    etf_symbol=symbol,
                    market=_market(symbol),
                    actual_price=source.get("research_value", "unavailable"),
                    theoretical_price="unavailable",
                    deviation_pct="unavailable",
                    currency=currency,
                    data_status=source.get("data_status", "unavailable"),
                    source_quality=source.get("source_quality", "unavailable"),
                    research_pack_status=source.get("research_pack_status", "unknown"),
                    final_plan_status="closed_quality_gate_failed",
                    lot_size=_lot_size(symbol),
                    today_buy_reference_zone="closed",
                    today_sell_reference_zone="closed",
                    rolling_t_buy_reference_zone="closed",
                    rolling_t_sell_reference_zone="closed",
                    short_term_plan="closed because research pack is not usable",
                    medium_term_plan="manual review required",
                    long_term_plan="manual review required",
                    stop_loss_trigger="closed",
                    take_profit_trigger="closed",
                    api_request_allowed="false",
                    action_allowed="false",
                    warning_flags=_flags("closed_quality_gate_failed", source.get("warning_flags", "none")),
                    notes="quality gate or research pack status failed",
                    timestamp_jst=source.get("timestamp_jst", ts_jst) or ts_jst,
                    timestamp_et=source.get("timestamp_et", ts_et) or ts_et,
                )
            )
            continue

        theoretical = actual
        deviation = 0.0

        output.append(
            LiveFinalResearchReviewPackRow(
                etf_symbol=symbol,
                market=_market(symbol),
                actual_price=source.get("research_value", "unavailable"),
                theoretical_price=f"{theoretical:.6f}",
                deviation_pct=f"{deviation:.6f}",
                currency=currency,
                data_status=source.get("data_status", "unavailable"),
                source_quality=source.get("source_quality", "unavailable"),
                research_pack_status=source.get("research_pack_status", "unknown"),
                final_plan_status=status,
                lot_size=_lot_size(symbol),
                today_buy_reference_zone=_zone(actual, 0.9970, 0.9990, currency),
                today_sell_reference_zone=_zone(actual, 1.0010, 1.0040, currency),
                rolling_t_buy_reference_zone=_zone(actual, 0.9960, 0.9980, currency),
                rolling_t_sell_reference_zone=_zone(actual, 1.0020, 1.0050, currency),
                short_term_plan="mock/live data passed quality gate; use only as research reference for intraday range planning",
                medium_term_plan="monitor premium/discount and upstream gold/silver/FX trend before increasing exposure",
                long_term_plan="core holding reference only; no automatic trade signal",
                stop_loss_trigger=_zone(actual, 0.9850, 0.9900, currency),
                take_profit_trigger=_zone(actual, 1.0100, 1.0200, currency),
                api_request_allowed="false",
                action_allowed="false",
                warning_flags=_flags(status, source.get("warning_flags", "none")),
                notes=_time_plan(symbol),
                timestamp_jst=source.get("timestamp_jst", ""),
                timestamp_et=source.get("timestamp_et", ""),
            )
        )

    return output


def write_live_final_research_review_pack_csv(path: Path, rows: list[LiveFinalResearchReviewPackRow]) -> None:
    fields = list(LiveFinalResearchReviewPackRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_live_final_research_review_pack_report(
    path: Path,
    rows: list[LiveFinalResearchReviewPackRow],
    input_source: str,
) -> None:
    statuses = sorted({row.final_plan_status for row in rows})
    included_count = sum(1 for row in rows if row.final_plan_status == "live_mock_final_reference")
    closed_count = sum(1 for row in rows if row.final_plan_status.startswith("closed"))

    lines = [
        "# Phase 10F Live Final Research Review Pack Report",
        "",
        "- phase: Phase 10F",
        "- scope: live/mock research pack to final research review pack bridge",
        "- input_source: " + input_source,
        "- row_count: " + str(len(rows)),
        "- included_count: " + str(included_count),
        "- closed_count: " + str(closed_count),
        "- final_plan_statuses: " + (",".join(statuses) if statuses else "none"),
        "- api_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Final Research Rows",
        "",
        "| etf_symbol | actual_price | theoretical_price | deviation_pct | currency | final_plan_status | today_buy_reference_zone | today_sell_reference_zone | action_allowed |",
        "|---|---:|---:|---:|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.etf_symbol} | {row.actual_price} | {row.theoretical_price} | {row.deviation_pct} | {row.currency} | {row.final_plan_status} | {row.today_buy_reference_zone} | {row.today_sell_reference_zone} | {row.action_allowed} |"
        )

    lines.extend(["", "## Rolling-T and Risk References", ""])
    for row in rows:
        lines.append(
            f"- {row.etf_symbol}: rolling_buy={row.rolling_t_buy_reference_zone}; rolling_sell={row.rolling_t_sell_reference_zone}; stop={row.stop_loss_trigger}; take_profit={row.take_profit_trigger}"
        )

    lines.extend(["", "## Safety Statement", ""])
    lines.extend(
        [
            "- live/mock final research review pack only",
            "- api_request_allowed=false for every row",
            "- action_allowed=false for every row",
            "- no API request",
            "- no IBKR connection",
            "- no reqMktData",
            "- no reqHistoricalData",
            "- no order",
            "- no cancel",
            "- no rebalance",
            "- no auto trade",
            "- no automatic execution",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
