from pathlib import Path

from src.ibkr_historical_adapter import (
    build_ibkr_historical_fetch_config,
    validate_ibkr_historical_fetch_config,
    convert_ibkr_bars_to_raw_rows,
    write_ibkr_raw_prices_csv,
)
from src.ibkr_historical_fetcher import fetch_ibkr_historical_bars_readonly


class FakeClient:
    def __init__(self, fail_symbol: str | None = None, empty_symbol: str | None = None):
        self.calls: list[str] = []
        self.fail_symbol = fail_symbol
        self.empty_symbol = empty_symbol

    def request_historical_daily_bars_readonly(self, symbol: str, **_: object):
        self.calls.append(symbol)
        if symbol == self.fail_symbol:
            raise RuntimeError("boom")
        if symbol == self.empty_symbol:
            return []
        return [{"date": "20260102", "close": 123.4}]


def test_dry_run_default_not_executed() -> None:
    config = build_ibkr_historical_fetch_config()
    fake = FakeClient()
    results = fetch_ibkr_historical_bars_readonly(config, ibkr_client=fake)
    assert all(r.fetch_status == "dry_run_not_executed" for r in results)
    assert fake.calls == []


def test_execute_calls_readonly_method() -> None:
    config = build_ibkr_historical_fetch_config(execute=True)
    fake = FakeClient()
    results = fetch_ibkr_historical_bars_readonly(config, ibkr_client=fake)
    assert [r.symbol for r in results] == ["1540.T", "1542.T"]
    assert fake.calls == ["1540.T", "1542.T"]
    assert all(r.fetch_status == "executed_readonly" for r in results)


def test_execute_missing_client() -> None:
    config = build_ibkr_historical_fetch_config(execute=True)
    results = fetch_ibkr_historical_bars_readonly(config, ibkr_client=None)
    assert results[0].fetch_status == "missing_ibkr_client"


def test_execute_single_symbol_error_does_not_break_all() -> None:
    config = build_ibkr_historical_fetch_config(execute=True)
    fake = FakeClient(fail_symbol="1540.T")
    results = fetch_ibkr_historical_bars_readonly(config, ibkr_client=fake)
    assert results[0].fetch_status == "error"
    assert results[1].fetch_status in {"executed_readonly", "executed_readonly_empty"}


def test_empty_bars_status() -> None:
    config = build_ibkr_historical_fetch_config(execute=True, symbols=["1540.T"])
    fake = FakeClient(empty_symbol="1540.T")
    results = fetch_ibkr_historical_bars_readonly(config, ibkr_client=fake)
    assert results[0].fetch_status == "executed_readonly_empty"


def test_only_support_target_symbols() -> None:
    config = build_ibkr_historical_fetch_config(symbols=["9999.T"])
    validated = validate_ibkr_historical_fetch_config(config)
    assert validated["validation_status"] == "invalid"


def test_convert_bars_to_raw_rows_date_formats() -> None:
    rows = convert_ibkr_bars_to_raw_rows("1540.T", "JPY", [{"date": "20260102", "close": 1}, {"date": "2026-01-03", "close": "2"}])
    assert rows[0]["date"] == "2026-01-02"
    assert rows[1]["date"] == "2026-01-03"


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
    assert ".reqHistoricalData(" not in text


def test_reqhistoricaldata_only_in_data_client_method_or_docs() -> None:
    for file_path in ["src/monitor.py", "src/ibkr_historical_fetcher.py", "main.py"]:
        text = Path(file_path).read_text(encoding="utf-8")
        assert ".reqHistoricalData(" not in text
