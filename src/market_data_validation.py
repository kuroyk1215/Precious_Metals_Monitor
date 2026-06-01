from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional


REQUIRED_FIELDS = (
    "symbol",
    "market",
    "timestamp_utc",
    "price",
    "currency",
    "source_name",
    "source_type",
    "data_delay_status",
)
ALLOWED_SYMBOLS = ("GLD", "SLV")
ALLOWED_SOURCE_TYPES = ("manual", "public_pilot")
ALLOWED_DELAY_STATUS = ("manual_input", "delayed", "historical", "unknown")
STALE_HOURS = 36


def parse_utc_timestamp(value: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def validate_market_data_row(row: Dict[str, str], now: Optional[datetime] = None) -> Dict[str, object]:
    missing = [field for field in REQUIRED_FIELDS if not row.get(field)]
    errors: List[str] = []
    warnings: List[str] = []
    if missing:
        errors.append("INVALID_DATA")

    symbol = row.get("symbol", "")
    if symbol and symbol not in ALLOWED_SYMBOLS:
        errors.append("UNSUPPORTED_SYMBOL")
    if row.get("market") and row.get("market") != "US":
        errors.append("INVALID_MARKET")
    if row.get("currency") and row.get("currency") != "USD":
        errors.append("INVALID_CURRENCY")
    if row.get("source_type") and row.get("source_type") not in ALLOWED_SOURCE_TYPES:
        errors.append("INVALID_SOURCE_TYPE")
    if row.get("data_delay_status") and row.get("data_delay_status") not in ALLOWED_DELAY_STATUS:
        errors.append("INVALID_DELAY_STATUS")

    price_value: Optional[float] = None
    if row.get("price"):
        try:
            price_value = float(row["price"])
        except ValueError:
            errors.append("INVALID_PRICE")
        else:
            if price_value <= 0:
                errors.append("INVALID_PRICE")

    timestamp = parse_utc_timestamp(row.get("timestamp_utc", ""))
    if row.get("timestamp_utc") and timestamp is None:
        errors.append("INVALID_TIMESTAMP")
    if timestamp is not None:
        reference_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        age_hours = (reference_time - timestamp).total_seconds() / 3600
        if age_hours > STALE_HOURS:
            warnings.append("STALE_DATA")

    validation_status = "INVALID_DATA" if errors else ("STALE_DATA" if warnings else "VALID_DATA")
    return {
        "symbol": symbol,
        "validation_status": validation_status,
        "errors": errors,
        "warnings": warnings,
        "normalized": {
            "symbol": symbol,
            "market": row.get("market", ""),
            "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z") if timestamp else row.get("timestamp_utc", ""),
            "price": price_value,
            "currency": row.get("currency", ""),
            "source_name": row.get("source_name", ""),
            "source_type": row.get("source_type", ""),
            "data_delay_status": row.get("data_delay_status", ""),
        },
    }


def validate_market_data_rows(rows: Iterable[Dict[str, str]], now: Optional[datetime] = None) -> List[Dict[str, object]]:
    return [validate_market_data_row(row, now=now) for row in rows]
