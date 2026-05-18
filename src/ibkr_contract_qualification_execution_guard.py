from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv


@dataclass
class IBKRContractQualificationExecutionGuardRow:
    target_id: str
    symbol: str
    currency: str
    exchange: str
    sec_type: str
    qualification_dry_run_status: str
    future_qualification_candidate: str
    explicit_execution_flag: str
    execution_guard_status: str
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
        "phase10j_ibkr_contract_qualification_execution_guard",
        "execution_guard_only",
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


def _guard_decision(row: dict[str, str], explicit_execution_flag: bool) -> tuple[str, str, str]:
    if row.get("future_qualification_candidate") != "true":
        return (
            "blocked_not_future_qualification_candidate",
            "dry_run_row_is_not_a_future_qualification_candidate",
            "not_future_candidate",
        )

    if not explicit_execution_flag:
        return (
            "blocked_missing_explicit_execution_flag",
            "explicit_execution_flag_required",
            "missing_explicit_execution_flag",
        )

    return (
        "blocked_phase10j_guard_only",
        "phase10j_does_not_permit_real_contract_qualification",
        "phase10j_guard_only",
    )


def build_ibkr_contract_qualification_execution_guard_rows(
    dry_run_rows: list[Any],
    tz_cfg: dict[str, str],
    explicit_execution_flag: bool = False,
) -> list[IBKRContractQualificationExecutionGuardRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[IBKRContractQualificationExecutionGuardRow] = []

    for item in dry_run_rows:
        row = _row_dict(item)
        status, block_reason, extra_flag = _guard_decision(row, explicit_execution_flag)

        rows.append(
            IBKRContractQualificationExecutionGuardRow(
                target_id=row.get("target_id", "unknown"),
                symbol=row.get("symbol", "unknown"),
                currency=row.get("currency", "unknown"),
                exchange=row.get("exchange", "unknown"),
                sec_type=row.get("sec_type", "unknown"),
                qualification_dry_run_status=row.get("qualification_dry_run_status", "unknown"),
                future_qualification_candidate=row.get("future_qualification_candidate", "false"),
                explicit_execution_flag="true" if explicit_execution_flag else "false",
                execution_guard_status=status,
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                block_reason=block_reason,
                warning_flags=_flags(status, extra_flag, row.get("warning_flags", "none")),
                notes="IBKR contract qualification execution guard only; real qualification remains blocked",
                timestamp_jst=row.get("timestamp_jst", ts_jst) or ts_jst,
                timestamp_et=row.get("timestamp_et", ts_et) or ts_et,
            )
        )

    return rows


def load_ibkr_contract_qualification_dry_run_rows_by_target(path: str) -> dict[str, dict[str, str]]:
    if not Path(path).exists():
        return {}

    with open(path, "r", encoding="utf-8", newline="") as f:
        return {
            str(row.get("target_id", "")): {k: str(v) if v is not None else "" for k, v in row.items()}
            for row in csv.DictReader(f)
            if row.get("target_id")
        }


def write_ibkr_contract_qualification_execution_guard_csv(
    path: Path,
    rows: list[IBKRContractQualificationExecutionGuardRow],
) -> None:
    fields = list(IBKRContractQualificationExecutionGuardRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_contract_qualification_execution_guard_report(
    path: Path,
    rows: list[IBKRContractQualificationExecutionGuardRow],
    input_source: str,
) -> None:
    statuses = sorted({row.execution_guard_status for row in rows})
    explicit_flag_count = sum(1 for row in rows if row.explicit_execution_flag == "true")
    future_candidate_count = sum(1 for row in rows if row.future_qualification_candidate == "true")
    qualification_allowed_count = sum(1 for row in rows if row.qualification_allowed == "true")
    tws_allowed_count = sum(1 for row in rows if row.tws_connection_allowed == "true")

    lines = [
        "# Phase 10J IBKR Contract Qualification Execution Guard Report",
        "",
        "- phase: Phase 10J",
        "- scope: IBKR contract qualification execution guard only",
        "- input_source: " + input_source,
        "- row_count: " + str(len(rows)),
        "- future_qualification_candidate_count: " + str(future_candidate_count),
        "- explicit_execution_flag_count: " + str(explicit_flag_count),
        "- qualification_allowed_count: " + str(qualification_allowed_count),
        "- tws_connection_allowed_count: " + str(tws_allowed_count),
        "- execution_guard_statuses: " + (",".join(statuses) if statuses else "none"),
        "- api_request_allowed: false",
        "- action_allowed: false",
        "",
        "## Execution Guard Rows",
        "",
        "| target_id | symbol | currency | exchange | sec_type | future_qualification_candidate | explicit_execution_flag | execution_guard_status | qualification_allowed | action_allowed |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.target_id} | {row.symbol} | {row.currency} | {row.exchange} | {row.sec_type} | {row.future_qualification_candidate} | {row.explicit_execution_flag} | {row.execution_guard_status} | {row.qualification_allowed} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- IBKR contract qualification execution guard only",
            "- explicit execution flag alone is not enough in Phase 10J",
            "- no TWS connection",
            "- no IBKR connection",
            "- no real contract qualification",
            "- qualification_allowed=false for every row",
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
