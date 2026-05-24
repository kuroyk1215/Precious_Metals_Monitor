from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


TRUE_TEXT = "true"
FALSE_TEXT = "false"

CORE_HANDOFF_CSV = "daily_operator_handoff_summary.csv"
CORE_HANDOFF_REPORT = "reports/daily_operator_handoff_summary.md"
LATEST_HANDOFF_CSV = "latest_daily_operator_handoff_summary.csv"
LATEST_HANDOFF_REPORT = "reports/latest_operator_handoff_summary.md"
LATEST_MANIFEST_CSV = "latest_run_manifest.csv"
LATEST_MANIFEST_REPORT = "reports/latest_run_manifest.md"

FORBIDDEN_ACTION_WORDS = ("BUY", "SELL", "ORDER", "CANCEL", "REBALANCE", "AUTO_TRADE", "TRADE")
SAFETY_FIELDS = (
    "action_allowed",
    "broker_execution_triggered",
    "historical_data_request_triggered",
    "account_read_triggered",
    "position_read_triggered",
    "telegram_send_triggered",
)


@dataclass(frozen=True)
class ArtifactSpec:
    artifact_name: str
    artifact_path: str
    artifact_type: str
    safety_relevant: str
    operator_relevant: str
    notes: str = ""


@dataclass(frozen=True)
class ManifestRow:
    manifest_run_id: str
    manifest_timestamp: str
    artifact_name: str
    artifact_path: str
    artifact_type: str
    artifact_status: str
    source_path: str
    row_count: str
    file_size_bytes: str
    safety_relevant: str
    operator_relevant: str
    notes: str


MANIFEST_FIELDS = [
    "manifest_run_id",
    "manifest_timestamp",
    "artifact_name",
    "artifact_path",
    "artifact_type",
    "artifact_status",
    "source_path",
    "row_count",
    "file_size_bytes",
    "safety_relevant",
    "operator_relevant",
    "notes",
]

BASE_ARTIFACTS = [
    ArtifactSpec("daily_operator_handoff_summary", CORE_HANDOFF_CSV, "csv", TRUE_TEXT, TRUE_TEXT, "core_operator_handoff_summary"),
    ArtifactSpec("daily_operator_handoff_summary_report", CORE_HANDOFF_REPORT, "markdown", TRUE_TEXT, TRUE_TEXT, "core_operator_handoff_report"),
    ArtifactSpec("first_operator_run_post_analysis", "first_operator_run_post_analysis.csv", "csv", TRUE_TEXT, TRUE_TEXT),
    ArtifactSpec("first_operator_run_summary", "reports/first_operator_run_summary.md", "markdown", TRUE_TEXT, TRUE_TEXT),
    ArtifactSpec("ibkr_execution_c_validation_packet", "ibkr_execution_c_validation_packet.csv", "csv", TRUE_TEXT, TRUE_TEXT),
    ArtifactSpec("ibkr_daily_operator_packet", "ibkr_daily_operator_packet.csv", "csv", TRUE_TEXT, TRUE_TEXT),
    ArtifactSpec("ibkr_market_data_snapshot", "ibkr_market_data_snapshot.csv", "csv", FALSE_TEXT, TRUE_TEXT),
    ArtifactSpec("ibkr_market_data_api_errors", "ibkr_market_data_api_errors.csv", "csv", TRUE_TEXT, TRUE_TEXT),
    ArtifactSpec("ibkr_telegram_notification_packet", "ibkr_telegram_notification_packet.csv", "csv", TRUE_TEXT, TRUE_TEXT),
    ArtifactSpec("ibkr_telegram_message_preview", "reports/ibkr_telegram_message_preview.md", "markdown", TRUE_TEXT, TRUE_TEXT),
]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _clean(value: object) -> str:
    return str(value or "").strip()


def _artifact_path(root: Path, relative_path: str) -> Path:
    return root / relative_path


def _row_count(path: Path, artifact_type: str) -> str:
    if artifact_type != "csv" or not path.exists():
        return ""
    with path.open(newline="", encoding="utf-8") as f:
        return str(sum(1 for _ in csv.DictReader(f)))


def _file_size(path: Path) -> str:
    if not path.exists():
        return ""
    return str(path.stat().st_size)


def _manifest_row(
    *,
    run_id: str,
    timestamp: str,
    spec: ArtifactSpec,
    status: str,
    source_path: str = "",
    root: Path,
) -> ManifestRow:
    path = _artifact_path(root, spec.artifact_path)
    return ManifestRow(
        manifest_run_id=run_id,
        manifest_timestamp=timestamp,
        artifact_name=spec.artifact_name,
        artifact_path=spec.artifact_path,
        artifact_type=spec.artifact_type,
        artifact_status=status,
        source_path=source_path,
        row_count=_row_count(path, spec.artifact_type),
        file_size_bytes=_file_size(path),
        safety_relevant=spec.safety_relevant,
        operator_relevant=spec.operator_relevant,
        notes=spec.notes,
    )


def _find_latest_log_artifacts(root: Path) -> List[ArtifactSpec]:
    log_root = root / "logs" / "ibkr_daily"
    if not log_root.exists():
        return [
            ArtifactSpec("latest_ibkr_local_daily_runner_summary", "logs/ibkr_daily/latest/ibkr_local_daily_runner_summary.csv", "csv", TRUE_TEXT, TRUE_TEXT, "latest_runner_summary_not_found"),
            ArtifactSpec("latest_ibkr_local_daily_runner_report", "logs/ibkr_daily/latest/ibkr_local_daily_runner_report.md", "markdown", TRUE_TEXT, TRUE_TEXT, "latest_runner_report_not_found"),
        ]

    summaries = sorted(log_root.glob("*/*/ibkr_local_daily_runner_summary.csv"))
    reports = sorted(log_root.glob("*/*/ibkr_local_daily_runner_report.md"))
    specs: List[ArtifactSpec] = []
    if summaries:
        specs.append(ArtifactSpec("latest_ibkr_local_daily_runner_summary", str(summaries[-1].relative_to(root)), "csv", TRUE_TEXT, TRUE_TEXT, "latest_logs_ibkr_daily_summary"))
    else:
        specs.append(ArtifactSpec("latest_ibkr_local_daily_runner_summary", "logs/ibkr_daily/latest/ibkr_local_daily_runner_summary.csv", "csv", TRUE_TEXT, TRUE_TEXT, "latest_runner_summary_not_found"))
    if reports:
        specs.append(ArtifactSpec("latest_ibkr_local_daily_runner_report", str(reports[-1].relative_to(root)), "markdown", TRUE_TEXT, TRUE_TEXT, "latest_logs_ibkr_daily_report"))
    else:
        specs.append(ArtifactSpec("latest_ibkr_local_daily_runner_report", "logs/ibkr_daily/latest/ibkr_local_daily_runner_report.md", "markdown", TRUE_TEXT, TRUE_TEXT, "latest_runner_report_not_found"))
    return specs


def _copy_artifact(root: Path, source: str, destination: str) -> None:
    source_path = _artifact_path(root, source)
    destination_path = _artifact_path(root, destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, destination_path)


def _generate_core_handoff(root: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [
            "bash",
            str(repo_root / "scripts" / "daily_operator_handoff_summary.sh"),
            "--contract-map-csv",
            str(_artifact_path(root, "ibkr_verified_contract_map_gld_slv.csv")),
            "--snapshot-csv",
            str(_artifact_path(root, "ibkr_market_data_snapshot.csv")),
            "--api-errors-csv",
            str(_artifact_path(root, "ibkr_market_data_api_errors.csv")),
            "--execution-c-packet",
            str(_artifact_path(root, "ibkr_execution_c_validation_packet.csv")),
            "--operator-packet",
            str(_artifact_path(root, "ibkr_daily_operator_packet.csv")),
            "--post-analysis-csv",
            str(_artifact_path(root, "first_operator_run_post_analysis.csv")),
            "--telegram-notification-packet",
            str(_artifact_path(root, "ibkr_telegram_notification_packet.csv")),
            "--output-csv",
            str(_artifact_path(root, CORE_HANDOFF_CSV)),
            "--output-report",
            str(_artifact_path(root, CORE_HANDOFF_REPORT)),
        ],
        cwd=str(repo_root),
        check=True,
        capture_output=True,
        text=True,
    )


def ensure_core_handoff(root: Path) -> str:
    csv_path = _artifact_path(root, CORE_HANDOFF_CSV)
    report_path = _artifact_path(root, CORE_HANDOFF_REPORT)
    if csv_path.exists() and report_path.exists():
        return "PRESENT"
    _generate_core_handoff(root)
    if not csv_path.exists() or not report_path.exists():
        raise FileNotFoundError("daily operator handoff summary generation did not produce both core artifacts")
    return "GENERATED"


def _read_csv_rows(path: Path) -> List[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_latest_summary_action_values(root: Path) -> List[str]:
    rows = _read_csv_rows(_artifact_path(root, LATEST_HANDOFF_CSV))
    values: List[str] = []
    for row in rows:
        for key, value in row.items():
            lowered = key.lower()
            if "action" in lowered or key == "recommended_operator_action":
                values.append(_clean(value))
    return values


def forbidden_action_words_found(values: Iterable[str]) -> List[str]:
    found: List[str] = []
    for value in values:
        upper = value.upper()
        for word in FORBIDDEN_ACTION_WORDS:
            if word in upper and word not in found:
                found.append(word)
    return found


def read_safety_field_values(root: Path) -> dict[str, str]:
    rows = _read_csv_rows(_artifact_path(root, LATEST_HANDOFF_CSV))
    result = {field: FALSE_TEXT for field in SAFETY_FIELDS}
    for row in rows:
        for field in SAFETY_FIELDS:
            value = _clean(row.get(field)).lower()
            if value and value != FALSE_TEXT:
                result[field] = TRUE_TEXT
    return result


def _write_manifest_csv(path: Path, rows: Sequence[ManifestRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(MANIFEST_FIELDS)
        for row in rows:
            writer.writerow([getattr(row, field) for field in MANIFEST_FIELDS])


def _markdown_table(rows: Sequence[ManifestRow]) -> List[str]:
    lines = [
        "| artifact_name | artifact_path | artifact_type | artifact_status | source_path | row_count | file_size_bytes | safety_relevant | operator_relevant | notes |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.artifact_name} | {row.artifact_path} | {row.artifact_type} | {row.artifact_status} | {row.source_path or ''} | {row.row_count or ''} | {row.file_size_bytes or ''} | {row.safety_relevant} | {row.operator_relevant} | {row.notes} |"
        )
    return lines


def _build_manifest_report(
    *,
    manifest_run_id: str,
    manifest_timestamp: str,
    rows: Sequence[ManifestRow],
    handoff_status: str,
    safety_values: dict[str, str],
    forbidden_words: Sequence[str],
) -> str:
    missing = [row for row in rows if row.artifact_status == "MISSING"]
    core = [row for row in rows if row.artifact_path in {CORE_HANDOFF_CSV, CORE_HANDOFF_REPORT, LATEST_HANDOFF_CSV, LATEST_HANDOFF_REPORT}]
    missing_lines = [f"- {row.artifact_path}" for row in missing] or ["- none"]
    next_step = "open_reports_latest_operator_handoff_summary_md"
    if forbidden_words or any(value != FALSE_TEXT for value in safety_values.values()):
        next_step = "stop_and_review_latest_handoff_safety_fields"
    return "\n".join(
        [
            "# Latest Run Manifest",
            "",
            "## Latest entrypoint summary",
            "",
            f"- latest_entrypoint_status=LATEST_ENTRYPOINT_READY",
            f"- manifest_run_id={manifest_run_id}",
            f"- manifest_timestamp={manifest_timestamp}",
            f"- operator_handoff_summary_status={handoff_status}",
            f"- manifest_status=READY",
            "",
            "## Core operator files",
            "",
            *_markdown_table(core),
            "",
            "## Runtime artifact manifest table",
            "",
            *_markdown_table(rows),
            "",
            "## Missing artifact section",
            "",
            *missing_lines,
            "",
            "## Safety statement",
            "",
            f"- action_allowed={safety_values['action_allowed']}",
            f"- broker_execution_triggered={safety_values['broker_execution_triggered']}",
            f"- historical_data_request_triggered={safety_values['historical_data_request_triggered']}",
            f"- account_read_triggered={safety_values['account_read_triggered']}",
            f"- position_read_triggered={safety_values['position_read_triggered']}",
            f"- telegram_send_triggered={safety_values['telegram_send_triggered']}",
            f"- forbidden_latest_summary_action_words={','.join(forbidden_words) if forbidden_words else 'none'}",
            "- offline_only=true",
            "- tws_or_ib_gateway_connection_attempted=false",
            "- market_data_request_triggered=false",
            "",
            "## Next operator step",
            "",
            f"- {next_step}",
        ]
    ) + "\n"


def _write_manifest_report(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_latest_artifact_entrypoint(root: str | Path = ".") -> tuple[str, List[ManifestRow]]:
    root_path = Path(root)
    handoff_status = ensure_core_handoff(root_path)
    _copy_artifact(root_path, CORE_HANDOFF_CSV, LATEST_HANDOFF_CSV)
    _copy_artifact(root_path, CORE_HANDOFF_REPORT, LATEST_HANDOFF_REPORT)

    now = _utc_now()
    manifest_run_id = "latest_entrypoint_" + now.strftime("%Y%m%dT%H%M%SZ")
    manifest_timestamp = now.isoformat().replace("+00:00", "Z")
    specs = list(BASE_ARTIFACTS) + _find_latest_log_artifacts(root_path)
    rows: List[ManifestRow] = []
    for spec in specs:
        status = "PRESENT" if _artifact_path(root_path, spec.artifact_path).exists() else "MISSING"
        rows.append(_manifest_row(run_id=manifest_run_id, timestamp=manifest_timestamp, spec=spec, status=status, root=root_path))

    copied_specs = [
        ArtifactSpec("latest_daily_operator_handoff_summary", LATEST_HANDOFF_CSV, "csv", TRUE_TEXT, TRUE_TEXT, "copied_stable_latest_operator_csv"),
        ArtifactSpec("latest_operator_handoff_summary", LATEST_HANDOFF_REPORT, "markdown", TRUE_TEXT, TRUE_TEXT, "copied_stable_latest_operator_report"),
    ]
    for spec, source in zip(copied_specs, (CORE_HANDOFF_CSV, CORE_HANDOFF_REPORT)):
        rows.append(_manifest_row(run_id=manifest_run_id, timestamp=manifest_timestamp, spec=spec, status="COPIED", source_path=source, root=root_path))

    manifest_csv_spec = ArtifactSpec("latest_run_manifest", LATEST_MANIFEST_CSV, "csv", TRUE_TEXT, TRUE_TEXT, "generated_offline_latest_manifest_csv")
    manifest_report_spec = ArtifactSpec("latest_run_manifest_report", LATEST_MANIFEST_REPORT, "markdown", TRUE_TEXT, TRUE_TEXT, "generated_offline_latest_manifest_report")
    rows.append(_manifest_row(run_id=manifest_run_id, timestamp=manifest_timestamp, spec=manifest_csv_spec, status="GENERATED", root=root_path))

    safety_values = read_safety_field_values(root_path)
    forbidden_words = forbidden_action_words_found(read_latest_summary_action_values(root_path))
    report_text = _build_manifest_report(
        manifest_run_id=manifest_run_id,
        manifest_timestamp=manifest_timestamp,
        rows=rows,
        handoff_status=handoff_status,
        safety_values=safety_values,
        forbidden_words=forbidden_words,
    )
    _write_manifest_csv(_artifact_path(root_path, LATEST_MANIFEST_CSV), rows)
    final_report_row = _manifest_row(run_id=manifest_run_id, timestamp=manifest_timestamp, spec=manifest_report_spec, status="GENERATED", root=root_path)
    rows.append(final_report_row)
    report_text = _build_manifest_report(
        manifest_run_id=manifest_run_id,
        manifest_timestamp=manifest_timestamp,
        rows=rows,
        handoff_status=handoff_status,
        safety_values=safety_values,
        forbidden_words=forbidden_words,
    )
    _write_manifest_report(_artifact_path(root_path, LATEST_MANIFEST_REPORT), report_text)
    _write_manifest_csv(_artifact_path(root_path, LATEST_MANIFEST_CSV), rows)
    return handoff_status, rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build stable offline latest artifact entrypoints.")
    parser.add_argument("--root", default=".")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    root = Path(args.root)
    handoff_status, _ = build_latest_artifact_entrypoint(root)
    safety_values = read_safety_field_values(root)
    forbidden_words = forbidden_action_words_found(read_latest_summary_action_values(root))
    print("latest_entrypoint_status=LATEST_ENTRYPOINT_READY")
    print(f"operator_handoff_summary_status={handoff_status}")
    print("manifest_status=READY")
    for field in SAFETY_FIELDS:
        print(f"{field}={safety_values[field]}")
    print("forbidden_latest_summary_action_words=" + (",".join(forbidden_words) if forbidden_words else "none"))
    print(f"csv={LATEST_HANDOFF_CSV}")
    print(f"report={LATEST_HANDOFF_REPORT}")
    print(f"manifest_csv={LATEST_MANIFEST_CSV}")
    print(f"manifest_report={LATEST_MANIFEST_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
