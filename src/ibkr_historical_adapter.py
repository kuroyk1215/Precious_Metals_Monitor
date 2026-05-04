from __future__ import annotations

from pathlib import Path
from typing import Any
import csv

SUPPORTED_SYMBOLS = {"1540.T", "1542.T"}


def build_ibkr_historical_request_plan(
    symbols: list[str],
    duration: str = "1 Y",
    bar_size: str = "1 day",
    what_to_show: str = "TRADES",
    use_rth: int = 1,
) -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    for symbol in symbols:
        adapter_status = "supported" if symbol in SUPPORTED_SYMBOLS else "unsupported_symbol"
        plans.append(
            {
                "symbol": symbol,
                "duration": duration,
                "bar_size": bar_size,
                "what_to_show": what_to_show,
                "use_rth": use_rth,
                "adapter_status": adapter_status,
                "notes": "read_only|no_auto_trade|request_plan_only",
            }
        )
    return plans


def validate_ibkr_historical_plan(plan: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    validation_status = "valid"

    if not plan.get("symbol"):
        warnings.append("empty_symbol")
        validation_status = "invalid"
    if plan.get("bar_size") != "1 day":
        warnings.append("invalid_bar_size")
        validation_status = "invalid"
    if plan.get("what_to_show") != "TRADES":
        warnings.append("invalid_what_to_show")
        validation_status = "invalid"
    if plan.get("use_rth") != 1:
        warnings.append("invalid_use_rth")
        validation_status = "invalid"
    if plan.get("adapter_status") == "unsupported_symbol":
        warnings.append("unsupported_symbol")

    out = dict(plan)
    out["validation_status"] = validation_status
    out["warning_flags"] = "|".join(warnings) if warnings else "none"
    return out


def write_ibkr_historical_plan_csv(plans: list[dict[str, Any]], path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "symbol",
        "duration",
        "bar_size",
        "what_to_show",
        "use_rth",
        "adapter_status",
        "validation_status",
        "warning_flags",
        "notes",
    ]
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for plan in plans:
            writer.writerow(plan)


def write_ibkr_raw_prices_csv(rows: list[dict[str, Any]], path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = ["date", "symbol", "close", "currency", "source", "notes"]
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            payload = dict(row)
            payload["source"] = "ibkr_historical_bars_candidate"
            payload["notes"] = "read_only|not_calibrated|user_must_validate"
            writer.writerow(payload)


def summarize_ibkr_historical_adapter(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "symbol": row.get("symbol"),
            "adapter_status": row.get("adapter_status"),
            "validation_status": row.get("validation_status", "unknown"),
            "warning_flags": row.get("warning_flags", "none"),
        }
        for row in plans
    ]
