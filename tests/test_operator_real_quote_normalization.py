from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_real_quote_normalization import NORMALIZATION_FIELDS, generate_normalization


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "operator_real_quote_normalization.sh"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_chain_sources(tmp_path: Path, *, connection: str = "false", request: str = "false", snapshots: str = "0") -> tuple[Path, Path, Path]:
    latest = tmp_path / "operator_real_marketdata_latest.csv"
    daily = tmp_path / "operator_real_marketdata_daily_run_summary.csv"
    decision = tmp_path / "operator_real_marketdata_decision_gate.csv"
    latest.write_text(
        "latest_status,operator_decision,source_diagnostic_category\n"
        "HOLD_SAFE_FAILURE,HOLD_SAFE_FAILURE,PASS_READY\n",
        encoding="utf-8",
    )
    daily.write_text(
        "daily_run_status,operator_decision,source_diagnostic_category\n"
        "DAILY_OPERATOR_CHAIN_HOLD_SAFE_FAILURE,HOLD_SAFE_FAILURE,PASS_READY\n",
        encoding="utf-8",
    )
    decision.write_text(
        "operator_decision,source_diagnostic_category,snapshot_rows_detected,connection_succeeded,market_data_request_triggered\n"
        f"HOLD_SAFE_FAILURE,PASS_READY,{snapshots},{connection},{request}\n",
        encoding="utf-8",
    )
    return latest, daily, decision


def test_normalization_safe_unavailable_when_real_quote_missing(tmp_path: Path):
    latest, daily, decision = _write_chain_sources(tmp_path, connection="false", request="false", snapshots="0")

    rows = generate_normalization(
        latest_csv=latest,
        daily_summary_csv=daily,
        decision_gate_csv=decision,
        output_csv=tmp_path / "operator_real_quote_normalization.csv",
        output_report=tmp_path / "reports/operator_real_quote_normalization_report.md",
        generated_at="2026-05-25T00:00:00+00:00",
    )

    assert {row["symbol"] for row in rows} == {"GLD", "SLV"}
    assert all(row["quote_status"] == "UNAVAILABLE" for row in rows)
    assert all(row["normalized_status"] == "SAFE_UNAVAILABLE" for row in rows)
    assert all(row["operator_next_step"] == "review_real_marketdata_connection" for row in rows)
    assert set(_read_rows(tmp_path / "operator_real_quote_normalization.csv")[0]) == set(NORMALIZATION_FIELDS)


def test_normalization_uses_available_symbol_quote_fields(tmp_path: Path):
    latest, daily, decision = _write_chain_sources(tmp_path, connection="true", request="true", snapshots="2")
    latest.write_text(
        "symbol,last_price,bid,ask,close,quote_time\n"
        "GLD,200.25,200.20,200.30,199.90,2026-05-25T00:00:00+00:00\n"
        "SLV,31.50,31.49,31.52,31.20,2026-05-25T00:00:00+00:00\n",
        encoding="utf-8",
    )

    rows = generate_normalization(
        latest_csv=latest,
        daily_summary_csv=daily,
        decision_gate_csv=decision,
        output_csv=tmp_path / "quotes.csv",
        output_report=tmp_path / "quotes.md",
    )

    by_symbol = {row["symbol"]: row for row in rows}
    assert by_symbol["GLD"]["quote_status"] == "AVAILABLE"
    assert by_symbol["GLD"]["normalized_status"] == "NORMALIZED"
    assert by_symbol["SLV"]["last_price"] == "31.50"


def test_normalization_wrapper_does_not_read_local_config_or_api_error_log(tmp_path: Path):
    latest, daily, decision = _write_chain_sources(tmp_path)
    (tmp_path / "config.yaml").write_text("must_not_be_read: true\n", encoding="utf-8")
    (tmp_path / "ibkr_market_data_api_errors.csv").write_text("must_not_be_read\n", encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", str(REPO_ROOT / ".venv/bin/python"))
    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--latest-csv",
            str(latest),
            "--daily-summary-csv",
            str(daily),
            "--decision-gate-csv",
            str(decision),
            "--output-csv",
            str(tmp_path / "quotes.csv"),
            "--output-report",
            str(tmp_path / "quotes.md"),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert _read_rows(tmp_path / "quotes.csv")[0]["normalized_status"] == "SAFE_UNAVAILABLE"
