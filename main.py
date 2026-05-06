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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    monitor = PreciousMetalsMonitor(args.config, args.watchlist, mock_mode=(args.mock or args.ibkr_smoke or bool(args.contract_search) or args.calibrate_model or args.pricing_mock or bool(args.calibration_csv) or bool(args.validate_history) or bool(args.build_history) or bool(args.source_audit) or args.ibkr_historical_plan or args.ibkr_historical_fetch or bool(args.quality_gate) or args.historical_pipeline_check or args.upstream_factors or args.theoretical_pricing is not None or args.actual_etf_prices or args.deviation_check is not None or args.reference_signals is not None or args.daily_trade_plan is not None or args.strategy_plan is not None or args.manual_research_pipeline or args.market_data_source_plan or args.manual_market_data_adapter is not None or args.integrate_manual_market_data is not None or args.manual_market_data_pipeline is not None or args.validate_filled_manual_scenario is not None))


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
