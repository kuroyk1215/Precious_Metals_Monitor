from __future__ import annotations

import argparse
import csv
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

MASTER_WRAPPERS = (
    "operator_real_marketdata_daily_run.sh",
    "operator_real_quote_normalization.sh",
    "operator_real_quote_signal_bridge.sh",
    "operator_daily_real_market_report.sh",
    "operator_real_market_mvp_status.sh",
    "operator_real_market_archive_compare.sh",
    "operator_signal_threshold_explainer.sh",
    "operator_strategy_quality_report.sh",
    "operator_daily_checklist.sh",
    "operator_real_market_mvp_regression_check.sh",
)

MASTER_RUN_FIELDS = (
    "generated_at",
    "master_status",
    "wrappers_attempted",
    "wrapper_failures",
    "quote_unavailable",
    "real_quote_available",
    "safety_clean",
    "mvp_status",
    "strategy_quality_status",
    "regression_status",
    "diagnostic_reason",
    "operator_next_step",
    "auto_trade_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "telegram_real_send_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
)

PathLike = Union[str, Path]
CommandRunner = Callable[[Sequence[str], Path], int]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_rows(path: PathLike) -> List[Dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _latest(path: PathLike) -> Dict[str, str]:
    rows = _read_rows(path)
    return rows[-1] if rows else {}


def _is_true(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _is_false(value: object) -> bool:
    return str(value or "").strip().lower() in {"false", "0", "no", ""}


def _default_runner(command: Sequence[str], cwd: Path) -> int:
    result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    return int(result.returncode)


def _field_clean(rows: Sequence[Dict[str, str]]) -> bool:
    forbidden_fields = (
        "auto_trade_allowed",
        "account_read_allowed",
        "position_read_allowed",
        "historical_data_request_allowed",
        "telegram_send_allowed",
        "telegram_real_send_allowed",
        "order_action_allowed",
        "cancel_action_allowed",
        "rebalance_action_allowed",
        "broker_execution_triggered",
        "account_read_triggered",
        "position_read_triggered",
        "telegram_send_triggered",
    )
    for row in rows:
        for field in forbidden_fields:
            if field in row and not _is_false(row.get(field)):
                return False
    return True


def _status_inputs(repo_root: Path) -> List[Dict[str, str]]:
    files = (
        "operator_real_quote_normalization.csv",
        "operator_real_quote_signal_bridge.csv",
        "operator_daily_real_market_report.csv",
        "operator_real_market_mvp_status.csv",
        "operator_strategy_quality_report.csv",
        "operator_real_market_mvp_regression.csv",
    )
    rows: List[Dict[str, str]] = []
    for name in files:
        rows.extend(_read_rows(repo_root / name))
    return rows


def _quote_available(rows: Sequence[Dict[str, str]]) -> bool:
    return any(
        row.get("quote_status") == "AVAILABLE"
        or row.get("normalized_status") == "NORMALIZED"
        or row.get("real_quote_available") == TRUE_TEXT
        or row.get("real_quote_state") == "REAL_QUOTE_AVAILABLE"
        for row in rows
    )


def _quote_unavailable(rows: Sequence[Dict[str, str]]) -> bool:
    return any(
        row.get("safe_unavailable") == TRUE_TEXT
        or row.get("normalized_status") == "SAFE_UNAVAILABLE"
        or row.get("signal_bridge_status") == "HOLD_NO_REAL_QUOTE"
        or row.get("mvp_status") == "MVP_SAFE_UNAVAILABLE"
        or row.get("quality_status") == "DATA_UNAVAILABLE_BUT_SAFE"
        for row in rows
    )


def run_master_chain(
    *,
    repo_root: PathLike = ".",
    wrappers: Sequence[str] = MASTER_WRAPPERS,
    command_runner: CommandRunner = _default_runner,
) -> Dict[str, int]:
    root = Path(repo_root)
    exit_codes: Dict[str, int] = {}
    for wrapper in wrappers:
        script = root / "scripts" / wrapper
        if script.exists():
            exit_codes[wrapper] = command_runner(["bash", str(script)], root)
        else:
            exit_codes[wrapper] = 127
    return exit_codes


def build_master_row(
    *,
    repo_root: PathLike = ".",
    exit_codes: Optional[Dict[str, int]] = None,
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    root = Path(repo_root)
    codes = exit_codes or {}
    rows = _status_inputs(root)
    safety_clean = _field_clean(rows)
    real_quote_available = _quote_available(rows)
    quote_unavailable = _quote_unavailable(rows)
    mvp = _latest(root / "operator_real_market_mvp_status.csv")
    quality = _latest(root / "operator_strategy_quality_report.csv")
    regression = _latest(root / "operator_real_market_mvp_regression.csv")
    failures = [name for name, code in codes.items() if code != 0]

    if not safety_clean:
        master_status = "MASTER_BLOCKED"
        reason = "forbidden_action_or_read_field_detected"
        next_step = "stop_and_review_safety_boundary"
    elif quote_unavailable and not real_quote_available:
        master_status = "MASTER_SAFE_UNAVAILABLE"
        reason = "real_quote_unavailable_but_safety_clean_audit_chain_completed"
        next_step = "review_connection_permission_continue_daily_collection"
    elif real_quote_available:
        master_status = "MASTER_READY_FOR_DAILY_REVIEW"
        reason = "real_quote_available_safety_clean_manual_review_only"
        next_step = "manual_review_daily_real_market_outputs"
    elif failures:
        master_status = "MASTER_REVIEW_REQUIRED"
        reason = "wrapper_failures:" + ",".join(failures)
        next_step = "review_failed_wrapper_outputs"
    else:
        master_status = "MASTER_REVIEW_REQUIRED"
        reason = "audit_chain_completed_without_decisive_quote_status"
        next_step = "review_master_summary_sources"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "master_status": master_status,
        "wrappers_attempted": str(len(codes)),
        "wrapper_failures": ",".join(failures) if failures else "none",
        "quote_unavailable": TRUE_TEXT if quote_unavailable else FALSE_TEXT,
        "real_quote_available": TRUE_TEXT if real_quote_available else FALSE_TEXT,
        "safety_clean": TRUE_TEXT if safety_clean else FALSE_TEXT,
        "mvp_status": mvp.get("mvp_status", "MISSING"),
        "strategy_quality_status": quality.get("quality_status", "MISSING"),
        "regression_status": regression.get("regression_status", "MISSING"),
        "diagnostic_reason": reason,
        "operator_next_step": next_step,
        "auto_trade_allowed": FALSE_TEXT,
        "account_read_allowed": FALSE_TEXT,
        "position_read_allowed": FALSE_TEXT,
        "historical_data_request_allowed": FALSE_TEXT,
        "telegram_real_send_allowed": FALSE_TEXT,
        "order_action_allowed": FALSE_TEXT,
        "cancel_action_allowed": FALSE_TEXT,
        "rebalance_action_allowed": FALSE_TEXT,
    }


def write_master_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(MASTER_RUN_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_markdown_report(row: Dict[str, str], exit_codes: Dict[str, int]) -> str:
    wrapper_lines = [f"- {name}: exit_code={code}" for name, code in exit_codes.items()]
    return "\n".join(
        [
            "# Operator Daily Master Run Report",
            "",
            "## Safety Banner",
            "",
            "- no auto trading",
            "- no account reads",
            "- no position reads",
            "- no historical data requests",
            "- no Telegram real send",
            "- no order/cancel/rebalance",
            "",
            "## Master Status",
            "",
            f"- master_status={row['master_status']}",
            f"- safety_clean={row['safety_clean']}",
            f"- quote_unavailable={row['quote_unavailable']}",
            f"- real_quote_available={row['real_quote_available']}",
            f"- diagnostic_reason={row['diagnostic_reason']}",
            f"- operator_next_step={row['operator_next_step']}",
            "",
            "## Wrapper Exit Codes",
            "",
            *(wrapper_lines or ["- none"]),
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, row: Dict[str, str], exit_codes: Dict[str, int]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(row, exit_codes), encoding="utf-8")


def generate_master_run(
    *,
    repo_root: PathLike = ".",
    output_csv: PathLike = "operator_daily_master_run_summary.csv",
    output_report: PathLike = "reports/operator_daily_master_run_report.md",
    run_wrappers: bool = True,
    generated_at: Optional[str] = None,
    command_runner: CommandRunner = _default_runner,
) -> Dict[str, str]:
    root = Path(repo_root)
    exit_codes = run_master_chain(repo_root=root, command_runner=command_runner) if run_wrappers else {}
    row = build_master_row(repo_root=root, exit_codes=exit_codes, generated_at=generated_at)
    write_master_csv(output_csv, row)
    write_markdown_report(output_report, row, exit_codes)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Phase 456 daily operator master chain.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-csv", default="operator_daily_master_run_summary.csv")
    parser.add_argument("--output-report", default="reports/operator_daily_master_run_report.md")
    parser.add_argument("--skip-wrappers", action="store_true")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_master_run(
        repo_root=args.repo_root,
        output_csv=args.output_csv,
        output_report=args.output_report,
        run_wrappers=not args.skip_wrappers,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator daily master run generated")
    print(f"master_status={row['master_status']}:safety_clean={row['safety_clean']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
