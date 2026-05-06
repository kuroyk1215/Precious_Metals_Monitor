from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import csv


@dataclass
class FinalResearchReviewPackRow:
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
    confidence: str
    source_quality: str
    final_review_label: str
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
        return {
            str(row.get(key_field, "")): {k: str(v) if v is not None else "" for k, v in row.items()}
            for row in csv.DictReader(f)
            if row.get(key_field)
        }


def _final_review_label(plan_status: str) -> str:
    if plan_status.startswith("closed"):
        return "closed_review_only"
    if plan_status == "lower_side_trade_reference":
        return "lower_side_final_reference"
    if plan_status == "upper_side_trade_reference":
        return "upper_side_final_reference"
    if plan_status == "neutral_range_trade_reference":
        return "neutral_final_reference"
    return "manual_final_review_required"


def _join_flags(value: str) -> str:
    flags = {flag.strip() for flag in value.split(";") if flag.strip() and flag.strip() != "none"}
    flags.add("phase8d_final_review_pack")
    flags.add("action_allowed_false")
    flags.add("manual_review_only")
    return ";".join(sorted(flags))


def build_final_research_review_pack_rows(
    trading_plan_rows: dict[str, dict[str, str]],
    tz_cfg: dict[str, str],
) -> list[FinalResearchReviewPackRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    output: list[FinalResearchReviewPackRow] = []

    for symbol in sorted(trading_plan_rows.keys()):
        row = trading_plan_rows[symbol]
        plan_status = row.get("plan_status", "closed_data_invalid") or "closed_data_invalid"
        output.append(
            FinalResearchReviewPackRow(
                etf_symbol=symbol,
                plan_status=plan_status,
                action_allowed="false",
                lot_size=row.get("lot_size", "unavailable") or "unavailable",
                actual_price=row.get("actual_price", "unavailable") or "unavailable",
                theoretical_price=row.get("theoretical_price", "unavailable") or "unavailable",
                deviation_pct=row.get("deviation_pct", "unavailable") or "unavailable",
                currency=row.get("currency", "unavailable") or "unavailable",
                today_buy_reference_zone=row.get("today_buy_reference_zone", "closed") or "closed",
                today_sell_reference_zone=row.get("today_sell_reference_zone", "closed") or "closed",
                rolling_t_buy_reference_zone=row.get("rolling_t_buy_reference_zone", "closed") or "closed",
                rolling_t_sell_reference_zone=row.get("rolling_t_sell_reference_zone", "closed") or "closed",
                short_term_plan=row.get("short_term_plan", "unavailable") or "unavailable",
                medium_term_plan=row.get("medium_term_plan", "unavailable") or "unavailable",
                long_term_plan=row.get("long_term_plan", "unavailable") or "unavailable",
                stop_loss_trigger=row.get("stop_loss_trigger", "closed") or "closed",
                take_profit_trigger=row.get("take_profit_trigger", "closed") or "closed",
                time_trigger=row.get("time_trigger", "unavailable") or "unavailable",
                confidence=row.get("confidence", "low") or "low",
                source_quality=row.get("source_quality", "low") or "low",
                final_review_label=_final_review_label(plan_status),
                warning_flags=_join_flags(row.get("warning_flags", "none") or "none"),
                notes=row.get("notes", "none") or "none",
                timestamp_jst=row.get("timestamp_jst", ts_jst) or ts_jst,
                timestamp_et=row.get("timestamp_et", ts_et) or ts_et,
            )
        )

    return output


def write_final_research_review_pack_csv(path: Path, rows: list[FinalResearchReviewPackRow]) -> None:
    fields = list(FinalResearchReviewPackRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_final_research_review_pack_report(
    path: Path,
    rows: list[FinalResearchReviewPackRow],
    input_csv: str,
    pipeline_summary_csv: str,
    trading_plan_csv: str,
) -> None:
    labels = sorted({r.final_review_label for r in rows})
    statuses = sorted({r.plan_status for r in rows})

    lines = [
        "# Phase 8D Final Research Review Pack",
        "",
        "- phase: Phase 8D",
        "- scope: final manual research review pack",
        f"- input_csv: {input_csv}",
        f"- pipeline_summary_csv: {pipeline_summary_csv}",
        f"- trading_plan_csv: {trading_plan_csv}",
        f"- row_count: {len(rows)}",
        "- action_allowed: false",
        "- plan_statuses: " + (",".join(statuses) if statuses else "none"),
        "- final_review_labels: " + (",".join(labels) if labels else "none"),
        "",
        "## Final Overview",
        "",
        "| etf_symbol | final_review_label | plan_status | lot_size | actual_price | theoretical_price | deviation_pct | today_buy_reference_zone | today_sell_reference_zone | action_allowed |",
        "|---|---|---|---:|---:|---:|---:|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.etf_symbol} | {row.final_review_label} | {row.plan_status} | {row.lot_size} | {row.actual_price} | {row.theoretical_price} | {row.deviation_pct} | {row.today_buy_reference_zone} | {row.today_sell_reference_zone} | {row.action_allowed} |"
        )

    lines.extend(["", "## Rolling-T and Risk References", ""])
    for row in rows:
        lines.append(
            f"- {row.etf_symbol}: rolling_buy={row.rolling_t_buy_reference_zone}; rolling_sell={row.rolling_t_sell_reference_zone}; stop={row.stop_loss_trigger}; take_profit={row.take_profit_trigger}"
        )

    lines.extend(["", "## Multi-Horizon Summary", ""])
    for row in rows:
        lines.append(f"### {row.etf_symbol}")
        lines.append(f"- short_term: {row.short_term_plan}")
        lines.append(f"- medium_term: {row.medium_term_plan}")
        lines.append(f"- long_term: {row.long_term_plan}")
        lines.append(f"- time_trigger: {row.time_trigger}")

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- final research review pack only",
            "- action_allowed=false for every row",
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
