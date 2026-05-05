from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import csv
from typing import Optional


@dataclass
class HistoricalPipelineCheckResult:
    timestamp: str
    status: str
    current_blocking_step: str
    ibkr_candidate_exists: bool
    quality_gate_report_exists: bool
    quality_gate_log_exists: bool
    validated_historical_data_exists: bool
    calibration_log_exists: bool
    warning_flags: list[str]
    notes: str


def _latest_quality_gate_status(log_path: Path) -> Optional[str]:
    if not log_path.exists():
        return None
    with log_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None
    return (rows[-1].get("status") or "").strip().lower() or None


def run_historical_pipeline_check(
    candidate_csv: str = "data/raw/ibkr_jp_etf_prices_candidate.csv",
    quality_gate_report: str = "reports/historical_quality_gate_report.md",
    quality_gate_log: str = "historical_quality_gate_log.csv",
    validated_csv: str = "data/validated_historical_data.csv",
    calibration_log: str = "conversion_factor_calibration_log.csv",
) -> HistoricalPipelineCheckResult:
    timestamp = datetime.now(timezone.utc).isoformat()
    candidate_exists = Path(candidate_csv).exists()
    qg_report_exists = Path(quality_gate_report).exists()
    qg_log_path = Path(quality_gate_log)
    qg_log_exists = qg_log_path.exists()
    validated_exists = Path(validated_csv).exists()
    calibration_exists = Path(calibration_log).exists()
    qg_status = _latest_quality_gate_status(qg_log_path)

    warning_flags: list[str] = []
    blocking_step = "none"
    status = "ready_for_fetch"
    notes = "manual-only integration check."

    if not candidate_exists:
        status = "ready_for_fetch"
        blocking_step = "ibkr_historical_fetch"
        warning_flags.append("candidate_missing")
        notes = "手动执行 --ibkr-historical-fetch 以生成候选 CSV；不会自动执行。"
    elif not (qg_report_exists and qg_log_exists):
        status = "blocked_at_quality_gate"
        blocking_step = "quality_gate"
        warning_flags.append("quality_gate_outputs_missing")
        notes = "请手动执行 --quality-gate；不会自动执行。"
    elif qg_status == "fail":
        status = "blocked_at_quality_gate"
        blocking_step = "quality_gate_fail"
        warning_flags.append("quality_gate_fail")
        notes = "quality-gate=fail，阻断 validate-history 与 calibration-csv。"
    elif qg_status == "warn":
        status = "ready_for_validate_history_with_manual_confirmation"
        blocking_step = "manual_confirmation_required"
        warning_flags.append("quality_gate_warn_manual_confirmation")
        notes = "quality-gate=warn，需人工确认后才可手动执行 --validate-history。"
    elif qg_status == "pass":
        status = "ready_for_validate_history"
        blocking_step = "validate_history"
        notes = "quality-gate=pass，可手动执行 --validate-history；不会自动执行。"
    else:
        status = "blocked_at_quality_gate"
        blocking_step = "quality_gate_status_unknown"
        warning_flags.append("quality_gate_status_unknown")
        notes = "quality-gate 状态未知，请人工复核。"

    if status in {"ready_for_validate_history", "ready_for_validate_history_with_manual_confirmation"} and not validated_exists:
        status = "blocked_before_calibration"
        blocking_step = "validate_history"
        warning_flags.append("validated_data_missing")
        notes = "请先手动执行 --validate-history 生成 validated_historical_data.csv。"
    elif validated_exists and not calibration_exists:
        status = "ready_for_calibration_review"
        blocking_step = "calibration_csv"
        warning_flags.append("calibration_not_run")
        notes = "可手动执行 --calibration-csv data/validated_historical_data.csv；不会自动执行。"
    elif validated_exists and calibration_exists:
        status = "complete_for_research_review"
        blocking_step = "none"
        notes = "手动链路产物齐全，可进入 research review。"

    return HistoricalPipelineCheckResult(
        timestamp=timestamp,
        status=status,
        current_blocking_step=blocking_step,
        ibkr_candidate_exists=candidate_exists,
        quality_gate_report_exists=qg_report_exists,
        quality_gate_log_exists=qg_log_exists,
        validated_historical_data_exists=validated_exists,
        calibration_log_exists=calibration_exists,
        warning_flags=warning_flags,
        notes=notes,
    )


def write_historical_pipeline_check_report(path: str, result: HistoricalPipelineCheckResult) -> None:
    lines = [
        "# Historical Pipeline Manual Integration Check Report",
        "",
        "## 当前检查时间",
        f"- {result.timestamp}",
        "",
        "## 手动 pipeline 阶段清单（manual-only）",
        "1. python main.py --config config.yaml --ibkr-historical-fetch",
        "2. python main.py --config config.yaml --quality-gate data/raw/ibkr_jp_etf_prices_candidate.csv",
        "3. python main.py --config config.yaml --validate-history data/raw/ibkr_jp_etf_prices_candidate.csv",
        "4. python main.py --config config.yaml --calibration-csv data/validated_historical_data.csv",
        "",
        "## 当前产物状态",
        f"- status: {result.status}",
        f"- current_blocking_step: {result.current_blocking_step}",
        f"- ibkr_candidate_exists: {str(result.ibkr_candidate_exists).lower()}",
        f"- quality_gate_report_exists: {str(result.quality_gate_report_exists).lower()}",
        f"- quality_gate_log_exists: {str(result.quality_gate_log_exists).lower()}",
        f"- validated_historical_data_exists: {str(result.validated_historical_data_exists).lower()}",
        f"- calibration_log_exists: {str(result.calibration_log_exists).lower()}",
        f"- warning_flags: {';'.join(result.warning_flags) if result.warning_flags else 'none'}",
        f"- notes: {result.notes}",
        "",
        "## 安全声明",
        "- manual-only",
        "- research-only",
        "- no auto chain",
        "- no auto calibration",
        "- no auto trade / no trading order APIs / no historical fetch API auto call",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def append_historical_pipeline_check_log(path: str, result: HistoricalPipelineCheckResult) -> None:
    fields = [
        "timestamp", "status", "current_blocking_step", "ibkr_candidate_exists", "quality_gate_report_exists",
        "quality_gate_log_exists", "validated_historical_data_exists", "calibration_log_exists", "warning_flags", "notes"
    ]
    p = Path(path)
    with p.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow({
            "timestamp": result.timestamp,
            "status": result.status,
            "current_blocking_step": result.current_blocking_step,
            "ibkr_candidate_exists": str(result.ibkr_candidate_exists).lower(),
            "quality_gate_report_exists": str(result.quality_gate_report_exists).lower(),
            "quality_gate_log_exists": str(result.quality_gate_log_exists).lower(),
            "validated_historical_data_exists": str(result.validated_historical_data_exists).lower(),
            "calibration_log_exists": str(result.calibration_log_exists).lower(),
            "warning_flags": ";".join(result.warning_flags),
            "notes": result.notes,
        })
