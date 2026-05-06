from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo
import csv


@dataclass
class DailyTradePlanRow:
    etf_symbol: str
    plan_label: str
    action_allowed: str
    reference_label: str
    deviation_pct: str
    currency: str
    manual_plan: str
    entry_observation: str
    exit_observation: str
    risk_close_condition: str
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
    if value in (None, "", "unavailable"):
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _market_time_trigger(symbol: str) -> str:
    if symbol.endswith(".T"):
        return "JST 09:00 open check; JST 12:32-13:00 lunch-gap window; JST 15:25-15:30 close-auction check"
    if symbol.endswith(".SH") or symbol.endswith(".SZ"):
        return "CST 09:30 open check; CST 13:00 afternoon reopen check; CST 14:50-15:00 close-window check"
    return "session open / mid-session / close-window manual checks"


def _event_trigger(reference_label: str, confidence: str, source_quality: str) -> str:
    if reference_label in {"data_invalid", "risk_off"}:
        return "rerun only after data validity and warning flags normalize"
    if source_quality == "low" or confidence == "low":
        return "requires higher-quality source confirmation before any manual interpretation"
    return "rerun after upstream factor, theoretical price, actual price, or deviation snapshot changes"


def _risk_close_condition(reference_label: str, deviation_value: Optional[float], warning_flags: str) -> str:
    if reference_label == "risk_off":
        return "keep plan closed while hard risk flags or extreme deviation remain"
    if reference_label == "data_invalid":
        return "keep plan closed until deviation_status and price inputs are valid"
    if deviation_value is not None and abs(deviation_value) >= 0.20:
        return "keep plan closed while absolute deviation remains >= 0.20"
    if "currency_mismatch" in warning_flags or "unavailable" in warning_flags or "invalid" in warning_flags:
        return "keep plan closed while hard warning flags remain"
    return "close manual observation if source quality deteriorates, deviation normalizes, or fresh snapshot contradicts current label"


def _plan_for_reference(row: dict[str, str]) -> tuple[str, str, str, str]:
    reference_label = row.get("reference_label", "data_invalid")
    deviation_value = _parse_float(row.get("deviation_pct"))

    if reference_label == "data_invalid":
        return (
            "data_invalid_no_plan",
            "data invalid; no daily observation plan should be interpreted",
            "not available until inputs are valid",
            "not available until inputs are valid",
        )

    if reference_label == "risk_off":
        return (
            "risk_review_only",
            "risk review only; daily plan remains closed",
            "no lower-side observation zone while risk_off is active",
            "no upper-side observation zone while risk_off is active",
        )

    if reference_label == "undervalued_watch":
        level_text = row.get("deviation_pct", "unavailable")
        return (
            "lower_side_observation",
            "manual observation focused on negative deviation persistence",
            f"observe only if deviation remains near or below {level_text}; action_allowed=false",
            "observe normalization back toward neutral band; action_allowed=false",
        )

    if reference_label == "overvalued_watch":
        level_text = row.get("deviation_pct", "unavailable")
        return (
            "upper_side_observation",
            "manual observation focused on positive deviation persistence",
            "observe pullback toward neutral band; action_allowed=false",
            f"observe only if deviation remains near or above {level_text}; action_allowed=false",
        )

    if reference_label == "no_trade":
        return (
            "neutral_band_observation",
            "neutral band; maintain observation-only status",
            "no lower-side observation zone because deviation is inside neutral band",
            "no upper-side observation zone because deviation is inside neutral band",
        )

    if deviation_value is None:
        return (
            "data_invalid_no_plan",
            "unrecognized reference label and unavailable deviation",
            "not available",
            "not available",
        )

    return (
        "neutral_band_observation",
        "fallback neutral observation; action_allowed=false",
        "manual observation only",
        "manual observation only",
    )


def build_daily_trade_plan_rows(
    reference_rows: dict[str, dict[str, str]],
    tz_cfg: dict[str, str],
) -> list[DailyTradePlanRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[DailyTradePlanRow] = []

    for symbol in sorted(reference_rows.keys()):
        row = reference_rows[symbol]
        reference_label = row.get("reference_label", "data_invalid")
        deviation_pct = row.get("deviation_pct", "unavailable")
        deviation_value = _parse_float(deviation_pct)
        confidence = row.get("confidence", "low") or "low"
        source_quality = row.get("source_quality", "low") or "low"
        warning_flags = row.get("warning_flags", "none") or "none"

        plan_label, manual_plan, entry_observation, exit_observation = _plan_for_reference(row)

        rows.append(
            DailyTradePlanRow(
                etf_symbol=symbol,
                plan_label=plan_label,
                action_allowed="false",
                reference_label=reference_label,
                deviation_pct=deviation_pct,
                currency=row.get("currency", "unavailable"),
                manual_plan=manual_plan,
                entry_observation=entry_observation,
                exit_observation=exit_observation,
                risk_close_condition=_risk_close_condition(reference_label, deviation_value, warning_flags),
                time_trigger=_market_time_trigger(symbol),
                event_trigger=_event_trigger(reference_label, confidence, source_quality),
                confidence=confidence,
                source_quality=source_quality,
                warning_flags=warning_flags,
                notes=row.get("notes", "none") or "none",
                timestamp_jst=row.get("timestamp_jst", ts_jst),
                timestamp_et=row.get("timestamp_et", ts_et),
            )
        )

    return rows


def write_daily_trade_plan_csv(path: Path, rows: list[DailyTradePlanRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "etf_symbol",
                "plan_label",
                "action_allowed",
                "reference_label",
                "deviation_pct",
                "currency",
                "manual_plan",
                "entry_observation",
                "exit_observation",
                "risk_close_condition",
                "time_trigger",
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
                    r.plan_label,
                    r.action_allowed,
                    r.reference_label,
                    r.deviation_pct,
                    r.currency,
                    r.manual_plan,
                    r.entry_observation,
                    r.exit_observation,
                    r.risk_close_condition,
                    r.time_trigger,
                    r.event_trigger,
                    r.confidence,
                    r.source_quality,
                    r.warning_flags,
                    r.notes,
                    r.timestamp_jst,
                    r.timestamp_et,
                ]
            )


def write_daily_trade_plan_report(path: Path, rows: list[DailyTradePlanRow], reference_path: str) -> None:
    lines = [
        "# Daily Manual Trade Plan Report",
        "",
        f"- reference_signal_input: {reference_path}",
        "- action_allowed: false for every row",
        "- scope: manual observation plan only",
        "",
        "## Daily Plan Rows",
        "",
        "| etf_symbol | plan_label | action_allowed | reference_label | deviation_pct | currency | confidence | source_quality |",
        "|---|---|---|---|---:|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r.etf_symbol} | {r.plan_label} | {r.action_allowed} | {r.reference_label} | {r.deviation_pct} | {r.currency} | {r.confidence} | {r.source_quality} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- manual observation only",
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
