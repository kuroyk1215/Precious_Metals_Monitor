from pathlib import Path

from src.ibkr_historical_adapter import (
    build_ibkr_historical_fetch_config,
    validate_ibkr_historical_fetch_config,
    convert_ibkr_bars_to_raw_rows,
    write_ibkr_raw_prices_csv,
)
from src.ibkr_historical_fetcher import fetch_ibkr_historical_bars_readonly


def test_dry_run_default_not_executed() -> None:
    config = build_ibkr_historical_fetch_config()
    results = fetch_ibkr_historical_bars_readonly(config)
    assert all(r.fetch_status == "dry_run_not_executed" for r in results)


def test_execute_false_status() -> None:
    config = build_ibkr_historical_fetch_config(execute=False)
    results = fetch_ibkr_historical_bars_readonly(config)
    assert results[0].fetch_status == "dry_run_not_executed"


def test_execute_without_explicit_confirmation_invalid() -> None:
    config = build_ibkr_historical_fetch_config(execute=True)
    config["explicit_user_confirmed"] = False
    validated = validate_ibkr_historical_fetch_config(config)
    assert validated["validation_status"] == "invalid"


def test_execute_missing_client() -> None:
    config = build_ibkr_historical_fetch_config(execute=True)
    results = fetch_ibkr_historical_bars_readonly(config, ibkr_client=None)
    assert results[0].fetch_status in {"missing_ibkr_client", "adapter_not_implemented"}


def test_only_support_target_symbols() -> None:
    config = build_ibkr_historical_fetch_config(symbols=["9999.T"])
    validated = validate_ibkr_historical_fetch_config(config)
    assert validated["validation_status"] == "invalid"


def test_convert_bars_to_raw_rows() -> None:
    rows = convert_ibkr_bars_to_raw_rows("1540.T", "JPY", [{"date": "2026-01-02", "close": 123.4}])
    assert rows[0]["source"] == "ibkr_historical_bars"
    assert set(rows[0].keys()) == {"date", "symbol", "close", "currency", "source", "notes"}


def test_empty_bars_to_empty_rows() -> None:
    assert convert_ibkr_bars_to_raw_rows("1540.T", "JPY", []) == []


def test_write_raw_csv_header(tmp_path: Path) -> None:
    p = tmp_path / "candidate.csv"
    write_ibkr_raw_prices_csv([], str(p))
    assert p.read_text(encoding="utf-8").splitlines()[0] == "date,symbol,close,currency,source,notes"


def test_no_trade_keywords_in_entrypoints() -> None:
    banned = ["placeOrder", "cancelOrder", "reqOpenOrders", "bracketOrder", "whatIfOrder", "exerciseOptions", "Order(", "自动买入", "自动卖出", "自动调仓", "自动撤单"]
    for file_path in ["main.py", "src/monitor.py", "src/ibkr_historical_fetcher.py"]:
        text = Path(file_path).read_text(encoding="utf-8")
        for token in banned:
            assert token not in text


def test_dry_run_path_no_reqhistoricaldata_call() -> None:
    text = Path("src/ibkr_historical_fetcher.py").read_text(encoding="utf-8")
    assert "dry_run_not_executed" in text


def test_ibkr_data_client_not_modified() -> None:
    text = Path("src/ibkr_data_client.py").read_text(encoding="utf-8")
    assert "class IBKRDataClient" in text
