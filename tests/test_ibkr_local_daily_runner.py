from datetime import datetime
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

from src.ibkr_local_daily_runner import (
    build_run_id,
    build_runner_summary,
    copy_outputs_to_run_dir,
    ensure_run_dir,
    rotate_old_run_dirs,
)


def test_build_run_id_contains_jst_date():
    now = datetime(2026, 5, 22, 16, 10, 5, tzinfo=ZoneInfo("Asia/Tokyo"))
    run_date, run_id, run_ts = build_run_id(now, "Asia/Tokyo")
    assert run_date == "20260522"
    assert run_id == "20260522_161005_JST"
    assert "2026-05-22" in run_ts


def test_ensure_run_dir_creates_tmp_path_directory(tmp_path: Path):
    run_dir = ensure_run_dir(tmp_path, "20260522", "20260522_161005_JST")
    assert run_dir.exists()
    assert run_dir.is_dir()
    assert run_dir.parent.name == "20260522"


def test_copy_outputs_to_run_dir_only_copies_existing_files(tmp_path: Path):
    existing = tmp_path / "existing.csv"
    missing = tmp_path / "missing.csv"
    run_dir = tmp_path / "run"
    existing.write_text("a,b\n1,2\n", encoding="utf-8")

    copied = copy_outputs_to_run_dir([existing, missing], run_dir)

    assert copied == [run_dir / "existing.csv"]
    assert (run_dir / "existing.csv").exists()
    assert not (run_dir / "missing.csv").exists()


def test_missing_output_does_not_crash(tmp_path: Path):
    copied = copy_outputs_to_run_dir([tmp_path / "missing.csv"], tmp_path / "run")
    assert copied == []


def test_build_runner_summary_forces_safety_fields(tmp_path: Path):
    summary = build_runner_summary(
        run_id="20260522_161005_JST",
        run_timestamp="2026-05-22T16:10:05+09:00",
        run_date="20260522",
        run_dir=tmp_path,
        execution_c_mode="dry_run",
        pipeline_exit_code=0,
        archive_status="ARCHIVED",
        copied_file_count=2,
        rotation_enabled=True,
        retention_days=30,
        notes="ok",
    )
    assert summary.action_allowed == "false"
    assert summary.broker_execution_triggered == "false"
    assert summary.historical_data_request_triggered == "false"
    assert summary.account_read_triggered == "false"
    assert summary.position_read_triggered == "false"
    assert summary.manual_review_required == "true"


def test_rotate_old_run_dirs_deletes_old_date_directory(tmp_path: Path):
    old_dir = tmp_path / "20260401"
    old_dir.mkdir()
    (old_dir / "run").mkdir()
    current = datetime(2026, 5, 22, 12, 0, 0)

    removed = rotate_old_run_dirs(tmp_path, 30, enabled=True, now=current)

    assert old_dir in removed
    assert not old_dir.exists()


def test_rotate_old_run_dirs_keeps_recent_date_directory(tmp_path: Path):
    recent_dir = tmp_path / "20260520"
    recent_dir.mkdir()
    current = datetime(2026, 5, 22, 12, 0, 0)

    removed = rotate_old_run_dirs(tmp_path, 30, enabled=True, now=current)

    assert removed == []
    assert recent_dir.exists()


def test_invalid_retention_days_falls_back_without_dangerous_delete(tmp_path: Path):
    date_dir = tmp_path / "20260501"
    date_dir.mkdir()
    current = datetime(2026, 5, 22, 12, 0, 0)

    removed = rotate_old_run_dirs(tmp_path, 0, enabled=True, now=current)

    assert removed == []
    assert date_dir.exists()


def test_rotation_does_not_delete_non_date_directory(tmp_path: Path):
    keep_dir = tmp_path / "not_a_date"
    keep_dir.mkdir()
    current = datetime(2026, 5, 22, 12, 0, 0)

    removed = rotate_old_run_dirs(tmp_path, 7, enabled=True, now=current)

    assert removed == []
    assert keep_dir.exists()


def test_scheduler_plan_script_does_not_trigger_launchctl_or_crontab():
    result = subprocess.run(
        ["bash", "scripts/ibkr_scheduler_plan.sh", "--hour=16", "--minute=10"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "scheduler_install_triggered=false" in result.stdout
    assert "launchctl_triggered=false" in result.stdout
    assert "crontab_modified=false" in result.stdout
    report = Path("reports/ibkr_scheduler_plan_report.md").read_text(encoding="utf-8")
    assert "scheduler_install_triggered | false" in report
    assert "launchctl_triggered | false" in report
    assert "crontab_modified | false" in report
