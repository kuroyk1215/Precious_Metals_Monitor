from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
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
    conId: int | None
    selected_exchange: str | None
    selected_primary_exchange: str | None
    selected_local_symbol: str | None
    candidate_index: int | None
    fallback_price: float | None
    fallback_method: str
    has_valid_price: bool


@dataclass
class ContractSearchRow:
    query: str
    conId: int | None
    symbol: str
    localSymbol: str
    tradingClass: str
    secType: str
    exchange: str
    primaryExchange: str
    currency: str
    longName: str
    validExchanges: str
    marketRuleIds: str
    status: str


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

    def _contract_candidates(self, symbol_config: dict[str, Any]) -> list[dict[str, str]]:
        if symbol_config.get("data_source") == "external_required":
            return []
        ibkr_cfg = symbol_config.get("ibkr", {})
        if ibkr_cfg.get("conId"):
            return [ibkr_cfg]
        symbol = symbol_config.get("symbol", "")
        if symbol == "1540.T":
            return [
                {"symbol": "1540", "secType": "STK", "exchange": "TSEJ", "currency": "JPY", "primaryExchange": "TSEJ", "localSymbol": "1540"},
                {"symbol": "1540", "secType": "STK", "exchange": "SMART", "currency": "JPY", "primaryExchange": "TSEJ", "localSymbol": "1540"},
                {"symbol": "1540", "secType": "STK", "exchange": "TSE.JPN", "currency": "JPY", "localSymbol": "1540"},
                {"symbol": "1540", "secType": "STK", "exchange": "TSE", "currency": "JPY", "localSymbol": "1540"},
            ]
        if symbol == "1542.T":
            return [
                {"symbol": "1542", "secType": "STK", "exchange": "TSEJ", "currency": "JPY", "primaryExchange": "TSEJ", "localSymbol": "1542"},
                {"symbol": "1542", "secType": "STK", "exchange": "SMART", "currency": "JPY", "primaryExchange": "TSEJ", "localSymbol": "1542"},
                {"symbol": "1542", "secType": "STK", "exchange": "TSE.JPN", "currency": "JPY", "localSymbol": "1542"},
                {"symbol": "1542", "secType": "STK", "exchange": "TSE", "currency": "JPY", "localSymbol": "1542"},
            ]
        if symbol == "518880.SH":
            return [
                {"symbol": "518880", "secType": "STK", "exchange": "SHSE", "currency": "CNY", "localSymbol": "518880"},
                {"symbol": "518880", "secType": "STK", "exchange": "SMART", "currency": "CNY", "primaryExchange": "SHSE", "localSymbol": "518880"},
                {"symbol": "518880", "secType": "STK", "exchange": "SEHKNTL", "currency": "CNY", "localSymbol": "518880"},
            ]
        return [symbol_config.get("ibkr", {})]

    def build_contract(self, symbol_config: dict[str, Any], candidate: dict[str, str] | None = None) -> tuple[Any | None, str, str]:
        ibkr = candidate or symbol_config.get("ibkr", {})
        if symbol_config.get("data_source") == "external_required":
            return None, "unqualified", "external_required"
        required = ["secType", "exchange", "currency"]
        if any(not ibkr.get(k) for k in required):
            return None, "invalid_config", "missing_required_ibkr_fields"
        if not ibkr.get("localSymbol") and not symbol_config.get("symbol"):
            return None, "needs_manual_contract_config", "missing_symbol_and_local_symbol"

        try:
            from ib_insync import Contract
        except ImportError:
            return None, "needs_manual_contract_config", "ib_insync_not_installed"

        contract_kwargs = {
            "secType": ibkr.get("secType"),
            "exchange": ibkr.get("exchange"),
            "currency": ibkr.get("currency"),
            "primaryExchange": ibkr.get("primaryExchange") or "",
            "localSymbol": ibkr.get("localSymbol") or "",
            "tradingClass": ibkr.get("tradingClass") or "",
        }
        if ibkr.get("conId"):
            contract = Contract(
                conId=int(ibkr.get("conId")),
                **contract_kwargs,
            )
        else:
            contract = Contract(
                symbol=(ibkr.get("localSymbol") or symbol_config.get("symbol").split(".")[0]),
                **contract_kwargs,
            )
        if not contract.symbol:
            if not ibkr.get("conId"):
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
        if symbol_config.get("data_source") == "external_required":
            return SmokeQuote(symbol, market, None, None, None, None, None, "unavailable", "unavailable", "unqualified", "needs_external_data_source", "external_required_symbol", None, None, None, None, None, None, "unavailable", False)

        selected_contract = None
        selected_candidate = None
        selected_index = None
        last_err = ""
        for idx, candidate in enumerate(self._contract_candidates(symbol_config), start=1):
            contract, contract_status, err = self.build_contract(symbol_config, candidate)
            if contract_status in {"invalid_config", "needs_manual_contract_config"}:
                last_err = err
                continue
            selected_contract = contract
            selected_candidate = candidate
            selected_index = idx
            qualified, q_status, q_err = self.qualify_contract(contract)
            if q_status == "qualified":
                selected_contract = qualified
                break
            last_err = q_err
            selected_contract = None

        if selected_contract is None:
            src = "all_contract_candidates_failed"
            err = "qualify_returned_empty_after_all_candidates"
            return SmokeQuote(symbol, market, None, None, None, None, None, "unavailable", "unavailable", "unqualified", src, err, None, None, None, None, None, None, "unavailable", False)

        if self.ib is None or not self.ib.isConnected():
            return SmokeQuote(symbol, market, None, None, None, None, None, "unavailable", "unavailable", "unqualified", "fallback_no_ibkr_connection", f"{self.connection_status}@{timestamp}", None, None, None, None, None, None, "unavailable", False)

        ticker, md_type, md_err = self.request_market_data(selected_contract, preferred_data_type)
        if ticker is None:
            return SmokeQuote(symbol, market, None, None, None, None, None, "unavailable", md_type, "qualified", "market_data_failed", md_err, getattr(selected_contract, "conId", None), selected_candidate.get("exchange") if selected_candidate else None, selected_candidate.get("primaryExchange") if selected_candidate else None, selected_candidate.get("localSymbol") if selected_candidate else None, selected_index, None, "unavailable", False)

        bid = self._normalize_price(getattr(ticker, "bid", None))
        ask = self._normalize_price(getattr(ticker, "ask", None))
        last = self._normalize_price(getattr(ticker, "last", None))
        close = self._normalize_price(getattr(ticker, "close", None))
        volume = getattr(ticker, "volume", None)

        source_status = "ibkr_market_data"
        error_message = ""
        current_md_type = md_type

        if self._all_quotes_empty(bid, ask, last, close):
            retry_ticker, retry_md_type, retry_err = self.request_market_data(selected_contract, "delayed_frozen")
            if retry_ticker is not None:
                retry_bid = self._normalize_price(getattr(retry_ticker, "bid", None))
                retry_ask = self._normalize_price(getattr(retry_ticker, "ask", None))
                retry_last = self._normalize_price(getattr(retry_ticker, "last", None))
                retry_close = self._normalize_price(getattr(retry_ticker, "close", None))
                if not self._all_quotes_empty(retry_bid, retry_ask, retry_last, retry_close):
                    bid, ask, last, close = retry_bid, retry_ask, retry_last, retry_close
                    current_md_type = retry_md_type
                    source_status = "ibkr_market_data_delayed_frozen_fallback"
            else:
                error_message = f"delayed_frozen_failed:{retry_err}"

        if self._all_quotes_empty(bid, ask, last, close):
            hist_close, hist_err = self.request_historical_daily_close(selected_contract)
            if hist_close is not None:
                close = hist_close
                source_status = "historical_daily_close_fallback"
                error_message = "historical_daily_close_used"
            else:
                if error_message:
                    error_message = f"{error_message}; historical_close_failed:{hist_err}"
                else:
                    error_message = f"historical_close_failed:{hist_err}"

        data_status = self.detect_data_status(current_md_type, bid, ask, last, close)
        fallback_price = last if last is not None else (close if source_status == "historical_daily_close_fallback" else None)
        if source_status == "historical_daily_close_fallback":
            fallback_method = "historical_daily_close"
        elif current_md_type == "1":
            fallback_method = "market_data_live"
        elif current_md_type == "3":
            fallback_method = "market_data_delayed"
        elif current_md_type == "4":
            fallback_method = "market_data_delayed_frozen"
        else:
            fallback_method = "unavailable"
        has_valid_price = any(v is not None for v in [bid, ask, last, close, fallback_price])
        return SmokeQuote(symbol, market, bid, ask, last, close, volume, data_status, current_md_type, "qualified", source_status, error_message, getattr(selected_contract, "conId", None), selected_candidate.get("exchange") if selected_candidate else None, selected_candidate.get("primaryExchange") if selected_candidate else None, selected_candidate.get("localSymbol") if selected_candidate else None, selected_index, fallback_price, fallback_method, has_valid_price)
    @staticmethod
    def _normalize_price(value: Any) -> float | None:
        if value is None:
            return None
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(v) or math.isinf(v):
            return None
        return v

    def _all_quotes_empty(self, bid: float | None, ask: float | None, last: float | None, close: float | None) -> bool:
        return bid is None and ask is None and last is None and close is None

    def request_historical_daily_close(self, contract: Any) -> tuple[float | None, str]:
        if self.ib is None or not self.ib.isConnected():
            return None, "not_connected"
        try:
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime="",
                durationStr="3 D",
                barSizeSetting="1 day",
                whatToShow="TRADES",
                useRTH=True,
                formatDate=1,
            )
            if not bars:
                return None, "empty_historical_data"
            close = self._normalize_price(getattr(bars[-1], "close", None))
            if close is None:
                return None, "invalid_historical_close"
            return close, "ok"
        except Exception as exc:  # pragma: no cover
            return None, str(exc)

    def request_historical_daily_bars_readonly(
        self,
        symbol: str,
        duration: str = "1 Y",
        bar_size: str = "1 day",
        what_to_show: str = "TRADES",
        use_rth: int = 1,
        timeout_sec: int = 30,
    ) -> list[dict[str, Any]]:
        if symbol not in {"1540.T", "1542.T"}:
            raise ValueError(f"unsupported_symbol:{symbol}")
        if self.ib is None or not self.ib.isConnected():
            raise RuntimeError("ibkr_not_connected")
        symbol_num = symbol.split(".", 1)[0]
        contract_config = {
            "symbol": symbol_num,
            "secType": "STK",
            "exchange": "TSEJ",
            "currency": "JPY",
            "primaryExchange": "TSEJ",
            "localSymbol": symbol_num,
        }
        contract, status, _ = self.build_contract({"symbol": symbol, "ibkr": contract_config}, contract_config)
        if contract is None or status != "qualified":
            raise RuntimeError(f"contract_not_qualified:{status}")
        try:
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime="",
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=bool(use_rth),
                formatDate=1,
                keepUpToDate=False,
                timeout=float(timeout_sec),
            )
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"reqHistoricalData_error:{exc}") from exc
        out: list[dict[str, Any]] = []
        for bar in bars or []:
            out.append(
                {
                    "date": str(getattr(bar, "date", "")),
                    "close": getattr(bar, "close", None),
                    "open": getattr(bar, "open", None),
                    "high": getattr(bar, "high", None),
                    "low": getattr(bar, "low", None),
                    "volume": getattr(bar, "volume", None),
                }
            )
        return out

    def search_contracts(self, query: str) -> tuple[list[ContractSearchRow], str]:
        if self.ib is None or not self.ib.isConnected():
            return [ContractSearchRow(query, None, "", "", "", "", "", "", "", "", "", "", "no_ibkr_contract_match")], "not_connected"
        try:
            candidates = self.ib.reqMatchingSymbols(query)
        except Exception as exc:  # pragma: no cover
            return [ContractSearchRow(query, None, "", "", "", "", "", "", "", "", "", "", f"no_ibkr_contract_match:{exc}")], "failed"

        if not candidates:
            return [ContractSearchRow(query, None, "", "", "", "", "", "", "", "", "", "", "no_ibkr_contract_match")], "ok"

        rows: list[ContractSearchRow] = []
        for candidate in candidates:
            contract = getattr(candidate, "contract", None)
            if contract is None:
                continue
            try:
                details = self.ib.reqContractDetails(contract)
            except Exception as exc:  # pragma: no cover
                rows.append(ContractSearchRow(query, getattr(contract, "conId", None), getattr(contract, "symbol", ""), getattr(contract, "localSymbol", ""), getattr(contract, "tradingClass", ""), getattr(contract, "secType", ""), getattr(contract, "exchange", ""), getattr(contract, "primaryExchange", ""), getattr(contract, "currency", ""), "", "", "", f"contract_details_failed:{exc}"))
                continue

            if not details:
                rows.append(ContractSearchRow(query, getattr(contract, "conId", None), getattr(contract, "symbol", ""), getattr(contract, "localSymbol", ""), getattr(contract, "tradingClass", ""), getattr(contract, "secType", ""), getattr(contract, "exchange", ""), getattr(contract, "primaryExchange", ""), getattr(contract, "currency", ""), "", "", "", "no_ibkr_contract_match"))
                continue

            for d in details:
                resolved = getattr(d, "contract", contract)
                rows.append(ContractSearchRow(
                    query=query,
                    conId=getattr(resolved, "conId", None),
                    symbol=getattr(resolved, "symbol", ""),
                    localSymbol=getattr(resolved, "localSymbol", ""),
                    tradingClass=getattr(resolved, "tradingClass", ""),
                    secType=getattr(resolved, "secType", ""),
                    exchange=getattr(resolved, "exchange", ""),
                    primaryExchange=getattr(resolved, "primaryExchange", ""),
                    currency=getattr(resolved, "currency", ""),
                    longName=getattr(d, "longName", ""),
                    validExchanges=getattr(d, "validExchanges", ""),
                    marketRuleIds=getattr(d, "marketRuleIds", ""),
                    status="ok",
                ))
        if not rows:
            rows.append(ContractSearchRow(query, None, "", "", "", "", "", "", "", "", "", "", "no_ibkr_contract_match"))
        return rows, "ok"
