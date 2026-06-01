from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

from src.market_data_validation import REQUIRED_FIELDS, validate_market_data_rows


DEFAULT_SAMPLE_CSV = "data/manual_market_data_sample_GLD_SLV.csv"
DEFAULT_TEMPLATE_CSV = "data/manual_market_data_template.csv"
PathLike = Union[str, Path]


def read_manual_csv(path: PathLike) -> List[Dict[str, str]]:
    input_path = Path(path)
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
    return rows


def preview_manual_csv(path: PathLike = DEFAULT_SAMPLE_CSV) -> Dict[str, object]:
    rows = read_manual_csv(path)
    missing_fields = [field for field in REQUIRED_FIELDS if rows and field not in rows[0]]
    if not rows:
        missing_fields = list(REQUIRED_FIELDS)
    validations = validate_market_data_rows(rows)
    valid_rows = [item for item in validations if item["validation_status"] in {"VALID_DATA", "STALE_DATA"} and not item["errors"]]
    return {
        "status": "MANUAL_CSV_IMPORT_PREVIEW_READY" if not missing_fields else "INVALID_DATA",
        "input_path": str(path),
        "required_fields": list(REQUIRED_FIELDS),
        "missing_fields": missing_fields,
        "row_count": len(rows),
        "valid_row_count": len(valid_rows),
        "invalid_row_count": len(rows) - len(valid_rows),
        "rows": validations,
        "trade_signal_generated": "NO",
    }


def write_manual_csv_template(path: PathLike = DEFAULT_TEMPLATE_CSV) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(REQUIRED_FIELDS)


def write_sample_manual_csv(path: PathLike = DEFAULT_SAMPLE_CSV) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(
            {
                "symbol": "GLD",
                "market": "US",
                "timestamp_utc": "2026-06-01T00:00:00Z",
                "price": "220.10",
                "currency": "USD",
                "source_name": "manual_operator_sample",
                "source_type": "manual",
                "data_delay_status": "manual_input",
            }
        )
        writer.writerow(
            {
                "symbol": "SLV",
                "market": "US",
                "timestamp_utc": "2026-06-01T00:00:00Z",
                "price": "28.40",
                "currency": "USD",
                "source_name": "manual_operator_sample",
                "source_type": "manual",
                "data_delay_status": "manual_input",
            }
        )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Preview manual GLD / SLV CSV market data without generating signals.")
    parser.add_argument("--input", default=DEFAULT_SAMPLE_CSV)
    args = parser.parse_args(argv)
    preview = preview_manual_csv(args.input)
    print("[MANUAL_CSV_IMPORT_PREVIEW] generated")
    print(f"status={preview['status']}")
    print(f"row_count={preview['row_count']}")
    print(f"valid_row_count={preview['valid_row_count']}")
    print(f"trade_signal_generated={preview['trade_signal_generated']}")
    return 0 if preview["status"] == "MANUAL_CSV_IMPORT_PREVIEW_READY" else 2
