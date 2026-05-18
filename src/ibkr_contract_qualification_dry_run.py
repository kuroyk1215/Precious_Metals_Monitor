from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv


@dataclass
class IBKRContractQualificationDryRunRow:
    target_id: str
    asset_class: str
    symbol: str
    currency: str
    exchange: str
    primary_exchange: str
    sec_type: str
    mapping_status: str
    contract_status: str
    qualification_dry_run_status: str
    future_qualification_candidate: str
    qualification_allowed: str
    tws_connection_allowed: str
    contract_qualification_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    api_request_allowed: str
    action_allowed: str
    block_reason: str
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
        "phase10i_ibkr_contract_qualification_dry_run",
        "qualification_dry_run_only",
        "no_tws_connection",
        "no_contract_qualification",
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


def _row_dict(item: Any) -> dict[str, str]:
    raw = item if isinstance(item, dict) else item.__dict__
    return {str(k): str(v) for k, v in raw.items()}


def _dry_run_decision(row: dict[str, str]) -> tuple[str, str, str, str]:
    mapping_status = row.get("mapping_status", "unknown")
    contract_status = row.get("contract_status", "unknown")

    if mapping_status == "candidate_mapping_ready" and contract_status == "candidate_mapping":
        return (
            "dry_run_ready_for_future_qualification",
            "true",
            "qualification_blocked_by_phase10i_safety_gate",
            "candidate_ready_but_no_real_qualification",
        )

    if mapping_status == "candidate_review_required":
        return (
            "blocked_mapping_review_required",
            "false",
            "mapping_requires_manual_review_before_qualification",
            "mapping_review_required",
        )

    if mapping_status == "manual_review_required":
        return (
            "blocked_manual_review_required",
            "false",
            "manual_mapping_review_required",
            "manual_review_required",
        )

    return (
        "blocked_unknown_mapping_status",
        "false",
        "unknown_mapping_status",
        "unknown_mapping_status",
    )


def build_ibkr_contract_qualification_dry_run_rows(
    mapping_rows: list[Any],
    tz_cfg: dict[str, str],
) -> list[IBKRContractQualificationDryRunRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[IBKRContractQualificationDryRunRow] = []

    for item in mapping_rows:
        row = _row_dict(item)
        status, future_candidate, block_reason, extra_flag = _dry_run_decision(row)

        rows.append(
            IBKRContractQualificationDryRunRow(
                target_id=row.get("target_id", "unknown"),
                asset_class=row.get("asset_class", "unknown"),
                symbol=row.get("symbol", "unknown"),
                currency=row.get("currency", "unknown"),
                exchange=row.get("exchange", "unknown"),
                primary_exchange=row.get("primary_exchange", "unknown"),
                sec_type=row.get("sec_type", "unknown"),
                mapping_status=row.get("mapping_status", "unknown"),
                contract_status=row.get("contract_status", "unknown"),
                qualification_dry_run_status=status,
                future_qualification_candidate=future_candidate,
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                block_reason=block_reason,
                warning_flags=_flags(status, extra_flag, row.get("warning_flags", "none")),
                notes="IBKR contract qualification dry-run only; no TWS connection and no real qualification performed",
                timestamp_jst=row.get("timestamp_jst", ts_jst) or ts_jst,
                timestamp_et=row.get("timestamp_et", ts_et) or ts_et,
            )
        )

    return rows


def load_ibkr_contract_mapping_rows_by_target(path: str) -> dict[str, dict[str, str]]:
    if not Path(path).exists():
        return {}

    with open(path, "r", encoding="utf-8", newline="") as f:
        return {
            str(row.get("target_id", "")): {k: str(v) if v is not None else "" for k, v in row.items()}
            for row in csv.DictReader(f)
            if row.get("target_id")
        }


def write_ibkr_contract_qualification_dry_run_csv(
    path: Path,
    rows: list[IBKRContractQualificationDryRunRow],
) -> None:
    fields = list(IBKRContractQualificationDryRunRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_contract_qualification_dry_run_report(
    path: Path,
    rows: list[IBKRContractQualificationDryRunRow],
    input_source: str,
) -> None:
    statuses = sorted({row.qualification_dry_run_status for row in rows})
    future_candidate_count = sum(1 for row in rows if row.future_qualification_candidate == "true")
    blocked_count = sum(1 for row in rows if row.future_qualification_candidate == "false")
    qualification_allowed_count = sum(1 for row in rows if row.qualification_allowed == "true")
    tws_allowed_count = sum(1 for row in rows if row.tws_connection_allowed == "true")

    lines = [
        "# Phase 10I IBKR Contract Qualification Dry Run Report",
        "",
        "- phase: Phase 10I",
        "- scope: IBKR contract qualification dry-run plan only",
        "- input_source: " + input_source,
        "- row_count: " + str(len(rows)),
        "- future_qualification_candidate_count: " + str(future_candidate_count),
        "- blocked_count: " + str(blocked_count),
        "- qualification_allowed_count: " + str(qualification_allowed_count),
        "- tws_connection_allowed_count: " + str(tws_allowed_count),
        "- qualification_dry_run_statuses: " + (",".join(statuses) if statuses else "none"),
        "- api_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Qualification Dry Run Rows",
        "",
        "| target_id | symbol | currency | exchange | sec_type | mapping_status | qualification_dry_run_status | future_qualification_candidate | qualification_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.target_id} | {row.symbol} | {row.currency} | {row.exchange} | {row.sec_type} | {row.mapping_status} | {row.qualification_dry_run_status} | {row.future_qualification_candidate} | {row.qualification_allowed} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- IBKR contract qualification dry-run only",
            "- no TWS connection",
            "- no IBKR connection",
            "- no real contract qualification",
            "- contract_qualification_allowed=false for every row",
            "- market_data_request_allowed=false for every row",
            "- historical_data_request_allowed=false for every row",
            "- api_request_allowed=false for every row",
            "- action_allowed=false for every row",
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
