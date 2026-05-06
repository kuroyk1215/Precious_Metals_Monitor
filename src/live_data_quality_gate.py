from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo
import csv


EXPECTED_TARGETS = ["XAUUSD", "XAGUSD", "USDJPY", "USDCNH", "1540.T", "1542.T", "518880.SH"]
ALLOWED_DATA_STATUS = {"mock_live_adapter"}
ALLOWED_SOURCE_QUALITY = {"mock_only", "manual_or_sample"}


@dataclass
class LiveDataQualityGateRow:
    target_id: str
    target_type: str
    market: str
    data_role: str
    input_value: str
    currency: str
    data_status: str
    source_quality: str
    quality_status: str
    usable_for_research: str
    api_request_allowed: str
    action_allowed: str
    failure_reasons: str
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


def _parse_positive(value: str) -> bool:
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _flags(*values: str) -> str:
    flags: set[str] = {
        "phase10d_live_data_quality_gate",
        "quality_gate_only",
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


def load_live_provider_adapter_rows_by_target(path: str) -> dict[str, dict[str, str]]:
    if not Path(path).exists():
        return {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        return {
            str(row.get("target_id", "")): {k: str(v) if v is not None else "" for k, v in row.items()}
            for row in csv.DictReader(f)
            if row.get("target_id")
        }


def _evaluate_row(row: Optional[dict[str, str]]) -> tuple[str, str, str]:
    if row is None:
        return "fail_missing_target", "false", "missing_target"

    failures: list[str] = []
    value = row.get("mock_value", row.get("input_value", "unavailable"))
    currency = row.get("currency", "unavailable")
    data_status = row.get("data_status", "unavailable")
    source_quality = row.get("source_quality", "unavailable")
    api_request_allowed = row.get("api_request_allowed", "false")
    action_allowed = row.get("action_allowed", "false")

    if not value or value == "unavailable":
        failures.append("missing_value")
    elif not _parse_positive(value):
        failures.append("non_positive_value")

    if not currency or currency == "unavailable":
        failures.append("missing_currency")

    if data_status not in ALLOWED_DATA_STATUS:
        failures.append("data_status_not_allowed")

    if source_quality not in ALLOWED_SOURCE_QUALITY:
        failures.append("source_quality_not_allowed")

    if api_request_allowed != "false":
        failures.append("api_request_allowed_must_be_false")

    if action_allowed != "false":
        failures.append("action_allowed_must_be_false")

    if failures:
        return "fail_quality_gate", "false", ";".join(failures)

    return "pass_mock_quality_gate", "true", "none"


def build_live_data_quality_gate_rows(
    adapter_rows_by_target: dict[str, dict[str, str]],
    tz_cfg: dict[str, str],
    expected_targets: Optional[list[str]] = None,
) -> list[LiveDataQualityGateRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    targets = expected_targets or EXPECTED_TARGETS
    rows: list[LiveDataQualityGateRow] = []

    for target_id in targets:
        source = adapter_rows_by_target.get(target_id)
        quality_status, usable, failures = _evaluate_row(source)

        if source is None:
            source = {}

        rows.append(
            LiveDataQualityGateRow(
                target_id=target_id,
                target_type=source.get("target_type", "missing"),
                market=source.get("market", "missing"),
                data_role=source.get("data_role", "missing"),
                input_value=source.get("mock_value", source.get("input_value", "unavailable")),
                currency=source.get("currency", "unavailable"),
                data_status=source.get("data_status", "unavailable"),
                source_quality=source.get("source_quality", "unavailable"),
                quality_status=quality_status,
                usable_for_research=usable,
                api_request_allowed="false",
                action_allowed="false",
                failure_reasons=failures,
                warning_flags=_flags(quality_status, failures),
                notes="live/mock data quality gate output only; no real API request was made",
                timestamp_jst=source.get("timestamp_jst", ts_jst) or ts_jst,
                timestamp_et=source.get("timestamp_et", ts_et) or ts_et,
            )
        )

    return rows


def write_live_data_quality_gate_csv(path: Path, rows: list[LiveDataQualityGateRow]) -> None:
    fields = list(LiveDataQualityGateRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_live_data_quality_gate_report(
    path: Path,
    rows: list[LiveDataQualityGateRow],
    input_source: str,
) -> None:
    statuses = sorted({row.quality_status for row in rows})
    failed_count = sum(1 for row in rows if row.quality_status.startswith("fail"))
    usable_count = sum(1 for row in rows if row.usable_for_research == "true")

    lines = [
        "# Phase 10D Live Data Quality Gate Report",
        "",
        "- phase: Phase 10D",
        "- scope: live/mock data quality gate",
        "- input_source: " + input_source,
        "- row_count: " + str(len(rows)),
        "- usable_for_research_count: " + str(usable_count),
        "- failed_count: " + str(failed_count),
        "- quality_statuses: " + (",".join(statuses) if statuses else "none"),
        "- api_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Quality Gate Rows",
        "",
        "| target_id | input_value | currency | data_status | source_quality | quality_status | usable_for_research | failure_reasons | action_allowed |",
        "|---|---:|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.target_id} | {row.input_value} | {row.currency} | {row.data_status} | {row.source_quality} | {row.quality_status} | {row.usable_for_research} | {row.failure_reasons} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- data quality gate only",
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
