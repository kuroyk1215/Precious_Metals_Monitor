import argparse
import sys

from src.monitor import PreciousMetalsMonitor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Precious Metals Monitor")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--watchlist", default="watchlist.yaml")
    parser.add_argument("--mock", action="store_true", help="run with built-in mock data and skip IBKR")
    parser.add_argument("--ibkr-smoke", action="store_true", help="run IBKR read-only smoke test")
    parser.add_argument("--contract-search", help="search IBKR contracts by query string (read-only)")
    parser.add_argument("--calibrate-model", action="store_true", help="run phase-3 theoretical pricing model calibration (read-only)")
    parser.add_argument("--pricing-mock", action="store_true", help="run phase-3 pricing model framework verification with mock inputs")
    parser.add_argument("--calibration-csv", help="run phase-3B conversion_factor calibration using historical sample csv")
    parser.add_argument("--validate-history", help="run phase-3C historical import validator")
    parser.add_argument("--build-history", help="run phase-4A raw history builder from source manifest")
    parser.add_argument("--source-audit", help="run phase-4B-0 source adapter audit from provider manifest")
    parser.add_argument("--ibkr-historical-plan", action="store_true", help="run phase-4B-1 IBKR historical adapter plan-only workflow")
    parser.add_argument("--ibkr-historical-fetch", action="store_true", help="run phase-4B-2A IBKR historical fetch workflow (dry-run default)")
    parser.add_argument("--execute-ibkr-historical-fetch", action="store_true", help="explicitly execute read-only IBKR historical fetch")
    parser.add_argument("--quality-gate", help="run phase-4C historical data quality gate for candidate csv")
    parser.add_argument("--historical-pipeline-check", action="store_true", help="run phase-4D manual historical pipeline integration check")
    parser.add_argument("--upstream-factors", action="store_true", help="run phase-5B upstream precious metals factor monitor")
    parser.add_argument("--theoretical-pricing", nargs="?", const="", help="run phase-5C ETF theoretical pricing from upstream snapshot csv")
    parser.add_argument("--actual-etf-prices", action="store_true", help="run phase-5D manual/mock ETF actual price snapshot")
    parser.add_argument("--deviation-check", nargs="*", help="run phase-5D deviation check: optional [theoretical_csv actual_csv]")
    parser.add_argument("--reference-signals", nargs="?", const="", help="run phase-5E manual reference signal layer from deviation snapshot csv")
    parser.add_argument("--daily-trade-plan", nargs="?", const="", help="run phase-5F daily manual trade plan from reference signal snapshot csv")
    parser.add_argument("--strategy-plan", nargs="?", const="", help="run phase-5G multi-horizon manual strategy plan from daily trade plan snapshot csv")
    parser.add_argument("--manual-research-pipeline", action="store_true", help="run phase-5H explicit manual end-to-end research pipeline")
    parser.add_argument("--market-data-source-plan", action="store_true", help="run phase-6A real market data source adapter planning only")
    parser.add_argument("--manual-market-data-adapter", nargs="?", const="", help="run phase-6B manual CSV market data adapter skeleton")
    parser.add_argument("--integrate-manual-market-data", nargs="?", const="", help="run phase-6C manual market data snapshot integration")
    parser.add_argument("--manual-market-data-pipeline", nargs="?", const="", help="run phase-6D manual CSV market data end-to-end research pipeline")
    parser.add_argument("--validate-filled-manual-scenario", nargs="?", const="", help="run phase-6E filled manual CSV scenario validation")
    parser.add_argument("--manual-market-data-review-pack", nargs="?", const="", help="run phase-6G manual CSV pipeline output review pack")
    parser.add_argument("--generated-output-guard", action="store_true", help="run phase-6H generated output cleanup guard")
    parser.add_argument("--manual-csv-smoke", nargs="?", const="", help="run phase-6I final manual CSV workflow smoke command")
    parser.add_argument("--market-data-provider-registry", action="store_true", help="run phase-7A market data provider registry skeleton")
    parser.add_argument("--market-data-adapter-contract", action="store_true", help="run phase-7B market data adapter interface contract")
    parser.add_argument("--manual-csv-adapter-interface", nargs="?", const="", help="run phase-7C manual CSV adapter through market data interface")
    parser.add_argument("--adapter-interface-bridge", nargs="?", const="", help="run phase-7D adapter interface to pipeline bridge")
    parser.add_argument("--research-trading-plan", nargs="?", const="", help="run phase-8A final manual research trading plan from review pack csv")
    parser.add_argument("--manual-research-trading-pipeline", nargs="?", const="", help="run phase-8C one-command manual research trading pipeline")
    parser.add_argument("--final-research-review-pack", nargs="?", const="", help="run phase-8D final manual research review pack")
    parser.add_argument("--market-data-provider-readiness", action="store_true", help="run phase-9A market data provider readiness planning")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    monitor = PreciousMetalsMonitor(args.config, args.watchlist, mock_mode=(args.mock or args.ibkr_smoke or bool(args.contract_search) or args.calibrate_model or args.pricing_mock or bool(args.calibration_csv) or bool(args.validate_history) or bool(args.build_history) or bool(args.source_audit) or args.ibkr_historical_plan or args.ibkr_historical_fetch or bool(args.quality_gate) or args.historical_pipeline_check or args.upstream_factors or args.theoretical_pricing is not None or args.actual_etf_prices or args.deviation_check is not None or args.reference_signals is not None or args.daily_trade_plan is not None or args.strategy_plan is not None or args.manual_research_pipeline or args.market_data_source_plan or args.manual_market_data_adapter is not None or args.integrate_manual_market_data is not None or args.manual_market_data_pipeline is not None or args.validate_filled_manual_scenario is not None or args.manual_market_data_review_pack is not None or args.generated_output_guard or args.manual_csv_smoke is not None or args.market_data_provider_registry or args.market_data_adapter_contract or args.manual_csv_adapter_interface is not None or args.adapter_interface_bridge is not None or args.research_trading_plan is not None or args.manual_research_trading_pipeline is not None or args.final_research_review_pack is not None or args.market_data_provider_readiness))


    if args.upstream_factors:
        rows, csv_path, md_path = monitor.run_upstream_factors()
        statuses = sorted({r.source_status for r in rows})
        overall = "ok" if statuses == ["ok"] else ("unavailable" if statuses == ["unavailable"] else "partial")
        print(f"[UPSTREAM_FACTORS] factors={len(rows)} status={overall}")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Research-only upstream factor monitor. No trading / no order / no auto calibration.")
        return 0
    if args.theoretical_pricing is not None:
        input_path = args.theoretical_pricing if args.theoretical_pricing else None
        rows, csv_path, md_path = monitor.run_theoretical_pricing(input_path)
        statuses = sorted({r.pricing_status for r in rows})
        overall = "ok" if statuses == ["ok"] else ("unavailable" if statuses == ["unavailable"] else "partial")
        print(f"[THEORETICAL_PRICING] etfs={len(rows)} status={overall}")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Research-only theoretical pricing input layer. No trading / no order / no IBKR connection / no reqHistoricalData / no auto calibration / no auto pipeline chaining.")
        return 0


    if args.actual_etf_prices:
        rows, csv_path, md_path = monitor.run_actual_etf_prices()
        print(f"[ACTUAL_ETF_PRICES] etfs={len(rows)} status=manual_mock_only")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Manual/mock only. Not real-time market data. No IBKR connection / no reqMktData / no reqHistoricalData / no trading.")
        return 0

    if args.deviation_check is not None:
        paths = args.deviation_check
        if len(paths) > 2:
            print("--deviation-check accepts at most 2 paths: [theoretical_csv actual_csv]", file=sys.stderr)
            return 2
        theoretical_path = paths[0] if len(paths) >= 1 else None
        actual_path = paths[1] if len(paths) >= 2 else None
        rows, csv_path, md_path = monitor.run_deviation_check(theoretical_path, actual_path)
        statuses = sorted({r.deviation_status for r in rows})
        overall = "ok" if statuses == ["ok"] else ("unavailable" if statuses == ["unavailable"] else "partial")
        print(f"[DEVIATION_CHECK] etfs={len(rows)} status={overall}")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Deviation-only phase. No buy/sell/trade output / no IBKR connection / no reqMktData / no reqHistoricalData / no auto calibration / no auto pipeline chaining.")
        return 0

    if args.reference_signals is not None:
        input_path = args.reference_signals if args.reference_signals else None
        rows, csv_path, md_path = monitor.run_reference_signals(input_path)
        labels = sorted({r.reference_label for r in rows})
        print(f"[REFERENCE_SIGNALS] etfs={len(rows)} labels={','.join(labels)} action_allowed=false")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Observation-only reference layer. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no auto calibration / no auto pipeline chaining.")
        return 0

    if args.daily_trade_plan is not None:
        input_path = args.daily_trade_plan if args.daily_trade_plan else None
        rows, csv_path, md_path = monitor.run_daily_trade_plan(input_path)
        labels = sorted({r.plan_label for r in rows})
        print(f"[DAILY_TRADE_PLAN] etfs={len(rows)} labels={','.join(labels)} action_allowed=false")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Manual observation-only daily plan. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no auto calibration / no auto pipeline chaining.")
        return 0

    if args.strategy_plan is not None:
        input_path = args.strategy_plan if args.strategy_plan else None
        rows, csv_path, md_path = monitor.run_strategy_plan(input_path)
        labels = sorted({r.strategy_label for r in rows})
        print(f"[STRATEGY_PLAN] etfs={len(rows)} labels={','.join(labels)} action_allowed=false")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Multi-horizon manual observation framework. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no auto calibration / no auto pipeline chaining.")
        return 0

    if args.manual_research_pipeline:
        rows, csv_path, md_path = monitor.run_manual_research_pipeline()
        statuses = sorted({r.status for r in rows})
        print(f"[MANUAL_RESEARCH_PIPELINE] steps={len(rows)} statuses={','.join(statuses)} action_allowed=false")
        print(f"summary_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Explicit manual research run only. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no auto calibration / no automatic execution.")
        return 0

    if args.market_data_source_plan:
        rows, csv_path, md_path = monitor.run_market_data_source_plan()
        statuses = sorted({r.adapter_status for r in rows})
        print(f"[MARKET_DATA_SOURCE_PLAN] targets={len(rows)} statuses={','.join(statuses)} planning_only=true")
        print(f"plan_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Planning only. No IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.manual_market_data_adapter is not None:
        input_path = args.manual_market_data_adapter if args.manual_market_data_adapter else None
        rows, csv_path, md_path = monitor.run_manual_market_data_adapter(input_path)
        statuses = sorted({r.normalized_status for r in rows})
        print(f"[MANUAL_MARKET_DATA_ADAPTER] rows={len(rows)} statuses={','.join(statuses)} manual_csv_only=true")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Manual CSV only. No IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.integrate_manual_market_data is not None:
        input_path = args.integrate_manual_market_data if args.integrate_manual_market_data else None
        upstream_rows, actual_rows, summary_rows, upstream_csv, actual_csv, summary_csv, report = monitor.run_integrate_manual_market_data(input_path)
        statuses = sorted({r.output_status for r in summary_rows})
        print(f"[INTEGRATE_MANUAL_MARKET_DATA] upstream={len(upstream_rows)} actual={len(actual_rows)} statuses={','.join(statuses)} manual_snapshot_only=true")
        print(f"upstream_csv={upstream_csv}")
        print(f"actual_csv={actual_csv}")
        print(f"summary_csv={summary_csv}")
        print(f"report={report}")
        print("NOTICE: Manual snapshot integration only. No IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade / no automatic pipeline chaining.")
        return 0

    if args.manual_market_data_pipeline is not None:
        input_path = args.manual_market_data_pipeline if args.manual_market_data_pipeline else None
        rows, csv_path, md_path = monitor.run_manual_market_data_pipeline(input_path)
        statuses = sorted({r.status for r in rows})
        print(f"[MANUAL_MARKET_DATA_PIPELINE] steps={len(rows)} statuses={','.join(statuses)} action_allowed=false")
        print(f"summary_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Explicit manual CSV research pipeline only. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.validate_filled_manual_scenario is not None:
        input_path = args.validate_filled_manual_scenario if args.validate_filled_manual_scenario else None
        rows, csv_path, md_path = monitor.run_validate_filled_manual_scenario(input_path)
        statuses = sorted({r.status for r in rows})
        print(f"[FILLED_MANUAL_SCENARIO] checks={len(rows)} statuses={','.join(statuses)} action_allowed=false")
        print(f"validation_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Filled manual CSV scenario validation only. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.manual_market_data_review_pack is not None:
        input_path = args.manual_market_data_review_pack if args.manual_market_data_review_pack else None
        rows, csv_path, md_path = monitor.run_manual_market_data_review_pack(input_path)
        labels = sorted({r.strategy_label for r in rows})
        print(f"[MANUAL_MARKET_DATA_REVIEW_PACK] etfs={len(rows)} labels={','.join(labels)} action_allowed=false")
        print(f"review_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Manual CSV review only. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.generated_output_guard:
        rows, csv_path, md_path = monitor.run_generated_output_guard()
        print(f"[GENERATED_OUTPUT_GUARD] detected={len(rows)} report_only=true")
        print(f"guard_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Report only. No file deletion / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.manual_csv_smoke is not None:
        input_path = args.manual_csv_smoke if args.manual_csv_smoke else None
        rows, csv_path, md_path = monitor.run_manual_csv_smoke(input_path)
        statuses = sorted({r.status for r in rows})
        print(f"[MANUAL_CSV_SMOKE] steps={len(rows)} statuses={','.join(statuses)} action_allowed=false")
        print(f"summary_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Manual CSV smoke only. report_only=true / action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.market_data_provider_registry:
        rows, csv_path, md_path = monitor.run_market_data_provider_registry()
        statuses = sorted({r.provider_status for r in rows})
        print(f"[MARKET_DATA_PROVIDER_REGISTRY] providers={len(rows)} statuses={','.join(statuses)} registry_only=true")
        print(f"registry_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Registry only. No connection / no API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.market_data_adapter_contract:
        rows, csv_path, md_path = monitor.run_market_data_adapter_contract()
        groups = sorted({r.field_group for r in rows})
        print(f"[MARKET_DATA_ADAPTER_CONTRACT] rows={len(rows)} groups={','.join(groups)} interface_only=true")
        print(f"contract_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Interface contract only. No connection / no API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.manual_csv_adapter_interface is not None:
        input_path = args.manual_csv_adapter_interface if args.manual_csv_adapter_interface else None
        rows, csv_path, md_path = monitor.run_manual_csv_adapter_interface(input_path)
        statuses = sorted({r.adapter_status for r in rows})
        print(f"[MANUAL_CSV_ADAPTER_INTERFACE] rows={len(rows)} statuses={','.join(statuses)} local_csv_only=true")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Manual CSV adapter interface only. No connection / no API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.adapter_interface_bridge is not None:
        input_path = args.adapter_interface_bridge if args.adapter_interface_bridge else None
        rows, summary_rows, snapshot_csv, summary_csv, md_path = monitor.run_adapter_interface_bridge(input_path)
        statuses = sorted({r.bridge_status for r in summary_rows})
        print(f"[ADAPTER_INTERFACE_BRIDGE] rows={len(rows)} statuses={','.join(statuses)} local_csv_bridge=true")
        print(f"snapshot_csv={snapshot_csv}")
        print(f"summary_csv={summary_csv}")
        print(f"report={md_path}")
        print("NOTICE: Adapter bridge only. No connection / no API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0





    if args.market_data_provider_readiness:
        from pathlib import Path
        from src.market_data_provider_readiness import (
            build_market_data_provider_readiness_rows,
            write_market_data_provider_readiness_csv,
            write_market_data_provider_readiness_report,
        )

        rows = build_market_data_provider_readiness_rows(monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("market_data_provider_readiness_csv", "market_data_provider_readiness.csv"))
        md_path = Path(monitor.config["runtime"].get("market_data_provider_readiness_report", "reports/market_data_provider_readiness_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_market_data_provider_readiness_csv(csv_path, rows)
        write_market_data_provider_readiness_report(md_path, rows)

        statuses = sorted({r.readiness_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[MARKET_DATA_PROVIDER_READINESS] rows={len(rows)} statuses={status_text} live_request_allowed=false action_allowed=false")
        print(f"readiness_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Provider readiness planning only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.final_research_review_pack is not None:
        from pathlib import Path
        from src.final_research_review_pack import (
            build_final_research_review_pack_rows,
            load_csv_by_key,
            write_final_research_review_pack_csv,
            write_final_research_review_pack_report,
        )

        input_csv = args.final_research_review_pack if args.final_research_review_pack else monitor.config["runtime"].get("manual_market_data_sample_valid_csv", "data/manual_market_data_sample_valid.csv")

        pipeline_args = type("PipelineArgs", (), {})()
        pipeline_args.manual_research_trading_pipeline = input_csv

        # Reuse the same pipeline building logic by invoking the underlying monitor methods directly.
        pipeline_rows, pipeline_csv, pipeline_report = monitor.run_manual_market_data_pipeline(input_csv)
        review_rows, review_csv, review_report = monitor.run_manual_market_data_review_pack(input_csv)

        from src.research_trading_plan_generator import (
            build_research_trading_plan_rows,
            load_review_pack_by_symbol,
            write_research_trading_plan_csv,
            write_research_trading_plan_report,
        )
        from src.manual_research_trading_pipeline import (
            build_manual_research_trading_pipeline_step_row,
            summarize_step_status,
            write_manual_research_trading_pipeline_summary_csv,
            write_manual_research_trading_pipeline_report,
        )

        tz_cfg = monitor.config["runtime"]["timezone"]
        review_by_symbol = load_review_pack_by_symbol(review_csv)
        trading_rows = build_research_trading_plan_rows(review_by_symbol, tz_cfg)

        trading_csv = Path(monitor.config["runtime"].get("research_trading_plan_csv", "research_trading_plan.csv"))
        trading_report = Path(monitor.config["runtime"].get("research_trading_plan_report", "reports/research_trading_plan_report.md"))
        trading_csv.parent.mkdir(parents=True, exist_ok=True)
        trading_report.parent.mkdir(parents=True, exist_ok=True)
        write_research_trading_plan_csv(trading_csv, trading_rows)
        write_research_trading_plan_report(trading_report, trading_rows, review_csv)

        summary_rows = [
            build_manual_research_trading_pipeline_step_row(1, "Phase 6D", "manual_market_data_pipeline", summarize_step_status([getattr(r, "status", "") for r in pipeline_rows]), pipeline_csv, pipeline_report, len(pipeline_rows), tz_cfg, f"input_csv={input_csv}"),
            build_manual_research_trading_pipeline_step_row(2, "Phase 6G", "manual_market_data_review_pack", summarize_step_status([getattr(r, "strategy_label", "") for r in review_rows]), review_csv, review_report, len(review_rows), tz_cfg, "review pack from manual pipeline"),
            build_manual_research_trading_pipeline_step_row(3, "Phase 8A", "research_trading_plan", summarize_step_status([r.plan_status for r in trading_rows]), str(trading_csv), str(trading_report), len(trading_rows), tz_cfg, "final research trading plan"),
        ]

        summary_csv = Path(monitor.config["runtime"].get("manual_research_trading_pipeline_summary_csv", "manual_research_trading_pipeline_summary.csv"))
        summary_report = Path(monitor.config["runtime"].get("manual_research_trading_pipeline_report", "reports/manual_research_trading_pipeline_report.md"))
        summary_csv.parent.mkdir(parents=True, exist_ok=True)
        summary_report.parent.mkdir(parents=True, exist_ok=True)
        write_manual_research_trading_pipeline_summary_csv(summary_csv, summary_rows)
        write_manual_research_trading_pipeline_report(summary_report, summary_rows, input_csv)

        trading_by_symbol = load_csv_by_key(str(trading_csv), "etf_symbol")
        final_rows = build_final_research_review_pack_rows(trading_by_symbol, tz_cfg)

        final_csv = Path(monitor.config["runtime"].get("final_research_review_pack_csv", "final_research_review_pack.csv"))
        final_report = Path(monitor.config["runtime"].get("final_research_review_pack_report", "reports/final_research_review_pack_report.md"))
        final_csv.parent.mkdir(parents=True, exist_ok=True)
        final_report.parent.mkdir(parents=True, exist_ok=True)

        write_final_research_review_pack_csv(final_csv, final_rows)
        write_final_research_review_pack_report(final_report, final_rows, input_csv, str(summary_csv), str(trading_csv))

        labels = sorted({r.final_review_label for r in final_rows})
        label_text = chr(44).join(labels) if labels else "none"
        print(f"[FINAL_RESEARCH_REVIEW_PACK] rows={len(final_rows)} labels={label_text} action_allowed=false")
        print(f"final_csv={final_csv}")
        print(f"final_report={final_report}")
        print(f"pipeline_summary_csv={summary_csv}")
        print(f"trading_plan_csv={trading_csv}")
        print("NOTICE: Final research review pack only. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.manual_research_trading_pipeline is not None:
        from pathlib import Path
        from src.research_trading_plan_generator import (
            build_research_trading_plan_rows,
            load_review_pack_by_symbol,
            write_research_trading_plan_csv,
            write_research_trading_plan_report,
        )
        from src.manual_research_trading_pipeline import (
            build_manual_research_trading_pipeline_step_row,
            summarize_step_status,
            write_manual_research_trading_pipeline_report,
            write_manual_research_trading_pipeline_summary_csv,
        )

        input_csv = args.manual_research_trading_pipeline if args.manual_research_trading_pipeline else monitor.config["runtime"].get("manual_market_data_sample_valid_csv", "data/manual_market_data_sample_valid.csv")
        tz_cfg = monitor.config["runtime"]["timezone"]

        pipeline_rows, pipeline_csv, pipeline_report = monitor.run_manual_market_data_pipeline(input_csv)
        pipeline_status = summarize_step_status([getattr(r, "status", "") for r in pipeline_rows])

        review_rows, review_csv, review_report = monitor.run_manual_market_data_review_pack(input_csv)
        review_status = summarize_step_status([getattr(r, "strategy_label", "") for r in review_rows])

        review_by_symbol = load_review_pack_by_symbol(review_csv)
        trading_rows = build_research_trading_plan_rows(review_by_symbol, tz_cfg)

        trading_csv = Path(monitor.config["runtime"].get("research_trading_plan_csv", "research_trading_plan.csv"))
        trading_report = Path(monitor.config["runtime"].get("research_trading_plan_report", "reports/research_trading_plan_report.md"))
        trading_csv.parent.mkdir(parents=True, exist_ok=True)
        trading_report.parent.mkdir(parents=True, exist_ok=True)
        write_research_trading_plan_csv(trading_csv, trading_rows)
        write_research_trading_plan_report(trading_report, trading_rows, review_csv)

        trading_status = summarize_step_status([r.plan_status for r in trading_rows])

        summary_rows = [
            build_manual_research_trading_pipeline_step_row(1, "Phase 6D", "manual_market_data_pipeline", pipeline_status, pipeline_csv, pipeline_report, len(pipeline_rows), tz_cfg, f"input_csv={input_csv}"),
            build_manual_research_trading_pipeline_step_row(2, "Phase 6G", "manual_market_data_review_pack", review_status, review_csv, review_report, len(review_rows), tz_cfg, "review pack from manual pipeline"),
            build_manual_research_trading_pipeline_step_row(3, "Phase 8A", "research_trading_plan", trading_status, str(trading_csv), str(trading_report), len(trading_rows), tz_cfg, "final research trading plan"),
        ]

        summary_csv = Path(monitor.config["runtime"].get("manual_research_trading_pipeline_summary_csv", "manual_research_trading_pipeline_summary.csv"))
        summary_report = Path(monitor.config["runtime"].get("manual_research_trading_pipeline_report", "reports/manual_research_trading_pipeline_report.md"))
        summary_csv.parent.mkdir(parents=True, exist_ok=True)
        summary_report.parent.mkdir(parents=True, exist_ok=True)

        write_manual_research_trading_pipeline_summary_csv(summary_csv, summary_rows)
        write_manual_research_trading_pipeline_report(summary_report, summary_rows, input_csv)

        statuses = sorted({r.status for r in summary_rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[MANUAL_RESEARCH_TRADING_PIPELINE] steps={len(summary_rows)} statuses={status_text} action_allowed=false")
        print(f"summary_csv={summary_csv}")
        print(f"report={summary_report}")
        print(f"trading_plan_csv={trading_csv}")
        print(f"trading_plan_report={trading_report}")
        print("NOTICE: One-command manual research trading pipeline only. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.research_trading_plan is not None:
        from pathlib import Path
        from src.research_trading_plan_generator import (
            build_research_trading_plan_rows,
            load_review_pack_by_symbol,
            write_research_trading_plan_csv,
            write_research_trading_plan_report,
        )

        input_path = args.research_trading_plan if args.research_trading_plan else monitor.config["runtime"].get("manual_market_data_review_pack_csv", "manual_market_data_review_pack.csv")
        review_rows = load_review_pack_by_symbol(input_path)
        rows = build_research_trading_plan_rows(review_rows, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("research_trading_plan_csv", "research_trading_plan.csv"))
        md_path = Path(monitor.config["runtime"].get("research_trading_plan_report", "reports/research_trading_plan_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_research_trading_plan_csv(csv_path, rows)
        write_research_trading_plan_report(md_path, rows, input_path)

        statuses = sorted({r.plan_status for r in rows})
        print(f"[RESEARCH_TRADING_PLAN] etfs={len(rows)} statuses={chr(44).join(statuses) if statuses else none} action_allowed=false")
        print(f"plan_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Final manual research trading plan only. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.pricing_mock:
        rows, csv_path, md_path = monitor.run_pricing_mock("data/mock_pricing_inputs.yaml")
        print(f"[PRICING_MOCK] symbols={len(rows)}")
        print(f"csv={csv_path}")
        print(f"markdown={md_path}")
        print("NOTICE: Pricing mock is research-only model framework verification. No auto order / no auto sell / no cancel.")
        return 0

    if args.ibkr_smoke:
        quotes, csv_path, md_path, conn_status = monitor.run_ibkr_smoke(preferred_data_type="delayed")
        print(f"[IBKR_SMOKE] status={conn_status} symbols={len(quotes)}")
        print(f"csv={csv_path}")
        print(f"markdown={md_path}")
        print("NOTICE: Read-only smoke test only. No auto order / no auto sell / no cancel.")
        return 0

    if args.contract_search:
        rows, csv_path, md_path, conn_status = monitor.run_contract_search(args.contract_search)
        print(f"[IBKR_CONTRACT_SEARCH] status={conn_status} query={args.contract_search} candidates={len(rows)}")
        print(f"csv={csv_path}")
        print(f"markdown={md_path}")
        print("NOTICE: Read-only contract discovery only. No auto order / no auto sell / no cancel.")
        return 0

    if args.source_audit:
        rows, report_md, log_csv = monitor.run_source_audit(args.source_audit)
        print(f"[SOURCE_ADAPTER_AUDIT] providers={len(rows)}")
        print(f"report={report_md}")
        print(f"log_csv={log_csv}")
        print("NOTICE: Source audit is research-only workflow. No auto order / no auto sell / no cancel.")
        return 0


    if args.ibkr_historical_plan:
        rows, plan_csv, report_md, raw_csv = monitor.run_ibkr_historical_plan()
        print(f"[IBKR_HISTORICAL_PLAN] symbols={len(rows)}")
        print(f"plan_csv={plan_csv}")
        print(f"report={report_md}")
        print(f"raw_csv={raw_csv}")
        print("NOTICE: IBKR historical adapter is plan-only in Phase 4B-1. No reqHistoricalData call / no auto order / no auto sell / no cancel.")
        return 0


    if args.ibkr_historical_fetch:
        rows, raw_csv, report_md, log_csv = monitor.run_ibkr_historical_fetch(execute=args.execute_ibkr_historical_fetch)
        print(f"[IBKR_HISTORICAL_FETCH] mode={'execute' if args.execute_ibkr_historical_fetch else 'dry_run'} symbols={len(rows)}")
        print(f"raw_csv={raw_csv}")
        print(f"report={report_md}")
        print(f"log_csv={log_csv}")
        if args.execute_ibkr_historical_fetch:
            print("NOTICE: Read-only historical fetch requested by explicit user switch. No auto order / no auto sell / no cancel.")
        else:
            print("NOTICE: Dry-run only. No TWS connection / no reqHistoricalData call / no auto order / no auto sell / no cancel.")
        return 0

    if args.quality_gate:
        summary, report_md, log_csv = monitor.run_historical_quality_gate(args.quality_gate)
        print(f"[HISTORICAL_QUALITY_GATE] status={summary['status']} total_rows={summary['total_rows']}")
        print(f"symbols={','.join(summary['symbols'])}")
        print(f"date_range={summary['start_date']}->{summary['end_date']}")
        print(f"warning_flags={';'.join(summary['warning_flags']) if summary['warning_flags'] else 'none'}")
        print(f"fail_reasons={';'.join(summary['fail_reasons']) if summary['fail_reasons'] else 'none'}")
        print(f"report={report_md}")
        print(f"log_csv={log_csv}")
        print("NOTICE: Historical quality gate is research-only. No IBKR connection / no reqHistoricalData / no auto validate-history / no auto calibration-csv / no auto order / no auto sell / no cancel.")
        return 0


    if args.historical_pipeline_check:
        summary, report_md, log_csv = monitor.run_historical_pipeline_check()
        print(f"[HISTORICAL_PIPELINE_CHECK] status={summary['status']}")
        print(f"current_blocking_step={summary['current_blocking_step']}")
        print(f"warning_flags={';'.join(summary['warning_flags']) if summary['warning_flags'] else 'none'}")
        print(f"notes={summary['notes']}")
        print(f"report={report_md}")
        print(f"log_csv={log_csv}")
        print("NOTICE: Manual-only / research-only integration check. No auto chain / no auto ibkr-historical-fetch / no auto quality-gate / no auto validate-history / no auto calibration-csv / no auto trade.")
        return 0

    if args.build_history:
        rows, candidate_csv, report_md, log_csv = monitor.run_build_history(args.build_history)
        print(f"[HISTORICAL_DATA_BUILD] symbols={len(rows)}")
        print(f"candidate_csv={candidate_csv}")
        print(f"report={report_md}")
        print(f"log_csv={log_csv}")
        print("NOTICE: Raw history build is research-only workflow. No auto order / no auto sell / no cancel.")
        return 0

    if args.validate_history:
        rows, validated_csv, report_md, log_csv = monitor.run_validate_history(args.validate_history)
        print(f"[HISTORICAL_DATA_VALIDATION] symbols={len(rows)}")
        print(f"validated_csv={validated_csv}")
        print(f"report={report_md}")
        print(f"log_csv={log_csv}")
        print("NOTICE: Historical validation is research-only workflow. No auto order / no auto sell / no cancel.")
        return 0

    if args.calibration_csv:
        rows, csv_path, md_path = monitor.run_conversion_factor_calibration_csv(args.calibration_csv)
        print(f"[CONVERSION_FACTOR_CALIBRATION] symbols={len(rows)}")
        print(f"csv={csv_path}")
        print(f"markdown={md_path}")
        print("NOTICE: Calibration is read-only research workflow. No auto order / no auto sell / no cancel.")
        return 0

    if args.calibrate_model:
        rows, json_path, md_path = monitor.run_model_calibration(force_mock=True)
        print(f"[MODEL_CALIBRATION] symbols={len(rows)}")
        print(f"json={json_path}")
        print(f"markdown={md_path}")
        print("NOTICE: Calibration is read-only research workflow. No auto order / no auto sell / no cancel.")
        return 0

    if args.mock:
        ok, msg = False, "mock_mode_enabled"
    else:
        ok, msg = monitor.test_ibkr_connection()
    print(f"[IBKR] connection={ok} detail={msg}")

    rows, csv_path, md_path = monitor.run(ibkr_connected=ok, force_mock=args.mock)
    print(f"generated_rows={len(rows)}")
    print(f"csv={csv_path}")
    print(f"markdown={md_path}")
    print("NOTICE: No auto order / no auto sell / no cancel / manual execution only.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
