from __future__ import annotations

from datetime import datetime
from typing import Any
from collections import defaultdict

REQUIRED_FIELDS = [
    "date",
    "symbol",
    "actual_price",
    "metal_price_used",
    "fx_used",
    "premium_discount_pct",
    "data_source",
    "notes",
]


def _parse_date(value: str) -> str:
    return datetime.fromisoformat(value).date().isoformat()


def validate_historical_csv(path: str) -> dict[str, Any]:
    import csv

    valid_rows: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    missing_counts = defaultdict(int)

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != REQUIRED_FIELDS:
            raise RuntimeError(f"CSV fields mismatch, required={REQUIRED_FIELDS}")

        for idx, row in enumerate(reader, start=2):
            errors: list[str] = []
            parsed = dict(row)
            try:
                parsed["date"] = _parse_date(str(row.get("date", "")))
            except Exception:
                errors.append("invalid_date")

            symbol = (row.get("symbol") or "").strip()
            if not symbol:
                errors.append("missing_symbol")
            parsed["symbol"] = symbol

            for col in ["actual_price", "metal_price_used", "fx_used"]:
                val = row.get(col)
                if val in (None, ""):
                    errors.append(f"missing_{col}")
                    missing_counts[col] += 1
                    continue
                try:
                    fv = float(val)
                    if fv <= 0:
                        errors.append(f"invalid_{col}")
                    parsed[col] = fv
                except Exception:
                    errors.append(f"invalid_{col}")

            prem = row.get("premium_discount_pct")
            parsed["premium_discount_pct"] = 0.0 if prem in (None, "") else float(prem)

            data_source = (row.get("data_source") or "").strip()
            if not data_source:
                errors.append("missing_data_source")
            parsed["data_source"] = data_source
            parsed["notes"] = row.get("notes", "")

            if errors:
                invalid_rows.append({"line": idx, "errors": ",".join(errors), **parsed})
            else:
                valid_rows.append(parsed)

    return {
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "validation_summary": {
            "total_rows": len(valid_rows) + len(invalid_rows),
            "valid_rows": len(valid_rows),
            "invalid_rows": len(invalid_rows),
            "missing_actual_price_count": missing_counts["actual_price"],
            "missing_metal_price_count": missing_counts["metal_price_used"],
            "missing_fx_count": missing_counts["fx_used"],
        },
    }


def normalize_historical_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        out.append(
            {
                "date": _parse_date(str(row["date"])),
                "symbol": row["symbol"],
                "actual_price": float(row["actual_price"]),
                "metal_price_used": float(row["metal_price_used"]),
                "fx_used": float(row["fx_used"]),
                "premium_discount_pct": float(row.get("premium_discount_pct") or 0.0),
                "data_source": row.get("data_source", ""),
                "notes": row.get("notes", ""),
            }
        )
    return out


def summarize_data_quality(rows: list[dict[str, Any]], invalid_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    invalid_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        grouped[r["symbol"]].append(r)
    for r in invalid_rows:
        invalid_grouped[r.get("symbol", "UNKNOWN")].append(r)

    symbols = sorted(set(grouped.keys()) | set(invalid_grouped.keys()))
    summaries = []
    for symbol in symbols:
        valid = grouped.get(symbol, [])
        inv = invalid_grouped.get(symbol, [])
        total = len(valid) + len(inv)
        dates = [r["date"] for r in valid]
        unique_dates = set(dates)
        duplicate_date_count = len(dates) - len(unique_dates)
        missing_actual = sum(1 for r in inv if "missing_actual_price" in r.get("errors", ""))
        missing_metal = sum(1 for r in inv if "missing_metal_price_used" in r.get("errors", ""))
        missing_fx = sum(1 for r in inv if "missing_fx_used" in r.get("errors", ""))

        score = 1.0
        if total > 0 and len(inv) / total > 0.05:
            score -= 0.2
        if duplicate_date_count > 0:
            score -= 0.1
        if missing_actual > 0 or missing_metal > 0 or missing_fx > 0:
            score -= 0.2

        flags = []
        if len(valid) < 20:
            flags.append("insufficient_history")
        if duplicate_date_count > 0:
            flags.append("duplicate_dates")
        if len(inv) > 0:
            flags.append("invalid_rows_detected")

        summaries.append({
            "symbol": symbol,
            "total_rows": total,
            "valid_rows": len(valid),
            "invalid_rows": len(inv),
            "date_start": min(dates) if dates else None,
            "date_end": max(dates) if dates else None,
            "missing_actual_price_count": missing_actual,
            "missing_metal_price_count": missing_metal,
            "missing_fx_count": missing_fx,
            "duplicate_date_count": duplicate_date_count,
            "data_quality_score": round(max(0.0, score), 4),
            "validation_status": "ok" if score >= 0.7 else "needs_review",
            "warning_flags": ",".join(flags) if flags else "none",
        })
    return summaries
