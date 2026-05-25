from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


PHASE_RANGE = "465-467"

CODEBASE_MAP_FIELDS = (
    "generated_at",
    "phase_range",
    "module_name",
    "script_path",
    "source_path",
    "csv_output",
    "report_output",
    "depends_on",
    "role",
    "safety_boundary",
    "operator_usage",
)

MODULE_SPECS = (
    {
        "module_name": "real marketdata smoke",
        "script_path": "scripts/operator_real_marketdata_smoke.sh",
        "source_path": "src/operator_real_marketdata_smoke_summary.py",
        "csv_output": "operator_real_marketdata_smoke_summary.csv",
        "report_output": "reports/operator_real_marketdata_smoke_report.md",
        "depends_on": "manual operator TWS environment; watchlist/config local files",
        "role": "read-only real marketdata smoke summary",
        "operator_usage": "run only when manually checking real marketdata connectivity",
    },
    {
        "module_name": "archive",
        "script_path": "scripts/operator_real_marketdata_smoke_archive.sh",
        "source_path": "src/operator_real_marketdata_smoke_archive.py",
        "csv_output": "operator_real_marketdata_smoke_archive.csv",
        "report_output": "reports/operator_real_marketdata_smoke_archive_report.md",
        "depends_on": "operator_real_marketdata_smoke_summary.csv",
        "role": "archive real marketdata smoke output for continuity",
        "operator_usage": "preserve latest smoke result for review",
    },
    {
        "module_name": "decision gate",
        "script_path": "scripts/operator_real_marketdata_decision_gate.sh",
        "source_path": "src/operator_real_marketdata_decision_gate.py",
        "csv_output": "operator_real_marketdata_decision_gate.csv",
        "report_output": "reports/operator_real_marketdata_decision_gate_report.md",
        "depends_on": "operator_real_marketdata_smoke_summary.csv; operator_real_marketdata_smoke_archive.csv",
        "role": "classify real marketdata smoke result",
        "operator_usage": "review gate before continuing daily chain",
    },
    {
        "module_name": "latest",
        "script_path": "scripts/operator_real_marketdata_latest.sh",
        "source_path": "src/operator_real_marketdata_latest.py",
        "csv_output": "operator_real_marketdata_latest.csv",
        "report_output": "reports/operator_real_marketdata_latest_report.md",
        "depends_on": "operator_real_marketdata_smoke_summary.csv; operator_real_marketdata_decision_gate.csv",
        "role": "select latest real marketdata state",
        "operator_usage": "inspect latest quote availability and safety state",
    },
    {
        "module_name": "daily run",
        "script_path": "scripts/operator_real_marketdata_daily_run.sh",
        "source_path": "src/operator_real_marketdata_daily_run.py",
        "csv_output": "operator_real_marketdata_daily_run_summary.csv",
        "report_output": "reports/operator_real_marketdata_daily_run_report.md",
        "depends_on": "latest; archive; decision gate",
        "role": "daily real marketdata chain wrapper summary",
        "operator_usage": "run as part of daily observation chain",
    },
    {
        "module_name": "quote normalization",
        "script_path": "scripts/operator_real_quote_normalization.sh",
        "source_path": "src/operator_real_quote_normalization.py",
        "csv_output": "operator_real_quote_normalization.csv",
        "report_output": "reports/operator_real_quote_normalization_report.md",
        "depends_on": "operator_real_marketdata_latest.csv",
        "role": "normalize available real quote fields",
        "operator_usage": "review quote shape before strategy bridge",
    },
    {
        "module_name": "signal bridge",
        "script_path": "scripts/operator_real_quote_signal_bridge.sh",
        "source_path": "src/operator_real_quote_signal_bridge.py",
        "csv_output": "operator_real_quote_signal_bridge.csv",
        "report_output": "reports/operator_real_quote_signal_bridge_report.md",
        "depends_on": "operator_real_quote_normalization.csv",
        "role": "bridge quote availability into reference signals",
        "operator_usage": "review signal availability without execution",
    },
    {
        "module_name": "daily real-market report",
        "script_path": "scripts/operator_daily_real_market_report.sh",
        "source_path": "src/operator_daily_real_market_report.py",
        "csv_output": "operator_daily_real_market_report.csv",
        "report_output": "reports/operator_daily_real_market_report.md",
        "depends_on": "operator_real_quote_signal_bridge.csv; operator_real_marketdata_daily_run_summary.csv",
        "role": "daily human-readable real-market report",
        "operator_usage": "read daily observation report",
    },
    {
        "module_name": "MVP status",
        "script_path": "scripts/operator_real_market_mvp_status.sh",
        "source_path": "src/operator_real_market_mvp_status.py",
        "csv_output": "operator_real_market_mvp_status.csv",
        "report_output": "reports/operator_real_market_mvp_status_report.md",
        "depends_on": "daily real-market report; signal bridge",
        "role": "summarize MVP availability and safety",
        "operator_usage": "confirm current MVP state",
    },
    {
        "module_name": "checklist",
        "script_path": "scripts/operator_daily_checklist.sh",
        "source_path": "src/operator_daily_checklist.py",
        "csv_output": "operator_daily_checklist.csv",
        "report_output": "reports/operator_daily_checklist.md",
        "depends_on": "none",
        "role": "fixed manual daily checklist",
        "operator_usage": "follow before and after daily master run",
    },
    {
        "module_name": "regression",
        "script_path": "scripts/operator_real_market_mvp_regression_check.sh",
        "source_path": "src/operator_real_market_mvp_regression.py",
        "csv_output": "operator_real_market_mvp_regression.csv",
        "report_output": "reports/operator_real_market_mvp_regression_report.md",
        "depends_on": "generated artifacts and static safety checks",
        "role": "regression gate for read-only safety",
        "operator_usage": "run when validating MVP chain health",
    },
    {
        "module_name": "strategy quality",
        "script_path": "scripts/operator_strategy_quality_report.sh",
        "source_path": "src/operator_strategy_quality_report.py",
        "csv_output": "operator_strategy_quality_report.csv",
        "report_output": "reports/operator_strategy_quality_report.md",
        "depends_on": "signal bridge; daily real-market report",
        "role": "classify strategy quality under available data",
        "operator_usage": "review strategy quality status",
    },
    {
        "module_name": "master run",
        "script_path": "scripts/operator_daily_master_run.sh",
        "source_path": "src/operator_daily_master_run.py",
        "csv_output": "operator_daily_master_run_summary.csv",
        "report_output": "reports/operator_daily_master_run_report.md",
        "depends_on": "daily run; checklist; regression; MVP status; strategy quality",
        "role": "main daily operator entrypoint",
        "operator_usage": "primary daily command for the MVP skeleton",
    },
    {
        "module_name": "continuity index",
        "script_path": "scripts/operator_continuity_archive_index.sh",
        "source_path": "src/operator_continuity_archive_index.py",
        "csv_output": "operator_continuity_archive_index.csv",
        "report_output": "reports/operator_continuity_archive_index.md",
        "depends_on": "daily artifacts and reports",
        "role": "index daily artifacts for handoff",
        "operator_usage": "review continuity coverage",
    },
    {
        "module_name": "readiness report",
        "script_path": "scripts/operator_mvp_readiness_report.sh",
        "source_path": "src/operator_mvp_readiness_report.py",
        "csv_output": "operator_mvp_readiness_report.csv",
        "report_output": "reports/operator_mvp_readiness_report.md",
        "depends_on": "master run; continuity index; MVP status; strategy quality; regression",
        "role": "MVP readiness summary",
        "operator_usage": "review readiness before final packet",
    },
    {
        "module_name": "GLD/SLV spread",
        "script_path": "scripts/operator_gld_slv_spread_framework.sh",
        "source_path": "src/operator_gld_slv_spread_framework.py",
        "csv_output": "operator_gld_slv_spread_framework.csv",
        "report_output": "reports/operator_gld_slv_spread_framework_report.md",
        "depends_on": "quote normalization; signal bridge",
        "role": "GLD/SLV spread observation framework",
        "operator_usage": "review spread state without execution",
    },
    {
        "module_name": "range framework",
        "script_path": "scripts/operator_real_market_range_framework.sh",
        "source_path": "src/operator_real_market_range_framework.py",
        "csv_output": "operator_real_market_range_framework.csv",
        "report_output": "reports/operator_real_market_range_framework_report.md",
        "depends_on": "quote normalization; daily real-market report",
        "role": "range observation framework",
        "operator_usage": "review range status without execution",
    },
    {
        "module_name": "strategy explanation",
        "script_path": "scripts/operator_strategy_explanation_upgrade.sh",
        "source_path": "src/operator_strategy_explanation_upgrade.py",
        "csv_output": "operator_strategy_explanation_upgrade.csv",
        "report_output": "reports/operator_strategy_explanation_upgrade_report.md",
        "depends_on": "strategy quality; range framework; GLD/SLV spread",
        "role": "explain current strategy state for humans",
        "operator_usage": "read why the strategy is available, held, or review-only",
    },
    {
        "module_name": "final daily packet",
        "script_path": "scripts/operator_final_daily_packet.sh",
        "source_path": "src/operator_final_daily_packet.py",
        "csv_output": "operator_final_daily_packet.csv",
        "report_output": "reports/operator_final_daily_packet.md",
        "depends_on": "master run; readiness report; strategy explanation; quality; checklist; MVP status",
        "role": "final daily human observation packet",
        "operator_usage": "final packet for daily manual review",
    },
    {
        "module_name": "latest strategy decision",
        "script_path": "scripts/operator_latest_strategy_decision.sh",
        "source_path": "src/operator_latest_strategy_decision.py",
        "csv_output": "operator_latest_strategy_decision.csv",
        "report_output": "reports/operator_latest_strategy_decision_report.md",
        "depends_on": "final daily packet; strategy explanation; readiness; range; GLD/SLV spread",
        "role": "latest strategy state entrypoint",
        "operator_usage": "inspect latest strategy status after final packet",
    },
    {
        "module_name": "completion gate",
        "script_path": "scripts/operator_real_market_mvp_completion_gate.sh",
        "source_path": "src/operator_real_market_mvp_completion_gate.py",
        "csv_output": "operator_real_market_mvp_completion_gate.csv",
        "report_output": "reports/operator_real_market_mvp_completion_gate_report.md",
        "depends_on": "final daily packet; latest strategy decision; readiness; regression; continuity",
        "role": "MVP completion state entrypoint",
        "operator_usage": "confirm completion status for handoff",
    },
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_codebase_map_rows(*, generated_at: Optional[str] = None) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    rows: List[Dict[str, str]] = []
    for spec in MODULE_SPECS:
        row = {
            "generated_at": timestamp,
            "phase_range": PHASE_RANGE,
            "safety_boundary": (
                "no auto trading; no account reads; no position reads; "
                "no historical data requests; no Telegram real send; no order/cancel/rebalance"
            ),
            **spec,
        }
        rows.append(row)
    return rows


def write_codebase_map_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CODEBASE_MAP_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(rows: Sequence[Dict[str, str]]) -> str:
    lines = [
        "# Operator MVP Codebase Map",
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
        "## Module Map",
        "",
        "| module | script | source | csv | report | role |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['module_name']} | {row['script_path']} | {row['source_path']} | "
            f"{row['csv_output']} | {row['report_output']} | {row['role']} |"
        )
    lines.extend(
        [
            "",
            "## Operator Entrypoints",
            "",
            "- daily master run is the primary daily command",
            "- final daily packet is the final manual observation packet",
            "- latest strategy decision is the latest strategy status entrypoint",
            "- completion gate is the MVP completion status entrypoint",
        ]
    )
    return "\n".join(lines) + "\n"


def write_markdown_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(rows), encoding="utf-8")


def generate_mvp_codebase_map(
    *,
    output_csv: PathLike = "operator_mvp_codebase_map.csv",
    output_report: PathLike = "reports/operator_mvp_codebase_map.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_codebase_map_rows(generated_at=generated_at)
    write_codebase_map_csv(output_csv, rows)
    write_markdown_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 465 MVP codebase map.")
    parser.add_argument("--output-csv", default="operator_mvp_codebase_map.csv")
    parser.add_argument("--output-report", default="reports/operator_mvp_codebase_map.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_mvp_codebase_map(
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator MVP codebase map generated")
    print(f"module_count={len(rows)}:phase_range={PHASE_RANGE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
