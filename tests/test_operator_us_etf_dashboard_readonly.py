from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_us_etf_dashboard_readonly import (
    CSV_FIELDS,
    DASHBOARD_ID,
    MARKET_DATA_CLASSIFICATION,
    MARKET_DATA_STATUS,
    build_us_etf_dashboard_readonly_rows,
    generate_us_etf_dashboard_readonly,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_source_csv(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "phase,packet_id,symbol,asset_class,contract_qualification_status,connectivity_status,market_data_status,market_data_classification,subscription_required,delayed_available,realtime_market_data_verified,operator_action,dashboard_ready,telegram_ready,jp_status,cn_status,external_effect,evidence,recommendation,timestamp_utc",
                "Phase 581-588,US_ETF_OPERATOR_PACKET_ARTIFACT_INTEGRATION,GLD,US_ETF,GLD_SLV_QUALIFIED,VERIFIED_CONNECT_DISCONNECT,BLOCKED_BY_SUBSCRIPTION,MARKET_DATA_BLOCKED_BY_SUBSCRIPTION,YES,YES,NO,ARCHIVE_PACKET_AND_USE_READONLY_DASHBOARD_ARTIFACT_ONLY,YES,YES,FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION,FROZEN_PENDING_DATA_SOURCE_DECISION,NONE_LOCAL_ARTIFACT_GENERATION_ONLY,GLD_ibkr_api_error_captured; IBKR_10089_MARKET_DATA_SUBSCRIPTION_REQUIRED_DELAYED_AVAILABLE,Keep blocked,2026-05-31T00:00:00+00:00",
                "Phase 581-588,US_ETF_OPERATOR_PACKET_ARTIFACT_INTEGRATION,SLV,US_ETF,GLD_SLV_QUALIFIED,VERIFIED_CONNECT_DISCONNECT,BLOCKED_BY_SUBSCRIPTION,MARKET_DATA_BLOCKED_BY_SUBSCRIPTION,YES,YES,NO,ARCHIVE_PACKET_AND_USE_READONLY_DASHBOARD_ARTIFACT_ONLY,YES,YES,FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION,FROZEN_PENDING_DATA_SOURCE_DECISION,NONE_LOCAL_ARTIFACT_GENERATION_ONLY,SLV_ibkr_api_error_captured; IBKR_10089_MARKET_DATA_SUBSCRIPTION_REQUIRED_DELAYED_AVAILABLE,Keep blocked,2026-05-31T00:00:00+00:00",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_dashboard_rows_keep_us_etf_blocked_state_readonly(tmp_path: Path) -> None:
    source = tmp_path / "operator_us_etf_operator_packet_artifact_integration.csv"
    _write_source_csv(source)
    rows = build_us_etf_dashboard_readonly_rows(
        source_csv=source,
        generated_at="2026-05-31T00:00:00+00:00",
    )
    assert [row["symbol"] for row in rows] == ["GLD", "SLV"]
    assert all(row["dashboard_id"] == DASHBOARD_ID for row in rows)
    assert all(row["connectivity_status"] == "VERIFIED_CONNECT_DISCONNECT" for row in rows)
    assert all(row["contract_qualification_status"] == "GLD_SLV_QUALIFIED" for row in rows)
    assert all(row["market_data_status"] == MARKET_DATA_STATUS for row in rows)
    assert all(row["market_data_classification"] == MARKET_DATA_CLASSIFICATION for row in rows)
    assert all(row["subscription_required"] == "YES" for row in rows)
    assert all(row["delayed_available"] == "YES" for row in rows)
    assert all(row["realtime_market_data_verified"] == "NO" for row in rows)
    assert all(row["operator_review_required"] == "YES" for row in rows)
    assert all(row["operator_action"] == "SUBSCRIBE_NETWORK_B_OR_CONTINUE_FRAMEWORK_ONLY_MVP" for row in rows)
    assert all(row["dashboard_ready"] == "YES" for row in rows)
    assert all(row["jp_status"] == "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION" for row in rows)
    assert all(row["cn_status"] == "FROZEN_PENDING_DATA_SOURCE_DECISION" for row in rows)


def test_generate_writes_csv_report_and_static_html(tmp_path: Path) -> None:
    source = tmp_path / "operator_us_etf_operator_packet_artifact_integration.csv"
    output_csv = tmp_path / "operator_us_etf_dashboard_readonly.csv"
    output_report = tmp_path / "reports/operator_us_etf_dashboard_readonly_report.md"
    output_html = tmp_path / "dashboard/us_etf_dashboard_readonly.html"
    _write_source_csv(source)
    rows = generate_us_etf_dashboard_readonly(
        source_csv=source,
        output_csv=output_csv,
        output_report=output_report,
        output_html=output_html,
        generated_at="2026-05-31T00:00:00+00:00",
    )
    assert rows == _read_rows(output_csv)
    assert set(rows[0]) == set(CSV_FIELDS)
    report = output_report.read_text(encoding="utf-8")
    for section in (
        "# Phase 589-600 US ETF Dashboard Readonly",
        "## Final Dashboard Status",
        "## Scope Boundary",
        "## Dashboard Artifacts",
        "## GLD / SLV Panels",
        "## Market Data Blocked Panel",
        "## JP / CN Frozen Panel",
        "## Operator Review Workflow",
        "## Explicitly Prohibited Actions",
        "## Artifact Summary",
        "## Residual Risks",
        "## Next Phase Preconditions",
    ):
        assert section in report
    html = output_html.read_text(encoding="utf-8")
    assert "GLD" in html
    assert "SLV" in html
    assert "market data blocked by subscription" in html
    assert "IBKR 10089" in html
    assert "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION" in html
    assert "FROZEN_PENDING_DATA_SOURCE_DECISION" in html
    assert "SUBSCRIBE_NETWORK_B_OR_CONTINUE_FRAMEWORK_ONLY_MVP" in html
    assert "no trading" in html
    assert "no account reads" in html
    assert "no positions reads" in html
    assert "http://" not in html
    assert "https://" not in html


def test_main_cli_outputs_required_dashboard_summary(tmp_path: Path) -> None:
    _write_source_csv(tmp_path / "operator_us_etf_operator_packet_artifact_integration.csv")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--us-etf-dashboard-readonly"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0
    assert "[US_ETF_DASHBOARD_READONLY] generated" in result.stdout
    assert "dashboard_status=US_ETF_DASHBOARD_READONLY_READY" in result.stdout
    assert "dashboard_mode=READ_ONLY_ARTIFACT_VIEWER" in result.stdout
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
    assert "operator_review_required=YES" in result.stdout
    assert "dashboard_artifact_ready=YES" in result.stdout
    assert "trading_enabled=NO" in result.stdout
    assert "account_read_enabled=NO" in result.stdout
    assert "positions_read_enabled=NO" in result.stdout
    assert "telegram_real_send_enabled=NO" in result.stdout
    assert "next_phase_telegram_skeleton_candidate=YES" in result.stdout
    assert "market_data_verified=YES" not in result.stdout
    assert "realtime_market_data_verified=YES" not in result.stdout
    assert "trading_enabled=YES" not in result.stdout
    assert "production_ready=YES" not in result.stdout
    assert "account_read_enabled=YES" not in result.stdout
    assert "positions_read_enabled=YES" not in result.stdout
    assert "telegram_real_send_enabled=YES" not in result.stdout
