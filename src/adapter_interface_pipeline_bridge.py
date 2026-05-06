from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import csv


@dataclass
class AdapterInterfaceBridgeRow:
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


@dataclass
class AdapterInterfaceBridgeSummaryRow:
    target_id: str
    provider_id: str
    adapter_status: str
    normalized_status: str
    included: str
    bridge_status: str
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


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    if not Path(path).exists():
        return []
    with open(path, "r", encoding="utf-8", newline="") as f:
        return [
            {k: str(v) if v is not None else "" for k, v in row.items()}
            for row in csv.DictReader(f)
        ]


def _parse_positive_float(value: str) -> bool:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return False
    return parsed > 0


def _join_flags(*values: str) -> str:
    flags: set[str] = set()
    for value in values:
        if not value or value == "none":
            continue
        flags.update(flag.strip() for flag in value.split(";") if flag.strip())

    flags.add("adapter_interface_pipeline_bridge")
    flags.add("local_csv_bridge")
    flags.add("no_api_request")
    flags.add("no_ibkr_connection")
    flags.add("no_reqMktData")
    flags.add("no_reqHistoricalData")
    flags.add("no_order")
    flags.add("no_auto_trade")

    return ";".join(sorted(flags))


def _normalize_status(row: dict[str, str]) -> str:
    adapter_status = row.get("adapter_status", "")
    value = row.get("value", "")

    if adapter_status == "ok" and _parse_positive_float(value):
        return "ok"
    return "unavailable"


def load_adapter_interface_rows(path: str) -> list[dict[str, str]]:
    return _read_csv_rows(path)


def build_adapter_interface_bridge_rows(
    adapter_rows: list[dict[str, str]],
    tz_cfg: dict[str, str],
) -> tuple[list[AdapterInterfaceBridgeRow], list[AdapterInterfaceBridgeSummaryRow]]:
    ts_jst, ts_et = _now_pair(tz_cfg)

    output_rows: list[AdapterInterfaceBridgeRow] = []
    summary_rows: list[AdapterInterfaceBridgeSummaryRow] = []

    for row in adapter_rows:
        target_id = row.get("target_id", "")
        adapter_status = row.get("adapter_status", "unavailable")
        normalized_status = _normalize_status(row)

        value = row.get("value", "unavailable") if normalized_status == "ok" else "unavailable"
        currency = row.get("currency", "unavailable") if normalized_status == "ok" else row.get("currency", "unavailable")
        timestamp_jst = row.get("timestamp_jst", ts_jst) or ts_jst
        timestamp_et = row.get("timestamp_et", ts_et) or ts_et
        source_timestamp = timestamp_jst if normalized_status == "ok" else "unavailable"

        warning_flags = _join_flags(row.get("warning_flags", "none"))
        notes = row.get("notes", "none") or "none"

        output_rows.append(
            AdapterInterfaceBridgeRow(
                target_id=target_id,
                target_type=row.get("target_type", "unknown"),
                market=row.get("market", "UNKNOWN"),
                data_role=row.get("data_role", "unknown"),
                value=value,
                currency=currency,
                source=row.get("source", "adapter_interface"),
                source_status=row.get("source_status", "unavailable"),
                source_timestamp=source_timestamp,
                normalized_status=normalized_status,
                warning_flags=warning_flags,
                notes=notes,
                timestamp_jst=timestamp_jst,
                timestamp_et=timestamp_et,
            )
        )

        summary_rows.append(
            AdapterInterfaceBridgeSummaryRow(
                target_id=target_id,
                provider_id=row.get("provider_id", "unknown"),
                adapter_status=adapter_status,
                normalized_status=normalized_status,
                included="true" if normalized_status == "ok" else "false",
                bridge_status="ok" if normalized_status == "ok" else "unavailable",
                warning_flags=warning_flags,
                notes=notes,
                timestamp_jst=timestamp_jst,
                timestamp_et=timestamp_et,
            )
        )

    return output_rows, summary_rows


def write_adapter_interface_bridge_snapshot_csv(path: Path, rows: list[AdapterInterfaceBridgeRow]) -> None:
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


def write_adapter_interface_bridge_summary_csv(path: Path, rows: list[AdapterInterfaceBridgeSummaryRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "target_id",
                "provider_id",
                "adapter_status",
                "normalized_status",
                "included",
                "bridge_status",
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
                    r.provider_id,
                    r.adapter_status,
                    r.normalized_status,
                    r.included,
                    r.bridge_status,
                    r.warning_flags,
                    r.notes,
                    r.timestamp_jst,
                    r.timestamp_et,
                ]
            )


def write_adapter_interface_bridge_report(
    path: Path,
    summary_rows: list[AdapterInterfaceBridgeSummaryRow],
    input_csv: str,
    output_csv: str,
) -> None:
    statuses = sorted({r.bridge_status for r in summary_rows})
    included_count = sum(1 for r in summary_rows if r.included == "true")
    unavailable_count = sum(1 for r in summary_rows if r.bridge_status == "unavailable")

    lines = [
        "# Adapter Interface to Pipeline Bridge Report",
        "",
        "- phase: Phase 7D",
        "- scope: adapter interface output to pipeline-compatible snapshot",
        "- action: local CSV bridge only; no connection and no data request is performed",
        f"- input_csv: {input_csv}",
        f"- output_csv: {output_csv}",
        f"- row_count: {len(summary_rows)}",
        f"- statuses: {','.join(statuses) if statuses else 'none'}",
        f"- included_count: {included_count}",
        f"- unavailable_count: {unavailable_count}",
        "",
        "## Bridge Summary",
        "",
        "| target_id | provider_id | adapter_status | normalized_status | included | bridge_status |",
        "|---|---|---|---|---|---|",
    ]

    for r in summary_rows:
        lines.append(
            f"| {r.target_id} | {r.provider_id} | {r.adapter_status} | {r.normalized_status} | {r.included} | {r.bridge_status} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- local CSV bridge only",
            "- no connection",
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
