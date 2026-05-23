from __future__ import annotations

from typing import Any, Mapping, Optional


def _positive_conid(value: Optional[str]) -> Optional[int]:
    try:
        conid = int((value or "").strip())
    except ValueError:
        return None
    return conid if conid > 0 else None


def build_market_data_contract_kwargs(row: Mapping[str, str]) -> dict[str, Any]:
    conid = _positive_conid(row.get("conid"))
    sec_type = row.get("sec_type") or "STK"
    exchange = row.get("exchange") or "SMART"
    currency = row.get("currency") or "USD"

    if conid is not None:
        return {
            "conId": conid,
            "secType": sec_type,
            "exchange": exchange,
            "currency": currency,
        }

    kwargs: dict[str, Any] = {
        "symbol": row.get("symbol") or row.get("display_symbol") or "",
        "secType": sec_type,
        "exchange": exchange,
        "currency": currency,
    }
    optional_fields = {
        "primaryExchange": row.get("primary_exchange") or "",
        "localSymbol": row.get("local_symbol") or "",
        "tradingClass": row.get("trading_class") or "",
    }
    kwargs.update({key: value for key, value in optional_fields.items() if value})
    return kwargs


def build_market_data_contract(contract_class: type, row: Mapping[str, str]) -> Any:
    return contract_class(**build_market_data_contract_kwargs(row))
