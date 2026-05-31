from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_us_etf_market_data_classifier_readiness import (
    CLASSIFICATION,
    CSV_FIELDS,
    READINESS_STATUS,
    build_us_etf_market_data_classifier_readiness_rows,
    generate_us_etf_market_data_classifier_readiness,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_source_csv(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "phase,symbol,market_data_status,error_type,bid_present,ask_present,last_present,close_present,error_message_redacted,evidence",
                "Phase 569-572,GLD,PERMISSION_DENIED,PERMISSION_DENIED,NO,NO,NO,NO,IBKR_10089_MARKET_DATA_SUBSCRIPTION_REQUIRED_DELAYED_AVAILABLE,GLD_ibkr_api_error_captured",
                "Phase 569-572,SLV,PERMISSION_DENIED,PERMISSION_DENIED,NO,NO,NO,NO,IBKR_10089_MARKET_DATA_SUBSCRIPTION_REQUIRED_DELAYED_AVAILABLE,SLV_ibkr_api_error_captured",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_classifier_rows_preserve_permission_denied_without_ready_claim(tmp_path: Path) -> None:
    source = tmp_path / "operator_us_etf_market_data_execute.csv"
    _write_source_csv(source)
    rows = build_us_etf_market_data_classifier_readiness_rows(
        source_csv=source,
        generated_at="2026-05-31T00:00:00+00:00",
    )
    assert [row["symbol"] for row in rows] == ["GLD", "SLV"]
    assert all(row["market_data_status"] == "PERMISSION_DENIED" for row in rows)
    assert all(row["error_type"] == "IBKR_ERROR_10089" for row in rows)
    assert all(row["ibkr_error_code"] == "10089" for row in rows)
    assert all(row["subscription_required"] == "YES" for row in rows)
    assert all(row["delayed_available"] == "YES" for row in rows)
    assert all(row["realtime_market_data_verified"] == "NO" for row in rows)
    assert all(row["market_data_request_tested"] == "YES" for row in rows)
    assert all(row["classification"] == CLASSIFICATION for row in rows)
    assert all(row["readiness_status"] == READINESS_STATUS for row in rows)
    assert all("production-ready" not in row["recommendation"] for row in rows)


def test_generate_writes_csv_and_required_report_sections(tmp_path: Path) -> None:
    source = tmp_path / "operator_us_etf_market_data_execute.csv"
    output_csv = tmp_path / "operator_us_etf_market_data_classifier_readiness.csv"
    output_report = tmp_path / "reports/operator_us_etf_market_data_classifier_readiness_report.md"
    _write_source_csv(source)
    rows = generate_us_etf_market_data_classifier_readiness(
        source_csv=source,
        output_csv=output_csv,
        output_report=output_report,
        generated_at="2026-05-31T00:00:00+00:00",
    )
    csv_rows = _read_rows(output_csv)
    assert rows == csv_rows
    assert set(csv_rows[0]) == set(CSV_FIELDS)
    report = output_report.read_text(encoding="utf-8")
    for section in (
        "# Phase 573-580 US ETF Market Data Classifier Readiness",
        "## Final Readiness Status",
        "## Scope Boundary",
        "## Source Market Data Result",
        "## Permission Denied Classification",
        "## Delayed Data Policy",
        "## US ETF Readiness Summary",
        "## JP / CN Frozen Status",
        "## Explicitly Prohibited Actions",
        "## Artifact Summary",
        "## Residual Risks",
        "## Next Phase Preconditions",
    ):
        assert section in report
    for classification in (
        "PERMISSION_DENIED",
        "IBKR_ERROR_10089",
        "SUBSCRIPTION_REQUIRED",
        "DELAYED_AVAILABLE",
        "REALTIME_NOT_VERIFIED",
        "MARKET_DATA_BLOCKED_BY_SUBSCRIPTION",
        "CONNECTIVITY_AND_CONTRACTS_VERIFIED_ONLY",
    ):
        assert classification in report
    assert "realtime_market_data_verified=YES" not in report
    assert "trading_enabled=YES" not in report
    assert "production_ready=YES" not in report


def test_main_cli_outputs_required_summary(tmp_path: Path) -> None:
    _write_source_csv(tmp_path / "operator_us_etf_market_data_execute.csv")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--us-etf-market-data-classifier-readiness"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0
    assert "[US_ETF_MARKET_DATA_CLASSIFIER_READINESS] generated" in result.stdout
    assert "market_data_classifier_status=US_ETF_MARKET_DATA_CLASSIFIER_READINESS_READY" in result.stdout
    assert "source_phase=Phase 569-572" in result.stdout
    assert "symbols=GLD,SLV" in result.stdout
    assert "GLD_market_data_status=PERMISSION_DENIED" in result.stdout
    assert "SLV_market_data_status=PERMISSION_DENIED" in result.stdout
    assert "ibkr_error_code=10089" in result.stdout
    assert "subscription_required=YES" in result.stdout
    assert "delayed_available=YES" in result.stdout
    assert "realtime_market_data_verified=NO" in result.stdout
    assert "market_data_request_tested=YES" in result.stdout
    assert f"classification={CLASSIFICATION}" in result.stdout
    assert f"us_etf_readiness_status={READINESS_STATUS}" in result.stdout
    assert "market_data_verified=YES" not in result.stdout
    assert "realtime_market_data_verified=YES" not in result.stdout
    assert "trading_enabled=YES" not in result.stdout
    assert "production_ready=YES" not in result.stdout
