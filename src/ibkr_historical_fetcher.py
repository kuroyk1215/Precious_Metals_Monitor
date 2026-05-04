from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class IBKRHistoricalFetchResult:
    symbol: str
    rows: list[dict[str, Any]]
    fetch_status: str
    warning_flags: str
    notes: str


def fetch_ibkr_historical_bars_readonly(config: dict[str, Any], ibkr_client: Any = None) -> list[IBKRHistoricalFetchResult]:
    symbols = config.get("symbols", [])
    execute = bool(config.get("execute", False))
    explicit_confirmed = config.get("explicit_user_confirmed") is True
    results: list[IBKRHistoricalFetchResult] = []

    if not execute:
        for symbol in symbols:
            results.append(IBKRHistoricalFetchResult(symbol=symbol, rows=[], fetch_status="dry_run_not_executed", warning_flags="none", notes="read_only|dry_run|user_explicit_execute_required"))
        return results

    if not explicit_confirmed:
        for symbol in symbols:
            results.append(IBKRHistoricalFetchResult(symbol=symbol, rows=[], fetch_status="explicit_user_confirmation_required", warning_flags="missing_explicit_confirmation", notes="read_only|execute_blocked"))
        return results

    if ibkr_client is None:
        for symbol in symbols:
            results.append(IBKRHistoricalFetchResult(symbol=symbol, rows=[], fetch_status="missing_ibkr_client", warning_flags="adapter_not_connected", notes="read_only|adapter_not_implemented"))
        return results

    fetch_method = getattr(ibkr_client, "request_historical_daily_bars_readonly", None)
    if fetch_method is None:
        for symbol in symbols:
            results.append(IBKRHistoricalFetchResult(symbol=symbol, rows=[], fetch_status="adapter_not_implemented", warning_flags="missing_readonly_adapter", notes="read_only|adapter_not_implemented"))
        return results

    for symbol in symbols:
        bars = fetch_method(symbol=symbol, duration=config.get("duration", "1 Y"), bar_size=config.get("bar_size", "1 day"), what_to_show=config.get("what_to_show", "TRADES"), use_rth=config.get("use_rth", 1))
        if bars is None:
            bars = []
        results.append(IBKRHistoricalFetchResult(symbol=symbol, rows=bars, fetch_status="executed_readonly", warning_flags="none", notes="read_only|no_auto_trade"))
    return results
