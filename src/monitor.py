from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any

import csv

from src.ibkr_data_client import ContractSearchRow, IBKRDataClient, SmokeQuote


def _default_config() -> dict[str, Any]:
    return {
        "ibkr": {"host": "127.0.0.1", "port": 7496, "client_id": 1, "timeout_sec": 5, "readonly": True, "account_mode": "live", "read_only_required": True},
        "runtime": {
            "csv_log": "precious_metals_signal_log.csv",
            "markdown_report": "reports/latest_report.md",
            "ibkr_smoke_csv": "ibkr_smoke_log.csv",
            "ibkr_smoke_report": "reports/ibkr_smoke_report.md",
            "timezone": {"jst": "Asia/Tokyo", "cst": "Asia/Shanghai", "et": "America/New_York"},
        },
        "market_data": {"delayed_data_trade_threshold_deviation_pct": 1.5},
        "model": {
            "shanghai_gold_premium_pct": 0.8,
            "historical_premium_discount_pct": {"518880.SH": 0.2, "1540.T": 0.1, "1542.T": 0.1},
            "etf_conversion_factor": {"1540.T": 0.1, "1542.T": 0.1},
        },
    }




def _default_watchlist() -> dict[str, Any]:
    return {"symbols": [
        {"symbol": "518880.SH", "market": "CN", "name": "华安黄金ETF", "role": "gold_etf", "ibkr": {"secType": "STK", "exchange": "SEHKSZSE", "currency": "CNY", "primaryExchange": "SEHKSZSE", "localSymbol": "518880", "tradingClass": ""}},
        {"symbol": "1540.T", "market": "JP", "name": "Japan Physical Gold ETF", "role": "gold_etf", "ibkr": {"secType": "STK", "exchange": "TSEJ", "currency": "JPY", "primaryExchange": "TSEJ", "localSymbol": "1540", "tradingClass": ""}},
        {"symbol": "1542.T", "market": "JP", "name": "Japan Physical Silver ETF", "role": "silver_etf", "ibkr": {"secType": "STK", "exchange": "TSEJ", "currency": "JPY", "primaryExchange": "TSEJ", "localSymbol": "1542", "tradingClass": ""}},
        {"symbol": "GLD", "market": "US", "name": "SPDR Gold Shares", "role": "gold_etf", "ibkr": {"secType": "STK", "exchange": "SMART", "currency": "USD", "primaryExchange": "ARCA", "localSymbol": "GLD", "tradingClass": "GLD"}}
    ]}

@dataclass
class Quote:
    symbol: str
    market: str
    actual_price: float | None
    volume: float | None
    data_status: str
    source_status: str


@dataclass
class SignalRow:
    timestamp_jst: str
    timestamp_et: str
    symbol: str
    market: str
    data_status: str
    actual_price: float | None
    theoretical_price: float | None
    deviation_pct: float | None
    premium_discount: float | None
    fx_used: str
    gold_price: float | None
    silver_price: float | None
    signal: str
    reason: str
    risk_flag: str
    source_status: str


class PreciousMetalsMonitor:
    def __init__(self, config_path: str, watchlist_path: str, mock_mode: bool = False):
        self.mock_mode = mock_mode
        self.config = self._load_yaml(config_path, kind="config")
        self.watchlist = self._load_yaml(watchlist_path, kind="watchlist")

    def _load_yaml(self, path: str, kind: str) -> dict[str, Any]:
        try:
            import yaml
        except ImportError:
            if kind == "config":
                return _default_config()
            if self.mock_mode:
                return _default_watchlist()
            raise RuntimeError("缺少 PyYAML，请先 pip install -r requirements.txt")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            return _default_config() if kind == "config" else {"symbols": []}
        return data

    def test_ibkr_connection(self) -> tuple[bool, str]:
        client = IBKRDataClient(self.config["ibkr"])
        ok, status = client.connect()
        client.disconnect()
        return ok, status

    def _symbols(self) -> list[dict[str, Any]]:
        return self.watchlist.get("symbols", [])

    def now_triplet(self) -> dict[str, str]:
        now_utc = datetime.now(timezone.utc)
        tz_cfg = self.config["runtime"]["timezone"]
        return {
            "jst": now_utc.astimezone(ZoneInfo(tz_cfg["jst"])).isoformat(),
            "cst": now_utc.astimezone(ZoneInfo(tz_cfg["cst"])).isoformat(),
            "et": now_utc.astimezone(ZoneInfo(tz_cfg["et"])).isoformat(),
        }

    def _build_quotes(self, use_mock: bool, ibkr_connected: bool) -> list[Quote]:
        quotes: list[Quote] = []
        sample = {"518880.SH": (5.12, 50000, "delayed"), "1540.T": (2910.0, 30000, "delayed"), "1542.T": (440.0, 25000, "delayed"), "GLD": (218.1, 8000000, "real_time")}
        for item in self._symbols():
            symbol = item.get("symbol")
            market = item.get("market", "UNKNOWN")
            if (use_mock or ibkr_connected) and symbol in sample:
                px, vol, ds = sample[symbol]
                quotes.append(Quote(symbol, market, px, vol, ds, "mock_data"))
            else:
                quotes.append(Quote(symbol, market, None, None, "unavailable", "fallback_no_feed"))
        return quotes

    def run(self, ibkr_connected: bool = False, force_mock: bool = False) -> tuple[list[SignalRow], str, str]:
        times = self.now_triplet()
        anchors = {"XAUUSD": 2350.0, "XAGUSD": 28.5, "USDJPY": 155.0, "USDCNH": 7.2}
        rows: list[SignalRow] = []
        for q in self._build_quotes(force_mock, ibkr_connected):
            theo = None
            if q.symbol == "518880.SH":
                theo = anchors["XAUUSD"] * anchors["USDCNH"] * 0.001
            elif q.symbol == "1540.T":
                theo = anchors["XAUUSD"] * anchors["USDJPY"] * 0.1
            elif q.symbol == "1542.T":
                theo = anchors["XAGUSD"] * anchors["USDJPY"] * 0.1
            dev = None if (theo is None or not q.actual_price) else ((q.actual_price - theo) / theo) * 100
            signal = "BLOCKED" if q.data_status == "unavailable" else "WATCH"
            rows.append(SignalRow(times["jst"], times["et"], q.symbol, q.market, q.data_status, q.actual_price, theo, dev, 0.0 if theo else None, "USDJPY/USDCNH", anchors["XAUUSD"], anchors["XAGUSD"], signal, "phase1_monitor", "none", q.source_status))

        csv_path = Path(self.config["runtime"].get("csv_log", "precious_metals_signal_log.csv"))
        md_path = Path(self.config["runtime"].get("markdown_report", "reports/latest_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_csv(csv_path, rows)
        self._write_markdown(md_path, rows, times)
        return rows, str(csv_path), str(md_path)

    def run_ibkr_smoke(self, preferred_data_type: str = "delayed") -> tuple[list[SmokeQuote], str, str, str]:
        times = self.now_triplet()
        client = IBKRDataClient(self.config["ibkr"])
        connected, conn_status = client.connect()
        if not connected and conn_status.startswith("failed"):
            conn_status = "failed"

        quotes: list[SmokeQuote] = []
        for item in self._symbols():
            q = client.get_quote_snapshot(item, preferred_data_type=preferred_data_type)
            if not connected and q.source_status == "fallback_no_ibkr_connection":
                q.source_status = "fallback_no_ibkr_connection"
                q.data_status = "unavailable"
            quotes.append(q)

        client.disconnect()
        csv_path = Path(self.config["runtime"].get("ibkr_smoke_csv", "ibkr_smoke_log.csv"))
        md_path = Path(self.config["runtime"].get("ibkr_smoke_report", "reports/ibkr_smoke_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_ibkr_smoke_csv(csv_path, quotes, times)
        account_mode = self.config.get("ibkr", {}).get("account_mode", "unknown")
        self._write_ibkr_smoke_report(md_path, quotes, times, conn_status if connected else (conn_status or "fallback_no_ibkr_connection"), account_mode)
        return quotes, str(csv_path), str(md_path), (conn_status if connected else (conn_status or "fallback_no_ibkr_connection"))

    def run_contract_search(self, query: str) -> tuple[list[ContractSearchRow], str, str, str]:
        client = IBKRDataClient(self.config["ibkr"])
        connected, conn_status = client.connect()
        rows, search_status = client.search_contracts(query)
        client.disconnect()
        times = self.now_triplet()
        csv_path = Path("contract_search_results.csv")
        md_path = Path(f"reports/contract_search_{query}.md")
        md_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_contract_search_csv(csv_path, rows, times)
        self._write_contract_search_report(md_path, rows, times, conn_status if connected else conn_status, search_status)
        return rows, str(csv_path), str(md_path), (conn_status if connected else conn_status)

    def _write_csv(self, path: Path, rows: list[SignalRow]) -> None:
        fields = ["timestamp_jst", "timestamp_et", "symbol", "market", "data_status", "actual_price", "theoretical_price", "deviation_pct", "premium_discount", "fx_used", "gold_price", "silver_price", "signal", "reason", "risk_flag", "source_status"]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow(row.__dict__)

    def _write_markdown(self, path: Path, rows: list[SignalRow], times: dict[str, str]) -> None:
        lines = ["# Precious Metals Monitor Report", "", "## 时间", f"- JST: {times['jst']}", f"- CST: {times['cst']}", f"- ET: {times['et']}", "", "## 信号总览", "| Symbol | Market | Data Status | Signal |", "|---|---|---|---|"]
        for r in rows:
            lines.append(f"| {r.symbol} | {r.market} | {r.data_status} | {r.signal} |")
        path.write_text("\n".join(lines), encoding="utf-8")

    def _write_ibkr_smoke_csv(self, path: Path, rows: list[SmokeQuote], times: dict[str, str]) -> None:
        fields = ["timestamp_jst", "timestamp_et", "symbol", "market", "contract_status", "data_status", "market_data_type", "bid", "ask", "last", "close", "volume", "conId", "selected_exchange", "selected_primary_exchange", "selected_local_symbol", "candidate_index", "fallback_price", "fallback_method", "has_valid_price", "source_status", "error_message"]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for r in rows:
                writer.writerow({"timestamp_jst": times["jst"], "timestamp_et": times["et"], "symbol": r.symbol, "market": r.market, "contract_status": r.contract_status, "data_status": r.data_status, "market_data_type": r.market_data_type, "bid": r.bid, "ask": r.ask, "last": r.last, "close": r.close, "volume": r.volume, "conId": r.conId, "selected_exchange": r.selected_exchange, "selected_primary_exchange": r.selected_primary_exchange, "selected_local_symbol": r.selected_local_symbol, "candidate_index": r.candidate_index, "fallback_price": r.fallback_price, "fallback_method": r.fallback_method, "has_valid_price": str(r.has_valid_price).lower(), "source_status": r.source_status, "error_message": r.error_message})

    def _write_ibkr_smoke_report(self, path: Path, rows: list[SmokeQuote], times: dict[str, str], conn_status: str, account_mode: str) -> None:
        unresolved = [r.symbol for r in rows if r.contract_status in {"unqualified", "invalid_config"}]
        unavailable = [r.symbol for r in rows if r.data_status == "unavailable"]
        delayed_only = [r.symbol for r in rows if r.data_status in {"delayed", "delayed_frozen"}]
        manual_cfg = [r.symbol for r in rows if r.contract_status == "needs_manual_contract_config"]
        hist_only = [r.symbol for r in rows if r.source_status == "historical_daily_close_fallback"]
        invalid_price = [r.symbol for r in rows if not r.has_valid_price]
        need_external = [r.symbol for r in rows if r.source_status == "needs_external_data_source_or_manual_contract_config"]
        all_candidates_failed = [r.symbol for r in rows if r.source_status in {"all_contract_candidates_failed", "needs_external_data_source_or_manual_contract_config"}]
        lines = [
            "# IBKR Smoke Report",
            "",
            "## 当前时间",
            f"- JST: {times['jst']}",
            f"- CST: {times['cst']}",
            f"- ET: {times['et']}",
            "",
            "## IBKR 连接状态",
            f"- {conn_status}",
            f"- account_mode: {account_mode}",
            "",
            "## 只读安全声明",
            "- 当前连接为 Live 环境时，本项目仍只执行行情读取，不执行任何交易请求。",
            f"- read_only_required: {str(self.config.get('ibkr', {}).get('read_only_required', False)).lower()}",
            "- trade_execution_enabled: false",
            "",
            "## 标的明细",
            "| symbol | market | contract_status | data_status | market_data_type | bid | ask | last | close | volume | conId | selected_exchange | selected_primary_exchange | selected_local_symbol | candidate_index | fallback_price | fallback_method | has_valid_price | source_status | error_message |",
            "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---:|---:|---|---|---|---|",
        ]
        for r in rows:
            lines.append(f"| {r.symbol} | {r.market} | {r.contract_status} | {r.data_status} | {r.market_data_type} | {r.bid} | {r.ask} | {r.last} | {r.close} | {r.volume} | {r.conId} | {r.selected_exchange} | {r.selected_primary_exchange} | {r.selected_local_symbol} | {r.candidate_index} | {r.fallback_price} | {r.fallback_method} | {str(r.has_valid_price).lower()} | {r.source_status} | {r.error_message} |")
        lines += [
            "",
            "## 问题清单",
            f"- 合约无法解析的标的: {', '.join(unresolved) if unresolved else '无'}",
            f"- 行情不可用的标的: {', '.join(unavailable) if unavailable else '无'}",
            f"- 仅有延迟行情的标的: {', '.join(delayed_only) if delayed_only else '无'}",
            f"- 需要手动补充 IBKR 合约参数的标的: {', '.join(manual_cfg) if manual_cfg else '无'}",
            f"- 合约已识别但仅能使用 historical_daily_close fallback 的标的: {', '.join(hist_only) if hist_only else '无'}",
            f"- has_valid_price=false 的标的: {', '.join(invalid_price) if invalid_price else '无'}",
            f"- 需要外部数据源替代 IBKR 的标的: {', '.join(need_external) if need_external else '无'}",
            f"- 所有候选合约均失败的标的: {', '.join(all_candidates_failed) if all_candidates_failed else '无'}",
            "",
            "本报告仅用于行情接入测试，不构成交易建议，不执行自动交易。",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")

    def _write_contract_search_csv(self, path: Path, rows: list[ContractSearchRow], times: dict[str, str]) -> None:
        fields = ["timestamp_jst", "timestamp_et", "query", "conId", "symbol", "localSymbol", "tradingClass", "secType", "exchange", "primaryExchange", "currency", "longName", "validExchanges", "marketRuleIds", "status"]
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            if f.tell() == 0:
                writer.writeheader()
            for r in rows:
                writer.writerow({"timestamp_jst": times["jst"], "timestamp_et": times["et"], **r.__dict__})

    def _write_contract_search_report(self, path: Path, rows: list[ContractSearchRow], times: dict[str, str], conn_status: str, search_status: str) -> None:
        lines = [
            "# IBKR Contract Search Report",
            "",
            "## 当前时间",
            f"- JST: {times['jst']}",
            f"- CST: {times['cst']}",
            f"- ET: {times['et']}",
            "",
            "## 状态",
            f"- ibkr_connection: {conn_status}",
            f"- search_status: {search_status}",
            "",
            "## 候选合约",
            "| query | conId | symbol | localSymbol | tradingClass | secType | exchange | primaryExchange | currency | longName | validExchanges | marketRuleIds | status |",
            "|---|---:|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for r in rows:
            lines.append(f"| {r.query} | {r.conId} | {r.symbol} | {r.localSymbol} | {r.tradingClass} | {r.secType} | {r.exchange} | {r.primaryExchange} | {r.currency} | {r.longName} | {r.validExchanges} | {r.marketRuleIds} | {r.status} |")
        path.write_text("\n".join(lines), encoding="utf-8")
