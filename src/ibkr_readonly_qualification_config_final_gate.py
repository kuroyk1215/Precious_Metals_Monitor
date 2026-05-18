from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv


@dataclass
class IBKRReadOnlyQualificationConfigFinalGateRow:
    layer_id: str
    layer_name: str
    input_row_count: str
    pass_or_safe_count: str
    manual_required_count: str
    violation_count: str
    final_gate_status: str
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
        "phase11d_ibkr_readonly_qualification_config_final_gate",
        "config_final_gate_only",
        "gate_closed_by_default",
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
        if status in blocked_values or status.startswith("blocked"):
            reason = row.get("block_reason", status)
            if reason:
                reasons.append(reason)
    return ";".join(sorted(set(reasons))) if reasons else "none"


def _layer_row(
    layer_id: str,
    layer_name: str,
    input_rows: list[Any],
    pass_or_safe_count: int,
    manual_required_count: int,
    violation_count: int,
    blocking_summary: str,
    ts_jst: str,
    ts_et: str,
) -> IBKRReadOnlyQualificationConfigFinalGateRow:
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

    return IBKRReadOnlyQualificationConfigFinalGateRow(
        layer_id=layer_id,
        layer_name=layer_name,
        input_row_count=str(len(input_rows)),
        pass_or_safe_count=str(pass_or_safe_count),
        manual_required_count=str(manual_required_count),
        violation_count=str(violation_count),
        final_gate_status="CLOSED",
        apply_allowed="false",
        qualification_allowed="false",
        tws_connection_allowed="false",
        contract_qualification_allowed="false",
        market_data_request_allowed="false",
        historical_data_request_allowed="false",
        api_request_allowed="false",
        action_allowed="false",
        blocking_summary=summary,
        warning_flags=_flags("CLOSED", summary),
        notes="Configuration final gate only; no file mutation, no TWS connection, and no IBKR API request is performed.",
        timestamp_jst=ts_jst,
        timestamp_et=ts_et,
    )


def build_ibkr_readonly_qualification_config_final_gate_rows(
    template_rows: list[Any],
    audit_rows: list[Any],
    apply_plan_rows: list[Any],
    tz_cfg: dict[str, str],
) -> list[IBKRReadOnlyQualificationConfigFinalGateRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)

    template_safe = _count(
        template_rows,
        "template_status",
        {"template_safe_disabled", "template_required_true", "template_candidate_value"},
    )
    template_manual = _count(template_rows, "template_status", {"template_requires_manual_config"})

    audit_safe = _count(
        audit_rows,
        "config_audit_status",
        {"blocked_or_disabled", "required_true", "candidate_value_configured"},
    )
    audit_manual = _count(audit_rows, "config_audit_status", {"manual_config_required"})
    audit_violation = _count(audit_rows, "violation_detected", {"true"})

    apply_safe = _count(apply_plan_rows, "apply_plan_status", {"keep_disabled", "keep_required_true"})
    apply_manual = _count(
        apply_plan_rows,
        "apply_plan_status",
        {"blocked_manual_config_required", "manual_review_candidate_value"},
    )
    apply_violation = _count(apply_plan_rows, "apply_plan_status", {"blocked_config_violation"})

    rows = [
        _layer_row(
            "11A",
            "Config template",
            template_rows,
            template_safe,
            template_manual,
            0,
            _blocking_summary(template_rows, "template_status", {"template_requires_manual_config"}),
            ts_jst,
            ts_et,
        ),
        _layer_row(
            "11B",
            "Config audit",
            audit_rows,
            audit_safe,
            audit_manual,
            audit_violation,
            _blocking_summary(audit_rows, "config_audit_status", {"manual_config_required", "config_violation_blocked"}),
            ts_jst,
            ts_et,
        ),
        _layer_row(
            "11C",
            "Config apply plan",
            apply_plan_rows,
            apply_safe,
            apply_manual,
            apply_violation,
            _blocking_summary(
                apply_plan_rows,
                "apply_plan_status",
                {"blocked_manual_config_required", "manual_review_candidate_value", "blocked_config_violation"},
            ),
            ts_jst,
            ts_et,
        ),
    ]

    rows.append(
        IBKRReadOnlyQualificationConfigFinalGateRow(
            layer_id="FINAL",
            layer_name="Final config gate",
            input_row_count=str(sum(int(row.input_row_count) for row in rows)),
            pass_or_safe_count=str(sum(int(row.pass_or_safe_count) for row in rows)),
            manual_required_count=str(sum(int(row.manual_required_count) for row in rows)),
            violation_count=str(sum(int(row.violation_count) for row in rows)),
            final_gate_status="CLOSED",
            apply_allowed="false",
            qualification_allowed="false",
            tws_connection_allowed="false",
            contract_qualification_allowed="false",
            market_data_request_allowed="false",
            historical_data_request_allowed="false",
            api_request_allowed="false",
            action_allowed="false",
            blocking_summary="final_config_gate_closed_until_manual_config_and_operator_review_complete",
            warning_flags=_flags("CLOSED", "final_config_gate_closed_until_manual_config_and_operator_review_complete"),
            notes="Final configuration gate remains CLOSED by design.",
            timestamp_jst=ts_jst,
            timestamp_et=ts_et,
        )
    )

    return rows


def write_ibkr_readonly_qualification_config_final_gate_csv(
    path: Path,
    rows: list[IBKRReadOnlyQualificationConfigFinalGateRow],
) -> None:
    fields = list(IBKRReadOnlyQualificationConfigFinalGateRow.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([getattr(row, field) for field in fields])


def write_ibkr_readonly_qualification_config_final_gate_report(
    path: Path,
    rows: list[IBKRReadOnlyQualificationConfigFinalGateRow],
    input_source: str,
) -> None:
    statuses = sorted({row.final_gate_status for row in rows})
    closed_count = sum(1 for row in rows if row.final_gate_status == "CLOSED")
    manual_required_count = sum(int(row.manual_required_count) for row in rows if row.layer_id != "FINAL")
    violation_count = sum(int(row.violation_count) for row in rows if row.layer_id != "FINAL")
    apply_allowed_count = sum(1 for row in rows if row.apply_allowed == "true")
    qualification_allowed_count = sum(1 for row in rows if row.qualification_allowed == "true")
    tws_allowed_count = sum(1 for row in rows if row.tws_connection_allowed == "true")
    api_allowed_count = sum(1 for row in rows if row.api_request_allowed == "true")
    action_allowed_count = sum(1 for row in rows if row.action_allowed == "true")

    lines = [
        "# Phase 11D IBKR Read-Only Qualification Config Final Gate Report",
        "",
        "- phase: Phase 11D",
        "- scope: IBKR read-only qualification config final gate",
        "- input_source: " + input_source,
        "- row_count: " + str(len(rows)),
        "- final_gate_status: CLOSED",
        "- closed_count: " + str(closed_count),
        "- manual_required_count: " + str(manual_required_count),
        "- violation_count: " + str(violation_count),
        "- apply_allowed_count: " + str(apply_allowed_count),
        "- qualification_allowed_count: " + str(qualification_allowed_count),
        "- tws_connection_allowed_count: " + str(tws_allowed_count),
        "- api_request_allowed_count: " + str(api_allowed_count),
        "- action_allowed_count: " + str(action_allowed_count),
        "- final_gate_statuses: " + (",".join(statuses) if statuses else "none"),
        "",
        "## Final Gate Rows",
        "",
        "| layer_id | layer_name | input_row_count | pass_or_safe_count | manual_required_count | violation_count | final_gate_status | apply_allowed | action_allowed |",
        "|---|---|---:|---:|---:|---:|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row.layer_id} | {row.layer_name} | {row.input_row_count} | {row.pass_or_safe_count} | {row.manual_required_count} | {row.violation_count} | {row.final_gate_status} | {row.apply_allowed} | {row.action_allowed} |"
        )

    lines.extend(
        [
            "",
            "## Final Decision",
            "",
            "- Final config gate status: CLOSED",
            "- Configuration apply remains blocked.",
            "- Real IBKR qualification remains blocked.",
            "- TWS connection remains blocked.",
            "- Market data requests remain blocked.",
            "- Trading actions remain blocked.",
            "",
            "## Safety Statement",
            "",
            "- IBKR read-only qualification config final gate only",
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
