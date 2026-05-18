from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv


@dataclass
class IBKRReadOnlyQualificationSafetySummaryRow:
    section_id: str
    section_name: str
    source_layer: str
    input_row_count: str
    blocked_or_closed_count: str
    pass_or_ready_count: str
    summary_status: str
    overall_status: str
    apply_allowed: str
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
        "phase11e_ibkr_readonly_qualification_safety_summary",
        "full_safety_summary_only",
        "overall_blocked_by_default",
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


def _count(rows: list[Any], key: str, values: set[str]) -> int:
    return sum(1 for item in rows if _row_dict(item).get(key) in values)


def _sum_int(rows: list[Any], key: str) -> int:
    total = 0
    for item in rows:
        value = _row_dict(item).get(key, "0")
        try:
            total += int(value)
        except ValueError:
            total += 0
    return total


def _any_true(rows: list[Any], keys: list[str]) -> bool:
    for item in rows:
        row = _row_dict(item)
        for key in keys:
            if row.get(key) == "true":
                return True
    return False


def _blocking_summary(rows: list[Any], key: str, blocked_values: set[str]) -> str:
    reasons: list[str] = []
    for item in rows:
        row = _row_dict(item)
        status = row.get(key, "unknown")
        if status in blocked_values or status.startswith("blocked") or status in {"NO_GO", "CLOSED"}:
            reason = row.get("blocking_summary") or row.get("block_reason") or status
            if reason:
                reasons.append(reason)
    return ";".join(sorted(set(reasons))) if reasons else "none"


def _summary_row(
    section_id: str,
    section_name: str,
    source_layer: str,
    input_rows: list[Any],
    blocked_or_closed_count: int,
    pass_or_ready_count: int,
    summary_status: str,
    blocking_summary: str,
    ts_jst: str,
    ts_et: str,
) -> IBKRReadOnlyQualificationSafetySummaryRow:
    unsafe = _any_true(
        input_rows,
        [
            "apply_allowed",
            "qualification_allowed",
            "tws_connection_allowed",
            "contract_qualification_allowed",
            "market_data_request_allowed",
            "historical_data_request_allowed",
            "api_request_allowed",
            "action_allowed",
        ],
    )

    summary = blocking_summary
    if unsafe:
        summary = "unsafe_true_permission_detected;" + summary

    return IBKRReadOnlyQualificationSafetySummaryRow(
        section_id=section_id,
        section_name=section_name,
        source_layer=source_layer,
        input_row_count=str(len(input_rows)),
        blocked_or_closed_count=str(blocked_or_closed_count),
        pass_or_ready_count=str(pass_or_ready_count),
        summary_status=summary_status,
        overall_status="BLOCKED",
        apply_allowed="false",
        qualification_allowed="false",
        tws_connection_allowed="false",
        contract_qualification_allowed="false",
        market_data_request_allowed="false",
        historical_data_request_allowed="false",
        api_request_allowed="false",
        action_allowed="false",
        blocking_summary=summary,
        warning_flags=_flags("BLOCKED", summary_status, summary),
        notes="Full safety summary only; no TWS connection, no IBKR API request, no qualification, no market data, and no trading.",
        timestamp_jst=ts_jst,
        timestamp_et=ts_et,
    )


def build_ibkr_readonly_qualification_safety_summary_rows(
    go_no_go_rows: list[Any],
    config_final_gate_rows: list[Any],
    tz_cfg: dict[str, str],
) -> list[IBKRReadOnlyQualificationSafetySummaryRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)

    go_no_go_count = _count(go_no_go_rows, "go_no_go_status", {"NO_GO"})
    go_pass_ready = _sum_int(go_no_go_rows, "pass_or_ready_count")
    gate_closed_count = _count(config_final_gate_rows, "final_gate_status", {"CLOSED"})
    gate_pass_safe = _sum_int(config_final_gate_rows, "pass_or_safe_count")

    rows = [
        _summary_row(
            "10G_10M",
            "IBKR read-only qualification execution safety chain",
            "Phase 10G-10M",
            go_no_go_rows,
            go_no_go_count,
            go_pass_ready,
            "NO_GO",
            _blocking_summary(go_no_go_rows, "go_no_go_status", {"NO_GO"}),
            ts_jst,
            ts_et,
        ),
        _summary_row(
            "11A_11D",
            "IBKR read-only qualification configuration safety chain",
            "Phase 11A-11D",
            config_final_gate_rows,
            gate_closed_count,
            gate_pass_safe,
            "CLOSED",
            _blocking_summary(config_final_gate_rows, "final_gate_status", {"CLOSED"}),
            ts_jst,
            ts_et,
        ),
    ]

    rows.append(
        IBKRReadOnlyQualificationSafetySummaryRow(
            section_id="FINAL",
            section_name="Final IBKR read-only qualification full safety summary",
            source_layer="Phase 10G-10M + Phase 11A-11D",
            input_row_count=str(sum(int(row.input_row_count) for row in rows)),
            blocked_or_closed_count=str(sum(int(row.blocked_or_closed_count) for row in rows)),
            pass_or_ready_count=str(sum(int(row.pass_or_ready_count) for row in rows)),
            summary_status="BLOCKED",
            overall_status="BLOCKED",
            apply_allowed="false",
            qualification_allowed="false",
            tws_connection_allowed="false",
            contract_qualification_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            api_request_allowed="false",
            action_allowed="false",
            blocking_summary="overall_status_blocked_until_explicit_future_phase_design_and_manual_operator_review",
            warning_flags=_flags("BLOCKED", "overall_status_blocked_until_explicit_future_phase_design_and_manual_operator_review"),
            notes="Final safety status remains BLOCKED. A later explicitly reviewed phase is required before any real IBKR operation.",
            timestamp_jst=ts_jst,
            timestamp_et=ts_et,
        )
    )

    return rows


def write_ibkr_readonly_qualification_safety_summary_csv(
    path: Path,
    rows: list[IBKRReadOnlyQualificationSafetySummaryRow],
) -> None:
    fields = list(IBKRReadOnlyQualificationSafetySummaryRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_readonly_qualification_safety_summary_report(
    path: Path,
    rows: list[IBKRReadOnlyQualificationSafetySummaryRow],
    input_source: str,
) -> None:
    statuses = sorted({row.overall_status for row in rows})
    blocked_count = sum(1 for row in rows if row.overall_status == "BLOCKED")
    apply_allowed_count = sum(1 for row in rows if row.apply_allowed == "true")
    qualification_allowed_count = sum(1 for row in rows if row.qualification_allowed == "true")
    tws_allowed_count = sum(1 for row in rows if row.tws_connection_allowed == "true")
    api_allowed_count = sum(1 for row in rows if row.api_request_allowed == "true")
    action_allowed_count = sum(1 for row in rows if row.action_allowed == "true")

    lines = [
        "# Phase 11E IBKR Read-Only Qualification Full Safety Summary Report",
        "",
        "- phase: Phase 11E",
        "- scope: IBKR read-only qualification full safety summary",
        "- input_source: " + input_source,
        "- row_count: " + str(len(rows)),
        "- final_overall_status: BLOCKED",
        "- blocked_count: " + str(blocked_count),
        "- apply_allowed_count: " + str(apply_allowed_count),
        "- qualification_allowed_count: " + str(qualification_allowed_count),
        "- tws_connection_allowed_count: " + str(tws_allowed_count),
        "- api_request_allowed_count: " + str(api_allowed_count),
        "- action_allowed_count: " + str(action_allowed_count),
        "- overall_statuses: " + (",".join(statuses) if statuses else "none"),
        "",
        "## Safety Summary Rows",
        "",
        "| section_id | source_layer | input_row_count | blocked_or_closed_count | pass_or_ready_count | summary_status | overall_status | qualification_allowed | action_allowed |",
        "|---|---|---:|---:|---:|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.section_id} | {row.source_layer} | {row.input_row_count} | {row.blocked_or_closed_count} | {row.pass_or_ready_count} | {row.summary_status} | {row.overall_status} | {row.qualification_allowed} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Final Decision",
            "",
            "- Final overall status: BLOCKED",
            "- Real IBKR qualification remains blocked.",
            "- TWS connection remains blocked.",
            "- Market data requests remain blocked.",
            "- Historical data requests remain blocked.",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- IBKR read-only qualification full safety summary only",
            "- no configuration file is modified",
            "- apply_allowed=false for every row",
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
