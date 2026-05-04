from pathlib import Path
import csv
import subprocess


def test_mock_run_generates_outputs():
    subprocess.run(["python3", "main.py", "--config", "config.yaml", "--watchlist", "watchlist.yaml", "--mock"], check=True)
    assert Path("precious_metals_signal_log.csv").exists()
    assert Path("reports/latest_report.md").exists()


def test_all_symbols_have_data_status():
    with open("precious_metals_signal_log.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows
    for row in rows:
        assert row["symbol"]
        assert row["data_status"] in {"real_time", "delayed", "inferred", "unavailable"}


def test_no_trading_api_strings_present():
    targets = [Path("src/monitor.py"), Path("main.py"), Path("README.md"), Path("config.yaml"), Path("watchlist.yaml")]
    content = "\n".join(p.read_text(encoding="utf-8") for p in targets)
    banned = ["placeOrder", "cancelOrder", "reqOpenOrders", "bracketOrder", "whatIfOrder"]
    for token in banned:
        assert token not in content


def test_calibration_csv_generates_outputs():
    subprocess.run(["python3", "main.py", "--config", "config.yaml", "--calibration-csv", "data/historical_calibration_sample.csv"], check=True)
    assert Path("conversion_factor_calibration_log.csv").exists()
    assert Path("reports/conversion_factor_calibration_report.md").exists()
