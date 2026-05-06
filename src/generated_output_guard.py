from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import csv
import fnmatch


GENERATED_OUTPUT_RULES = [
    ("*.csv", "runtime_csv", "Generated runtime CSV outputs should usually not be committed."),
    ("reports/*_report.md", "runtime_report", "Generated runtime markdown reports should usually not be committed."),
    ("reports/latest_report.md", "runtime_report", "Generated latest report should usually not be committed."),
    ("ibkr_smoke_log.csv", "runtime_log", "Generated IBKR smoke log should usually not be committed."),
    ("precious_metals_signal_log.csv", "runtime_log", "Generated monitor signal log should usually not be committed."),
    ("conversion_factor_calibration_log.csv", "runtime_log", "Generated calibration log should usually not be committed."),
    ("historical_quality_gate_log.csv", "runtime_log", "Generated quality gate log should usually not be committed."),
    ("ibkr_historical_fetch_log.csv", "runtime_log", "Generated historical fetch log should usually not be committed."),
    ("data/raw/*", "runtime_raw_data", "Generated raw data candidates should usually not be committed unless explicitly promoted."),
]

ALLOWED_STATIC_FILES = {
    "data/manual_market_data_template.csv",
    "data/manual_market_data_sample_valid.csv",
}


@dataclass
class GeneratedOutputGuardRow:
    path: str
    category: str
    exists: str
    safe_to_commit: str
    recommendation: str
    removal_command: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


def _now_pair(tz_cfg: dict[str, str]) -> tuple[str, str]:
    now_utc = datetime.now(timezone.utc)
    return (
        now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat(),
        now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat(),
    )


def _matches_rule(path: str) -> tuple[str, str]:
    for pattern, category, notes in GENERATED_OUTPUT_RULES:
        if fnmatch.fnmatch(path, pattern):
            return category, notes
    return "unknown", "No generated-output rule matched."


def _should_exclude(path: Path) -> bool:
    text = str(path)
    parts = set(path.parts)
    if ".git" in parts or ".venv" in parts or "__pycache__" in parts:
        return True
    if text.endswith(".pyc"):
        return True
    return False


def scan_generated_outputs(root: Path, tz_cfg: dict[str, str]) -> list[GeneratedOutputGuardRow]:
    ts_jst, ts_et = _now_pair(tz_cfg)
    rows: list[GeneratedOutputGuardRow] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file() or _should_exclude(path):
            continue

        rel = path.relative_to(root).as_posix()
        if rel in ALLOWED_STATIC_FILES:
            continue

        category, notes = _matches_rule(rel)
        if category == "unknown":
            continue

        rows.append(
            GeneratedOutputGuardRow(
                path=rel,
                category=category,
                exists="true",
                safe_to_commit="false",
                recommendation="remove_before_commit",
                removal_command=f"rm -f {rel}",
                notes=notes,
                timestamp_jst=ts_jst,
                timestamp_et=ts_et,
            )
        )

    return rows


def write_generated_output_guard_csv(path: Path, rows: list[GeneratedOutputGuardRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "path",
                "category",
                "exists",
                "safe_to_commit",
                "recommendation",
                "removal_command",
                "notes",
                "timestamp_jst",
                "timestamp_et",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.path,
                    r.category,
                    r.exists,
                    r.safe_to_commit,
                    r.recommendation,
                    r.removal_command,
                    r.notes,
                    r.timestamp_jst,
                    r.timestamp_et,
                ]
            )


def write_generated_output_guard_report(path: Path, rows: list[GeneratedOutputGuardRow]) -> None:
    lines = [
        "# Generated Output Cleanup Guard Report",
        "",
        "- phase: Phase 6H",
        "- scope: local generated-output detection only",
        "- action: report only; no deletion is performed",
        f"- detected_count: {len(rows)}",
        "",
        "## Detected Generated Outputs",
        "",
        "| path | category | safe_to_commit | recommendation | removal_command |",
        "|---|---|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r.path} | {r.category} | {r.safe_to_commit} | {r.recommendation} | `{r.removal_command}` |"
        )

    if not rows:
        lines.append("| none | none | n/a | no generated outputs detected | n/a |")

    lines.extend(
        [
            "",
            "## Allowed Static Files",
            "",
            "- data/manual_market_data_template.csv",
            "- data/manual_market_data_sample_valid.csv",
            "",
            "## Safety Statement",
            "",
            "- report only",
            "- no file deletion",
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
