from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from src.operator_dashboard_ui_enhancement_pack import (
    DASHBOARD_CSS,
    DASHBOARD_INDEX,
    DASHBOARD_SNAPSHOT,
    STATUS,
    build_status_snapshot,
    generate_dashboard_ui_enhancement_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_builder_generates_all_target_artifacts(tmp_path: Path) -> None:
    row = generate_dashboard_ui_enhancement_pack(
        output_index=tmp_path / DASHBOARD_INDEX,
        output_css=tmp_path / DASHBOARD_CSS,
        output_snapshot=tmp_path / DASHBOARD_SNAPSHOT,
        output_csv=tmp_path / "operator_dashboard_ui_enhancement_pack.csv",
        output_report=tmp_path / "reports/operator_dashboard_ui_enhancement_pack_report.md",
        output_pack=tmp_path / "Precious_Metals_Monitor_Dashboard_UI_Enhancement_Pack.md",
        generated_at="2026-05-31T00:00:00+00:00",
    )

    for relative_path in (
        DASHBOARD_INDEX,
        DASHBOARD_CSS,
        DASHBOARD_SNAPSHOT,
        "operator_dashboard_ui_enhancement_pack.csv",
        "reports/operator_dashboard_ui_enhancement_pack_report.md",
        "Precious_Metals_Monitor_Dashboard_UI_Enhancement_Pack.md",
    ):
        assert (tmp_path / relative_path).exists()
    assert row["status"] == STATUS


def test_index_uses_local_css_and_no_external_references(tmp_path: Path) -> None:
    generate_dashboard_ui_enhancement_pack(
        output_index=tmp_path / DASHBOARD_INDEX,
        output_css=tmp_path / DASHBOARD_CSS,
        output_snapshot=tmp_path / DASHBOARD_SNAPSHOT,
        output_csv=tmp_path / "operator_dashboard_ui_enhancement_pack.csv",
        output_report=tmp_path / "reports/operator_dashboard_ui_enhancement_pack_report.md",
        output_pack=tmp_path / "Precious_Metals_Monitor_Dashboard_UI_Enhancement_Pack.md",
        generated_at="2026-05-31T00:00:00+00:00",
    )

    html = (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8")
    css = (tmp_path / DASHBOARD_CSS).read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="assets/style.css">' in html
    assert "AI Research Console / Precious Metals Monitor" in html
    assert "MARKET_DATA_BLOCKED_BY_SUBSCRIPTION" in html
    assert "ready for live trading" not in html.lower()
    assert "production ready" not in html.lower()
    assert "realtime ready" not in html.lower()
    combined = html + css
    for marker in ("http://", "https://", "cdn", "script src", "@import"):
        assert marker not in combined.lower()


def test_status_snapshot_preserves_blocked_market_data_and_disabled_flags() -> None:
    snapshot = build_status_snapshot(generated_at="2026-05-31T00:00:00+00:00")
    assert snapshot["status"] == "DASHBOARD_UI_ENHANCEMENT_READY"
    assert snapshot["market_data_status"] == "BLOCKED_BY_SUBSCRIPTION"
    assert snapshot["market_data_classification"] == "MARKET_DATA_BLOCKED_BY_SUBSCRIPTION"
    assert snapshot["realtime_market_data_verified"] == "NO"
    assert snapshot["trading_enabled"] == "NO"
    assert snapshot["account_read_enabled"] == "NO"
    assert snapshot["positions_read_enabled"] == "NO"
    assert snapshot["telegram_real_send_enabled"] == "NO"
    assert snapshot["historical_data_enabled"] == "NO"
    assert snapshot["ibkr_error_code"] == "10089"
    assert snapshot["symbols"] == ["GLD", "SLV"]


def test_cli_generates_static_pack_without_external_actions(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "main.py"), "--dashboard-ui-enhancement-pack"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert "status=DASHBOARD_UI_ENHANCEMENT_READY" in result.stdout
    assert "market_data_status=BLOCKED_BY_SUBSCRIPTION" in result.stdout
    assert "realtime_market_data_verified=NO" in result.stdout
    assert "trading_enabled=NO" in result.stdout
    assert "account_read_enabled=NO" in result.stdout
    assert "positions_read_enabled=NO" in result.stdout
    assert "historical_data_enabled=NO" in result.stdout
    assert "telegram_real_send_enabled=NO" in result.stdout

    snapshot_path = tmp_path / DASHBOARD_SNAPSHOT
    assert snapshot_path.exists()
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert snapshot["status"] == "DASHBOARD_UI_ENHANCEMENT_READY"
    assert snapshot["external_effect"] == "NONE_LOCAL_ARTIFACT_GENERATION_ONLY"

    combined = "\n".join(
        [
            result.stdout,
            (tmp_path / DASHBOARD_INDEX).read_text(encoding="utf-8"),
            (tmp_path / DASHBOARD_CSS).read_text(encoding="utf-8"),
            snapshot_path.read_text(encoding="utf-8"),
        ]
    )
    for forbidden in (
        "ibkr_connected=YES",
        "market_data_request=YES",
        "historical_data_request=YES",
        "account_read_enabled=YES",
        "positions_read_enabled=YES",
        "telegram_real_send_enabled=YES",
        "trading_enabled=YES",
        "contract_qualification=YES",
    ):
        assert forbidden not in combined
