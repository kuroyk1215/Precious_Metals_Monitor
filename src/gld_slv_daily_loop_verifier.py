from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


SYMBOLS = ("GLD", "SLV")
REQUIRED_CSV_FIELDS = (
    "date_jst",
    "market",
    "symbol",
    "strategy",
    "price",
    "source",
    "data_delay_flag",
    "signal",
    "action_rating",
    "entry_zone",
    "exit_zone",
    "stop_loss",
    "invalidation_level",
    "time_trigger",
    "event_trigger",
    "risk_pct",
    "confidence",
    "action_allowed",
    "result",
    "notes",
)
TRACKED_GENERATED_PATHS = ("dashboard/index.html", "reports/latest_gld_slv_research.md")

PathLike = Union[str, Path]


def _read_csv(path: PathLike) -> List[Dict[str, str]]:
    csv_path = Path(path)
    with csv_path.open(newline="", encoding="utf-8") as f:
        return [{k: str(v or "") for k, v in row.items()} for row in csv.DictReader(f)]


def _check(condition: bool, message: str, failures: List[str]) -> None:
    if not condition:
        failures.append(message)


def _git_dirty_lines(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "status", "--short", "--", *paths],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return [result.stderr.strip() or "git status failed"]
    return [line for line in result.stdout.splitlines() if line.strip()]


def _scan_forbidden_terms(paths: Sequence[PathLike]) -> List[str]:
    forbidden = ("place" + "Order", "cancel" + "Order", "what" + "If" + "Order")
    hits: List[str] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            continue
        files = [path] if path.is_file() else [item for item in path.rglob("*") if item.is_file()]
        for file_path in files:
            if ".git" in file_path.parts or "__pycache__" in file_path.parts:
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for term in forbidden:
                if term in text:
                    hits.append(f"{file_path}:{term}")
    return hits


def verify_daily_loop(
    *,
    report_path: PathLike = "runtime/reports/latest_gld_slv_research.md",
    csv_path: PathLike = "logs/research_log_US.csv",
    dashboard_path: PathLike = "runtime/dashboard/index.html",
    check_git_clean: bool = True,
) -> List[str]:
    failures: List[str] = []
    report = Path(report_path)
    csv_file = Path(csv_path)
    dashboard = Path(dashboard_path)

    _check(report.exists(), f"missing report: {report}", failures)
    _check(csv_file.exists(), f"missing csv: {csv_file}", failures)
    _check(dashboard.exists(), f"missing dashboard: {dashboard}", failures)

    rows: List[Dict[str, str]] = []
    if csv_file.exists():
        rows = _read_csv(csv_file)
        header = set(rows[0].keys()) if rows else set()
        for field in REQUIRED_CSV_FIELDS:
            _check(field in header, f"missing csv field: {field}", failures)
        symbols = {row.get("symbol", "").upper() for row in rows}
        for symbol in SYMBOLS:
            _check(symbol in symbols, f"missing symbol row: {symbol}", failures)
        for row in rows:
            if row.get("data_delay_flag") == "no_price":
                _check(row.get("action_rating") == "NO_TRADE", "no_price row must action_rating=NO_TRADE", failures)
                _check(row.get("action_allowed") == "false", "no_price row must action_allowed=false", failures)

    if dashboard.exists():
        html = dashboard.read_text(encoding="utf-8")
        for text in (
            "GLD",
            "SLV",
            "action_rating",
            "data_delay_flag",
            "US_30mEcho",
            "IBKR cash account",
            "settled cash",
            "GFV",
        ):
            _check(text in html, f"dashboard missing text: {text}", failures)

    scan_paths = (
        "dashboard",
        "src",
        "scripts/batch1_gld_slv_core_research_loop.sh",
        "scripts/gld_slv_dashboard_mvp.sh",
        "scripts/verify_gld_slv_daily_loop.sh",
    )
    forbidden_hits = _scan_forbidden_terms(scan_paths)
    _check(not forbidden_hits, "forbidden automatic trading API terms found: " + ",".join(forbidden_hits), failures)

    if check_git_clean:
        dirty_lines = _git_dirty_lines(TRACKED_GENERATED_PATHS)
        _check(
            not dirty_lines,
            "tracked generated files are dirty; run: git restore dashboard/index.html reports/latest_gld_slv_research.md",
            failures,
        )

    return failures


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify GLD/SLV daily research loop runtime outputs.")
    parser.add_argument("--report-path", default="runtime/reports/latest_gld_slv_research.md")
    parser.add_argument("--csv-path", default="logs/research_log_US.csv")
    parser.add_argument("--dashboard-path", default="runtime/dashboard/index.html")
    parser.add_argument("--skip-git-clean-check", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    failures = verify_daily_loop(
        report_path=args.report_path,
        csv_path=args.csv_path,
        dashboard_path=args.dashboard_path,
        check_git_clean=not args.skip_git_clean_check,
    )
    if failures:
        print("[FAIL] GLD/SLV daily loop verification failed")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("[PASS] GLD/SLV daily loop verification passed")
    print(f"report={args.report_path}")
    print(f"csv={args.csv_path}")
    print(f"dashboard={args.dashboard_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
