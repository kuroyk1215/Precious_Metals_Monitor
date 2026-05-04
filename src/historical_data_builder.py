from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

REQUIRED_STANDARD_FIELDS = [
    "date",
    "symbol",
    "actual_price",
    "metal_price_used",
    "fx_used",
    "premium_discount_pct",
    "data_source",
    "notes",
]


def load_source_manifest(path: str) -> dict[str, Any]:
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    symbols = data.get("symbols", []) if isinstance(data, dict) else []
    if not isinstance(symbols, list):
        raise RuntimeError("source manifest must contain symbols list")
    return {"symbols": symbols}


def _load_csv(path: str) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_raw_price_csv(path: str) -> list[dict[str, str]]:
    return _load_csv(path)


def load_metal_spot_csv(path: str) -> list[dict[str, str]]:
    return _load_csv(path)


def load_fx_rates_csv(path: str) -> list[dict[str, str]]:
    return _load_csv(path)


def build_standard_historical_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cfg in manifest.get("symbols", []):
        symbol = cfg.get("symbol", "").strip()
        actual_price_source = cfg.get("actual_price_source", "")
        metal_price_source = cfg.get("metal_price_source", "")
        fx_source = cfg.get("fx_source", "")
        metal = cfg.get("metal", "")
        fx_pair = cfg.get("fx_pair", "")

        actual_rows = [r for r in load_raw_price_csv(actual_price_source) if (r.get("symbol") or "").strip() == symbol]
        metal_index = {(r.get("date", "").strip(), (r.get("metal") or "").strip()): (r.get("price_usd") or "").strip() for r in load_metal_spot_csv(metal_price_source)}
        fx_index = {(r.get("date", "").strip(), (r.get("pair") or "").strip()): (r.get("rate") or "").strip() for r in load_fx_rates_csv(fx_source)}

        for raw in actual_rows:
            date = (raw.get("date") or "").strip()
            metal_price = metal_index.get((date, metal), "")
            fx_rate = fx_index.get((date, fx_pair), "")
            notes = [
                "raw_build",
                f"actual_price_source={actual_price_source}",
                f"metal_price_source={metal_price_source}",
                f"fx_source={fx_source}",
            ]
            joined = " ".join([str(raw.get("notes", "")), str(cfg.get("data_source", ""))]).lower()
            if "sample" in joined or "template" in joined:
                notes.append("not real market data")
            if metal_price in (None, ""):
                notes.append("missing_metal_price")
            if fx_rate in (None, ""):
                notes.append("missing_fx")

            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "actual_price": (raw.get("close") or "").strip(),
                    "metal_price_used": metal_price,
                    "fx_used": fx_rate,
                    "premium_discount_pct": str(cfg.get("premium_discount_pct", 0.0)),
                    "data_source": str(cfg.get("data_source", "")).strip(),
                    "notes": "; ".join(notes),
                }
            )
    return rows


def write_standard_historical_csv(rows: list[dict[str, Any]], path: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_STANDARD_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in REQUIRED_STANDARD_FIELDS})


def summarize_build(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["symbol"]].append(row)

    summary: list[dict[str, Any]] = []
    for symbol, item_rows in sorted(grouped.items()):
        dates = [r["date"] for r in item_rows if r.get("date")]
        missing_metal = sum(1 for r in item_rows if not r.get("metal_price_used"))
        missing_fx = sum(1 for r in item_rows if not r.get("fx_used"))
        flags: list[str] = []
        if missing_metal > 0:
            flags.append("missing_metal_price")
        if missing_fx > 0:
            flags.append("missing_fx")
        summary.append(
            {
                "symbol": symbol,
                "total_rows": len(item_rows),
                "missing_metal_price_count": missing_metal,
                "missing_fx_count": missing_fx,
                "date_start": min(dates) if dates else "",
                "date_end": max(dates) if dates else "",
                "build_status": "ok" if not flags else "needs_review",
                "warning_flags": ",".join(flags) if flags else "none",
            }
        )
    return summary
