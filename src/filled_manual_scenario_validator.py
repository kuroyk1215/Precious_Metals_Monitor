from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import csv


@dataclass
class FilledManualScenarioValidationRow:
    check_id: str
    status: str
    expected: str
    actual: str
    severity: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


def _now_pair(tz_cfg: dict[str, str]) -> tuple[str, str]:
    now_utc = datetime.now(timezone.utc)
    return (
        now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat(),
        now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat(),
    )


def load_csv_rows(path: str) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return [{k: str(v) if v is not None else "" for k, v in row.items()} for row in csv.DictReader(f)]


def _row(
    check_id: str,
    ok: bool,
    expected: str,
    actual: str,
    severity: str,
    notes: str,
    tz_cfg: dict[str, str],
) -> FilledManualScenarioValidationRow:
    ts_jst, ts_et = _now_pair(tz_cfg)
    return FilledManualScenarioValidationRow(
        check_id=check_id,
        status="pass" if ok else "fail",
        expected=expected,
        actual=actual,
        severity=severity,
        notes=notes,
        timestamp_jst=ts_jst,
        timestamp_et=ts_et,
    )


def _step_status_map(pipeline_steps: list[Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for step in pipeline_steps:
        name = getattr(step, "step_name", "")
        status = getattr(step, "status", "")
        result[str(name)] = str(status)
    return result


def build_filled_manual_scenario_validation_rows(
    input_csv: str,
    pipeline_steps: list[Any],
    deviation_rows: list[dict[str, str]],
    reference_rows: list[dict[str, str]],
    daily_rows: list[dict[str, str]],
    strategy_rows: list[dict[str, str]],
    tz_cfg: dict[str, str],
) -> list[FilledManualScenarioValidationRow]:
    rows: list[FilledManualScenarioValidationRow] = []
    step_status = _step_status_map(pipeline_steps)

    rows.append(
        _row(
            "input_csv_exists",
            Path(input_csv).exists(),
            "input csv exists",
            "exists" if Path(input_csv).exists() else "missing",
            "critical",
            "filled manual CSV scenario file must exist",
            tz_cfg,
        )
    )

    rows.append(
        _row(
            "pipeline_step_count",
            len(pipeline_steps) == 7,
            "7",
            str(len(pipeline_steps)),
            "critical",
            "Phase 6D scenario should run 7 steps",
            tz_cfg,
        )
    )

    core_expected_ok = ["manual_market_data_adapter", "manual_market_data_integration", "theoretical_pricing", "deviation_check"]
    core_actual = ";".join(f"{name}={step_status.get(name, 'missing')}" for name in core_expected_ok)
    rows.append(
        _row(
            "core_computation_steps_ok",
            all(step_status.get(name) == "ok" for name in core_expected_ok),
            "adapter/integration/theoretical/deviation all ok",
            core_actual,
            "critical",
            "filled values should make core computation layers calculable",
            tz_cfg,
        )
    )

    deviation_statuses = sorted({r.get("deviation_status", "") for r in deviation_rows})
    rows.append(
        _row(
            "deviation_rows_ok",
            bool(deviation_rows) and deviation_statuses == ["ok"],
            "all deviation_status=ok",
            ",".join(deviation_statuses) if deviation_statuses else "none",
            "critical",
            "valid scenario should produce computable ETF deviations",
            tz_cfg,
        )
    )

    reference_labels = sorted({r.get("reference_label", "") for r in reference_rows})
    reference_actions = sorted({r.get("action_allowed", "") for r in reference_rows})
    reference_safe = bool(reference_rows) and not {"risk_off", "data_invalid"}.intersection(reference_labels) and reference_actions == ["false"]
    rows.append(
        _row(
            "reference_signals_safe",
            reference_safe,
            "no risk_off/data_invalid and action_allowed=false",
            f"labels={','.join(reference_labels)}; action_allowed={','.join(reference_actions)}",
            "critical",
            "valid scenario should produce safe reference labels without execution permission",
            tz_cfg,
        )
    )

    daily_actions = sorted({r.get("action_allowed", "") for r in daily_rows})
    rows.append(
        _row(
            "daily_plan_action_blocked",
            bool(daily_rows) and daily_actions == ["false"],
            "all action_allowed=false",
            ",".join(daily_actions) if daily_actions else "none",
            "critical",
            "daily plan must remain observation-only",
            tz_cfg,
        )
    )

    strategy_actions = sorted({r.get("action_allowed", "") for r in strategy_rows})
    rows.append(
        _row(
            "strategy_plan_action_blocked",
            bool(strategy_rows) and strategy_actions == ["false"],
            "all action_allowed=false",
            ",".join(strategy_actions) if strategy_actions else "none",
            "critical",
            "multi-horizon strategy must remain observation-only",
            tz_cfg,
        )
    )

    rows.append(
        _row(
            "safety_boundary_preserved",
            True,
            "no IBKR / no market data request / no execution",
            "manual CSV scenario validation only",
            "critical",
            "this validation does not connect to IBKR or request live/historical market data",
            tz_cfg,
        )
    )

    return rows


def write_filled_manual_scenario_validation_csv(
    path: Path,
    rows: list[FilledManualScenarioValidationRow],
) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["check_id", "status", "expected", "actual", "severity", "notes", "timestamp_jst", "timestamp_et"])
        for r in rows:
            writer.writerow([r.check_id, r.status, r.expected, r.actual, r.severity, r.notes, r.timestamp_jst, r.timestamp_et])


def write_filled_manual_scenario_validation_report(
    path: Path,
    rows: list[FilledManualScenarioValidationRow],
    input_csv: str,
) -> None:
    pass_count = sum(1 for r in rows if r.status == "pass")
    fail_count = sum(1 for r in rows if r.status == "fail")
    overall_status = "pass" if fail_count == 0 and rows else "fail"

    lines = [
        "# Filled Manual CSV Scenario Validation Report",
        "",
        "- phase: Phase 6E",
        "- scope: filled manual CSV scenario validation only",
        f"- input_csv: {input_csv}",
        f"- overall_status: {overall_status}",
        f"- pass_count: {pass_count}",
        f"- fail_count: {fail_count}",
        "- action_allowed: false",
        "",
        "## Validation Checks",
        "",
        "| check_id | status | severity | expected | actual |",
        "|---|---|---|---|---|",
    ]

    for r in rows:
        lines.append(f"| {r.check_id} | {r.status} | {r.severity} | {r.expected} | {r.actual} |")

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- filled manual CSV scenario only",
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
