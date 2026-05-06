from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo
import csv


@dataclass
class ReferenceSignalRow:
    etf_symbol: str
    reference_label: str
    action_allowed: str
    deviation_pct: str
    currency: str
    source_quality: str
    confidence: str
    risk_flag: str
    warning_flags: str
    reason: str
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


def _split_flags(flags: str) -> set[str]:
    if not flags or flags == "none":
        return set()
    return {f.strip() for f in flags.split(";") if f.strip()}


def _has_hard_risk_flag(flags: set[str]) -> bool:
    tokens = ("currency_mismatch", "unavailable", "invalid")
    normalized = {f.lower() for f in flags}
    return any(any(token in flag for token in tokens) for flag in normalized)


def _source_quality(flags: set[str], row: dict[str, str], label: str) -> str:
    if label in {"data_invalid", "risk_off"}:
        return "low"

    lowered_flags = {f.lower() for f in flags}
    status_text = " ".join(
        [
            row.get("actual_source_status", ""),
            row.get("theoretical_source_status", ""),
            row.get("deviation_status", ""),
        ]
    ).lower()

    weak_tokens = (
        "manual_mock_data",
        "external_proxy",
        "no_realtime_source",
        "not_realtime_market_data",
        "manual",
        "mock",
        "unavailable",
    )

    if any(token in lowered_flags for token in weak_tokens):
        return "low"
    if any(token in status_text for token in weak_tokens):
        return "low"
    return "medium"


def _confidence(source_quality: str) -> str:
    if source_quality == "low":
        return "low"
    return "medium"


def build_reference_signal_rows(
    deviation_rows: dict[str, dict[str, str]],
    tz_cfg: dict[str, str],
    no_trade_threshold: float = 0.003,
    watch_threshold: float = 0.005,
    risk_off_threshold: float = 0.20,
) -> list[ReferenceSignalRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[ReferenceSignalRow] = []

    for symbol in sorted(deviation_rows.keys()):
        row = deviation_rows[symbol]
        flags = _split_flags(row.get("warning_flags", "none"))

        deviation_status = row.get("deviation_status", "unavailable")
        actual_val = _parse_float(row.get("actual_price"))
        theoretical_val = _parse_float(row.get("theoretical_price"))
        deviation_val = _parse_float(row.get("deviation_pct"))

        price_invalid = (
            actual_val is None
            or actual_val <= 0
            or theoretical_val is None
            or theoretical_val <= 0
        )
        status_invalid = deviation_status != "ok"
        hard_risk = _has_hard_risk_flag(flags)
        extreme_deviation = deviation_val is not None and abs(deviation_val) >= risk_off_threshold

        if hard_risk or extreme_deviation:
            label = "risk_off"
            risk_flag = "risk_off"
            reason = "hard risk flag or extreme deviation; observation-only reference"
        elif status_invalid or price_invalid or deviation_val is None:
            label = "data_invalid"
            risk_flag = "data_invalid"
            reason = "deviation status or price input invalid; observation-only reference"
        elif abs(deviation_val) < no_trade_threshold:
            label = "no_trade"
            risk_flag = "none"
            reason = "inside neutral reference band; action_allowed=false"
        elif deviation_val <= -watch_threshold:
            label = "undervalued_watch"
            risk_flag = "none"
            reason = "negative deviation reached watch band; observation-only reference"
        elif deviation_val >= watch_threshold:
            label = "overvalued_watch"
            risk_flag = "none"
            reason = "positive deviation reached watch band; observation-only reference"
        else:
            label = "no_trade"
            risk_flag = "watch_gap"
            reason = "between neutral and watch bands; action_allowed=false"

        quality = _source_quality(flags, row, label)
        confidence = _confidence(quality)

        input_notes = row.get("notes", "")
        notes = input_notes if input_notes and input_notes != "none" else "none"

        rows.append(
            ReferenceSignalRow(
                etf_symbol=symbol,
                reference_label=label,
                action_allowed="false",
                deviation_pct=row.get("deviation_pct", "unavailable"),
                currency=row.get("currency", "unavailable"),
                source_quality=quality,
                confidence=confidence,
                risk_flag=risk_flag,
                warning_flags=";".join(sorted(flags)) if flags else "none",
                reason=reason,
                notes=notes,
                timestamp_jst=row.get("timestamp_jst", ts_jst),
                timestamp_et=row.get("timestamp_et", ts_et),
            )
        )

    return rows


def write_reference_signal_csv(path: Path, rows: list[ReferenceSignalRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "etf_symbol",
                "reference_label",
                "action_allowed",
                "deviation_pct",
                "currency",
                "source_quality",
                "confidence",
                "risk_flag",
                "warning_flags",
                "reason",
                "notes",
                "timestamp_jst",
                "timestamp_et",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.etf_symbol,
                    r.reference_label,
                    r.action_allowed,
                    r.deviation_pct,
                    r.currency,
                    r.source_quality,
                    r.confidence,
                    r.risk_flag,
                    r.warning_flags,
                    r.reason,
                    r.notes,
                    r.timestamp_jst,
                    r.timestamp_et,
                ]
            )


def write_reference_signal_report(path: Path, rows: list[ReferenceSignalRow], deviation_path: str) -> None:
    lines = [
        "# Manual Reference Signal Report",
        "",
        f"- deviation_input: {deviation_path}",
        "- action_allowed: false for every row",
        "- current_scope: pipeline validation only",
        "",
        "## Label Set",
        "",
        "- data_invalid",
        "- no_trade",
        "- undervalued_watch",
        "- overvalued_watch",
        "- risk_off",
        "",
        "## Reference Rows",
        "",
        "| etf_symbol | reference_label | action_allowed | deviation_pct | currency | source_quality | confidence | risk_flag | warning_flags |",
        "|---|---|---|---:|---|---|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r.etf_symbol} | {r.reference_label} | {r.action_allowed} | {r.deviation_pct} | {r.currency} | {r.source_quality} | {r.confidence} | {r.risk_flag} | {r.warning_flags} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- observation-only reference layer",
            "- no IBKR connection",
            "- no reqMktData",
            "- no reqHistoricalData",
            "- no automatic calibration",
            "- no automatic pipeline chaining",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
