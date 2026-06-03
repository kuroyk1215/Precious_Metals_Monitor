from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "verify_gld_slv_daily_loop.sh"
RUNBOOK = REPO_ROOT / "reports" / "gld_slv_daily_loop_runbook.md"


def test_verify_script_exists_and_is_executable():
    assert VERIFY_SCRIPT.exists()
    assert os.access(VERIFY_SCRIPT, os.X_OK)


def test_runbook_contains_daily_loop_commands_and_state_explanations():
    text = RUNBOOK.read_text(encoding="utf-8")
    for term in (
        "scripts/batch1_gld_slv_core_research_loop.sh",
        "scripts/gld_slv_dashboard_mvp.sh",
        "scripts/verify_gld_slv_daily_loop.sh",
        "runtime/reports/latest_gld_slv_research.md",
        "runtime/dashboard/index.html",
        "logs/research_log_US.csv",
        "no_price",
        "delayed",
        "frozen",
        "source_conflict",
        "NO_TRADE",
        "action_allowed=false",
        "git restore dashboard/index.html reports/latest_gld_slv_research.md",
        "Research only, no automatic trading",
    ):
        assert term in text


def test_verify_script_runs_to_runtime_outputs_without_tracked_generated_dirty():
    result = subprocess.run(
        ["bash", str(VERIFY_SCRIPT)],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "GLD/SLV daily loop verification passed" in result.stdout
    assert (REPO_ROOT / "runtime/reports/latest_gld_slv_research.md").exists()
    assert (REPO_ROOT / "logs/research_log_US.csv").exists()
    assert (REPO_ROOT / "runtime/dashboard/index.html").exists()

    status = subprocess.run(
        ["git", "status", "--short", "--", "dashboard/index.html", "reports/latest_gld_slv_research.md"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    assert status.stdout.strip() == ""


def test_runtime_dashboard_contains_batch4_required_fields_after_verify():
    html = (REPO_ROOT / "runtime/dashboard/index.html").read_text(encoding="utf-8")
    for term in (
        "GLD",
        "SLV",
        "action_rating",
        "data_delay_flag",
        "US_30mEcho",
        "IBKR cash account",
        "settled cash",
        "GFV",
    ):
        assert term in html


def test_batch4_active_files_omit_automatic_trading_api_names():
    files = [
        REPO_ROOT / "src/gld_slv_daily_loop_verifier.py",
        REPO_ROOT / "src/gld_slv_dashboard_mvp.py",
        REPO_ROOT / "scripts/verify_gld_slv_daily_loop.sh",
        REPO_ROOT / "scripts/batch1_gld_slv_core_research_loop.sh",
        REPO_ROOT / "scripts/gld_slv_dashboard_mvp.sh",
        REPO_ROOT / "dashboard/index.html",
    ]
    forbidden = ["place" + "Order", "cancel" + "Order", "what" + "If" + "Order"]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert not any(term in text for term in forbidden), path
