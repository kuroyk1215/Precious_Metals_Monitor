from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv


@dataclass
class IBKRReadOnlyQualificationGoNoGoRow:
    phase_id: str
    phase_name: str
    input_row_count: str
    pass_or_ready_count: str
    blocked_count: str
    go_no_go_status: str
    qualification_allowed: str
    tws_connection_allowed: str
    contract_qualification_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    api_request_allowed: str
    action_allowed: str
    blocking_summary: str
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
        "phase10m_ibkr_readonly_qualification_go_no_go",
        "go_no_go_summary_only",
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


def _count(rows: list[Any], key: str, value: str) -> int:
    return sum(1 for item in rows if _row_dict(item).get(key) == value)


def _any_true(rows: list[Any], keys: list[str]) -> bool:
    for item in rows:
        row = _row_dict(item)
        for key in keys:
            if row.get(key) == "true":
                return True
    return False


def _summary_row(
    phase_id: str,
    phase_name: str,
    input_rows: list[Any],
    pass_or_ready_count: int,
    blocked_count: int,
    block_reasons: list[str],
    ts_jst: str,
    ts_et: str,
) -> IBKRReadOnlyQualificationGoNoGoRow:
    unsafe_true = _any_true(
        input_rows,
        [
            "qualification_allowed",
            "tws_connection_allowed",
            "contract_qualification_allowed",
            "market_data_request_allowed",
            "historical_data_request_allowed",
            "api_request_allowed",
            "action_allowed",
        ],
    )

    blocking_summary = ";".join(sorted(set(block_reasons))) if block_reasons else "none"
    status = "NO_GO"

    if unsafe_true:
        blocking_summary = "unsafe_true_permission_detected;" + blocking_summary

    return IBKRReadOnlyQualificationGoNoGoRow(
        phase_id=phase_id,
        phase_name=phase_name,
        input_row_count=str(len(input_rows)),
        pass_or_ready_count=str(pass_or_ready_count),
        blocked_count=str(blocked_count),
        go_no_go_status=status,
        qualification_allowed="false",
        tws_connection_allowed="false",
        contract_qualification_allowed="false",
        market_data_request_allowed="false",
        historical_data_request_allowed="false",
        api_request_allowed="false",
        action_allowed="false",
        blocking_summary=blocking_summary,
        warning_flags=_flags(status, blocking_summary),
        notes="Go/No-Go summary only; this command never enables TWS, qualification, market data, or trading.",
        timestamp_jst=ts_jst,
        timestamp_et=ts_et,
    )


def _block_reasons(rows: list[Any], status_key: str, block_values: set[str]) -> list[str]:
    reasons: list[str] = []
    for item in rows:
        row = _row_dict(item)
        status = row.get(status_key, "unknown")
        if status in block_values or status.startswith("blocked") or status.startswith("closed"):
            reason = row.get("block_reason", status)
            if reason:
                reasons.append(reason)
    return reasons


def build_ibkr_readonly_qualification_go_no_go_rows(
    adapter_rows: list[Any],
    mapping_rows: list[Any],
    dry_run_rows: list[Any],
    execution_guard_rows: list[Any],
    precheck_rows: list[Any],
    runbook_rows: list[Any],
    tz_cfg: dict[str, str],
) -> list[IBKRReadOnlyQualificationGoNoGoRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)

    adapter_blocked = _count(adapter_rows, "adapter_status", "blocked_provider_disabled")
    mapping_ready = _count(mapping_rows, "mapping_status", "candidate_mapping_ready")
    mapping_blocked = len(mapping_rows) - mapping_ready
    dry_future = _count(dry_run_rows, "future_qualification_candidate", "true")
    dry_blocked = len(dry_run_rows) - dry_future
    guard_blocked = len(execution_guard_rows)
    precheck_pass = _count(precheck_rows, "precheck_status", "precheck_pass")
    precheck_blocked = _count(precheck_rows, "precheck_status", "precheck_blocked")
    runbook_ready = _count(runbook_rows, "runbook_status", "ready_for_manual_review_only")
    runbook_blocked = _count(runbook_rows, "runbook_status", "blocked_by_precheck")

    rows = [
        _summary_row(
            "10G",
            "IBKR adapter skeleton",
            adapter_rows,
            0,
            adapter_blocked,
            _block_reasons(adapter_rows, "adapter_status", {"blocked_provider_disabled"}),
            ts_jst,
            ts_et,
        ),
        _summary_row(
            "10H",
            "IBKR contract mapping plan",
            mapping_rows,
            mapping_ready,
            mapping_blocked,
            _block_reasons(mapping_rows, "mapping_status", {"candidate_review_required", "manual_review_required"}),
            ts_jst,
            ts_et,
        ),
        _summary_row(
            "10I",
            "IBKR contract qualification dry run",
            dry_run_rows,
            dry_future,
            dry_blocked,
            _block_reasons(dry_run_rows, "qualification_dry_run_status", {"blocked_mapping_review_required", "blocked_manual_review_required"}),
            ts_jst,
            ts_et,
        ),
        _summary_row(
            "10J",
            "IBKR contract qualification execution guard",
            execution_guard_rows,
            0,
            guard_blocked,
            _block_reasons(execution_guard_rows, "execution_guard_status", {"blocked_missing_explicit_execution_flag", "blocked_not_future_qualification_candidate", "blocked_phase10j_guard_only"}),
            ts_jst,
            ts_et,
        ),
        _summary_row(
            "10K",
            "IBKR read-only qualification precheck",
            precheck_rows,
            precheck_pass,
            precheck_blocked,
            _block_reasons(precheck_rows, "precheck_status", {"precheck_blocked"}),
            ts_jst,
            ts_et,
        ),
        _summary_row(
            "10L",
            "IBKR read-only qualification runbook",
            runbook_rows,
            runbook_ready,
            runbook_blocked,
            _block_reasons(runbook_rows, "runbook_status", {"blocked_by_precheck"}),
            ts_jst,
            ts_et,
        ),
    ]

    rows.append(
        IBKRReadOnlyQualificationGoNoGoRow(
            phase_id="FINAL",
            phase_name="Final IBKR read-only qualification go/no-go",
            input_row_count=str(sum(int(row.input_row_count) for row in rows)),
            pass_or_ready_count=str(sum(int(row.pass_or_ready_count) for row in rows)),
            blocked_count=str(sum(int(row.blocked_count) for row in rows)),
            go_no_go_status="NO_GO",
            qualification_allowed="false",
            tws_connection_allowed="false",
            contract_qualification_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            api_request_allowed="false",
            action_allowed="false",
            blocking_summary="final_status_no_go_until_operator_resolves_precheck_and_mapping_blocks",
            warning_flags=_flags("NO_GO", "final_status_no_go_until_operator_resolves_precheck_and_mapping_blocks"),
            notes="Final decision remains NO_GO; a later phase must be explicitly designed before any real IBKR action.",
            timestamp_jst=ts_jst,
            timestamp_et=ts_et,
        )
    )

    return rows


def write_ibkr_readonly_qualification_go_no_go_csv(
    path: Path,
    rows: list[IBKRReadOnlyQualificationGoNoGoRow],
) -> None:
    fields = list(IBKRReadOnlyQualificationGoNoGoRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_readonly_qualification_go_no_go_report(
    path: Path,
    rows: list[IBKRReadOnlyQualificationGoNoGoRow],
    input_source: str,
) -> None:
    statuses = sorted({row.go_no_go_status for row in rows})
    no_go_count = sum(1 for row in rows if row.go_no_go_status == "NO_GO")
    qualification_allowed_count = sum(1 for row in rows if row.qualification_allowed == "true")
    tws_allowed_count = sum(1 for row in rows if row.tws_connection_allowed == "true")
    api_allowed_count = sum(1 for row in rows if row.api_request_allowed == "true")
    action_allowed_count = sum(1 for row in rows if row.action_allowed == "true")

    final_status = "NO_GO"
    for row in rows:
        if row.phase_id == "FINAL":
            final_status = row.go_no_go_status

    lines = [
        "# Phase 10M IBKR Read-Only Qualification Go/No-Go Report",
        "",
        "- phase: Phase 10M",
        "- scope: IBKR read-only qualification final go/no-go summary",
        "- input_source: " + input_source,
        "- row_count: " + str(len(rows)),
        "- final_go_no_go_status: " + final_status,
        "- no_go_count: " + str(no_go_count),
        "- qualification_allowed_count: " + str(qualification_allowed_count),
        "- tws_connection_allowed_count: " + str(tws_allowed_count),
        "- api_request_allowed_count: " + str(api_allowed_count),
        "- action_allowed_count: " + str(action_allowed_count),
        "- go_no_go_statuses: " + (",".join(statuses) if statuses else "none"),
        "",
        "## Go/No-Go Rows",
        "",
        "| phase_id | phase_name | input_row_count | pass_or_ready_count | blocked_count | go_no_go_status | qualification_allowed | action_allowed |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.phase_id} | {row.phase_name} | {row.input_row_count} | {row.pass_or_ready_count} | {row.blocked_count} | {row.go_no_go_status} | {row.qualification_allowed} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Final Decision",
            "",
            "- Final status: NO_GO",
            "- Real IBKR qualification remains blocked.",
            "- TWS connection remains blocked.",
            "- Market data requests remain blocked.",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- IBKR read-only qualification go/no-go summary only",
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
