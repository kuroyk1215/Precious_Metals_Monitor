from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any, Optional

import csv
import json
import statistics

from src.ibkr_data_client import ContractSearchRow, IBKRDataClient, SmokeQuote
from src.pricing_model import calculate_1540_theoretical_price, calculate_1542_theoretical_price, calculate_518880_theoretical_price
from src.calibration_model import calculate_conversion_factor, summarize_conversion_factors
from src.historical_data_validator import validate_historical_csv, normalize_historical_rows, summarize_data_quality
from src.historical_data_builder import load_source_manifest, build_standard_historical_rows, write_standard_historical_csv, summarize_build
from src.source_adapters import load_source_provider_manifest, summarize_source_providers, write_source_audit_log_csv, build_source_audit_report
from src.ibkr_historical_adapter import build_ibkr_historical_request_plan, validate_ibkr_historical_plan, write_ibkr_historical_plan_csv, write_ibkr_raw_prices_csv, summarize_ibkr_historical_adapter, build_ibkr_historical_fetch_config, validate_ibkr_historical_fetch_config, convert_ibkr_bars_to_raw_rows, write_ibkr_historical_fetch_report
from src.ibkr_historical_fetcher import fetch_ibkr_historical_bars_readonly
from src.historical_quality_gate import run_quality_gate, write_quality_gate_report, append_quality_gate_log
from src.historical_pipeline_check import run_historical_pipeline_check, write_historical_pipeline_check_report, append_historical_pipeline_check_log
from src.upstream_factors import ManualUpstreamFactorProvider, FactorSnapshotRow, build_upstream_factor_snapshot
from src.theoretical_pricing_engine import load_upstream_snapshot, build_theoretical_price_rows, write_theoretical_price_csv, write_theoretical_price_report, TheoreticalPriceRow
from src.deviation_engine import (
    ActualEtfPriceRow,
    DeviationRow,
    build_manual_actual_price_rows,
    load_snapshot_by_symbol,
    build_deviation_rows,
    write_actual_price_csv,
    write_actual_price_report,
    write_deviation_csv,
    write_deviation_report,
)
from src.reference_signal_engine import (
    ReferenceSignalRow,
    build_reference_signal_rows,
    write_reference_signal_csv,
    write_reference_signal_report,
)
from src.daily_trade_plan_engine import (
    DailyTradePlanRow,
    build_daily_trade_plan_rows,
    write_daily_trade_plan_csv,
    write_daily_trade_plan_report,
)
from src.multi_horizon_strategy_engine import (
    MultiHorizonStrategyRow,
    build_multi_horizon_strategy_rows,
    write_multi_horizon_strategy_csv,
    write_multi_horizon_strategy_report,
)
from src.manual_research_pipeline import (
    PipelineStepRow,
    build_pipeline_step_row,
    write_pipeline_summary_csv,
    write_pipeline_summary_report,
)
from src.market_data_source_plan import (
    MarketDataSourcePlanRow,
    build_market_data_source_plan_rows,
    write_market_data_source_plan_csv,
    write_market_data_source_plan_report,
)
from src.manual_market_data_adapter import (
    ManualMarketDataRow,
    build_manual_market_data_template_rows,
    load_manual_market_data_csv,
    normalize_manual_market_data_rows,
    write_manual_market_data_adapter_report,
    write_manual_market_data_snapshot_csv,
)
from src.manual_market_data_integration import (
    IntegratedActualEtfPriceRow,
    IntegratedUpstreamFactorRow,
    ManualMarketDataIntegrationSummaryRow,
    build_integrated_market_data_rows,
    load_manual_market_data_snapshot,
    write_integrated_actual_etf_price_csv,
    write_integrated_upstream_factor_csv,
    write_manual_market_data_integration_report,
    write_manual_market_data_integration_summary_csv,
)
from src.manual_market_data_pipeline import (
    ManualMarketDataPipelineStepRow,
    build_manual_market_data_pipeline_step_row,
    summarize_status,
    write_manual_market_data_pipeline_report,
    write_manual_market_data_pipeline_summary_csv,
)
from src.filled_manual_scenario_validator import (
    FilledManualScenarioValidationRow,
    build_filled_manual_scenario_validation_rows,
    load_csv_rows,
    write_filled_manual_scenario_validation_csv,
    write_filled_manual_scenario_validation_report,
)


def _default_config() -> dict[str, Any]:
    return {
        "ibkr": {"host": "127.0.0.1", "port": 7496, "client_id": 1, "timeout_sec": 5, "readonly": True, "account_mode": "live", "read_only_required": True},
            "runtime": {
                "csv_log": "precious_metals_signal_log.csv",
                "markdown_report": "reports/latest_report.md",
                "ibkr_smoke_csv": "ibkr_smoke_log.csv",
                "ibkr_smoke_report": "reports/ibkr_smoke_report.md",
                "model_calibration_json": "reports/model_calibration.json",
                "model_calibration_report": "reports/model_calibration.md",
                "upstream_factor_snapshot_csv": "upstream_factor_snapshot.csv",
                "upstream_factor_report": "reports/upstream_factor_report.md",
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
    actual_price: Optional[float]
    volume: Optional[float]
    data_status: str
    source_status: str


@dataclass
class SignalRow:
    timestamp_jst: str
    timestamp_et: str
    symbol: str
    market: str
    data_status: str
    actual_price: Optional[float]
    theoretical_price: Optional[float]
    deviation_pct: Optional[float]
    premium_discount: Optional[float]
    fx_used: str
    gold_price: Optional[float]
    silver_price: Optional[float]
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


    def run_upstream_factors(self) -> tuple[list[FactorSnapshotRow], str, str]:
        rows = build_upstream_factor_snapshot(
            tz_cfg=self.config["runtime"]["timezone"],
            provider=ManualUpstreamFactorProvider(),
        )

        csv_path = Path(self.config["runtime"].get("upstream_factor_snapshot_csv", "upstream_factor_snapshot.csv"))
        md_path = Path(self.config["runtime"].get("upstream_factor_report", "reports/upstream_factor_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        self._write_upstream_factors_csv(csv_path, rows)
        self._write_upstream_factors_report(md_path, rows)
        return rows, str(csv_path), str(md_path)

    def run_theoretical_pricing(self, upstream_snapshot_path: Optional[str] = None) -> tuple[list[TheoreticalPriceRow], str, str]:
        snapshot_path = upstream_snapshot_path or self.config["runtime"].get("upstream_factor_snapshot_csv", "upstream_factor_snapshot.csv")
        snapshot = load_upstream_snapshot(snapshot_path)
        conversion_factors = self.config.get("model", {}).get("etf_conversion_factor", {})
        if "518880.SH" not in conversion_factors:
            conversion_factors["518880.SH"] = 0.001
        rows = build_theoretical_price_rows(snapshot, self.config["runtime"]["timezone"], conversion_factors)

        csv_path = Path(self.config["runtime"].get("theoretical_price_snapshot_csv", "theoretical_price_snapshot.csv"))
        md_path = Path(self.config["runtime"].get("theoretical_price_report", "reports/theoretical_price_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        write_theoretical_price_csv(csv_path, rows)
        cst_time = datetime.now(timezone.utc).astimezone(ZoneInfo(self.config["runtime"]["timezone"]["cst"])).isoformat()
        write_theoretical_price_report(md_path, rows, snapshot_path, cst_time)
        return rows, str(csv_path), str(md_path)


    def run_actual_etf_prices(self) -> tuple[list[ActualEtfPriceRow], str, str]:
        rows = build_manual_actual_price_rows(self.config["runtime"]["timezone"])
        csv_path = Path(self.config["runtime"].get("actual_etf_price_snapshot_csv", "actual_etf_price_snapshot.csv"))
        md_path = Path(self.config["runtime"].get("actual_etf_price_report", "reports/actual_etf_price_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        write_actual_price_csv(csv_path, rows)
        write_actual_price_report(md_path, rows)
        return rows, str(csv_path), str(md_path)

    def run_deviation_check(self, theoretical_path: Optional[str] = None, actual_path: Optional[str] = None) -> tuple[list[DeviationRow], str, str]:
        theoretical_input = theoretical_path or self.config["runtime"].get("theoretical_price_snapshot_csv", "theoretical_price_snapshot.csv")
        actual_input = actual_path or self.config["runtime"].get("actual_etf_price_snapshot_csv", "actual_etf_price_snapshot.csv")

        theoretical = load_snapshot_by_symbol(theoretical_input, "etf_symbol")
        actual = load_snapshot_by_symbol(actual_input, "etf_symbol")
        rows = build_deviation_rows(theoretical, actual, self.config["runtime"]["timezone"])

        csv_path = Path(self.config["runtime"].get("deviation_snapshot_csv", "deviation_snapshot.csv"))
        md_path = Path(self.config["runtime"].get("deviation_report", "reports/deviation_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        write_deviation_csv(csv_path, rows)
        write_deviation_report(md_path, rows, theoretical_input, actual_input)
        return rows, str(csv_path), str(md_path)

    def run_reference_signals(self, deviation_path: Optional[str] = None) -> tuple[list[ReferenceSignalRow], str, str]:
        deviation_input = deviation_path or self.config["runtime"].get("deviation_snapshot_csv", "deviation_snapshot.csv")
        deviation = load_snapshot_by_symbol(deviation_input, "etf_symbol")
        rows = build_reference_signal_rows(deviation, self.config["runtime"]["timezone"])

        csv_path = Path(self.config["runtime"].get("reference_signal_snapshot_csv", "reference_signal_snapshot.csv"))
        md_path = Path(self.config["runtime"].get("reference_signal_report", "reports/reference_signal_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        write_reference_signal_csv(csv_path, rows)
        write_reference_signal_report(md_path, rows, deviation_input)
        return rows, str(csv_path), str(md_path)

    def run_daily_trade_plan(self, reference_path: Optional[str] = None) -> tuple[list[DailyTradePlanRow], str, str]:
        reference_input = reference_path or self.config["runtime"].get("reference_signal_snapshot_csv", "reference_signal_snapshot.csv")
        reference = load_snapshot_by_symbol(reference_input, "etf_symbol")
        rows = build_daily_trade_plan_rows(reference, self.config["runtime"]["timezone"])

        csv_path = Path(self.config["runtime"].get("daily_trade_plan_snapshot_csv", "daily_trade_plan_snapshot.csv"))
        md_path = Path(self.config["runtime"].get("daily_trade_plan_report", "reports/daily_trade_plan_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        write_daily_trade_plan_csv(csv_path, rows)
        write_daily_trade_plan_report(md_path, rows, reference_input)
        return rows, str(csv_path), str(md_path)

    def run_strategy_plan(self, daily_plan_path: Optional[str] = None) -> tuple[list[MultiHorizonStrategyRow], str, str]:
        daily_plan_input = daily_plan_path or self.config["runtime"].get("daily_trade_plan_snapshot_csv", "daily_trade_plan_snapshot.csv")
        daily_plan = load_snapshot_by_symbol(daily_plan_input, "etf_symbol")
        rows = build_multi_horizon_strategy_rows(daily_plan, self.config["runtime"]["timezone"])

        csv_path = Path(self.config["runtime"].get("multi_horizon_strategy_snapshot_csv", "multi_horizon_strategy_snapshot.csv"))
        md_path = Path(self.config["runtime"].get("multi_horizon_strategy_report", "reports/multi_horizon_strategy_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        write_multi_horizon_strategy_csv(csv_path, rows)
        write_multi_horizon_strategy_report(md_path, rows, daily_plan_input)
        return rows, str(csv_path), str(md_path)

    def run_manual_research_pipeline(self) -> tuple[list[PipelineStepRow], str, str]:
        tz_cfg = self.config["runtime"]["timezone"]
        summary_rows: list[PipelineStepRow] = []

        upstream_rows, upstream_csv, upstream_report = self.run_upstream_factors()
        upstream_statuses = sorted({r.source_status for r in upstream_rows})
        upstream_status = "ok" if upstream_statuses == ["ok"] else ("unavailable" if upstream_statuses == ["unavailable"] else "partial")
        summary_rows.append(build_pipeline_step_row(1, "Phase 5B", "upstream_factors", upstream_status, upstream_csv, upstream_report, len(upstream_rows), tz_cfg))

        theoretical_rows, theoretical_csv, theoretical_report = self.run_theoretical_pricing(upstream_csv)
        theoretical_statuses = sorted({r.pricing_status for r in theoretical_rows})
        theoretical_status = "ok" if theoretical_statuses == ["ok"] else ("unavailable" if theoretical_statuses == ["unavailable"] else "partial")
        summary_rows.append(build_pipeline_step_row(2, "Phase 5C", "theoretical_pricing", theoretical_status, theoretical_csv, theoretical_report, len(theoretical_rows), tz_cfg))

        actual_rows, actual_csv, actual_report = self.run_actual_etf_prices()
        summary_rows.append(build_pipeline_step_row(3, "Phase 5D", "actual_etf_prices", "manual_mock_only", actual_csv, actual_report, len(actual_rows), tz_cfg))

        deviation_rows, deviation_csv, deviation_report = self.run_deviation_check(theoretical_csv, actual_csv)
        deviation_statuses = sorted({r.deviation_status for r in deviation_rows})
        deviation_status = "ok" if deviation_statuses == ["ok"] else ("unavailable" if deviation_statuses == ["unavailable"] else "partial")
        summary_rows.append(build_pipeline_step_row(4, "Phase 5D", "deviation_check", deviation_status, deviation_csv, deviation_report, len(deviation_rows), tz_cfg))

        reference_rows, reference_csv, reference_report = self.run_reference_signals(deviation_csv)
        summary_rows.append(build_pipeline_step_row(5, "Phase 5E", "reference_signals", "ok", reference_csv, reference_report, len(reference_rows), tz_cfg))

        daily_rows, daily_csv, daily_report = self.run_daily_trade_plan(reference_csv)
        summary_rows.append(build_pipeline_step_row(6, "Phase 5F", "daily_trade_plan", "ok", daily_csv, daily_report, len(daily_rows), tz_cfg))

        strategy_rows, strategy_csv, strategy_report = self.run_strategy_plan(daily_csv)
        summary_rows.append(build_pipeline_step_row(7, "Phase 5G", "strategy_plan", "ok", strategy_csv, strategy_report, len(strategy_rows), tz_cfg))

        csv_path = Path(self.config["runtime"].get("manual_research_pipeline_summary_csv", "manual_research_pipeline_summary.csv"))
        md_path = Path(self.config["runtime"].get("manual_research_pipeline_report", "reports/manual_research_pipeline_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        write_pipeline_summary_csv(csv_path, summary_rows)
        write_pipeline_summary_report(md_path, summary_rows)
        return summary_rows, str(csv_path), str(md_path)

    def run_market_data_source_plan(self) -> tuple[list[MarketDataSourcePlanRow], str, str]:
        rows = build_market_data_source_plan_rows(self.config["runtime"]["timezone"])
        csv_path = Path(self.config["runtime"].get("market_data_source_plan_csv", "market_data_source_plan.csv"))
        md_path = Path(self.config["runtime"].get("market_data_source_plan_report", "reports/market_data_source_plan_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        write_market_data_source_plan_csv(csv_path, rows)
        write_market_data_source_plan_report(md_path, rows)
        return rows, str(csv_path), str(md_path)

    def run_manual_market_data_adapter(self, input_path: Optional[str] = None) -> tuple[list[ManualMarketDataRow], str, str]:
        default_input = self.config["runtime"].get("manual_market_data_template_csv", "data/manual_market_data_template.csv")
        manual_input = input_path or default_input
        input_file = Path(manual_input)
        if input_file.exists():
            raw_rows, missing_fields = load_manual_market_data_csv(str(input_file))
            rows = normalize_manual_market_data_rows(raw_rows, missing_fields, self.config["runtime"]["timezone"])
        else:
            rows = build_manual_market_data_template_rows(self.config["runtime"]["timezone"])

        csv_path = Path(self.config["runtime"].get("manual_market_data_snapshot_csv", "manual_market_data_snapshot.csv"))
        md_path = Path(self.config["runtime"].get("manual_market_data_adapter_report", "reports/manual_market_data_adapter_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        write_manual_market_data_snapshot_csv(csv_path, rows)
        write_manual_market_data_adapter_report(md_path, rows, str(input_file))
        return rows, str(csv_path), str(md_path)

    def run_integrate_manual_market_data(self, input_path: Optional[str] = None) -> tuple[list[IntegratedUpstreamFactorRow], list[IntegratedActualEtfPriceRow], list[ManualMarketDataIntegrationSummaryRow], str, str, str, str]:
        manual_input = input_path or self.config["runtime"].get("manual_market_data_snapshot_csv", "manual_market_data_snapshot.csv")
        input_file = Path(manual_input)
        if input_file.exists():
            snapshot = load_manual_market_data_snapshot(str(input_file))
        else:
            snapshot = {}
        upstream_rows, actual_rows, summary_rows = build_integrated_market_data_rows(snapshot, self.config["runtime"]["timezone"])

        upstream_csv = Path(self.config["runtime"].get("manual_upstream_factor_snapshot_csv", "manual_upstream_factor_snapshot.csv"))
        actual_csv = Path(self.config["runtime"].get("manual_actual_etf_price_snapshot_csv", "manual_actual_etf_price_snapshot.csv"))
        summary_csv = Path(self.config["runtime"].get("manual_market_data_integration_summary_csv", "manual_market_data_integration_summary.csv"))
        report_md = Path(self.config["runtime"].get("manual_market_data_integration_report", "reports/manual_market_data_integration_report.md"))
        upstream_csv.parent.mkdir(parents=True, exist_ok=True)
        actual_csv.parent.mkdir(parents=True, exist_ok=True)
        summary_csv.parent.mkdir(parents=True, exist_ok=True)
        report_md.parent.mkdir(parents=True, exist_ok=True)

        write_integrated_upstream_factor_csv(upstream_csv, upstream_rows)
        write_integrated_actual_etf_price_csv(actual_csv, actual_rows)
        write_manual_market_data_integration_summary_csv(summary_csv, summary_rows)
        write_manual_market_data_integration_report(report_md, summary_rows, str(input_file), str(upstream_csv), str(actual_csv))
        return upstream_rows, actual_rows, summary_rows, str(upstream_csv), str(actual_csv), str(summary_csv), str(report_md)

    def run_manual_market_data_pipeline(self, input_path: Optional[str] = None) -> tuple[list[ManualMarketDataPipelineStepRow], str, str]:
        tz_cfg = self.config["runtime"]["timezone"]
        input_csv = input_path or self.config["runtime"].get("manual_market_data_template_csv", "data/manual_market_data_template.csv")
        summary_rows: list[ManualMarketDataPipelineStepRow] = []

        adapter_rows, adapter_csv, adapter_report = self.run_manual_market_data_adapter(input_csv)
        adapter_status = summarize_status([r.normalized_status for r in adapter_rows])
        summary_rows.append(build_manual_market_data_pipeline_step_row(1, "Phase 6B", "manual_market_data_adapter", adapter_status, adapter_csv, adapter_report, len(adapter_rows), tz_cfg))

        upstream_rows, actual_rows, integration_rows, upstream_csv, actual_csv, integration_summary_csv, integration_report = self.run_integrate_manual_market_data(adapter_csv)
        integration_status = summarize_status([r.output_status for r in integration_rows])
        summary_rows.append(build_manual_market_data_pipeline_step_row(2, "Phase 6C", "manual_market_data_integration", integration_status, integration_summary_csv, integration_report, len(integration_rows), tz_cfg, notes=f"upstream_csv={upstream_csv}; actual_csv={actual_csv}"))

        theoretical_rows, theoretical_csv, theoretical_report = self.run_theoretical_pricing(upstream_csv)
        theoretical_status = summarize_status([r.pricing_status for r in theoretical_rows])
        summary_rows.append(build_manual_market_data_pipeline_step_row(3, "Phase 5C", "theoretical_pricing", theoretical_status, theoretical_csv, theoretical_report, len(theoretical_rows), tz_cfg))

        deviation_rows, deviation_csv, deviation_report = self.run_deviation_check(theoretical_csv, actual_csv)
        deviation_status = summarize_status([r.deviation_status for r in deviation_rows])
        summary_rows.append(build_manual_market_data_pipeline_step_row(4, "Phase 5D", "deviation_check", deviation_status, deviation_csv, deviation_report, len(deviation_rows), tz_cfg))

        reference_rows, reference_csv, reference_report = self.run_reference_signals(deviation_csv)
        reference_status = summarize_status([r.reference_label for r in reference_rows])
        summary_rows.append(build_manual_market_data_pipeline_step_row(5, "Phase 5E", "reference_signals", reference_status, reference_csv, reference_report, len(reference_rows), tz_cfg))

        daily_rows, daily_csv, daily_report = self.run_daily_trade_plan(reference_csv)
        daily_status = summarize_status([r.plan_label for r in daily_rows])
        summary_rows.append(build_manual_market_data_pipeline_step_row(6, "Phase 5F", "daily_trade_plan", daily_status, daily_csv, daily_report, len(daily_rows), tz_cfg))

        strategy_rows, strategy_csv, strategy_report = self.run_strategy_plan(daily_csv)
        strategy_status = summarize_status([r.strategy_label for r in strategy_rows])
        summary_rows.append(build_manual_market_data_pipeline_step_row(7, "Phase 5G", "strategy_plan", strategy_status, strategy_csv, strategy_report, len(strategy_rows), tz_cfg))

        csv_path = Path(self.config["runtime"].get("manual_market_data_pipeline_summary_csv", "manual_market_data_pipeline_summary.csv"))
        md_path = Path(self.config["runtime"].get("manual_market_data_pipeline_report", "reports/manual_market_data_pipeline_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        write_manual_market_data_pipeline_summary_csv(csv_path, summary_rows)
        write_manual_market_data_pipeline_report(md_path, summary_rows, input_csv)
        return summary_rows, str(csv_path), str(md_path)

    def run_validate_filled_manual_scenario(self, input_path: Optional[str] = None) -> tuple[list[FilledManualScenarioValidationRow], str, str]:
        input_csv = input_path or self.config["runtime"].get("manual_market_data_sample_valid_csv", "data/manual_market_data_sample_valid.csv")
        pipeline_rows, _, _ = self.run_manual_market_data_pipeline(input_csv)

        deviation_path = self.config["runtime"].get("deviation_snapshot_csv", "deviation_snapshot.csv")
        reference_path = self.config["runtime"].get("reference_signal_snapshot_csv", "reference_signal_snapshot.csv")
        daily_path = self.config["runtime"].get("daily_trade_plan_snapshot_csv", "daily_trade_plan_snapshot.csv")
        strategy_path = self.config["runtime"].get("multi_horizon_strategy_snapshot_csv", "multi_horizon_strategy_snapshot.csv")

        deviation_rows = load_csv_rows(deviation_path) if Path(deviation_path).exists() else []
        reference_rows = load_csv_rows(reference_path) if Path(reference_path).exists() else []
        daily_rows = load_csv_rows(daily_path) if Path(daily_path).exists() else []
        strategy_rows = load_csv_rows(strategy_path) if Path(strategy_path).exists() else []

        rows = build_filled_manual_scenario_validation_rows(
            input_csv,
            pipeline_rows,
            deviation_rows,
            reference_rows,
            daily_rows,
            strategy_rows,
            self.config["runtime"]["timezone"],
        )

        csv_path = Path(self.config["runtime"].get("filled_manual_scenario_validation_csv", "filled_manual_scenario_validation.csv"))
        md_path = Path(self.config["runtime"].get("filled_manual_scenario_validation_report", "reports/filled_manual_scenario_validation_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        write_filled_manual_scenario_validation_csv(csv_path, rows)
        write_filled_manual_scenario_validation_report(md_path, rows, input_csv)
        return rows, str(csv_path), str(md_path)

    def _write_upstream_factors_csv(self, path: Path, rows: list[FactorSnapshotRow]) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["factor", "value", "currency", "unit", "source", "source_status", "timestamp_jst", "timestamp_et", "warning_flags", "notes"])
            for r in rows:
                writer.writerow([r.factor, r.value, r.currency, r.unit, r.source, r.source_status, r.timestamp_jst, r.timestamp_et, r.warning_flags, r.notes])

    def _write_upstream_factors_report(self, path: Path, rows: list[FactorSnapshotRow]) -> None:
        unavailable = [r.factor for r in rows if r.source_status == "unavailable"]
        warning_flags = sorted({r.warning_flags for r in rows if r.warning_flags and r.warning_flags != "none"})
        status = "ok"
        if unavailable and len(unavailable) < len(rows):
            status = "partial"
        elif len(unavailable) == len(rows):
            status = "unavailable"

        current_jst = rows[0].timestamp_jst if rows else "n/a"
        current_et = rows[0].timestamp_et if rows else "n/a"
        current_cst = datetime.now(timezone.utc).astimezone(ZoneInfo(self.config["runtime"]["timezone"]["cst"])).isoformat()

        lines = [
            "# Upstream Factor Monitor Report",
            "",
            f"- overall_status: {status}",
            f"- current_time_jst: {current_jst}",
            f"- current_time_cst: {current_cst}",
            f"- current_time_et: {current_et}",
            "",
            "## Factors",
            "",
            "| factor | value | currency | unit | source | source_status | warning_flags | notes |",
            "|---|---:|---|---|---|---|---|---|",
        ]
        for r in rows:
            lines.append(f"| {r.factor} | {r.value} | {r.currency} | {r.unit} | {r.source} | {r.source_status} | {r.warning_flags} | {r.notes} |")

        lines.extend([
            "",
            "## Unavailable Factors",
            "",
            (", ".join(unavailable) if unavailable else "none"),
            "",
            "## Warning Flags",
            "",
            ("; ".join(warning_flags) if warning_flags else "none"),
            "",
            "## Next Step Note",
            "",
            "These upstream factors are intended for future theoretical pricing inputs only in a later phase.",
            "",
            "## Safety Statement",
            "",
            "- research-only",
            "- no trading",
            "- no order",
            "- no auto calibration",
            "- no auto pipeline chaining",
        ])
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def run_model_calibration(self, force_mock: bool = True, conversion_input_path: str = "data/conversion_factor_samples.yaml") -> tuple[list[dict[str, Any]], str, str]:
        anchors = {"XAUUSD": 2350.0, "XAGUSD": 28.5, "USDJPY": 155.0, "USDCNH": 7.2}
        quotes = self._build_quotes(use_mock=force_mock, ibkr_connected=False)
        historical_cfg = self.config.get("model", {}).get("historical_premium_discount_pct", {})
        conversion_cfg = self.config.get("model", {}).get("etf_conversion_factor", {})
        sh_premium_pct = float(self.config.get("model", {}).get("shanghai_gold_premium_pct", 0.0))
        calibrated_rows: list[dict[str, Any]] = []

        for q in quotes:
            theo_base = None
            if q.symbol == "518880.SH":
                theo_base = anchors["XAUUSD"] * anchors["USDCNH"] * 0.001
                theo_base *= (1 + sh_premium_pct / 100)
            elif q.symbol == "1540.T":
                theo_base = anchors["XAUUSD"] * anchors["USDJPY"] * float(conversion_cfg.get(q.symbol, 0.1))
            elif q.symbol == "1542.T":
                theo_base = anchors["XAGUSD"] * anchors["USDJPY"] * float(conversion_cfg.get(q.symbol, 0.1))

            old_premium_pct = float(historical_cfg.get(q.symbol, 0.0))
            calibrated_premium_pct = None
            if theo_base and q.actual_price:
                calibrated_premium_pct = ((q.actual_price / theo_base) - 1) * 100
            calibrated_rows.append(
                {
                    "symbol": q.symbol,
                    "market": q.market,
                    "data_status": q.data_status,
                    "actual_price": q.actual_price,
                    "theoretical_base_price": round(theo_base, 6) if theo_base else None,
                    "old_historical_premium_pct": old_premium_pct,
                    "calibrated_historical_premium_pct": round(calibrated_premium_pct, 6) if calibrated_premium_pct is not None else None,
                    "premium_shift_pct": round(calibrated_premium_pct - old_premium_pct, 6) if calibrated_premium_pct is not None else None,
                }
            )

        conversion_rows, conversion_summary = self._calibrate_conversion_factors(conversion_input_path)

        json_path = Path(self.config["runtime"].get("model_calibration_json", "reports/model_calibration.json"))
        md_path = Path(self.config["runtime"].get("model_calibration_report", "reports/model_calibration.md"))
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps({"anchors": anchors, "rows": calibrated_rows, "conversion_factor_calibration": {"samples": conversion_rows, "summary": conversion_summary}}, ensure_ascii=False, indent=2), encoding="utf-8")
        self._write_model_calibration_report(md_path, calibrated_rows, anchors, conversion_summary)
        return calibrated_rows, str(json_path), str(md_path)

    def _calibrate_conversion_factors(self, conversion_input_path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        data = self._load_yaml(conversion_input_path, kind="config")
        symbols = data.get("symbols", {}) if isinstance(data, dict) else {}
        mad_threshold = float(data.get("outlier_mad_threshold", 3.5)) if isinstance(data, dict) else 3.5
        sample_rows: list[dict[str, Any]] = []
        summary_rows: list[dict[str, Any]] = []

        for symbol, payload in symbols.items():
            premium_pct = float(payload.get("premium_discount_pct", 0.0))
            records = payload.get("records", [])
            factors: list[float] = []
            for idx, record in enumerate(records):
                actual_price = record.get("actual_price")
                metal_price = record.get("metal_price")
                fx_rate = record.get("fx_rate")
                if actual_price is None or metal_price is None or fx_rate in (None, 0) or metal_price == 0:
                    sample_rows.append({"symbol": symbol, "index": idx, "status": "invalid_sample", "raw_conversion_factor": None})
                    continue
                denominator = float(metal_price) * float(fx_rate) * (1 + premium_pct / 100)
                if denominator == 0:
                    sample_rows.append({"symbol": symbol, "index": idx, "status": "invalid_denominator", "raw_conversion_factor": None})
                    continue
                cf = float(actual_price) / denominator
                factors.append(cf)
                sample_rows.append({"symbol": symbol, "index": idx, "status": "ok", "raw_conversion_factor": round(cf, 10)})

            if not factors:
                summary_rows.append({"symbol": symbol, "sample_count": 0, "inlier_count": 0, "recommended_conversion_factor": None, "median_conversion_factor": None, "stdev_conversion_factor": None, "status": "insufficient_samples"})
                continue

            median_cf = statistics.median(factors)
            deviations = [abs(x - median_cf) for x in factors]
            mad = statistics.median(deviations) if deviations else 0.0
            if mad == 0:
                inliers = factors
            else:
                inliers = [x for x in factors if abs(x - median_cf) / mad <= mad_threshold]
            recommended = statistics.median(inliers) if inliers else median_cf
            stdev = statistics.pstdev(inliers) if len(inliers) > 1 else 0.0
            summary_rows.append({
                "symbol": symbol,
                "sample_count": len(factors),
                "inlier_count": len(inliers),
                "recommended_conversion_factor": round(recommended, 10),
                "median_conversion_factor": round(median_cf, 10),
                "stdev_conversion_factor": round(stdev, 10),
                "status": "ok" if inliers else "all_outliers",
            })
        return sample_rows, summary_rows



    def run_validate_history(self, csv_path: str) -> tuple[list[dict[str, Any]], str, str, str]:
        times = self.now_triplet()
        result = validate_historical_csv(csv_path)
        normalized = normalize_historical_rows(result["valid_rows"])
        quality = summarize_data_quality(normalized, result["invalid_rows"])

        validated_csv = Path("data/validated_historical_data.csv")
        report_md = Path("reports/historical_data_validation_report.md")
        log_csv = Path("historical_data_validation_log.csv")
        validated_csv.parent.mkdir(parents=True, exist_ok=True)
        report_md.parent.mkdir(parents=True, exist_ok=True)

        self._write_validated_history_csv(validated_csv, normalized)
        self._write_history_validation_log_csv(log_csv, quality, times)
        self._write_history_validation_report(report_md, quality, result["invalid_rows"], times)
        return quality, str(validated_csv), str(report_md), str(log_csv)

    def run_build_history(self, manifest_path: str) -> tuple[list[dict[str, Any]], str, str, str]:
        times = self.now_triplet()
        manifest = load_source_manifest(manifest_path)
        candidate_rows = build_standard_historical_rows(manifest)
        summary_rows = summarize_build(candidate_rows)

        candidate_csv = Path("data/real_historical_candidate.csv")
        report_md = Path("reports/historical_data_build_report.md")
        log_csv = Path("historical_data_build_log.csv")
        report_md.parent.mkdir(parents=True, exist_ok=True)

        write_standard_historical_csv(candidate_rows, str(candidate_csv))
        self._write_history_build_log_csv(log_csv, summary_rows, times)
        self._write_history_build_report(report_md, summary_rows, times)
        return summary_rows, str(candidate_csv), str(report_md), str(log_csv)

    def run_source_audit(self, manifest_path: str) -> tuple[list[dict[str, Any]], str, str]:
        times = self.now_triplet()
        providers = load_source_provider_manifest(manifest_path)
        summary_rows = summarize_source_providers(providers)

        report_md = Path("reports/source_audit_report.md")
        log_csv = Path("source_audit_log.csv")
        report_md.parent.mkdir(parents=True, exist_ok=True)
        write_source_audit_log_csv(summary_rows, str(log_csv), times)
        build_source_audit_report(summary_rows, str(report_md), times)
        return summary_rows, str(report_md), str(log_csv)


    def run_ibkr_historical_plan(self) -> tuple[list[dict[str, Any]], str, str, str]:
        times = self.now_triplet()
        symbols = ["1540.T", "1542.T"]
        plans = build_ibkr_historical_request_plan(symbols=symbols)
        validated_plans = [validate_ibkr_historical_plan(plan) for plan in plans]
        summary_rows = summarize_ibkr_historical_adapter(validated_plans)

        plan_csv = Path("reports/ibkr_historical_request_plan.csv")
        report_md = Path("reports/ibkr_historical_adapter_report.md")
        raw_csv = Path("data/raw/ibkr_jp_etf_prices_candidate.csv")
        report_md.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_historical_plan_csv(validated_plans, str(plan_csv))
        write_ibkr_raw_prices_csv([], str(raw_csv))
        self._write_ibkr_historical_adapter_report(report_md, summary_rows, times)
        return summary_rows, str(plan_csv), str(report_md), str(raw_csv)


    def run_ibkr_historical_fetch(self, execute: bool = False) -> tuple[list[dict[str, Any]], str, str, str]:
        times = self.now_triplet()
        config = build_ibkr_historical_fetch_config(execute=execute)
        config["explicit_user_confirmed"] = bool(execute)
        validated = validate_ibkr_historical_fetch_config(config)

        client = None
        results = []
        if execute and validated.get("validation_status") == "valid":
            client = IBKRDataClient(self.config["ibkr"])
            connected = False
            conn_status = "ibkr_not_connected"
            try:
                connected, conn_status = client.connect()
                if connected:
                    results = fetch_ibkr_historical_bars_readonly(validated, ibkr_client=client)
                else:
                    results = [
                        {
                            "symbol": symbol,
                            "rows": [],
                            "fetch_status": "error",
                            "warning_flags": f"fetch_error:{conn_status}",
                        }
                        for symbol in validated.get("symbols", [])
                    ]
            finally:
                client.disconnect()
        else:
            results = fetch_ibkr_historical_bars_readonly(validated, ibkr_client=client)
        raw_rows: list[dict[str, Any]] = []
        summary_rows: list[dict[str, Any]] = []
        for result in results:
            symbol = result.symbol if hasattr(result, "symbol") else result.get("symbol", "")
            rows = result.rows if hasattr(result, "rows") else result.get("rows", [])
            fetch_status = result.fetch_status if hasattr(result, "fetch_status") else result.get("fetch_status", "error")
            warning_flags = result.warning_flags if hasattr(result, "warning_flags") else result.get("warning_flags", "")

            converted = convert_ibkr_bars_to_raw_rows(symbol, "JPY", rows)
            raw_rows.extend(converted)
            summary_rows.append({
                "symbol": symbol,
                "row_count": len(converted),
                "fetch_status": fetch_status,
                "warning_flags": warning_flags,
            })

        raw_csv = Path("data/raw/ibkr_jp_etf_prices_candidate.csv")
        report_md = Path("reports/ibkr_historical_fetch_report.md")
        log_csv = Path("ibkr_historical_fetch_log.csv")
        write_ibkr_raw_prices_csv(raw_rows, str(raw_csv))
        write_ibkr_historical_fetch_report(str(report_md), summary_rows, validated, times)
        self._write_ibkr_historical_fetch_log_csv(log_csv, summary_rows, times, validated.get("mode", "dry_run"))
        return summary_rows, str(raw_csv), str(report_md), str(log_csv)


    def run_historical_quality_gate(self, csv_path: str) -> tuple[dict[str, Any], str, str]:
        times = self.now_triplet()
        result = run_quality_gate(csv_path)
        report_md = Path("reports/historical_quality_gate_report.md")
        log_csv = Path("historical_quality_gate_log.csv")
        write_quality_gate_report(str(report_md), csv_path, result, times["jst"])
        append_quality_gate_log(str(log_csv), csv_path, result, times["jst"])
        return {
            "status": result.status,
            "total_rows": result.total_rows,
            "symbols": result.symbols,
            "start_date": result.start_date,
            "end_date": result.end_date,
            "warning_flags": result.warning_flags,
            "fail_reasons": result.fail_reasons,
        }, str(report_md), str(log_csv)


    def run_historical_pipeline_check(self) -> tuple[dict[str, Any], str, str]:
        result = run_historical_pipeline_check()
        report_md = Path("reports/historical_pipeline_check_report.md")
        log_csv = Path("historical_pipeline_check_log.csv")
        write_historical_pipeline_check_report(str(report_md), result)
        append_historical_pipeline_check_log(str(log_csv), result)
        return {
            "status": result.status,
            "current_blocking_step": result.current_blocking_step,
            "warning_flags": result.warning_flags,
            "notes": result.notes,
        }, str(report_md), str(log_csv)

    def run_conversion_factor_calibration_csv(self, calibration_csv_path: str) -> tuple[list[dict[str, Any]], str, str]:
        times = self.now_triplet()
        input_rows: list[dict[str, Any]] = []
        with open(calibration_csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                input_rows.append(row)

        implied_rows = [calculate_conversion_factor(row) for row in input_rows]
        summary_rows = summarize_conversion_factors(implied_rows)

        csv_path = Path("conversion_factor_calibration_log.csv")
        md_path = Path("reports/conversion_factor_calibration_report.md")
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_conversion_factor_calibration_csv(csv_path, summary_rows, times)
        self._write_conversion_factor_calibration_report(md_path, summary_rows, times)
        return summary_rows, str(csv_path), str(md_path)

    def run_pricing_mock(self, pricing_input_path: str = "data/mock_pricing_inputs.yaml") -> tuple[list[dict[str, Any]], str, str]:
        inputs = self._load_yaml(pricing_input_path, kind="config")
        symbols = inputs.get("symbols", {})
        xau = float(inputs.get("gold_price_usd_per_oz", 0.0))
        xag = float(inputs.get("silver_price_usd_per_oz", 0.0))
        usd_jpy = float(inputs.get("usd_jpy", 0.0))
        usd_cnh = float(inputs.get("usd_cnh", 0.0))
        rows = [
            calculate_1540_theoretical_price(**symbols.get("1540.T", {}), xau_usd=xau, usd_jpy=usd_jpy),
            calculate_1542_theoretical_price(**symbols.get("1542.T", {}), xag_usd=xag, usd_jpy=usd_jpy),
            calculate_518880_theoretical_price(**symbols.get("518880.SH", {}), xau_usd=xau, usd_cnh=usd_cnh),
        ]
        times = self.now_triplet()
        csv_path = Path("pricing_model_log.csv")
        md_path = Path("reports/pricing_model_report.md")
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_pricing_mock_csv(csv_path, rows, times)
        self._write_pricing_mock_report(md_path, rows, times)
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
        unresolved = [r.symbol for r in rows if r.contract_status in {"unqualified", "invalid_config"} and r.source_status != "needs_external_data_source"]
        unavailable = [r.symbol for r in rows if r.data_status == "unavailable"]
        delayed_only = [r.symbol for r in rows if r.data_status in {"delayed", "delayed_frozen"}]
        manual_cfg = [r.symbol for r in rows if r.contract_status == "needs_manual_contract_config"]
        hist_only = [r.symbol for r in rows if r.source_status == "historical_daily_close_fallback"]
        invalid_price = [r.symbol for r in rows if not r.has_valid_price]
        need_external = [r.symbol for r in rows if r.source_status == "needs_external_data_source"]
        all_candidates_failed = [r.symbol for r in rows if r.source_status == "all_contract_candidates_failed"]
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

    def _write_model_calibration_report(self, path: Path, rows: list[dict[str, Any]], anchors: dict[str, float], conversion_summary: list[dict[str, Any]]) -> None:
        lines = [
            "# Phase-3 理论价格模型校准报告",
            "",
            "## 锚点价格（示例）",
            f"- XAUUSD: {anchors['XAUUSD']}",
            f"- XAGUSD: {anchors['XAGUSD']}",
            f"- USDJPY: {anchors['USDJPY']}",
            f"- USDCNH: {anchors['USDCNH']}",
            "",
            "## 校准结果",
            "| symbol | market | data_status | actual_price | theoretical_base_price | old_historical_premium_pct | calibrated_historical_premium_pct | premium_shift_pct |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
        for row in rows:
            lines.append(
                f"| {row['symbol']} | {row['market']} | {row['data_status']} | {row['actual_price']} | {row['theoretical_base_price']} | {row['old_historical_premium_pct']} | {row['calibrated_historical_premium_pct']} | {row['premium_shift_pct']} |"
            )
        lines += [
            "",
            "## conversion_factor 校准建议（Phase-3B）",
            "| symbol | sample_count | inlier_count | recommended_conversion_factor | median_conversion_factor | stdev_conversion_factor | status |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
        for row in conversion_summary:
            lines.append(
                f"| {row['symbol']} | {row['sample_count']} | {row['inlier_count']} | {row['recommended_conversion_factor']} | {row['median_conversion_factor']} | {row['stdev_conversion_factor']} | {row['status']} |"
            )
        lines += [
            "",
            "说明：该阶段仅输出模型参数建议值，不触发任何交易动作。",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")



    def _write_validated_history_csv(self, path: Path, rows: list[dict[str, Any]]) -> None:
        fields = ["date", "symbol", "actual_price", "metal_price_used", "fx_used", "premium_discount_pct", "data_source", "notes"]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    def _write_history_build_log_csv(self, path: Path, rows: list[dict[str, Any]], times: dict[str, str]) -> None:
        fields = ["timestamp_jst", "timestamp_et", "symbol", "total_rows", "missing_metal_price_count", "missing_fx_count", "date_start", "date_end", "build_status", "warning_flags"]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({"timestamp_jst": times["jst"], "timestamp_et": times["et"], **row})

    def _write_history_build_report(self, path: Path, rows: list[dict[str, Any]], times: dict[str, str]) -> None:
        lines = [
            "# Historical Data Build Report",
            "",
            "## 当前时间",
            f"- JST: {times['jst']}",
            f"- CST: {times['cst']}",
            f"- ET: {times['et']}",
            "",
            "## 模型状态",
            "- historical_data_build",
            "- research_only",
            "- no_auto_trade",
            "",
            "## 数据源说明",
            "- 当前 raw sample 不是最终真实市场数据。",
            "- Phase 4A 只负责 raw CSV 合并。",
            "- 真实 API / 授权数据源接入放在 Phase 4B。",
            "",
            "## Build Summary",
            "| symbol | total_rows | missing_metal_price_count | missing_fx_count | date_start | date_end | build_status | warning_flags |",
            "|---|---:|---:|---:|---|---|---|---|",
        ]
        for r in rows:
            lines.append(f"| {r['symbol']} | {r['total_rows']} | {r['missing_metal_price_count']} | {r['missing_fx_count']} | {r['date_start']} | {r['date_end']} | {r['build_status']} | {r['warning_flags']} |")
        path.write_text("\n".join(lines), encoding="utf-8")

    def _write_history_validation_log_csv(self, path: Path, rows: list[dict[str, Any]], times: dict[str, str]) -> None:
        fields = ["timestamp_jst", "timestamp_et", "symbol", "total_rows", "valid_rows", "invalid_rows", "date_start", "date_end", "missing_actual_price_count", "missing_metal_price_count", "missing_fx_count", "duplicate_date_count", "data_quality_score", "validation_status", "warning_flags"]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({"timestamp_jst": times["jst"], "timestamp_et": times["et"], **row})

    def _write_history_validation_report(self, path: Path, quality_rows: list[dict[str, Any]], invalid_rows: list[dict[str, Any]], times: dict[str, str]) -> None:
        lines = [
            "# Historical Data Validation Report",
            "",
            "## 当前时间",
            f"- JST: {times['jst']}",
            f"- CST: {times['cst']}",
            f"- ET: {times['et']}",
            "",
            "## 模型状态",
            "- historical_data_validation",
            "- research_only",
            "- no_auto_trade",
            "",
            "## 数据质量汇总",
            "| symbol | total_rows | valid_rows | invalid_rows | date_start | date_end | missing_actual_price_count | missing_metal_price_count | missing_fx_count | duplicate_date_count | data_quality_score | validation_status | warning_flags |",
            "|---|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---|---|",
        ]
        for r in quality_rows:
            lines.append(f"| {r['symbol']} | {r['total_rows']} | {r['valid_rows']} | {r['invalid_rows']} | {r['date_start']} | {r['date_end']} | {r['missing_actual_price_count']} | {r['missing_metal_price_count']} | {r['missing_fx_count']} | {r['duplicate_date_count']} | {r['data_quality_score']} | {r['validation_status']} | {r['warning_flags']} |")
        lines += ["", "## 无效行明细", "| line | symbol | date | errors |", "|---:|---|---|---|"]
        if not invalid_rows:
            lines.append("| - | - | - | none |")
        else:
            for r in invalid_rows:
                lines.append(f"| {r.get('line')} | {r.get('symbol')} | {r.get('date')} | {r.get('errors')} |")
        path.write_text("\n".join(lines), encoding="utf-8")

    def _write_conversion_factor_calibration_csv(self, path: Path, rows: list[dict[str, Any]], times: dict[str, str]) -> None:
        fields = ["timestamp_jst", "timestamp_et", "symbol", "observation_count", "mean_conversion_factor", "median_conversion_factor", "std_conversion_factor", "min_conversion_factor", "max_conversion_factor", "p10_conversion_factor", "p90_conversion_factor", "latest_conversion_factor", "recommended_conversion_factor", "stability_score", "calibration_status", "warning_flags"]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({"timestamp_jst": times["jst"], "timestamp_et": times["et"], **row})

    def _write_conversion_factor_calibration_report(self, path: Path, rows: list[dict[str, Any]], times: dict[str, str]) -> None:
        lines = [
            "# Conversion Factor Calibration Report",
            "",
            "## 当前时间",
            f"- JST: {times['jst']}",
            f"- CST: {times['cst']}",
            f"- ET: {times['et']}",
            "",
            "## 模型状态",
            "- conversion_factor_calibration",
            "- research_only",
            "- no_auto_trade",
            "",
            "## 汇总结果",
            "| symbol | observation_count | mean_conversion_factor | median_conversion_factor | std_conversion_factor | min_conversion_factor | max_conversion_factor | p10_conversion_factor | p90_conversion_factor | latest_conversion_factor | recommended_conversion_factor | stability_score | calibration_status | warning_flags |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
        for r in rows:
            lines.append(f"| {r['symbol']} | {r['observation_count']} | {r['mean_conversion_factor']} | {r['median_conversion_factor']} | {r['std_conversion_factor']} | {r['min_conversion_factor']} | {r['max_conversion_factor']} | {r['p10_conversion_factor']} | {r['p90_conversion_factor']} | {r['latest_conversion_factor']} | {r['recommended_conversion_factor']} | {r['stability_score']} | {r['calibration_status']} | {r['warning_flags']} |")
        lines += ["", "本报告仅用于研究，不构成投资建议，不执行自动交易。"]
        path.write_text("\n".join(lines), encoding="utf-8")

    def _write_pricing_mock_csv(self, path: Path, rows: list[dict[str, Any]], times: dict[str, str]) -> None:
        fields = ["timestamp_jst", "timestamp_et", "symbol", "model_type", "actual_price", "theoretical_price", "deviation_pct", "metal_price_used", "fx_used", "conversion_factor", "premium_discount_pct", "data_confidence_score", "pricing_status", "warning_flags"]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({"timestamp_jst": times["jst"], "timestamp_et": times["et"], **row})

    def _write_pricing_mock_report(self, path: Path, rows: list[dict[str, Any]], times: dict[str, str]) -> None:
        lines = [
            "# Pricing Model Framework Verification Report",
            "",
            "## 当前时间",
            f"- JST: {times['jst']}",
            f"- CST: {times['cst']}",
            f"- ET: {times['et']}",
            "",
            "## 模型状态",
            "- pricing_mock",
            "- no_auto_trade",
            "- research_only",
            "",
            "## 定价结果",
            "| symbol | model_type | actual_price | theoretical_price | deviation_pct | metal_price_used | fx_used | conversion_factor | premium_discount_pct | data_confidence_score | pricing_status | warning_flags |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
        for r in rows:
            lines.append(f"| {r['symbol']} | {r['model_type']} | {r['actual_price']} | {r['theoretical_price']} | {r['deviation_pct']} | {r['metal_price_used']} | {r['fx_used']} | {r['conversion_factor']} | {r['premium_discount_pct']} | {r['data_confidence_score']} | {r['pricing_status']} | {r['warning_flags']} |")
        lines += [
            "",
            "- 本报告仅用于理论价格模型框架验证；",
            "- 不构成投资建议；",
            "- 不执行自动交易；",
            "- conversion_factor 当前为 mock 示例，后续需要用历史 NAV / 实际 ETF 价格 / 金银价格 / 汇率数据校准。",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")


    def _write_ibkr_historical_adapter_report(self, path: Path, rows: list[dict[str, Any]], times: dict[str, str]) -> None:
        lines = [
            "# IBKR Historical Adapter Report",
            "",
            "## 当前时间",
            f"- JST: {times['jst']}",
            f"- CST: {times['cst']}",
            f"- ET: {times['et']}",
            "",
            "## 模型状态",
            "- ibkr_historical_adapter_plan",
            "- research_only",
            "- no_auto_trade",
            "- no_reqHistoricalData_call",
            "",
            "## 边界声明",
            "- Phase 4B-1 只生成 request plan；",
            "- 不连接 TWS；",
            "- 不调用 reqHistoricalData；",
            "- 不修改 existing smoke fallback；",
            "- 不输出买卖点；",
            "- 不写入 calibration 参数。",
            "",
            "## Request Plan Summary",
            "| symbol | adapter_status | validation_status | warning_flags |",
            "|---|---|---|---|",
        ]
        for r in rows:
            lines.append(f"| {r['symbol']} | {r['adapter_status']} | {r['validation_status']} | {r['warning_flags']} |")
        path.write_text("\n".join(lines), encoding="utf-8")

    def _write_ibkr_historical_fetch_log_csv(self, path: Path, rows: list[dict[str, Any]], times: dict[str, str], mode: str) -> None:
        fields = ["timestamp_jst", "timestamp_et", "mode", "symbol", "row_count", "fetch_status", "warning_flags"]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({"timestamp_jst": times["jst"], "timestamp_et": times["et"], "mode": mode, **row})

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
