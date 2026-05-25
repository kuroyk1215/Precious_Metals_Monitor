from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

CONTINUITY_FIELDS = (
    "generated_at",
    "source_file",
    "source_exists",
    "source_type",
    "detected_status",
    "detected_timestamp",
    "archive_role",
    "continuity_status",
    "operator_next_step",
)

INDEX_SOURCES = (
    ("operator_real_marketdata_smoke_summary.csv", "marketdata_smoke_source"),
    ("operator_real_marketdata_smoke_archive.csv", "marketdata_smoke_archive"),
    ("operator_real_marketdata_decision_gate.csv", "marketdata_decision_gate"),
    ("operator_real_marketdata_latest.csv", "marketdata_latest_pointer"),
    ("operator_real_marketdata_daily_run_summary.csv", "daily_marketdata_summary"),
    ("operator_real_quote_normalization.csv", "quote_normalization"),
    ("operator_real_quote_signal_bridge.csv", "quote_signal_bridge"),
    ("operator_daily_real_market_report.csv", "daily_real_market_report"),
    ("operator_real_market_mvp_status.csv", "mvp_status"),
    ("operator_real_market_archive_compare.csv", "archive_compare"),
    ("operator_signal_threshold_explainer.csv", "threshold_explainer"),
    ("operator_strategy_quality_report.csv", "strategy_quality"),
    ("operator_daily_checklist.csv", "daily_checklist"),
    ("operator_real_market_mvp_regression.csv", "mvp_regression"),
    ("operator_daily_master_run_summary.csv", "master_run"),
    ("reports/operator_daily_master_run_report.md", "master_run_report"),
)

STATUS_FIELDS = (
    "master_status",
    "mvp_status",
    "quality_status",
    "regression_status",
    "check_status",
    "latest_status",
    "operator_decision",
    "normalized_status",
    "signal_bridge_status",
    "real_quote_state",
    "status_consistency",
    "threshold_status",
    "top_level_status",
    "diagnostic_category",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_rows(path: PathLike) -> List[Dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _source_type(path: Path) -> str:
    if path.suffix.lower() == ".csv":
        return "csv"
    if path.suffix.lower() == ".md":
        return "markdown"
    return path.suffix.lower().lstrip(".") or "unknown"


def _status_from_row(row: Dict[str, str]) -> str:
    for field in STATUS_FIELDS:
        value = str(row.get(field, "")).strip()
        if value:
            return value
    return "STATUS_NOT_DETECTED"


def _timestamp_from_row(row: Dict[str, str], path: Path) -> str:
    for field in ("generated_at", "detected_timestamp", "quote_time", "timestamp"):
        value = str(row.get(field, "")).strip()
        if value:
            return value
    if path.exists():
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat()
    return ""


def _markdown_status(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"([a-z_]+status)=([A-Z0-9_]+)", text)
    if match:
        return match.group(2)
    return "MARKDOWN_REPORT_PRESENT"


def _markdown_timestamp(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat()


def build_continuity_rows(
    *,
    base_dir: PathLike = ".",
    sources: Sequence[tuple[str, str]] = INDEX_SOURCES,
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    base = Path(base_dir)
    generated = generated_at or _now_timestamp()
    preliminary: List[Dict[str, str]] = []
    timestamps: List[str] = []

    for source_file, role in sources:
        path = base / source_file
        exists = path.exists()
        detected_status = "MISSING"
        detected_timestamp = ""
        if exists and path.suffix.lower() == ".csv":
            rows = _read_rows(path)
            latest = rows[-1] if rows else {}
            detected_status = _status_from_row(latest) if latest else "CSV_EMPTY"
            detected_timestamp = _timestamp_from_row(latest, path)
        elif exists and path.suffix.lower() == ".md":
            detected_status = _markdown_status(path)
            detected_timestamp = _markdown_timestamp(path)
        if detected_timestamp:
            timestamps.append(detected_timestamp)
        preliminary.append(
            {
                "generated_at": generated,
                "source_file": source_file,
                "source_exists": TRUE_TEXT if exists else FALSE_TEXT,
                "source_type": _source_type(path),
                "detected_status": detected_status,
                "detected_timestamp": detected_timestamp,
                "archive_role": role,
                "continuity_status": "",
                "operator_next_step": "",
            }
        )

    unique_timestamps = sorted(set(timestamps))
    continuity_status = "SINGLE_RUN_BASELINE" if len(unique_timestamps) <= 1 else "CONTINUITY_INDEX_READY"
    next_step = "continue_daily_collection" if continuity_status == "SINGLE_RUN_BASELINE" else "review_multi_run_continuity"
    for row in preliminary:
        row["continuity_status"] = continuity_status
        row["operator_next_step"] = next_step
    return preliminary


def write_continuity_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CONTINUITY_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(rows: Sequence[Dict[str, str]]) -> str:
    status = rows[0]["continuity_status"] if rows else "SINGLE_RUN_BASELINE"
    next_step = rows[0]["operator_next_step"] if rows else "continue_daily_collection"
    source_lines = [f"- {row['source_file']}: exists={row['source_exists']}; detected_status={row['detected_status']}; archive_role={row['archive_role']}" for row in rows]
    return "\n".join(
        [
            "# Operator Continuity Archive Index Report",
            "",
            "## Continuity",
            "",
            f"- continuity_status={status}",
            f"- operator_next_step={next_step}",
            "",
            "## Sources",
            "",
            *source_lines,
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(rows), encoding="utf-8")


def generate_continuity_archive_index(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_continuity_archive_index.csv",
    output_report: PathLike = "reports/operator_continuity_archive_index_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_continuity_rows(base_dir=base_dir, generated_at=generated_at)
    write_continuity_csv(output_csv, rows)
    write_markdown_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 457 continuity archive index.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_continuity_archive_index.csv")
    parser.add_argument("--output-report", default="reports/operator_continuity_archive_index_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_continuity_archive_index(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    status = rows[0]["continuity_status"] if rows else "SINGLE_RUN_BASELINE"
    print("[PASS] Operator continuity archive index generated")
    print(f"continuity_status={status}:source_count={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
