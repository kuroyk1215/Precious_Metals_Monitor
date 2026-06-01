from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

from src.manual_csv_market_data_loader import preview_manual_csv


DEFAULT_STORE_PATH = "data/local_market_data_store.json"
PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_empty_store(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "status": "LOCAL_MARKET_DATA_STORE_READY",
        "symbols": {
            "GLD": {"data_status": "待导入", "source_display": "None", "latest_timestamp_utc": "暂无", "records": []},
            "SLV": {"data_status": "待导入", "source_display": "None", "latest_timestamp_utc": "暂无", "records": []},
        },
        "trade_signal_generated": "NO",
        "generated_at_utc": timestamp,
    }


def load_store(path: PathLike = DEFAULT_STORE_PATH) -> Dict[str, object]:
    store_path = Path(path)
    if not store_path.exists():
        return build_empty_store()
    return json.loads(store_path.read_text(encoding="utf-8"))


def write_store_from_preview(preview: Dict[str, object], path: PathLike = DEFAULT_STORE_PATH) -> Dict[str, object]:
    valid_rows: List[Dict[str, object]] = [
        item["normalized"]
        for item in preview["rows"]  # type: ignore[index]
        if item["validation_status"] in {"VALID_DATA", "STALE_DATA"} and not item["errors"]
    ]
    if preview["invalid_row_count"] != 0:
        raise ValueError("manual CSV contains invalid rows")
    store = build_empty_store()
    for row in valid_rows:
        symbol = str(row["symbol"])
        data_status = "已过期" if any(
            item["symbol"] == symbol and item["validation_status"] == "STALE_DATA" for item in preview["rows"]  # type: ignore[index]
        ) else "已导入"
        store["symbols"][symbol] = {  # type: ignore[index]
            "data_status": data_status,
            "source_display": "Manual CSV" if row["source_type"] == "manual" else "Public Pilot",
            "latest_timestamp_utc": row["timestamp_utc"],
            "records": [row],
        }
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(store, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return store


def load_manual_csv_to_store(input_path: PathLike, store_path: PathLike = DEFAULT_STORE_PATH) -> Dict[str, object]:
    preview = preview_manual_csv(input_path)
    if preview["status"] != "MANUAL_CSV_IMPORT_PREVIEW_READY" or preview["invalid_row_count"] != 0:
        raise ValueError("manual CSV validation failed")
    return write_store_from_preview(preview, store_path)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Load validated GLD / SLV manual CSV data into the local store.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--store", default=DEFAULT_STORE_PATH)
    args = parser.parse_args(argv)
    try:
        store = load_manual_csv_to_store(args.input, args.store)
    except ValueError as exc:
        print(f"[MANUAL_CSV_LOAD] failed: {exc}")
        return 2
    print("[MANUAL_CSV_LOAD] generated")
    print(f"status={store['status']}")
    print(f"store={args.store}")
    print("trade_signal_generated=NO")
    return 0
