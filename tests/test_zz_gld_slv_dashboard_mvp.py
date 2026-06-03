from __future__ import annotations

import os
import subprocess
from pathlib import Path

from src.gld_slv_dashboard_mvp import generate_dashboard_mvp


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "gld_slv_dashboard_mvp.sh"


def _write_research_log(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "date_jst,market,symbol,strategy,price,source,data_delay_flag,signal,action_rating,entry_zone,exit_zone,stop_loss,invalidation_level,time_trigger,event_trigger,risk_pct,position_unit_note,cash_account_note,overnight_allowed,review_required,confidence,action_allowed,result,notes\n"
        "2026-06-03,US,GLD,GLD 无有效报价等待,,test_source,no_price,不交易，等待有效报价,NO_TRADE,等待有效报价,等待有效报价,等待有效报价,等待有效报价,1-5个交易日复核,event,0,unit,cash,false,true,low,false,不交易，等待有效报价,no quote\n"
        "2026-06-03,US,SLV,SLV 延迟报价低置信观察,27.25,test_source,delayed,仅观察或低置信计划,WATCH,26.84-27.20,27.93-28.75,26.30-26.30,26.11-26.11,1-5个交易日复核,event,0.25,unit,cash,false,true,low,true,降级为观察/低置信计划,delayed quote\n",
        encoding="utf-8",
    )


def test_dashboard_mvp_contains_gld_slv_strategy_and_risk_fields(tmp_path: Path):
    csv_path = tmp_path / "logs/research_log_US.csv"
    _write_research_log(csv_path)
    output = tmp_path / "dashboard/index.html"

    generate_dashboard_mvp(csv_path=csv_path, report_path=tmp_path / "missing.md", output_html=output)

    html = output.read_text(encoding="utf-8")
    for text in (
        "GLD/SLV Research Dashboard",
        "GLD",
        "SLV",
        "action_rating",
        "data_delay_flag",
        "no_price",
        "delayed",
        "frozen",
        "source_conflict",
        "stop_loss",
        "invalidation_level",
    ):
        assert text in html


def test_dashboard_mvp_contains_us_30m_echo_jst_and_cash_account_copy(tmp_path: Path):
    csv_path = tmp_path / "logs/research_log_US.csv"
    _write_research_log(csv_path)
    output = tmp_path / "dashboard/index.html"

    generate_dashboard_mvp(csv_path=csv_path, report_path=tmp_path / "missing.md", output_html=output)

    html = output.read_text(encoding="utf-8")
    for text in (
        "10:00 ET",
        "14:30 ET",
        "15:10 ET",
        "15:50 ET",
        "JST",
        "IBKR cash account only",
        "settled cash only",
        "GFV / freeriding",
        "research only, no automatic trading",
        "一致性对账单",
        "风险与退出触发",
        "数据质量说明",
    ):
        assert text in html


def test_dashboard_mvp_wrapper_generates_repo_dashboard(tmp_path: Path):
    csv_path = tmp_path / "logs/research_log_US.csv"
    _write_research_log(csv_path)
    output = tmp_path / "dashboard/index.html"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHON"] = os.environ.get("PYTHON", "python3")

    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--csv-path",
            str(csv_path),
            "--report-path",
            str(tmp_path / "missing.md"),
            "--output-html",
            str(output),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "GLD/SLV Research Dashboard" in output.read_text(encoding="utf-8")


def test_batch3_dashboard_files_omit_automatic_trading_api_names():
    files = [
        REPO_ROOT / "dashboard/index.html",
        REPO_ROOT / "dashboard/assets/style.css",
        REPO_ROOT / "src/gld_slv_dashboard_mvp.py",
        REPO_ROOT / "scripts/gld_slv_dashboard_mvp.sh",
    ]
    forbidden = ["place" + "Order", "cancel" + "Order", "what" + "If" + "Order"]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert not any(term in text for term in forbidden), path
