from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.operator_manual_csv_public_data_pilot_pack import STATUS, build_status_snapshot


REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SIGNAL_TERMS = (
    "BUY",
    "SELL",
    "HOLD",
    "买入",
    "卖出",
    "持有",
    "target_price",
    "stop_loss",
    "take_profit",
    "目标价",
    "止损",
    "止盈",
)


def test_manual_csv_public_data_pilot_pack_cli_succeeds() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "main.py"), "--manual-csv-public-data-pilot-pack"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert STATUS in result.stdout
    assert "public_data_auto_fetch_enabled=NO" in result.stdout


def test_manual_csv_import_preview_cli_succeeds() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "main.py"), "--manual-csv-import-preview"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "status=MANUAL_CSV_IMPORT_PREVIEW_READY" in result.stdout
    assert "store_written=NO" in result.stdout


def test_public_data_pilot_dry_run_cli_succeeds() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "main.py"), "--public-data-pilot-dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "status=PUBLIC_DATA_PILOT_DRY_RUN_READY" in result.stdout
    assert "public_data_auto_fetch_enabled=NO" in result.stdout


def test_public_data_pilot_fetch_without_allow_does_not_network() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "main.py"), "--public-data-pilot-fetch"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "PUBLIC_DATA_PILOT_FETCH_DISABLED" in result.stdout
    assert "network_request_made=NO" in result.stdout


def test_snapshots_contain_registry_and_status_contract() -> None:
    status = json.loads((REPO_ROOT / "dashboard/data/status_snapshot.json").read_text(encoding="utf-8"))
    registry = json.loads((REPO_ROOT / "dashboard/data/public_data_source_registry_snapshot.json").read_text(encoding="utf-8"))
    pilot = json.loads((REPO_ROOT / "dashboard/data/public_data_pilot_snapshot.json").read_text(encoding="utf-8"))

    assert status["status"] == STATUS
    assert build_status_snapshot(status["generated_at_utc"])["status"] == STATUS
    assert status["ui_final_locked"] == "YES"
    assert status["public_data_auto_fetch_enabled"] == "NO"
    assert status["public_data_fetch_requires_explicit_allow"] == "YES"
    assert {item["source_name"] for item in registry["candidates"]} == {"Stooq", "Alpha Vantage", "Yahoo Finance"}
    assert pilot["default_network_behavior"] == "DISABLED"


def test_dashboard_keeps_final_nav_and_adds_data_status_fields() -> None:
    html = (REPO_ROOT / "dashboard/index.html").read_text(encoding="utf-8")

    for text in ("总览", "标的观察", "数据源", "本地报告", "风险边界", "设置", "数据来源", "最近更新时间", "待导入"):
        assert text in html
    assert "下一步操作" not in html


def test_phase_outputs_omit_trading_signal_terms() -> None:
    paths = [
        REPO_ROOT / "dashboard/index.html",
        REPO_ROOT / "dashboard/data/manual_csv_import_snapshot.json",
        REPO_ROOT / "dashboard/data/public_data_pilot_snapshot.json",
        REPO_ROOT / "dashboard/data/public_data_source_registry_snapshot.json",
        REPO_ROOT / "dashboard/data/market_data_validation_snapshot.json",
        REPO_ROOT / "dashboard/data/local_market_data_store_snapshot.json",
        REPO_ROOT / "dashboard/data/gld_slv_data_status_snapshot.json",
        REPO_ROOT / "dashboard/data/data_driven_research_framework_snapshot.json",
        REPO_ROOT / "reports/operator_manual_csv_public_data_pilot_pack_report.md",
        REPO_ROOT / "reports/manual_csv_market_data_user_guide.md",
        REPO_ROOT / "reports/public_data_pilot_report.md",
        REPO_ROOT / "reports/data_driven_research_framework_GLD_SLV.md",
        REPO_ROOT / "Precious_Metals_Monitor_Manual_CSV_Public_Data_Pilot_Pack.md",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)

    for term in FORBIDDEN_SIGNAL_TERMS:
        assert term not in combined
