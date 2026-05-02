from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class SmokeQuote:
    symbol: str
    market: str
    bid: float | None
    ask: float | None
    last: float | None
    close: float | None
    volume: float | None
    data_status: str
    market_data_type: str
    contract_status: str
    source_status: str
    error_message: str


class IBKRDataClient:
    def __init__(self, ibkr_config: dict[str, Any]):
        self.ibkr_config = ibkr_config
        self.ib = None
        self.connection_status = "fallback_no_ibkr_connection"

    def connect(self) -> tuple[bool, str]:
        try:
            from ib_insync import IB
        except ImportError:
            self.connection_status = "ib_insync_not_installed"
            return False, self.connection_status

        self.ib = IB()
        try:
            self.ib.connect(
                host=self.ibkr_config["host"],
                port=int(self.ibkr_config["port"]),
                clientId=int(self.ibkr_config["client_id"]),
                timeout=float(self.ibkr_config.get("timeout_sec", 5)),
                readonly=bool(self.ibkr_config.get("readonly", True)),
            )
            self.connection_status = "connected"
            return True, self.connection_status
        except Exception as exc:  # pragma: no cover
            self.connection_status = "failed"
            return False, f"failed:{exc}"

    def disconnect(self) -> None:
        if self.ib is not None and self.ib.isConnected():
            self.ib.disconnect()

    def build_contract(self, symbol_config: dict[str, Any]) -> tuple[Any | None, str, str]:
        ibkr = symbol_config.get("ibkr", {})
        required = ["secType", "exchange", "currency"]
        if any(not ibkr.get(k) for k in required):
            return None, "invalid_config", "missing_required_ibkr_fields"
        if not ibkr.get("localSymbol") and not symbol_config.get("symbol"):
            return None, "needs_manual_contract_config", "missing_symbol_and_local_symbol"

        try:
            from ib_insync import Contract
        except ImportError:
            return None, "needs_manual_contract_config", "ib_insync_not_installed"

        contract = Contract(
            symbol=(ibkr.get("localSymbol") or symbol_config.get("symbol").split(".")[0]),
            secType=ibkr.get("secType"),
            exchange=ibkr.get("exchange"),
            currency=ibkr.get("currency"),
            primaryExchange=ibkr.get("primaryExchange") or "",
            localSymbol=ibkr.get("localSymbol") or "",
            tradingClass=ibkr.get("tradingClass") or "",
        )
        if not contract.symbol:
            return None, "needs_manual_contract_config", "empty_contract_symbol"
        return contract, "built", "ok"

    def qualify_contract(self, contract: Any) -> tuple[Any | None, str, str]:
        if self.ib is None or not self.ib.isConnected():
            return None, "unqualified", "not_connected"
        try:
            qualified = self.ib.qualifyContracts(contract)
            if not qualified:
                return None, "unqualified", "qualify_returned_empty"
            return qualified[0], "qualified", "ok"
        except Exception as exc:  # pragma: no cover
            return None, "unqualified", str(exc)

    def request_market_data(self, contract: Any, preferred_data_type: str) -> tuple[Any | None, str, str]:
        if self.ib is None or not self.ib.isConnected():
            return None, "unavailable", "not_connected"
        mapping = {"live": 1, "frozen": 2, "delayed": 3, "delayed_frozen": 4}
        md_type = mapping.get(preferred_data_type, 3)
        try:
            self.ib.reqMarketDataType(md_type)
            ticker = self.ib.reqMktData(contract, "", snapshot=True, regulatorySnapshot=False)
            self.ib.sleep(1.0)
            return ticker, str(md_type), "ok"
        except Exception as exc:  # pragma: no cover
            return None, "unavailable", str(exc)

    @staticmethod
    def detect_data_status(market_data_type: str, bid: float | None, ask: float | None, last: float | None, close: float | None) -> str:
        if bid is None and ask is None and last is None and close is None:
            return "unavailable"
        mapping = {"1": "real_time", "2": "frozen", "3": "delayed", "4": "delayed_frozen"}
        return mapping.get(str(market_data_type), "unavailable")

    def get_quote_snapshot(self, symbol_config: dict[str, Any], preferred_data_type: str = "delayed") -> SmokeQuote:
        symbol = symbol_config.get("symbol", "UNKNOWN")
        market = symbol_config.get("market", "UNKNOWN")
        timestamp = datetime.now(timezone.utc).isoformat()

        contract, contract_status, err = self.build_contract(symbol_config)
        if contract_status in {"invalid_config", "needs_manual_contract_config"}:
            return SmokeQuote(symbol, market, None, None, None, None, None, "unavailable", "unavailable", contract_status, "contract_build_failed", err)

        if self.ib is None or not self.ib.isConnected():
            return SmokeQuote(symbol, market, None, None, None, None, None, "unavailable", "unavailable", "unqualified", "fallback_no_ibkr_connection", f"{self.connection_status}@{timestamp}")

        qualified, q_status, q_err = self.qualify_contract(contract)
        if q_status != "qualified":
            return SmokeQuote(symbol, market, None, None, None, None, None, "unavailable", "unavailable", q_status, "qualify_failed", q_err)

        ticker, md_type, md_err = self.request_market_data(qualified, preferred_data_type)
        if ticker is None:
            return SmokeQuote(symbol, market, None, None, None, None, None, "unavailable", md_type, "qualified", "market_data_failed", md_err)

        bid = getattr(ticker, "bid", None)
        ask = getattr(ticker, "ask", None)
        last = getattr(ticker, "last", None)
        close = getattr(ticker, "close", None)
        volume = getattr(ticker, "volume", None)
        data_status = self.detect_data_status(md_type, bid, ask, last, close)
        return SmokeQuote(symbol, market, bid, ask, last, close, volume, data_status, md_type, "qualified", "ibkr_market_data", "")
