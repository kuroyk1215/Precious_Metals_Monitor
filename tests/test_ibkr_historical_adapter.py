from pathlib import Path

from src.ibkr_historical_adapter import (
    build_ibkr_historical_request_plan,
    validate_ibkr_historical_plan,
    write_ibkr_raw_prices_csv,
)


def test_request_plan_for_supported_symbols() -> None:
    plans = build_ibkr_historical_request_plan(["1540.T", "1542.T"])
    assert len(plans) == 2
    assert plans[0]["adapter_status"] == "supported"
    assert plans[1]["adapter_status"] == "supported"


def test_unsupported_symbol_marked() -> None:
    plans = build_ibkr_historical_request_plan(["9999.T"])
    assert plans[0]["adapter_status"] == "unsupported_symbol"


def test_default_parameters() -> None:
    plan = build_ibkr_historical_request_plan(["1540.T"])[0]
    assert plan["bar_size"] == "1 day"
    assert plan["what_to_show"] == "TRADES"
    assert plan["use_rth"] == 1


def test_validate_plan_has_status() -> None:
    plan = build_ibkr_historical_request_plan(["1540.T"])[0]
    validated = validate_ibkr_historical_plan(plan)
    assert validated["validation_status"] == "valid"


def test_write_raw_csv_header_with_empty_rows(tmp_path: Path) -> None:
    p = tmp_path / "raw.csv"
    write_ibkr_raw_prices_csv([], str(p))
    content = p.read_text(encoding="utf-8")
    assert content.splitlines()[0] == "date,symbol,close,currency,source,notes"


def test_no_auto_trade_keywords_present() -> None:
    text = Path("src/ibkr_historical_adapter.py").read_text(encoding="utf-8")
    banned = ["placeOrder", "cancelOrder", "reqOpenOrders", "bracketOrder", "whatIfOrder", "exerciseOptions", "Order(", "自动买入", "自动卖出", "自动调仓", "自动撤单"]
    for token in banned:
        assert token not in text


def test_no_reqhistoricaldata_in_phase_4b1_entrypoints() -> None:
    for file_path in [
        "src/ibkr_historical_adapter.py",
        "main.py",
        "src/monitor.py",
        "tests/test_ibkr_historical_adapter.py",
    ]:
        text = Path(file_path).read_text(encoding="utf-8")
        forbidden = "reqHistorical" + "Data("
        assert forbidden not in text


def test_ibkr_data_client_not_modified_interface_still_has_class() -> None:
    text = Path("src/ibkr_data_client.py").read_text(encoding="utf-8")
    assert "class IBKRDataClient" in text
