from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo
import csv


@dataclass
class MultiHorizonStrategyRow:
    etf_symbol: str
    strategy_label: str
    action_allowed: str
    source_plan_label: str
    reference_label: str
    deviation_pct: str
    currency: str
    short_term_framework: str
    medium_term_framework: str
    long_term_framework: str
    short_term_observation: str
    medium_term_observation: str
    long_term_observation: str
    risk_close_condition: str
    review_frequency: str
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
    if value in (None, "", "unavailable"):
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _review_frequency(symbol: str) -> str:
    if symbol.endswith(".T"):
        return "JP: daily after TSE close; intraday only during JST 12:32-13:00 and JST 15:25-15:30 manual checks"
    if symbol.endswith(".SH") or symbol.endswith(".SZ"):
        return "CN: daily after A-share close; intraday only around CST open, afternoon reopen, and close-window checks"
    return "daily close review plus event-driven manual checks"


def _strategy_label(plan_label: str, reference_label: str, deviation_value: Optional[float]) -> str:
    if reference_label == "data_invalid" or plan_label == "data_invalid_no_plan":
        return "no_strategy_data_invalid"
    if reference_label == "risk_off" or plan_label == "risk_review_only":
        return "risk_review_only"
    if plan_label == "lower_side_observation" or reference_label == "undervalued_watch":
        return "lower_side_range_framework"
    if plan_label == "upper_side_observation" or reference_label == "overvalued_watch":
        return "upper_side_range_framework"
    if plan_label == "neutral_band_observation" or reference_label == "no_trade":
        return "neutral_range_framework"
    if deviation_value is None:
        return "no_strategy_data_invalid"
    return "neutral_range_framework"


def _frameworks(strategy_label: str) -> tuple[str, str, str]:
    if strategy_label == "no_strategy_data_invalid":
        return (
            "short-term disabled until input data is valid",
            "medium-term disabled until input data is valid",
            "long-term disabled until input data is valid",
        )
    if strategy_label == "risk_review_only":
        return (
            "short-term risk review only; no tactical framework active",
            "medium-term risk review only; wait for risk flags to normalize",
            "long-term preserve observation record; do not infer structural signal from invalid/risk state",
        )
    if strategy_label == "lower_side_range_framework":
        return (
            "short-term: monitor whether lower-side deviation persists or normalizes",
            "medium-term: compare repeated lower-side observations across several sessions",
            "long-term: classify whether lower-side behavior is temporary discount or recurring structural pattern",
        )
    if strategy_label == "upper_side_range_framework":
        return (
            "short-term: monitor whether upper-side deviation persists or normalizes",
            "medium-term: compare repeated upper-side observations across several sessions",
            "long-term: classify whether upper-side behavior is temporary premium or recurring structural pattern",
        )
    return (
        "short-term: neutral range tracking; avoid over-interpreting small deviation",
        "medium-term: wait for repeated deviation outside watch bands before changing framework",
        "long-term: maintain baseline relationship between actual price, theoretical price, and upstream factors",
    )


def _observations(strategy_label: str, deviation_pct: str) -> tuple[str, str, str]:
    if strategy_label == "no_strategy_data_invalid":
        return (
            "not available until input validity is restored",
            "not available until input validity is restored",
            "not available until input validity is restored",
        )
    if strategy_label == "risk_review_only":
        return (
            "manual risk review only; action_allowed=false",
            "manual risk review only; action_allowed=false",
            "manual risk review only; action_allowed=false",
        )
    if strategy_label == "lower_side_range_framework":
        return (
            f"observe negative deviation persistence around {deviation_pct}; action_allowed=false",
            "observe whether repeated lower-side readings form a stable range; action_allowed=false",
            "observe whether discount pattern is structurally repeatable before treating it as a long-term framework",
        )
    if strategy_label == "upper_side_range_framework":
        return (
            f"observe positive deviation persistence around {deviation_pct}; action_allowed=false",
            "observe whether repeated upper-side readings form a stable range; action_allowed=false",
            "observe whether premium pattern is structurally repeatable before treating it as a long-term framework",
        )
    return (
        "observe neutral deviation behavior; action_allowed=false",
        "observe whether neutral band breaks repeatedly; action_allowed=false",
        "observe baseline stability between ETF actual price and theoretical price",
    )


def _risk_close_condition(row: dict[str, str], strategy_label: str) -> str:
    warning_flags = row.get("warning_flags", "none") or "none"
    source_risk = row.get("risk_close_condition", "")
    if strategy_label == "no_strategy_data_invalid":
        return "close framework until daily plan input and reference signal input are valid"
    if strategy_label == "risk_review_only":
        return "keep framework closed while risk_review_only, risk_off, hard warning flags, or extreme deviation remain"
    if "currency_mismatch" in warning_flags or "unavailable" in warning_flags or "invalid" in warning_flags:
        return "close framework while hard warning flags remain"
    if source_risk:
        return source_risk
    return "close framework if source quality deteriorates, confidence falls, or fresh snapshot contradicts current framework"


def _event_trigger(row: dict[str, str], strategy_label: str) -> str:
    if strategy_label in {"no_strategy_data_invalid", "risk_review_only"}:
        return "rebuild only after risk/data status normalizes"
    source_trigger = row.get("event_trigger", "")
    if source_trigger:
        return source_trigger
    return "rebuild after daily plan, reference signal, deviation, theoretical price, actual price, or upstream factor snapshot changes"


def build_multi_horizon_strategy_rows(
    daily_plan_rows: dict[str, dict[str, str]],
    tz_cfg: dict[str, str],
) -> list[MultiHorizonStrategyRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[MultiHorizonStrategyRow] = []

    for symbol in sorted(daily_plan_rows.keys()):
        row = daily_plan_rows[symbol]
        plan_label = row.get("plan_label", "data_invalid_no_plan")
        reference_label = row.get("reference_label", "data_invalid")
        deviation_pct = row.get("deviation_pct", "unavailable")
        deviation_value = _parse_float(deviation_pct)

        label = _strategy_label(plan_label, reference_label, deviation_value)
        short_fw, medium_fw, long_fw = _frameworks(label)
        short_obs, medium_obs, long_obs = _observations(label, deviation_pct)

        rows.append(
            MultiHorizonStrategyRow(
                etf_symbol=symbol,
                strategy_label=label,
                action_allowed="false",
                source_plan_label=plan_label,
                reference_label=reference_label,
                deviation_pct=deviation_pct,
                currency=row.get("currency", "unavailable"),
                short_term_framework=short_fw,
                medium_term_framework=medium_fw,
                long_term_framework=long_fw,
                short_term_observation=short_obs,
                medium_term_observation=medium_obs,
                long_term_observation=long_obs,
                risk_close_condition=_risk_close_condition(row, label),
                review_frequency=_review_frequency(symbol),
                event_trigger=_event_trigger(row, label),
                confidence=row.get("confidence", "low") or "low",
                source_quality=row.get("source_quality", "low") or "low",
                warning_flags=row.get("warning_flags", "none") or "none",
                notes=row.get("notes", "none") or "none",
                timestamp_jst=row.get("timestamp_jst", ts_jst),
                timestamp_et=row.get("timestamp_et", ts_et),
            )
        )

    return rows


def write_multi_horizon_strategy_csv(path: Path, rows: list[MultiHorizonStrategyRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "etf_symbol",
                "strategy_label",
                "action_allowed",
                "source_plan_label",
                "reference_label",
                "deviation_pct",
                "currency",
                "short_term_framework",
                "medium_term_framework",
                "long_term_framework",
                "short_term_observation",
                "medium_term_observation",
                "long_term_observation",
                "risk_close_condition",
                "review_frequency",
                "event_trigger",
                "confidence",
                "source_quality",
                "warning_flags",
                "notes",
                "timestamp_jst",
                "timestamp_et",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.etf_symbol,
                    r.strategy_label,
                    r.action_allowed,
                    r.source_plan_label,
                    r.reference_label,
                    r.deviation_pct,
                    r.currency,
                    r.short_term_framework,
                    r.medium_term_framework,
                    r.long_term_framework,
                    r.short_term_observation,
                    r.medium_term_observation,
                    r.long_term_observation,
                    r.risk_close_condition,
                    r.review_frequency,
                    r.event_trigger,
                    r.confidence,
                    r.source_quality,
                    r.warning_flags,
                    r.notes,
                    r.timestamp_jst,
                    r.timestamp_et,
                ]
            )


def write_multi_horizon_strategy_report(path: Path, rows: list[MultiHorizonStrategyRow], daily_plan_path: str) -> None:
    lines = [
        "# Multi-Horizon Manual Strategy Report",
        "",
        f"- daily_plan_input: {daily_plan_path}",
        "- action_allowed: false for every row",
        "- scope: short / medium / long-term manual observation framework only",
        "",
        "## Strategy Rows",
        "",
        "| etf_symbol | strategy_label | action_allowed | source_plan_label | reference_label | deviation_pct | confidence | source_quality |",
        "|---|---|---|---|---|---:|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r.etf_symbol} | {r.strategy_label} | {r.action_allowed} | {r.source_plan_label} | {r.reference_label} | {r.deviation_pct} | {r.confidence} | {r.source_quality} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- manual observation framework only",
            "- action_allowed=false",
            "- no IBKR connection",
            "- no reqMktData",
            "- no reqHistoricalData",
            "- no automatic calibration",
            "- no automatic pipeline chaining",
            "- no automatic execution",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
