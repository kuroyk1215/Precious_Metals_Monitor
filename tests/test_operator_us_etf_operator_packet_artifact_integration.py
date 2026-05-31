from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_us_etf_operator_packet_artifact_integration import (
    CSV_FIELDS,
    MARKET_DATA_CLASSIFICATION,
    MARKET_DATA_STATUS,
    PACKET_ID,
    build_us_etf_operator_packet_artifact_integration_rows,
    generate_us_etf_operator_packet_artifact_integration,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_source_csv(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "phase,symbol,market_data_status,error_type,ibkr_error_code,subscription_required,delayed_available,realtime_market_data_verified,classification,jp_status,cn_status,evidence",
                "Phase 573-580,GLD,PERMISSION_DENIED,IBKR_ERROR_10089,10089,YES,YES,NO,MARKET_DATA_BLOCKED_BY_SUBSCRIPTION,FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION,FROZEN_PENDING_DATA_SOURCE_DECISION,GLD_ibkr_api_error_captured",
                "Phase 573-580,SLV,PERMISSION_DENIED,IBKR_ERROR_10089,10089,YES,YES,NO,MARKET_DATA_BLOCKED_BY_SUBSCRIPTION,FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION,FROZEN_PENDING_DATA_SOURCE_DECISION,SLV_ibkr_api_error_captured",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_packet_rows_integrate_blocked_us_etf_state_without_ready_claim(tmp_path: Path) -> None:
    source = tmp_path / "operator_us_etf_market_data_classifier_readiness.csv"
    _write_source_csv(source)
    rows = build_us_etf_operator_packet_artifact_integration_rows(
        source_csv=source,
        generated_at="2026-05-31T00:00:00+00:00",
    )
    assert [row["symbol"] for row in rows] == ["GLD", "SLV"]
    assert all(row["packet_id"] == PACKET_ID for row in rows)
    assert all(row["asset_class"] == "US_ETF" for row in rows)
    assert all(row["contract_qualification_status"] == "GLD_SLV_QUALIFIED" for row in rows)
    assert all(row["connectivity_status"] == "VERIFIED_CONNECT_DISCONNECT" for row in rows)
    assert all(row["market_data_status"] == MARKET_DATA_STATUS for row in rows)
    assert all(row["market_data_classification"] == MARKET_DATA_CLASSIFICATION for row in rows)
    assert all(row["subscription_required"] == "YES" for row in rows)
    assert all(row["delayed_available"] == "YES" for row in rows)
    assert all(row["realtime_market_data_verified"] == "NO" for row in rows)
    assert all(row["dashboard_ready"] == "YES" for row in rows)
    assert all(row["telegram_ready"] == "YES" for row in rows)
    assert all(row["jp_status"] == "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION" for row in rows)
    assert all(row["cn_status"] == "FROZEN_PENDING_DATA_SOURCE_DECISION" for row in rows)
    assert all("production-ready" not in row["recommendation"] for row in rows)


def test_generate_writes_csv_and_required_report_sections(tmp_path: Path) -> None:
    source = tmp_path / "operator_us_etf_market_data_classifier_readiness.csv"
    output_csv = tmp_path / "operator_us_etf_operator_packet_artifact_integration.csv"
    output_report = tmp_path / "reports/operator_us_etf_operator_packet_artifact_integration_report.md"
    _write_source_csv(source)
    rows = generate_us_etf_operator_packet_artifact_integration(
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
        "# Phase 581-588 US ETF Operator Packet Artifact Integration",
        "## Final Packet Status",
        "## Scope Boundary",
        "## US ETF Status Summary",
        "## GLD / SLV Operator Packet",
        "## Market Data Blocked Classification",
        "## JP / CN Frozen Status",
        "## Dashboard Readiness",
        "## Telegram Readiness",
        "## Explicitly Prohibited Actions",
        "## Artifact Summary",
        "## Residual Risks",
        "## Next Phase Preconditions",
    ):
        assert section in report
    assert "PERMISSION_DENIED / IBKR_ERROR_10089 / SUBSCRIPTION_REQUIRED / DELAYED_AVAILABLE" in report
    assert "realtime_market_data_verified=YES" not in report
    assert "market_data_verified=YES" not in report
    assert "trading_enabled=YES" not in report
    assert "production_ready=YES" not in report
    assert "telegram_real_send_enabled=YES" not in report


def test_main_cli_outputs_required_summary(tmp_path: Path) -> None:
    _write_source_csv(tmp_path / "operator_us_etf_market_data_classifier_readiness.csv")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--us-etf-operator-packet-artifact-integration"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0
    assert "[US_ETF_OPERATOR_PACKET_ARTIFACT_INTEGRATION] generated" in result.stdout
    assert "operator_packet_status=US_ETF_OPERATOR_PACKET_ARTIFACT_INTEGRATION_READY" in result.stdout
    assert "symbols=GLD,SLV" in result.stdout
    assert "connectivity_status=VERIFIED_CONNECT_DISCONNECT" in result.stdout
    assert "contract_qualification_status=GLD_SLV_QUALIFIED" in result.stdout
    assert "market_data_status=BLOCKED_BY_SUBSCRIPTION" in result.stdout
    assert "market_data_classification=MARKET_DATA_BLOCKED_BY_SUBSCRIPTION" in result.stdout
    assert "ibkr_error_code=10089" in result.stdout
    assert "subscription_required=YES" in result.stdout
    assert "delayed_available=YES" in result.stdout
    assert "realtime_market_data_verified=NO" in result.stdout
    assert "jp_status=FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION" in result.stdout
    assert "cn_status=FROZEN_PENDING_DATA_SOURCE_DECISION" in result.stdout
    assert "dashboard_artifact_ready=YES" in result.stdout
    assert "telegram_artifact_ready=YES" in result.stdout
    assert "next_phase_dashboard_readonly_candidate=YES" in result.stdout
    assert "market_data_verified=YES" not in result.stdout
    assert "realtime_market_data_verified=YES" not in result.stdout
    assert "trading_enabled=YES" not in result.stdout
    assert "production_ready=YES" not in result.stdout
    assert "telegram_real_send_enabled=YES" not in result.stdout
