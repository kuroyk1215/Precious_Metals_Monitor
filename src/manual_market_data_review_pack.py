from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo
import csv


@dataclass
class ManualMarketDataReviewPackRow:
    etf_symbol: str
    actual_price: str
    theoretical_price: str
    deviation_pct: str
    currency: str
    reference_label: str
    daily_plan_label: str
    strategy_label: str
    action_allowed: str
    confidence: str
    source_quality: str
    risk_flag: str
    review_summary: str
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


def load_csv_by_key(path: str, key_field: str) -> dict[str, dict[str, str]]:
    if not Path(path).exists():
        return {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        rows = csv.DictReader(f)
        return {
            str(row.get(key_field, "")): {k: str(v) if v is not None else "" for k, v in row.items()}
            for row in rows
            if row.get(key_field)
        }


def _combine_flags(*flag_values: str) -> str:
    flags: set[str] = set()
    for value in flag_values:
        if not value or value == "none":
            continue
        flags.update(flag.strip() for flag in value.split(";") if flag.strip())
    flags.add("manual_review_pack")
    flags.add("action_allowed_false")
    return ";".join(sorted(flags)) if flags else "none"


def _select_action_allowed(*rows: dict[str, str]) -> str:
    values = {row.get("action_allowed", "") for row in rows if row}
    if values == {"false"} or "false" in values:
        return "false"
    return "false"


def _build_review_summary(
    symbol: str,
    actual_price: str,
    theoretical_price: str,
    deviation_pct: str,
    reference_label: str,
    daily_label: str,
    strategy_label: str,
) -> str:
    return (
        f"{symbol}: actual={actual_price}, theoretical={theoretical_price}, "
        f"deviation_pct={deviation_pct}, reference={reference_label}, "
        f"daily_plan={daily_label}, strategy={strategy_label}; action_allowed=false"
    )


def build_manual_market_data_review_pack_rows(
    actual_rows: dict[str, dict[str, str]],
    theoretical_rows: dict[str, dict[str, str]],
    deviation_rows: dict[str, dict[str, str]],
    reference_rows: dict[str, dict[str, str]],
    daily_rows: dict[str, dict[str, str]],
    strategy_rows: dict[str, dict[str, str]],
    tz_cfg: dict[str, str],
) -> list[ManualMarketDataReviewPackRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    symbols = sorted(
        set(actual_rows.keys())
        | set(theoretical_rows.keys())
        | set(deviation_rows.keys())
        | set(reference_rows.keys())
        | set(daily_rows.keys())
        | set(strategy_rows.keys())
    )

    output: list[ManualMarketDataReviewPackRow] = []

    for symbol in symbols:
        actual = actual_rows.get(symbol, {})
        theoretical = theoretical_rows.get(symbol, {})
        deviation = deviation_rows.get(symbol, {})
        reference = reference_rows.get(symbol, {})
        daily = daily_rows.get(symbol, {})
        strategy = strategy_rows.get(symbol, {})

        actual_price = actual.get("actual_price", actual.get("value", "unavailable"))
        theoretical_price = theoretical.get("theoretical_price", "unavailable")
        deviation_pct = deviation.get("deviation_pct", "unavailable")
        currency = deviation.get("currency", actual.get("currency", theoretical.get("currency", "unavailable")))
        reference_label = reference.get("reference_label", "unavailable")
        daily_label = daily.get("plan_label", "unavailable")
        strategy_label = strategy.get("strategy_label", "unavailable")
        confidence = strategy.get("confidence", daily.get("confidence", reference.get("confidence", "low")))
        source_quality = strategy.get("source_quality", daily.get("source_quality", reference.get("source_quality", "low")))
        risk_flag = daily.get("risk_flag", reference.get("risk_flag", "none"))

        warning_flags = _combine_flags(
            actual.get("warning_flags", "none"),
            theoretical.get("warning_flags", "none"),
            deviation.get("warning_flags", "none"),
            reference.get("warning_flags", "none"),
            daily.get("warning_flags", "none"),
            strategy.get("warning_flags", "none"),
        )

        notes = "; ".join(
            note
            for note in [
                actual.get("notes", ""),
                theoretical.get("notes", ""),
                deviation.get("notes", ""),
                reference.get("notes", ""),
                daily.get("notes", ""),
                strategy.get("notes", ""),
            ]
            if note and note != "none"
        ) or "none"

        output.append(
            ManualMarketDataReviewPackRow(
                etf_symbol=symbol,
                actual_price=actual_price,
                theoretical_price=theoretical_price,
                deviation_pct=deviation_pct,
                currency=currency,
                reference_label=reference_label,
                daily_plan_label=daily_label,
                strategy_label=strategy_label,
                action_allowed=_select_action_allowed(reference, daily, strategy),
                confidence=confidence or "low",
                source_quality=source_quality or "low",
                risk_flag=risk_flag or "none",
                review_summary=_build_review_summary(
                    symbol,
                    actual_price,
                    theoretical_price,
                    deviation_pct,
                    reference_label,
                    daily_label,
                    strategy_label,
                ),
                warning_flags=warning_flags,
                notes=notes,
                timestamp_jst=strategy.get("timestamp_jst", daily.get("timestamp_jst", reference.get("timestamp_jst", ts_jst))),
                timestamp_et=strategy.get("timestamp_et", daily.get("timestamp_et", reference.get("timestamp_et", ts_et))),
            )
        )

    return output


def write_manual_market_data_review_pack_csv(path: Path, rows: list[ManualMarketDataReviewPackRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "etf_symbol",
                "actual_price",
                "theoretical_price",
                "deviation_pct",
                "currency",
                "reference_label",
                "daily_plan_label",
                "strategy_label",
                "action_allowed",
                "confidence",
                "source_quality",
                "risk_flag",
                "review_summary",
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
                    r.actual_price,
                    r.theoretical_price,
                    r.deviation_pct,
                    r.currency,
                    r.reference_label,
                    r.daily_plan_label,
                    r.strategy_label,
                    r.action_allowed,
                    r.confidence,
                    r.source_quality,
                    r.risk_flag,
                    r.review_summary,
                    r.warning_flags,
                    r.notes,
                    r.timestamp_jst,
                    r.timestamp_et,
                ]
            )


def write_manual_market_data_review_pack_report(
    path: Path,
    rows: list[ManualMarketDataReviewPackRow],
    input_csv: str,
) -> None:
    labels = sorted({r.strategy_label for r in rows})
    action_values = sorted({r.action_allowed for r in rows})
    overall_status = "ok" if rows and action_values == ["false"] else "check_required"

    lines = [
        "# Manual CSV Pipeline Output Review Pack",
        "",
        "- phase: Phase 6G",
        "- scope: manual CSV pipeline output review only",
        f"- input_csv: {input_csv}",
        f"- overall_status: {overall_status}",
        f"- strategy_labels: {','.join(labels) if labels else 'none'}",
        "- action_allowed: false",
        "",
        "## Review Rows",
        "",
        "| etf_symbol | actual_price | theoretical_price | deviation_pct | currency | reference_label | daily_plan_label | strategy_label | action_allowed |",
        "|---|---:|---:|---:|---|---|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r.etf_symbol} | {r.actual_price} | {r.theoretical_price} | {r.deviation_pct} | {r.currency} | {r.reference_label} | {r.daily_plan_label} | {r.strategy_label} | {r.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Review Summary",
            "",
        ]
    )

    for r in rows:
        lines.append(f"- {r.review_summary}")

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- manual CSV review only",
            "- action_allowed=false",
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
