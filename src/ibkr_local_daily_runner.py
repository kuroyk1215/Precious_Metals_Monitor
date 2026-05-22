from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import csv
import shutil
from typing import Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class IBKRLocalDailyRunnerSummary:
    run_id: str
    run_timestamp: str
    run_date: str
    run_dir: str
    execution_c_mode: str
    pipeline_exit_code: str
    archive_status: str
    copied_file_count: str
    rotation_enabled: str
    retention_days: str
    telegram_dry_run_enabled: str
    telegram_send_triggered: str
    action_allowed: str
    broker_execution_triggered: str
    historical_data_request_triggered: str
    account_read_triggered: str
    position_read_triggered: str
    manual_review_required: str
    notes: str


def build_run_id(now: Optional[datetime] = None, timezone: str = "Asia/Tokyo") -> Tuple[str, str, str]:
    tz = ZoneInfo(timezone)
    current = (now or datetime.now(tz)).astimezone(tz)
    return (
        current.strftime("%Y%m%d"),
        current.strftime("%Y%m%d_%H%M%S_JST"),
        current.isoformat(),
    )


def ensure_run_dir(log_root: str | Path, run_date: str, run_id: str) -> Path:
    root = Path(log_root)
    run_dir = root / run_date / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def collect_existing_outputs(paths: Iterable[str | Path]) -> List[Path]:
    return [Path(path) for path in paths if Path(path).exists()]


def copy_outputs_to_run_dir(outputs: Iterable[str | Path], run_dir: str | Path) -> List[Path]:
    destination = Path(run_dir)
    destination.mkdir(parents=True, exist_ok=True)
    copied: List[Path] = []
    for output in collect_existing_outputs(outputs):
        target = destination / output.name
        shutil.copy2(output, target)
        copied.append(target)
    return copied


def normalize_retention_days(retention_days: int) -> int:
    return retention_days if retention_days >= 1 else 30


def build_runner_summary(
    run_id: str,
    run_timestamp: str,
    run_date: str,
    run_dir: str | Path,
    execution_c_mode: str,
    pipeline_exit_code: int,
    archive_status: str,
    copied_file_count: int,
    rotation_enabled: bool,
    retention_days: int,
    notes: str,
    telegram_dry_run_enabled: bool = False,
) -> IBKRLocalDailyRunnerSummary:
    return IBKRLocalDailyRunnerSummary(
        run_id=run_id,
        run_timestamp=run_timestamp,
        run_date=run_date,
        run_dir=str(run_dir),
        execution_c_mode=execution_c_mode,
        pipeline_exit_code=str(pipeline_exit_code),
        archive_status=archive_status,
        copied_file_count=str(copied_file_count),
        rotation_enabled=str(rotation_enabled).lower(),
        retention_days=str(normalize_retention_days(retention_days)),
        telegram_dry_run_enabled=str(telegram_dry_run_enabled).lower(),
        telegram_send_triggered="false",
        action_allowed="false",
        broker_execution_triggered="false",
        historical_data_request_triggered="false",
        account_read_triggered="false",
        position_read_triggered="false",
        manual_review_required="true",
        notes=notes,
    )


def write_runner_summary_csv(path: str | Path, summary: IBKRLocalDailyRunnerSummary) -> None:
    fields = list(IBKRLocalDailyRunnerSummary.__dataclass_fields__.keys())
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerow([getattr(summary, field) for field in fields])


def write_runner_report(path: str | Path, summary: IBKRLocalDailyRunnerSummary, copied_files: Iterable[str | Path]) -> None:
    copied_lines = "\n".join(f"- {Path(item).name}" for item in copied_files) or "- none"
    runner_status = "FAILED_SAFE" if summary.pipeline_exit_code != "0" else "NO_GO"
    Path(path).write_text(
        "\n".join(
            [
                "# IBKR Local Daily Runner Report",
                "",
                "## Runner Decision",
                "",
                "| field | value |",
                "|---|---|",
                f"| runner_status | {runner_status} |",
                f"| execution_c_mode | {summary.execution_c_mode} |",
                f"| pipeline_exit_code | {summary.pipeline_exit_code} |",
                f"| telegram_dry_run_enabled | {summary.telegram_dry_run_enabled} |",
                "| telegram_send_triggered | false |",
                "| action_allowed | false |",
                "",
                "## Archive",
                "",
                f"- run_dir={summary.run_dir}",
                f"- archive_status={summary.archive_status}",
                f"- copied_file_count={summary.copied_file_count}",
                "",
                "## Copied Files",
                "",
                copied_lines,
                "",
                "## Rotation",
                "",
                f"- rotation_enabled={summary.rotation_enabled}",
                f"- retention_days={summary.retention_days}",
                "",
                "## Safety Confirmation",
                "",
                "- action_allowed=false",
                "- telegram_send_triggered=false",
                "- broker_execution_triggered=false",
                "- historical_data_request_triggered=false",
                "- account_read_triggered=false",
                "- position_read_triggered=false",
                "- manual_review_required=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def rotate_old_run_dirs(
    log_root: str | Path,
    retention_days: int,
    enabled: bool = True,
    now: Optional[datetime] = None,
    timezone: str = "Asia/Tokyo",
) -> List[Path]:
    if not enabled:
        return []
    retention = normalize_retention_days(retention_days)
    root = Path(log_root).resolve()
    if not root.exists():
        return []

    tz = ZoneInfo(timezone)
    current = (now or datetime.now(tz)).astimezone(tz)
    cutoff = current.date() - timedelta(days=retention)
    removed: List[Path] = []

    for child in root.iterdir():
        if not child.is_dir() or len(child.name) != 8 or not child.name.isdigit():
            continue
        try:
            child_date = datetime.strptime(child.name, "%Y%m%d").date()
        except ValueError:
            continue
        resolved_child = child.resolve()
        if root not in resolved_child.parents:
            continue
        if child_date < cutoff:
            shutil.rmtree(resolved_child)
            removed.append(child)
    return removed
