from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"

CHECKLIST_FIELDS = (
    "generated_at",
    "step_order",
    "check_name",
    "operator_action",
    "completion_required",
    "manual_review_only",
    "auto_trade_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "telegram_send_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
)

CHECKS = (
    ("git status safety check", "run git status --short and review local-only files"),
    ("confirm config.yaml remains local-only", "verify config.yaml is not staged or committed"),
    ("confirm ibkr_market_data_api_errors.csv remains local-only", "verify ibkr_market_data_api_errors.csv is not staged or committed"),
    ("run real marketdata daily wrapper", "run scripts/operator_real_marketdata_daily_run.sh"),
    ("run quote normalization", "run scripts/operator_real_quote_normalization.sh"),
    ("run signal bridge", "run scripts/operator_real_quote_signal_bridge.sh"),
    ("run daily real-market report", "run scripts/operator_daily_real_market_report.sh"),
    ("run MVP status aggregator", "run scripts/operator_real_market_mvp_status.sh"),
    ("review decision / quote / signal status", "manually review decision, quote, signal, and MVP status outputs"),
    ("do not trade automatically", "keep all trading, account, position, historical, and Telegram send actions disabled"),
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_checklist_rows(generated_at: Optional[str] = None) -> List[Dict[str, str]]:
    generated = generated_at or _now_timestamp()
    rows: List[Dict[str, str]] = []
    for index, (name, action) in enumerate(CHECKS, start=1):
        rows.append(
            {
                "generated_at": generated,
                "step_order": str(index),
                "check_name": name,
                "operator_action": action,
                "completion_required": "true",
                "manual_review_only": "true",
                "auto_trade_allowed": FALSE_TEXT,
                "account_read_allowed": FALSE_TEXT,
                "position_read_allowed": FALSE_TEXT,
                "historical_data_request_allowed": FALSE_TEXT,
                "telegram_send_allowed": FALSE_TEXT,
                "order_action_allowed": FALSE_TEXT,
                "cancel_action_allowed": FALSE_TEXT,
                "rebalance_action_allowed": FALSE_TEXT,
            }
        )
    return rows


def write_checklist_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CHECKLIST_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(rows: Sequence[Dict[str, str]]) -> str:
    lines = [f"{row['step_order']}. {row['check_name']}: {row['operator_action']}" for row in rows]
    return "\n".join(
        [
            "# Operator Daily Checklist",
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
            "## Checklist",
            "",
            *lines,
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(rows), encoding="utf-8")


def generate_daily_checklist(
    *,
    output_csv: PathLike = "operator_daily_checklist.csv",
    output_report: PathLike = "reports/operator_daily_checklist.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_checklist_rows(generated_at=generated_at)
    write_checklist_csv(output_csv, rows)
    write_markdown_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 451 operator daily checklist.")
    parser.add_argument("--output-csv", default="operator_daily_checklist.csv")
    parser.add_argument("--output-report", default="reports/operator_daily_checklist.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_daily_checklist(output_csv=args.output_csv, output_report=args.output_report, generated_at=args.generated_at)
    print("[PASS] Operator daily checklist generated")
    print(f"checklist_steps={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
