from pathlib import Path
import csv
import subprocess

from src.upstream_factors import ManualUpstreamFactorProvider, build_upstream_factor_snapshot


def test_manual_provider_generates_five_factor_rows():
    rows = build_upstream_factor_snapshot(
        tz_cfg={"jst": "Asia/Tokyo", "et": "America/New_York"},
        provider=ManualUpstreamFactorProvider(),
    )
    assert len(rows) == 5
    factors = {r.factor for r in rows}
    assert factors == {"XAUUSD", "XAGUSD", "USDJPY", "USDCNY", "SGE_AU99_99"}


def test_unavailable_factor_does_not_fail():
    rows = build_upstream_factor_snapshot(
        tz_cfg={"jst": "Asia/Tokyo", "et": "America/New_York"},
        provider=ManualUpstreamFactorProvider(),
    )
    sge = [r for r in rows if r.factor == "SGE_AU99_99"][0]
    assert sge.source_status == "unavailable"
    assert sge.value == "unavailable"


def test_upstream_factors_cli_outputs_files_with_expected_columns():
    subprocess.run(["python3", "main.py", "--config", "config.yaml", "--upstream-factors"], check=True)
    csv_path = Path("upstream_factor_snapshot.csv")
    md_path = Path("reports/upstream_factor_report.md")
    assert csv_path.exists()
    assert md_path.exists()

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 5
    required = {"factor", "value", "currency", "unit", "source", "source_status", "timestamp_jst", "timestamp_et", "warning_flags", "notes"}
    assert required.issubset(set(rows[0].keys()))


def test_no_new_trading_keywords_in_upstream_module():
    text = Path("src/upstream_factors.py").read_text(encoding="utf-8")
    banned = ["placeOrder", "cancelOrder", "reqOpenOrders", "bracketOrder", "whatIfOrder", "Order(", "reqHistoricalData"]
    for token in banned:
        assert token not in text
