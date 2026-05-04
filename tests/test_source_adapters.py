from src.source_adapters import load_source_provider_manifest, normalize_provider_record, summarize_source_providers


def test_manifest_loads_and_count():
    providers = load_source_provider_manifest("data/source_provider_manifest_template.yaml")
    assert isinstance(providers, list)
    assert len(providers) == 6


def test_normalize_provider_record_keys_complete():
    row = normalize_provider_record({"provider_id": "x", "symbols": ["A"], "fields": ["date"]})
    assert set(row.keys()) == {
        "provider_id", "provider_type", "status", "online_required", "license_required", "intended_use", "symbols", "fields", "notes"
    }


def test_summarize_readiness_and_warning_flags():
    rows = summarize_source_providers([
        {"provider_id": "p1", "provider_type": "file", "status": "planned", "online_required": True, "license_required": True, "symbols": ["A"], "fields": ["f"]},
    ])
    assert rows[0]["readiness_status"] == "planned"
    assert "license_required" in rows[0]["warning_flags"]
    assert "online_required" in rows[0]["warning_flags"]


def test_missing_symbols_and_fields_flags():
    rows = summarize_source_providers([
        {"provider_id": "p2", "provider_type": "x", "status": "available", "online_required": False, "license_required": False, "symbols": [], "fields": []}
    ])
    assert "missing_symbols" in rows[0]["warning_flags"]
    assert "missing_fields" in rows[0]["warning_flags"]


def test_no_auto_trade_keywords_and_no_reqhistoricaldata():
    banned = ["placeOrder", "cancelOrder", "reqOpenOrders", "bracketOrder", "whatIfOrder", "exerciseOptions", "Order(", "自动买入", "自动卖出", "自动调仓", "自动撤单"]
    paths = ["src/source_adapters.py", "src/monitor.py", "main.py"]
    text = "\n".join(open(x, "r", encoding="utf-8").read() for x in paths)
    for token in banned:
        assert token not in text
