from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_real_marketdata_smoke_summary import (
    READY,
    SAFETY_REVIEW_REQUIRED,
    SUMMARY_FIELDS,
    generate_summary,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_real_marketdata_smoke.sh"


SAFE_CONFIG = """ibkr:
  read_only_required: true
  real_connection_allowed: false
  contract_qualification_allowed: false
  market_data_request_allowed: false
  historical_data_request_allowed: false
  trading_actions_allowed: false
"""


def _read_one_csv(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


def test_summary_csv_and_markdown_generate_without_tws(tmp_path: Path):
    config = tmp_path / "config.yaml"
    config.write_text(SAFE_CONFIG, encoding="utf-8")

    top_status, row = generate_summary(
        config_path=config,
        snapshot_csv=tmp_path / "missing_snapshot.csv",
        output_csv=tmp_path / "operator_real_marketdata_smoke_summary.csv",
        output_report=tmp_path / "reports/operator_real_marketdata_smoke_report.md",
        started_at="2026-05-25T00:00:00+00:00",
        ended_at="2026-05-25T00:00:01+00:00",
        wrapper_exit_code=0,
        smoke_exit_code=0,
        config_restored=True,
        config_file_modified=False,
        real_connection_allowed_during_run=True,
        market_data_request_allowed_during_run=True,
    )

    assert top_status == READY
    assert row["top_level_status"] == READY
    assert (tmp_path / "operator_real_marketdata_smoke_summary.csv").exists()
    assert (tmp_path / "reports/operator_real_marketdata_smoke_report.md").exists()
    assert set(_read_one_csv(tmp_path / "operator_real_marketdata_smoke_summary.csv")) == set(SUMMARY_FIELDS)


def test_summary_default_safety_fields_are_false(tmp_path: Path):
    config = tmp_path / "config.yaml"
    config.write_text(SAFE_CONFIG, encoding="utf-8")
    _, row = generate_summary(
        config_path=config,
        output_csv=tmp_path / "summary.csv",
        output_report=tmp_path / "report.md",
        real_connection_allowed_during_run=True,
        market_data_request_allowed_during_run=True,
    )

    for field in (
        "contract_qualification_allowed",
        "historical_data_request_allowed",
        "trading_actions_allowed",
        "account_read_allowed",
        "position_read_allowed",
        "telegram_send_allowed",
        "req_historical_data_allowed",
        "order_action_allowed",
        "cancel_action_allowed",
        "rebalance_action_allowed",
        "historical_data_request_triggered",
        "broker_execution_triggered",
        "account_read_triggered",
        "position_read_triggered",
        "telegram_send_triggered",
    ):
        assert row[field] == "false"


def test_forbidden_snapshot_action_field_forces_safety_review(tmp_path: Path):
    config = tmp_path / "config.yaml"
    config.write_text(SAFE_CONFIG, encoding="utf-8")
    snapshot = tmp_path / "ibkr_market_data_snapshot.csv"
    snapshot.write_text(
        "display_symbol,historical_data_request_triggered,broker_execution_triggered,account_read_triggered,position_read_triggered,telegram_send_triggered\n"
        "GLD,true,false,false,false,false\n",
        encoding="utf-8",
    )

    top_status, row = generate_summary(
        config_path=config,
        snapshot_csv=snapshot,
        output_csv=tmp_path / "summary.csv",
        output_report=tmp_path / "report.md",
        real_connection_allowed_during_run=True,
        market_data_request_allowed_during_run=True,
    )

    assert top_status == SAFETY_REVIEW_REQUIRED
    assert row["historical_data_request_triggered"] == "true"
    assert row["final_safety_status"] == "SAFETY_REVIEW_REQUIRED"


def test_wrapper_restores_config_and_generates_audit_with_stub_smoke(tmp_path: Path):
    config = tmp_path / "config.yaml"
    before = SAFE_CONFIG + "custom: keep\n"
    config.write_text(before, encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "reports").mkdir()
    (tmp_path / "scripts/ibkr_market_data_snapshot_oneshot.sh").write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf 'display_symbol,connection_succeeded,market_data_request_triggered,historical_data_request_triggered,broker_execution_triggered,account_read_triggered,position_read_triggered,telegram_send_triggered\\nGLD,false,false,false,false,false,false,false\\n' > "${PHASE442_TEST_SNAPSHOT_CSV:?}"
exit "${PHASE442_STUB_SMOKE_EXIT:-0}"
""",
        encoding="utf-8",
    )
    (tmp_path / "scripts/ibkr_market_data_snapshot_oneshot.sh").chmod(0o755)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))
    env["PHASE442_SMOKE_SCRIPT"] = str(tmp_path / "scripts/ibkr_market_data_snapshot_oneshot.sh")
    env["PHASE442_TEST_SNAPSHOT_CSV"] = str(tmp_path / "ibkr_market_data_snapshot.csv")
    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--config",
            str(config),
            "--output-csv",
            str(tmp_path / "operator_real_marketdata_smoke_summary.csv"),
            "--output-report",
            str(tmp_path / "reports/operator_real_marketdata_smoke_report.md"),
            "--snapshot-csv",
            str(tmp_path / "ibkr_market_data_snapshot.csv"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert config.read_text(encoding="utf-8") == before
    row = _read_one_csv(tmp_path / "operator_real_marketdata_smoke_summary.csv")
    assert row["config_restored"] == "true"
    assert row["config_file_modified"] == "false"
    assert row["real_connection_allowed_during_run"] == "true"
    assert row["market_data_request_allowed_during_run"] == "true"


def test_wrapper_restores_config_when_stub_smoke_fails(tmp_path: Path):
    config = tmp_path / "config.yaml"
    before = SAFE_CONFIG
    config.write_text(before, encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "reports").mkdir()
    (tmp_path / "scripts/ibkr_market_data_snapshot_oneshot.sh").write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf 'display_symbol,historical_data_request_triggered,broker_execution_triggered,account_read_triggered,position_read_triggered,telegram_send_triggered\\nGLD,false,false,false,false,false\\n' > "${PHASE442_TEST_SNAPSHOT_CSV:?}"
exit 7
""",
        encoding="utf-8",
    )
    (tmp_path / "scripts/ibkr_market_data_snapshot_oneshot.sh").chmod(0o755)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))
    env["PHASE442_SMOKE_SCRIPT"] = str(tmp_path / "scripts/ibkr_market_data_snapshot_oneshot.sh")
    env["PHASE442_TEST_SNAPSHOT_CSV"] = str(tmp_path / "ibkr_market_data_snapshot.csv")
    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--config",
            str(config),
            "--output-csv",
            str(tmp_path / "operator_real_marketdata_smoke_summary.csv"),
            "--output-report",
            str(tmp_path / "reports/operator_real_marketdata_smoke_report.md"),
            "--snapshot-csv",
            str(tmp_path / "ibkr_market_data_snapshot.csv"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 7, result.stdout
    assert config.read_text(encoding="utf-8") == before
    row = _read_one_csv(tmp_path / "operator_real_marketdata_smoke_summary.csv")
    assert row["top_level_status"] == "REAL_MARKETDATA_SMOKE_AUDIT_FAILED"
    assert row["config_restored"] == "true"
    assert row["config_file_modified"] == "false"


def test_new_code_does_not_introduce_forbidden_direct_paths():
    combined = (
        WRAPPER.read_text(encoding="utf-8")
        + "\n"
        + (REPO_ROOT / "src/operator_real_marketdata_smoke_summary.py").read_text(encoding="utf-8")
    )
    forbidden = (
        "placeOrder(",
        "cancelOrder(",
        "reqHistoricalData(",
        "accountSummary(",
        "reqAccount",
        "reqPositions(",
        "api.telegram.org",
        "sendMessage",
        "requests.post",
    )
    for needle in forbidden:
        assert needle not in combined
