from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo
import csv


REQUIRED_FIELDS = [
    "target_id",
    "target_type",
    "market",
    "data_role",
    "value",
    "currency",
    "source",
    "source_status",
    "source_timestamp",
    "notes",
]


@dataclass
class ManualMarketDataRow:
    target_id: str
    target_type: str
    market: str
    data_role: str
    value: str
    currency: str
    source: str
    source_status: str
    source_timestamp: str
    normalized_status: str
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


def _parse_positive_float(value: object) -> Optional[float]:
    if value in (None, "", "unavailable", "nan", "NaN"):
        return None
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def validate_manual_market_data_header(fieldnames: Optional[list[str]]) -> list[str]:
    if not fieldnames:
        return REQUIRED_FIELDS[:]
    present = set(fieldnames)
    return [field for field in REQUIRED_FIELDS if field not in present]


def load_manual_market_data_csv(path: str) -> tuple[list[dict[str, str]], list[str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing_fields = validate_manual_market_data_header(reader.fieldnames)
        rows = [{k: str(v) if v is not None else "" for k, v in row.items()} for row in reader]
    return rows, missing_fields


def build_manual_market_data_template_rows(tz_cfg: dict[str, str]) -> list[ManualMarketDataRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    targets = [
        ("XAUUSD", "upstream_factor", "GLOBAL", "gold_spot_usd", "USD"),
        ("XAGUSD", "upstream_factor", "GLOBAL", "silver_spot_usd", "USD"),
        ("USDJPY", "upstream_factor", "FX", "fx_rate", "JPY"),
        ("USDCNY", "upstream_factor", "FX", "fx_rate", "CNY"),
        ("SGE_AU99_99", "upstream_factor", "CN", "shanghai_gold_benchmark", "CNY"),
        ("1540.T", "etf_actual_price", "JP", "jp_gold_etf_actual_price", "JPY"),
        ("1542.T", "etf_actual_price", "JP", "jp_silver_etf_actual_price", "JPY"),
        ("518880.SH", "etf_actual_price", "CN", "cn_gold_etf_actual_price", "CNY"),
    ]
    return [
        ManualMarketDataRow(
            target_id=target_id,
            target_type=target_type,
            market=market,
            data_role=data_role,
            value="unavailable",
            currency=currency,
            source="manual_csv_template",
            source_status="manual_csv_template",
            source_timestamp="unavailable",
            normalized_status="unavailable",
            warning_flags="template_row;manual_input_required;no_realtime_source",
            notes="template only; fill value/source_timestamp before use",
            timestamp_jst=ts_jst,
            timestamp_et=ts_et,
        )
        for target_id, target_type, market, data_role, currency in targets
    ]


def normalize_manual_market_data_rows(
    raw_rows: list[dict[str, str]],
    missing_fields: list[str],
    tz_cfg: dict[str, str],
) -> list[ManualMarketDataRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    normalized: list[ManualMarketDataRow] = []

    if missing_fields:
        return [
            ManualMarketDataRow(
                target_id="__file__",
                target_type="manual_csv",
                market="UNKNOWN",
                data_role="header_validation",
                value="unavailable",
                currency="unavailable",
                source="manual_csv",
                source_status="invalid_header",
                source_timestamp="unavailable",
                normalized_status="invalid",
                warning_flags="missing_required_fields",
                notes="missing_fields=" + ";".join(missing_fields),
                timestamp_jst=ts_jst,
                timestamp_et=ts_et,
            )
        ]

    for raw in raw_rows:
        target_id = raw.get("target_id", "").strip()
        value = raw.get("value", "").strip()
        source_status = raw.get("source_status", "").strip() or "manual_csv"
        notes = []
        flags = {"manual_csv"}

        parsed_value = _parse_positive_float(value)
        normalized_status = "ok"

        if not target_id:
            normalized_status = "invalid"
            flags.add("missing_target_id")
            notes.append("target_id missing")

        if parsed_value is None:
            normalized_status = "unavailable"
            flags.add("value_unavailable_or_invalid")
            notes.append("value unavailable/invalid")

        if source_status in {"", "unavailable", "invalid"}:
            normalized_status = "unavailable" if normalized_status == "ok" else normalized_status
            flags.add("source_status_unavailable")
            notes.append("source_status unavailable")

        source_timestamp = raw.get("source_timestamp", "").strip()
        if not source_timestamp or source_timestamp == "unavailable":
            flags.add("source_timestamp_missing")
            notes.append("source_timestamp missing")

        raw_notes = raw.get("notes", "").strip()
        if raw_notes and raw_notes != "none":
            notes.append(raw_notes)

        normalized.append(
            ManualMarketDataRow(
                target_id=target_id or "unavailable",
                target_type=raw.get("target_type", "unknown").strip() or "unknown",
                market=raw.get("market", "UNKNOWN").strip() or "UNKNOWN",
                data_role=raw.get("data_role", "unknown").strip() or "unknown",
                value=value if parsed_value is not None else "unavailable",
                currency=raw.get("currency", "unavailable").strip() or "unavailable",
                source=raw.get("source", "manual_csv").strip() or "manual_csv",
                source_status=source_status,
                source_timestamp=source_timestamp or "unavailable",
                normalized_status=normalized_status,
                warning_flags=";".join(sorted(flags)) if flags else "none",
                notes="; ".join(notes) if notes else "none",
                timestamp_jst=ts_jst,
                timestamp_et=ts_et,
            )
        )

    return normalized


def write_manual_market_data_snapshot_csv(path: Path, rows: list[ManualMarketDataRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "target_id",
                "target_type",
                "market",
                "data_role",
                "value",
                "currency",
                "source",
                "source_status",
                "source_timestamp",
                "normalized_status",
                "warning_flags",
                "notes",
                "timestamp_jst",
                "timestamp_et",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.target_id,
                    r.target_type,
                    r.market,
                    r.data_role,
                    r.value,
                    r.currency,
                    r.source,
                    r.source_status,
                    r.source_timestamp,
                    r.normalized_status,
                    r.warning_flags,
                    r.notes,
                    r.timestamp_jst,
                    r.timestamp_et,
                ]
            )


def write_manual_market_data_adapter_report(path: Path, rows: list[ManualMarketDataRow], input_path: str) -> None:
    statuses = sorted({r.normalized_status for r in rows})
    ok_count = sum(1 for r in rows if r.normalized_status == "ok")
    invalid_count = sum(1 for r in rows if r.normalized_status == "invalid")
    unavailable_count = sum(1 for r in rows if r.normalized_status == "unavailable")

    lines = [
        "# Manual CSV Market Data Adapter Report",
        "",
        "- phase: Phase 6B",
        "- scope: manual CSV adapter skeleton only",
        f"- input_csv: {input_path}",
        f"- row_count: {len(rows)}",
        f"- statuses: {','.join(statuses) if statuses else 'none'}",
        f"- ok_count: {ok_count}",
        f"- invalid_count: {invalid_count}",
        f"- unavailable_count: {unavailable_count}",
        "",
        "## Normalized Rows",
        "",
        "| target_id | target_type | market | value | currency | normalized_status | warning_flags |",
        "|---|---|---|---:|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r.target_id} | {r.target_type} | {r.market} | {r.value} | {r.currency} | {r.normalized_status} | {r.warning_flags} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- manual CSV only",
            "- no IBKR connection",
            "- no reqMktData",
            "- no reqHistoricalData",
            "- no order",
            "- no cancel",
            "- no rebalance",
            "- no auto trade",
            "- no automatic pipeline chaining",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
