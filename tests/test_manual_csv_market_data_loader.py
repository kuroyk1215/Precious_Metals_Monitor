from __future__ import annotations

import csv
from pathlib import Path

from src.manual_csv_market_data_loader import DEFAULT_SAMPLE_CSV, preview_manual_csv, read_manual_csv
from src.market_data_validation import REQUIRED_FIELDS


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_loader_reads_sample_gld_slv_csv() -> None:
    rows = read_manual_csv(REPO_ROOT / DEFAULT_SAMPLE_CSV)

    assert [row["symbol"] for row in rows] == ["GLD", "SLV"]


def test_preview_sample_csv_is_valid() -> None:
    preview = preview_manual_csv(REPO_ROOT / DEFAULT_SAMPLE_CSV)

    assert preview["status"] == "MANUAL_CSV_IMPORT_PREVIEW_READY"
    assert preview["valid_row_count"] == 2
    assert preview["trade_signal_generated"] == "NO"


def test_preview_rejects_missing_field(tmp_path: Path) -> None:
    csv_path = tmp_path / "missing.csv"
    fields = [field for field in REQUIRED_FIELDS if field != "price"]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow({field: "x" for field in fields})

    preview = preview_manual_csv(csv_path)

    assert preview["status"] == "INVALID_DATA"
    assert "price" in preview["missing_fields"]
