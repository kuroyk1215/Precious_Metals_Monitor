from pathlib import Path

from src.historical_data_builder import (
    REQUIRED_STANDARD_FIELDS,
    build_standard_historical_rows,
    load_fx_rates_csv,
    load_metal_spot_csv,
    load_raw_price_csv,
    load_source_manifest,
    write_standard_historical_csv,
)


def test_manifest_loads():
    m = load_source_manifest("data/source_manifest_template.yaml")
    assert len(m["symbols"]) == 3


def test_raw_csv_loaders():
    assert len(load_raw_price_csv("data/raw/jp_etf_prices_sample.csv")) == 6
    assert len(load_metal_spot_csv("data/raw/metal_spot_sample.csv")) == 6
    assert len(load_fx_rates_csv("data/raw/fx_rates_sample.csv")) == 6


def test_build_rows_and_symbols_present():
    rows = build_standard_historical_rows(load_source_manifest("data/source_manifest_template.yaml"))
    assert rows
    assert set(REQUIRED_STANDARD_FIELDS) == set(rows[0].keys())
    assert {"1540.T", "1542.T", "518880.SH"}.issubset({r["symbol"] for r in rows})


def test_missing_metal_or_fx_is_marked(tmp_path):
    manifest = tmp_path / "m.yaml"
    manifest.write_text(Path("data/source_manifest_template.yaml").read_text(encoding="utf-8").replace("data/raw/metal_spot_sample.csv", str(tmp_path / "metal.csv")).replace("data/raw/fx_rates_sample.csv", str(tmp_path / "fx.csv")), encoding="utf-8")
    (tmp_path / "metal.csv").write_text("date,metal,price_usd,unit,source,notes\n", encoding="utf-8")
    (tmp_path / "fx.csv").write_text("date,pair,rate,source,notes\n", encoding="utf-8")
    rows = build_standard_historical_rows(load_source_manifest(str(manifest)))
    assert any("missing_metal_price" in r["notes"] for r in rows)
    assert any("missing_fx" in r["notes"] for r in rows)


def test_csv_field_order_and_no_auto_trade_words(tmp_path):
    rows = build_standard_historical_rows(load_source_manifest("data/source_manifest_template.yaml"))
    out = tmp_path / "candidate.csv"
    write_standard_historical_csv(rows, str(out))
    header = out.read_text(encoding="utf-8").splitlines()[0]
    assert header.split(",") == REQUIRED_STANDARD_FIELDS

    content = "\n".join([
        Path("src/historical_data_builder.py").read_text(encoding="utf-8"),
        Path("src/monitor.py").read_text(encoding="utf-8"),
        Path("main.py").read_text(encoding="utf-8"),
    ])
    banned = ["placeOrder", "cancelOrder", "reqOpenOrders", "bracketOrder", "whatIfOrder", "exerciseOptions", "Order(", "自动买入", "自动卖出", "自动调仓", "自动撤单"]
    for token in banned:
        assert token not in content
