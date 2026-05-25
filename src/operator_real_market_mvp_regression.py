from __future__ import annotations

import argparse
import csv
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

REGRESSION_FIELDS = (
    "generated_at",
    "artifact_status",
    "py_compile_status",
    "pytest_status",
    "config_yaml_staged",
    "ibkr_market_data_api_errors_staged",
    "forbidden_static_call_status",
    "mvp_status",
    "regression_status",
    "diagnostic_reason",
    "auto_trade_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "telegram_send_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
)

REQUIRED_ARTIFACTS = (
    "src/operator_real_market_mvp_status.py",
    "src/operator_real_market_mvp_regression.py",
    "scripts/operator_real_market_mvp_status.sh",
    "operator_real_market_mvp_status.csv",
    "reports/operator_real_market_mvp_status_report.md",
    "tests/test_operator_real_market_mvp_status.py",
    "src/operator_daily_checklist.py",
    "scripts/operator_daily_checklist.sh",
    "operator_daily_checklist.csv",
    "reports/operator_daily_checklist.md",
    "tests/test_operator_daily_checklist.py",
    "scripts/operator_real_market_mvp_regression_check.sh",
    "scripts/phase450_452_real_market_mvp_hardening_check.sh",
    "tests/test_operator_real_market_mvp_regression.py",
)

FORBIDDEN_CALL_MARKERS = (
    "." + "place" + "Ord" + "er(",
    "." + "cancel" + "Ord" + "er(",
    "." + "req" + "Historical" + "Data(",
    "." + "account" + "Summary(",
    "." + "req" + "Positions(",
    "." + "positions(",
    "." + "position(",
    "place" + "Ord" + "er(",
    "cancel" + "Ord" + "er(",
    "req" + "Historical" + "Data(",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _run(command: Sequence[str], *, cwd: Path, env: Optional[Dict[str, str]] = None) -> int:
    result = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    return int(result.returncode)


def _staged_files(repo_root: Path) -> List[str]:
    result = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=repo_root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _artifact_status(repo_root: Path, required_artifacts: Iterable[str]) -> tuple[str, List[str]]:
    missing = [path for path in required_artifacts if not (repo_root / path).exists()]
    return ("PASS" if not missing else "FAIL", missing)


def _forbidden_static_hits(repo_root: Path, paths: Sequence[str]) -> List[str]:
    hits: List[str] = []
    for relative in paths:
        path = repo_root / relative
        if not path.exists() or path.suffix not in {".py", ".sh"}:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_CALL_MARKERS:
            if marker in text:
                hits.append(f"{relative}:{marker}")
        rebalance_call_marker = "re" + "balance("
        if rebalance_call_marker in text and "rebalance_action_allowed" not in text:
            hits.append(f"{relative}:{rebalance_call_marker}")
    return hits


def _read_mvp_status(repo_root: Path) -> str:
    path = repo_root / "operator_real_market_mvp_status.csv"
    if not path.exists():
        return "MISSING"
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[-1].get("mvp_status", "MISSING") if rows else "MISSING"


def build_regression_row(
    *,
    repo_root: PathLike = ".",
    run_py_compile: bool = False,
    run_pytest: bool = False,
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    root = Path(repo_root)
    artifact_status, missing = _artifact_status(root, REQUIRED_ARTIFACTS)
    py_compile_status = "SKIPPED"
    pytest_status = "SKIPPED"
    if run_py_compile:
        py_compile_status = "PASS" if _run(["python3", "-m", "py_compile", "main.py", *[str(p.relative_to(root)) for p in sorted((root / "src").glob("*.py"))]], cwd=root) == 0 else "FAIL"
    if run_pytest:
        pytest_status = "PASS" if _run(["python3", "-m", "pytest", "-q"], cwd=root) == 0 else "FAIL"

    staged = _staged_files(root)
    config_staged = "config.yaml" in staged
    errors_staged = "ibkr_market_data_api_errors.csv" in staged
    scan_paths = [path for path in REQUIRED_ARTIFACTS if path.endswith((".py", ".sh"))]
    forbidden_hits = _forbidden_static_hits(root, scan_paths)
    forbidden_status = "PASS" if not forbidden_hits else "FAIL"
    mvp_status = _read_mvp_status(root)

    hard_statuses = [artifact_status, forbidden_status]
    if run_py_compile:
        hard_statuses.append(py_compile_status)
    if run_pytest:
        hard_statuses.append(pytest_status)
    if config_staged or errors_staged:
        hard_statuses.append("FAIL")
    regression_status = "PASS" if all(status == "PASS" for status in hard_statuses) else "FAIL"
    reasons: List[str] = []
    if missing:
        reasons.append("missing_artifacts:" + ",".join(missing))
    if config_staged:
        reasons.append("config_yaml_staged")
    if errors_staged:
        reasons.append("ibkr_market_data_api_errors_staged")
    if forbidden_hits:
        reasons.append("forbidden_static_hits:" + ",".join(forbidden_hits))
    if py_compile_status == "FAIL":
        reasons.append("py_compile_failed")
    if pytest_status == "FAIL":
        reasons.append("pytest_failed")
    if not reasons:
        reasons.append("phase450_452_regression_gate_clean")

    return {
        "generated_at": generated_at or _now_timestamp(),
        "artifact_status": artifact_status,
        "py_compile_status": py_compile_status,
        "pytest_status": pytest_status,
        "config_yaml_staged": TRUE_TEXT if config_staged else FALSE_TEXT,
        "ibkr_market_data_api_errors_staged": TRUE_TEXT if errors_staged else FALSE_TEXT,
        "forbidden_static_call_status": forbidden_status,
        "mvp_status": mvp_status,
        "regression_status": regression_status,
        "diagnostic_reason": ";".join(reasons),
        "auto_trade_allowed": FALSE_TEXT,
        "account_read_allowed": FALSE_TEXT,
        "position_read_allowed": FALSE_TEXT,
        "historical_data_request_allowed": FALSE_TEXT,
        "telegram_send_allowed": FALSE_TEXT,
        "order_action_allowed": FALSE_TEXT,
        "cancel_action_allowed": FALSE_TEXT,
        "rebalance_action_allowed": FALSE_TEXT,
    }


def write_regression_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(REGRESSION_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Operator Real Market MVP Regression Report",
            "",
            "## Safety Banner",
            "",
            "- no IBKR connection",
            "- no real market data request",
            "- no auto trading",
            "- no account reads",
            "- no position reads",
            "- no historical data requests",
            "- no Telegram real send",
            "- no order/cancel/rebalance",
            "",
            "## Regression Status",
            "",
            f"- regression_status={row['regression_status']}",
            f"- mvp_status={row['mvp_status']}",
            f"- artifact_status={row['artifact_status']}",
            f"- py_compile_status={row['py_compile_status']}",
            f"- pytest_status={row['pytest_status']}",
            f"- forbidden_static_call_status={row['forbidden_static_call_status']}",
            f"- diagnostic_reason={row['diagnostic_reason']}",
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row), encoding="utf-8")


def generate_regression_report(
    *,
    repo_root: PathLike = ".",
    output_csv: PathLike = "operator_real_market_mvp_regression.csv",
    output_report: PathLike = "reports/operator_real_market_mvp_regression_report.md",
    run_py_compile: bool = False,
    run_pytest: bool = False,
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_regression_row(repo_root=repo_root, run_py_compile=run_py_compile, run_pytest=run_pytest, generated_at=generated_at)
    write_regression_csv(output_csv, row)
    write_markdown_report(output_report, row)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 452 MVP regression report.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-csv", default="operator_real_market_mvp_regression.csv")
    parser.add_argument("--output-report", default="reports/operator_real_market_mvp_regression_report.md")
    parser.add_argument("--run-py-compile", action="store_true")
    parser.add_argument("--run-pytest", action="store_true")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_regression_report(
        repo_root=args.repo_root,
        output_csv=args.output_csv,
        output_report=args.output_report,
        run_py_compile=args.run_py_compile,
        run_pytest=args.run_pytest,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator real-market MVP regression report generated")
    print(f"regression_status={row['regression_status']}:mvp_status={row['mvp_status']}")
    return 0 if row["regression_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
