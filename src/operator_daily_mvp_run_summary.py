from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union


TRUE_TEXT = "true"
FALSE_TEXT = "false"

READY = "DAILY_MVP_RUN_READY"
PARTIAL = "DAILY_MVP_RUN_PARTIAL"
FAILED = "DAILY_MVP_RUN_FAILED"
SAFETY_REVIEW_REQUIRED = "DAILY_MVP_RUN_SAFETY_REVIEW_REQUIRED"

SAFETY_FIELDS = (
    "action_allowed",
    "broker_execution_triggered",
    "historical_data_request_triggered",
    "account_read_triggered",
    "position_read_triggered",
    "telegram_send_triggered",
)

FORBIDDEN_OPERATOR_WORDS = (
    "BUY",
    "SELL",
    "ORDER",
    "CANCEL",
    "REBALANCE",
    "AUTO_TRADE",
    "EXECUTE",
)

STEP_NAMES = (
    "daily_operator_handoff_summary",
    "latest_artifact_entrypoint",
    "research_trading_plan",
    "watchlist_universe",
    "telegram_notification_gate",
    "local_dashboard",
)

STEP_OUTPUTS: Dict[str, Tuple[str, str]] = {
    "daily_operator_handoff_summary": ("daily_operator_handoff_summary.csv", "reports/daily_operator_handoff_summary.md"),
    "latest_artifact_entrypoint": ("latest_daily_operator_handoff_summary.csv", "reports/latest_operator_handoff_summary.md"),
    "research_trading_plan": ("research_trading_plan.csv", "reports/research_trading_plan_report.md"),
    "watchlist_universe": ("watchlist_universe.csv", "reports/watchlist_universe_report.md"),
    "telegram_notification_gate": ("telegram_notification_gate.csv", "reports/telegram_notification_gate_report.md"),
    "local_dashboard": ("", "reports/dashboard.html"),
}

SUMMARY_FIELDS = (
    "run_id",
    "run_timestamp",
    "step_name",
    "script_path",
    "step_status",
    "output_csv",
    "output_report",
    "important_status",
    "action_allowed",
    "broker_execution_triggered",
    "historical_data_request_triggered",
    "account_read_triggered",
    "position_read_triggered",
    "telegram_send_triggered",
    "offline_only",
    "notes",
)

PathLike = Union[str, Path]


@dataclass(frozen=True)
class StepResult:
    step_name: str
    script_path: str
    exit_code: int
    notes: str = ""


def _clean(value: object) -> str:
    return str(value or "").strip()


def _lower(value: object) -> str:
    return _clean(value).lower()


def _truthy(value: object) -> bool:
    return _lower(value) in {"1", "yes", "y", "true", "triggered", "allowed"}


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _run_id() -> str:
    return "daily_mvp_run_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")


def read_step_results(path: PathLike) -> List[StepResult]:
    rows: List[StepResult] = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            step_name, script_path, exit_code, notes = parts[:4]
            rows.append(StepResult(step_name, script_path, int(exit_code), notes))
    return rows


def _read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.suffix.lower() != ".csv":
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _artifact_safety(root: Path, relative_path: str) -> Tuple[Dict[str, str], List[str]]:
    flags = {field: FALSE_TEXT for field in SAFETY_FIELDS}
    notes: List[str] = []
    if not relative_path:
        return flags, notes
    path = root / relative_path
    for row_index, row in enumerate(_read_csv_rows(path), start=1):
        if _truthy(row.get("action_allowed")):
            flags["action_allowed"] = TRUE_TEXT
            notes.append(f"{relative_path}:row_{row_index}:action_allowed")
        for field in SAFETY_FIELDS[1:]:
            if _truthy(row.get(field)):
                flags[field] = TRUE_TEXT
                notes.append(f"{relative_path}:row_{row_index}:{field}")
    return flags, notes


def _important_status(root: Path, output_csv: str, output_report: str, step_status: str) -> str:
    for relative_path in (output_csv,):
        rows = _read_csv_rows(root / relative_path) if relative_path else []
        values: List[str] = []
        for row in rows:
            for key in ("top_level_status", "dashboard_status", "research_plan_status", "universe_status", "telegram_send_status"):
                value = _clean(row.get(key))
                if value and value not in values:
                    values.append(value)
        if values:
            return ",".join(values[:4])
    report_path = root / output_report if output_report else None
    if report_path and report_path.exists():
        text = report_path.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"(top_level_status|dashboard_status)=([A-Z0-9_]+)", text)
        if match:
            return match.group(2)
    return step_status


def _contains_forbidden_operator_instruction(text: str) -> bool:
    upper = text.upper()
    for word in FORBIDDEN_OPERATOR_WORDS:
        if re.search(rf"(?<![A-Z0-9_]){re.escape(word)}(?![A-Z0-9_])", upper):
            return True
    return False


def forbidden_operator_instruction_issues(root: Path, rows: Sequence[Dict[str, str]]) -> List[str]:
    issues: List[str] = []
    action_fields = ("recommended_operator_action", "recommended_notification_action", "next_manual_operator_step")
    for summary_row in rows:
        output_csv = summary_row.get("output_csv", "")
        if output_csv:
            for row_index, artifact_row in enumerate(_read_csv_rows(root / output_csv), start=1):
                for field in action_fields:
                    value = _clean(artifact_row.get(field))
                    if value and _contains_forbidden_operator_instruction(value):
                        issues.append(f"{output_csv}:row_{row_index}:{field}")
    return issues


def build_summary_rows(root: PathLike, step_results: Sequence[StepResult]) -> Tuple[str, List[Dict[str, str]], List[str]]:
    root_path = Path(root)
    run_id = _run_id()
    timestamp = _now_timestamp()
    by_step = {result.step_name: result for result in step_results}
    rows: List[Dict[str, str]] = []
    safety_notes: List[str] = []

    for step_name in STEP_NAMES:
        result = by_step.get(step_name)
        output_csv, output_report = STEP_OUTPUTS[step_name]
        status = "SKIPPED" if result is None else "PASS" if result.exit_code == 0 else "FAIL"
        flags, notes = _artifact_safety(root_path, output_csv)
        safety_notes.extend(notes)
        row = {
            "run_id": run_id,
            "run_timestamp": timestamp,
            "step_name": step_name,
            "script_path": result.script_path if result else "",
            "step_status": status,
            "output_csv": output_csv,
            "output_report": output_report,
            "important_status": _important_status(root_path, output_csv, output_report, status),
            **flags,
            "offline_only": TRUE_TEXT,
            "notes": result.notes if result else "step_not_attempted",
        }
        rows.append(row)

    forbidden = forbidden_operator_instruction_issues(root_path, rows)
    safety_notes.extend(f"forbidden_operator_instruction:{issue}" for issue in forbidden)

    any_safety = any(row[field] == TRUE_TEXT for row in rows for field in SAFETY_FIELDS) or bool(forbidden)
    any_required_failed = any(row["step_status"] != "PASS" for row in rows)
    all_core_artifacts_exist = all(
        ((not csv_path) or (root_path / csv_path).exists()) and ((not report_path) or (root_path / report_path).exists())
        for csv_path, report_path in STEP_OUTPUTS.values()
    )

    if any_safety:
        top_status = SAFETY_REVIEW_REQUIRED
    elif any_required_failed and all_core_artifacts_exist:
        top_status = PARTIAL
    elif any_required_failed:
        top_status = FAILED
    else:
        top_status = READY

    if safety_notes:
        note_text = "safety_review=" + ";".join(safety_notes)
        rows[0]["notes"] = rows[0]["notes"] + "; " + note_text if rows[0]["notes"] else note_text
    return top_status, rows, safety_notes


def write_summary_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SUMMARY_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _artifact_link(path: str) -> str:
    return f"[{path}]({path})" if path else "N/A"


def build_markdown_report(top_status: str, rows: Sequence[Dict[str, str]], safety_notes: Sequence[str]) -> str:
    step_table = "\n".join(
        f"| {row['step_name']} | {row['step_status']} | {row['important_status']} | {row['output_csv'] or 'N/A'} | {row['output_report'] or 'N/A'} |"
        for row in rows
    )
    links: List[str] = []
    for row in rows:
        if row["output_csv"]:
            links.append(f"- {_artifact_link(row['output_csv'])}")
        if row["output_report"]:
            links.append(f"- {_artifact_link(row['output_report'])}")
    warnings = "\n".join(f"- {note}" for note in safety_notes) if safety_notes else "- none"
    failed = [row for row in rows if row["step_status"] != "PASS"]
    if failed:
        warnings += "\n" + "\n".join(f"- {row['step_name']} status={row['step_status']} notes={row['notes']}" for row in failed)

    safety_lines = []
    for field in SAFETY_FIELDS:
        value = TRUE_TEXT if any(row[field] == TRUE_TEXT for row in rows) else FALSE_TEXT
        safety_lines.append(f"- {field}={value}")
    safety_lines.append("- offline_only=true")
    safety_lines.append("- tws_or_ib_gateway_connection_attempted=false")
    safety_lines.append("- market_data_request_triggered=false")

    return "\n".join(
        [
            "# Operator Daily MVP Run Summary",
            "",
            "## Top-level Run Status",
            "",
            f"- top_level_status={top_status}",
            "",
            "## Step Table",
            "",
            "| step_name | step_status | important_status | output_csv | output_report |",
            "|---|---|---|---|---|",
            step_table,
            "",
            "## Generated Artifact Links",
            "",
            *links,
            "",
            "## Safety Summary",
            "",
            *safety_lines,
            "",
            "## Failure / Warning Section",
            "",
            warnings,
            "",
            "## Next Manual Operator Step",
            "",
            "- Review the generated local artifacts and record any operator decision outside this offline run wrapper.",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, top_status: str, rows: Sequence[Dict[str, str]], safety_notes: Sequence[str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(top_status, rows, safety_notes), encoding="utf-8")


def generate_summary(
    *,
    root: PathLike = ".",
    step_results_path: PathLike,
    output_csv: PathLike = "operator_daily_mvp_run_summary.csv",
    output_report: PathLike = "reports/operator_daily_mvp_run_summary.md",
) -> Tuple[str, List[Dict[str, str]]]:
    root_path = Path(root)
    top_status, rows, safety_notes = build_summary_rows(root_path, read_step_results(step_results_path))
    write_summary_csv(root_path / output_csv, rows)
    write_markdown_report(root_path / output_report, top_status, rows, safety_notes)
    return top_status, rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an offline daily MVP run summary from wrapper step results.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--step-results", required=True)
    parser.add_argument("--output-csv", default="operator_daily_mvp_run_summary.csv")
    parser.add_argument("--output-report", default="reports/operator_daily_mvp_run_summary.md")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    top_status, rows = generate_summary(
        root=args.root,
        step_results_path=args.step_results,
        output_csv=args.output_csv,
        output_report=args.output_report,
    )
    print("[PASS] Operator daily MVP run summary generated")
    print(f"top_level_status={top_status}")
    for field in SAFETY_FIELDS:
        value = TRUE_TEXT if any(row[field] == TRUE_TEXT for row in rows) else FALSE_TEXT
        print(f"{field}={value}")
    print("offline_only=true")
    print("dashboard path: reports/dashboard.html")
    return 0 if top_status in {READY, PARTIAL} else 1


if __name__ == "__main__":
    raise SystemExit(main())
