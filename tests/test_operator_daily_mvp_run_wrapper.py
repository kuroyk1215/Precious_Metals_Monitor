from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional

from src.operator_daily_mvp_run_summary import (
    READY,
    SAFETY_REVIEW_REQUIRED,
    STEP_NAMES,
    build_markdown_report,
    build_summary_rows,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_daily_mvp_run.sh"
SAFETY_FIELDS = (
    "action_allowed",
    "broker_execution_triggered",
    "historical_data_request_triggered",
    "account_read_triggered",
    "position_read_triggered",
    "telegram_send_triggered",
)


def _write_fake_scripts(script_dir: Path) -> None:
    script_dir.mkdir(parents=True, exist_ok=True)
    body = r'''#!/usr/bin/env bash
set -uo pipefail

name="$(basename "$0" .sh)"
echo "$name" >> "${PHASE441_ORDER_LOG:?order log missing}"

root="."
output_csv=""
output_report=""
output_html=""
preview_report=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root=*) root="${1#--root=}"; shift ;;
    --root) root="${2:?--root requires a path}"; shift 2 ;;
    --output-csv=*) output_csv="${1#--output-csv=}"; shift ;;
    --output-csv) output_csv="${2:?--output-csv requires a path}"; shift 2 ;;
    --output-report=*) output_report="${1#--output-report=}"; shift ;;
    --output-report) output_report="${2:?--output-report requires a path}"; shift 2 ;;
    --output-html=*) output_html="${1#--output-html=}"; shift ;;
    --output-html) output_html="${2:?--output-html requires a path}"; shift 2 ;;
    --preview-report=*) preview_report="${1#--preview-report=}"; shift ;;
    --preview-report) preview_report="${2:?--preview-report requires a path}"; shift 2 ;;
    --contract-map-csv|--snapshot-csv|--api-errors-csv|--execution-c-packet|--operator-packet|--post-analysis-csv|--telegram-notification-packet) shift 2 ;;
    --contract-map-csv=*|--snapshot-csv=*|--api-errors-csv=*|--execution-c-packet=*|--operator-packet=*|--post-analysis-csv=*|--telegram-notification-packet=*) shift ;;
    *) shift ;;
  esac
done

mkdir -p "$root/reports"

write_csv() {
  local path="$1"
  local status="$2"
  local unsafe_field="${PHASE441_UNSAFE_FIELD:-}"
  local action_allowed="false"
  local broker_execution_triggered="false"
  local historical_data_request_triggered="false"
  local account_read_triggered="false"
  local position_read_triggered="false"
  local telegram_send_triggered="false"
  case "$unsafe_field" in
    action_allowed) action_allowed="true" ;;
    broker_execution_triggered) broker_execution_triggered="true" ;;
    historical_data_request_triggered) historical_data_request_triggered="true" ;;
    account_read_triggered) account_read_triggered="true" ;;
    position_read_triggered) position_read_triggered="true" ;;
    telegram_send_triggered) telegram_send_triggered="true" ;;
  esac
  mkdir -p "$(dirname "$path")"
  {
    printf 'top_level_status,display_symbol,symbol,recommended_operator_action,action_allowed,broker_execution_triggered,historical_data_request_triggered,account_read_triggered,position_read_triggered,telegram_send_triggered\n'
    printf '%s,GLD,GLD,manual review only,%s,%s,%s,%s,%s,%s\n' "$status" "$action_allowed" "$broker_execution_triggered" "$historical_data_request_triggered" "$account_read_triggered" "$position_read_triggered" "$telegram_send_triggered"
  } > "$path"
}

case "$name" in
  daily_operator_handoff_summary)
    write_csv "${output_csv:-$root/daily_operator_handoff_summary.csv}" "OPERATOR_HANDOFF_REFERENCE_READY"
    printf '# Daily Operator Handoff Summary\n\n- top_level_status=OPERATOR_HANDOFF_REFERENCE_READY\n' > "${output_report:-$root/reports/daily_operator_handoff_summary.md}"
    ;;
  latest_artifact_entrypoint)
    cp "$root/daily_operator_handoff_summary.csv" "$root/latest_daily_operator_handoff_summary.csv"
    cp "$root/reports/daily_operator_handoff_summary.md" "$root/reports/latest_operator_handoff_summary.md"
    printf 'artifact_path,artifact_status\nlatest_daily_operator_handoff_summary.csv,PRESENT\n' > "$root/latest_run_manifest.csv"
    printf '# Latest Run Manifest\n\n- top_level_status=LATEST_ENTRYPOINT_READY\n' > "$root/reports/latest_run_manifest.md"
    ;;
  research_trading_plan)
    write_csv "${output_csv:-$root/research_trading_plan.csv}" "RESEARCH_PLAN_REFERENCE_READY"
    printf '# Research Trading Plan Report\n\n- top_level_status=RESEARCH_PLAN_REFERENCE_READY\n' > "${output_report:-$root/reports/research_trading_plan_report.md}"
    ;;
  watchlist_universe)
    write_csv "${output_csv:-$root/watchlist_universe.csv}" "WATCHLIST_UNIVERSE_READY"
    printf '# Watchlist Universe Report\n\n- top_level_status=WATCHLIST_UNIVERSE_READY\n' > "${output_report:-$root/reports/watchlist_universe_report.md}"
    ;;
  telegram_notification_gate)
    write_csv "${output_csv:-$root/telegram_notification_gate.csv}" "TELEGRAM_GATE_APPROVAL_REQUIRED"
    printf '# Telegram Notification Gate Report\n\n- top_level_status=TELEGRAM_GATE_APPROVAL_REQUIRED\n' > "${output_report:-$root/reports/telegram_notification_gate_report.md}"
    printf '# Telegram Notification Approval Preview\n\nmanual review only\n' > "${preview_report:-$root/reports/telegram_notification_approval_preview.md}"
    ;;
  local_dashboard)
    out="${output_html:-reports/dashboard.html}"
    mkdir -p "$root/$(dirname "$out")"
    printf '<!doctype html><title>Dashboard</title><p>dashboard_status=DASHBOARD_READY</p>' > "$root/$out"
    ;;
esac

if [[ "${PHASE441_FAIL_STEP:-}" == "$name" ]]; then
  exit 7
fi
exit 0
'''
    for script in (
        "daily_operator_handoff_summary.sh",
        "latest_artifact_entrypoint.sh",
        "research_trading_plan.sh",
        "watchlist_universe.sh",
        "telegram_notification_gate.sh",
        "local_dashboard.sh",
    ):
        path = script_dir / script
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)


def _run_wrapper(tmp_path: Path, *, extra_env: Optional[Dict[str, str]] = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    script_dir = tmp_path / "scripts"
    _write_fake_scripts(script_dir)
    order_log = tmp_path / "order.log"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PHASE441_ORDER_LOG"] = str(order_log)
    if extra_env:
        env.update(extra_env)
    config_path = tmp_path / "config.yaml"
    if not config_path.exists():
        config_path.write_text("real_connection_allowed: false\n", encoding="utf-8")
    return subprocess.run(
        ["bash", str(WRAPPER), "--root", str(tmp_path), "--script-dir", str(script_dir)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
    )


def _summary_rows(root: Path) -> list[dict[str, str]]:
    with (root / "operator_daily_mvp_run_summary.csv").open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_wrapper_happy_path_generates_summary_report_and_ready_status(tmp_path: Path):
    result = _run_wrapper(tmp_path)

    assert "top_level_status=DAILY_MVP_RUN_READY" in result.stdout
    assert (tmp_path / "operator_daily_mvp_run_summary.csv").exists()
    assert (tmp_path / "reports/operator_daily_mvp_run_summary.md").exists()
    assert (tmp_path / "reports/dashboard.html").exists()
    rows = _summary_rows(tmp_path)
    assert [row["step_name"] for row in rows] == list(STEP_NAMES)
    assert {row["step_status"] for row in rows} == {"PASS"}
    assert all(row["offline_only"] == "true" for row in rows)
    for row in rows:
        for field in SAFETY_FIELDS:
            assert row[field] == "false"


def test_wrapper_runs_scripts_in_required_order(tmp_path: Path):
    _run_wrapper(tmp_path)

    order = (tmp_path / "order.log").read_text(encoding="utf-8").splitlines()
    assert order == list(STEP_NAMES)


def test_safety_flag_true_produces_safety_review_required(tmp_path: Path):
    result = _run_wrapper(tmp_path, extra_env={"PHASE441_UNSAFE_FIELD": "broker_execution_triggered"}, check=False)

    assert result.returncode == 1
    assert "top_level_status=DAILY_MVP_RUN_SAFETY_REVIEW_REQUIRED" in result.stdout
    report = (tmp_path / "reports/operator_daily_mvp_run_summary.md").read_text(encoding="utf-8")
    assert SAFETY_REVIEW_REQUIRED in report
    assert "broker_execution_triggered=true" in report
    assert "broker_execution_triggered" in _summary_rows(tmp_path)[0]["notes"]


def test_failed_step_is_recorded_as_fail_and_later_steps_still_run(tmp_path: Path):
    _run_wrapper(tmp_path, extra_env={"PHASE441_FAIL_STEP": "research_trading_plan"})

    rows = _summary_rows(tmp_path)
    by_step = {row["step_name"]: row for row in rows}
    assert by_step["research_trading_plan"]["step_status"] == "FAIL"
    assert by_step["watchlist_universe"]["step_status"] == "PASS"
    assert by_step["telegram_notification_gate"]["step_status"] == "PASS"
    assert by_step["local_dashboard"]["step_status"] == "PASS"


def test_no_forbidden_execution_words_appear_as_operator_instructions(tmp_path: Path):
    _run_wrapper(tmp_path)

    rows = _summary_rows(tmp_path)
    report = build_markdown_report(READY, rows, [])
    for word in ("BUY", "SELL", "ORDER", "CANCEL", "REBALANCE", "AUTO_TRADE", "EXECUTE"):
        assert word not in report.upper()


def test_wrapper_does_not_modify_config_yaml(tmp_path: Path):
    before = "real_connection_allowed: false\ncustom: keep\n"
    (tmp_path / "config.yaml").write_text(before, encoding="utf-8")
    _run_wrapper(tmp_path)

    assert (tmp_path / "config.yaml").read_text(encoding="utf-8") == before


def test_wrapper_runs_offline_only(tmp_path: Path):
    _run_wrapper(tmp_path)

    rows = _summary_rows(tmp_path)
    assert all(row["offline_only"] == "true" for row in rows)
    wrapper_text = WRAPPER.read_text(encoding="utf-8")
    module_text = (REPO_ROOT / "src/operator_daily_mvp_run_summary.py").read_text(encoding="utf-8")
    forbidden = (
        "api.telegram.org",
        "sendMessage",
        "reqMktData",
        "reqHistoricalData",
        "reqAccount",
        "reqPositions",
        "placeOrder",
        "cancelOrder",
        "real_connection_allowed: true",
        "market_data_request_allowed: true",
        "historical_data_request_allowed: true",
        "trading_actions_allowed: true",
    )
    for needle in forbidden:
        assert needle not in wrapper_text
        assert needle not in module_text
