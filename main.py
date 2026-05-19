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
    parser.add_argument("--market-data-provider-config-audit", nargs="?", const="", help="run phase-9B market data provider config audit")
    parser.add_argument("--market-data-provider-selector", nargs="?", const="", help="run phase-9D market data provider selector and fallback planner")
    parser.add_argument("--live-provider-interface-check", nargs="?", const="", help="run phase-10A live provider interface safety check")
    parser.add_argument("--live-provider-request-gate", nargs="?", const="", help="run phase-10B live provider request gate safety check")
    parser.add_argument("--live-provider-mock-adapter", nargs="?", const="", help="run phase-10C live provider mock adapter")
    parser.add_argument("--live-data-quality-gate", nargs="?", const="", help="run phase-10D live/mock data quality gate")
    parser.add_argument("--live-research-review-pack", nargs="?", const="", help="run phase-10E live/mock research review pack bridge")
    parser.add_argument("--live-final-research-review-pack", nargs="?", const="", help="run phase-10F live/mock final research review pack")
    parser.add_argument("--ibkr-live-provider-adapter-check", nargs="?", const="", help="run phase-10G IBKR live provider adapter skeleton check")
    parser.add_argument("--ibkr-contract-mapping-plan", nargs="?", const="", help="run phase-10H IBKR contract mapping plan")
    parser.add_argument("--ibkr-contract-qualification-dry-run", nargs="?", const="", help="run phase-10I IBKR contract qualification dry-run plan")
    parser.add_argument("--ibkr-contract-qualification-execution-guard", nargs="?", const="", help="run phase-10J IBKR contract qualification execution guard")
    parser.add_argument("--ibkr-readonly-qualification-precheck", nargs="?", const="", help="run phase-10K IBKR read-only qualification precheck")
    parser.add_argument("--ibkr-readonly-qualification-runbook", nargs="?", const="", help="run phase-10L IBKR read-only qualification runbook")
    parser.add_argument("--ibkr-readonly-qualification-go-no-go", nargs="?", const="", help="run phase-10M IBKR read-only qualification go/no-go summary")
    parser.add_argument("--ibkr-readonly-qualification-config-template", nargs="?", const="", help="run phase-11A IBKR read-only qualification config template")
    parser.add_argument("--ibkr-readonly-qualification-config-audit", nargs="?", const="", help="run phase-11B IBKR read-only qualification config audit")
    parser.add_argument("--ibkr-readonly-qualification-config-apply-plan", nargs="?", const="", help="run phase-11C IBKR read-only qualification config apply plan")
    parser.add_argument("--ibkr-readonly-qualification-config-final-gate", nargs="?", const="", help="run phase-11D IBKR read-only qualification config final gate")
    parser.add_argument("--ibkr-readonly-qualification-safety-summary", nargs="?", const="", help="run phase-11E IBKR read-only qualification full safety summary")
    parser.add_argument("--ibkr-readonly-qualification-candidate-resolver", nargs="?", const="", help="run phase-12A IBKR read-only qualification candidate resolver")
    parser.add_argument("--ibkr-readonly-qualification-candidate-review-pack", nargs="?", const="", help="run phase-12B IBKR read-only qualification candidate review pack")
    parser.add_argument("--ibkr-readonly-qualification-candidate-final-gate", nargs="?", const="", help="run phase-12C IBKR read-only qualification candidate final gate")
    parser.add_argument("--ibkr-readonly-qualification-candidate-safety-summary", nargs="?", const="", help="run phase-12D IBKR read-only qualification candidate safety summary")
    parser.add_argument(
        "--ibkr-readonly-qualification-operator-decision-ledger",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 12E IBKR read-only qualification operator decision ledger without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-operator-approval-stub",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 12F IBKR read-only qualification operator approval stub without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-effective-approval-gate",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 12G IBKR read-only qualification effective approval gate without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-final-authorization-packet",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 12H IBKR read-only qualification final authorization packet without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-phase12-closure-report",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 12I IBKR read-only qualification Phase 12 closure report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-design",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13A IBKR read-only qualification sandbox design report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-input-contract",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13B IBKR read-only qualification sandbox input contract report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-input-validator",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13C IBKR read-only qualification sandbox input validator report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-qualification-simulator",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13D IBKR read-only qualification sandbox qualification simulator report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-result-pack",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13E IBKR read-only qualification sandbox result pack report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-safety-gate",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13F IBKR read-only qualification sandbox safety gate report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-final-review-pack",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13G IBKR read-only qualification sandbox final review pack report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-closure-report",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13H IBKR read-only qualification sandbox closure report without connecting to IBKR.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    monitor = PreciousMetalsMonitor(args.config, args.watchlist, mock_mode=(args.mock or args.ibkr_smoke or bool(args.contract_search) or args.calibrate_model or args.pricing_mock or bool(args.calibration_csv) or bool(args.validate_history) or bool(args.build_history) or bool(args.source_audit) or args.ibkr_historical_plan or args.ibkr_historical_fetch or bool(args.quality_gate) or args.historical_pipeline_check or args.upstream_factors or args.theoretical_pricing is not None or args.actual_etf_prices or args.deviation_check is not None or args.reference_signals is not None or args.daily_trade_plan is not None or args.strategy_plan is not None or args.manual_research_pipeline or args.market_data_source_plan or args.manual_market_data_adapter is not None or args.integrate_manual_market_data is not None or args.manual_market_data_pipeline is not None or args.validate_filled_manual_scenario is not None or args.manual_market_data_review_pack is not None or args.generated_output_guard or args.manual_csv_smoke is not None or args.market_data_provider_registry or args.market_data_adapter_contract or args.manual_csv_adapter_interface is not None or args.adapter_interface_bridge is not None or args.research_trading_plan is not None or args.manual_research_trading_pipeline is not None or args.final_research_review_pack is not None or args.market_data_provider_readiness or args.market_data_provider_config_audit is not None or args.market_data_provider_selector is not None or args.live_provider_interface_check is not None or args.live_provider_request_gate is not None or args.live_provider_mock_adapter is not None or args.live_data_quality_gate is not None or args.live_research_review_pack is not None or args.live_final_research_review_pack is not None or args.ibkr_live_provider_adapter_check is not None or args.ibkr_contract_mapping_plan is not None or args.ibkr_contract_qualification_dry_run is not None or args.ibkr_contract_qualification_execution_guard is not None or args.ibkr_readonly_qualification_precheck is not None or args.ibkr_readonly_qualification_runbook is not None or args.ibkr_readonly_qualification_go_no_go is not None or args.ibkr_readonly_qualification_config_template is not None or args.ibkr_readonly_qualification_config_audit is not None or args.ibkr_readonly_qualification_config_apply_plan is not None or args.ibkr_readonly_qualification_config_final_gate is not None or args.ibkr_readonly_qualification_safety_summary is not None or args.ibkr_readonly_qualification_candidate_resolver is not None or args.ibkr_readonly_qualification_candidate_review_pack is not None or args.ibkr_readonly_qualification_candidate_final_gate is not None or args.ibkr_readonly_qualification_candidate_safety_summary is not None or args.ibkr_readonly_qualification_operator_decision_ledger is not None or args.ibkr_readonly_qualification_operator_approval_stub is not None or args.ibkr_readonly_qualification_effective_approval_gate is not None or args.ibkr_readonly_qualification_final_authorization_packet is not None or args.ibkr_readonly_qualification_phase12_closure_report is not None or args.ibkr_readonly_qualification_sandbox_design is not None or args.ibkr_readonly_qualification_sandbox_input_contract is not None or args.ibkr_readonly_qualification_sandbox_input_validator is not None or args.ibkr_readonly_qualification_sandbox_qualification_simulator is not None or args.ibkr_readonly_qualification_sandbox_result_pack is not None or args.ibkr_readonly_qualification_sandbox_safety_gate is not None or args.ibkr_readonly_qualification_sandbox_final_review_pack is not None or args.ibkr_readonly_qualification_sandbox_closure_report is not None))


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





























    if args.ibkr_readonly_qualification_sandbox_closure_report is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_closure_report import (
            build_ibkr_readonly_qualification_sandbox_closure_report_rows,
            write_ibkr_readonly_qualification_sandbox_closure_report_csv,
            write_ibkr_readonly_qualification_sandbox_closure_report_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_closure_report
            if args.ibkr_readonly_qualification_sandbox_closure_report
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_closure_report_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_closure_report_csv",
                "ibkr_readonly_qualification_sandbox_closure_report.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_closure_report",
                "reports/ibkr_readonly_qualification_sandbox_closure_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_closure_report_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_closure_report_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_closure_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        complete_count = sum(1 for r in rows if r.sandbox_closure_status == "COMPLETE")
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_CLOSURE_REPORT] "
            f"rows={len(rows)} statuses={status_text} complete={complete_count} "
            "sandbox_final_review_status=READY_FOR_REVIEW sandbox_safety_gate_status=CLOSED "
            "simulated_result_only=true real_qualification_allowed=false "
            "tws_connection_allowed=false ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_closure_report_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox closure report only. "
            "Phase 13 sandbox loop is complete but execution remains blocked. "
            "No TWS connection / no IBKR connection / no reqMktData / no reqHistoricalData / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_final_review_pack is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_final_review_pack import (
            build_ibkr_readonly_qualification_sandbox_final_review_pack_rows,
            write_ibkr_readonly_qualification_sandbox_final_review_pack_csv,
            write_ibkr_readonly_qualification_sandbox_final_review_pack_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_final_review_pack
            if args.ibkr_readonly_qualification_sandbox_final_review_pack
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_final_review_pack_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_final_review_pack_csv",
                "ibkr_readonly_qualification_sandbox_final_review_pack.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_final_review_pack_report",
                "reports/ibkr_readonly_qualification_sandbox_final_review_pack_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_final_review_pack_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_final_review_pack_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_final_review_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        review_count = sum(1 for r in rows if r.sandbox_result_accepted_for_review == "true")
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_FINAL_REVIEW_PACK] "
            f"rows={len(rows)} statuses={status_text} review_accepted={review_count} "
            "sandbox_safety_gate_status=CLOSED simulated_result_only=true "
            "real_qualification_allowed=false tws_connection_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_final_review_pack_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox final review pack only. "
            "Sandbox outputs are for review only; safety gate remains CLOSED. "
            "No TWS connection / no IBKR connection / no reqMktData / no reqHistoricalData / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_safety_gate is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_safety_gate import (
            build_ibkr_readonly_qualification_sandbox_safety_gate_rows,
            write_ibkr_readonly_qualification_sandbox_safety_gate_csv,
            write_ibkr_readonly_qualification_sandbox_safety_gate_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_safety_gate
            if args.ibkr_readonly_qualification_sandbox_safety_gate
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_safety_gate_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_safety_gate_csv",
                "ibkr_readonly_qualification_sandbox_safety_gate.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_safety_gate_report",
                "reports/ibkr_readonly_qualification_sandbox_safety_gate_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_safety_gate_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_safety_gate_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_safety_gate_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        review_count = sum(1 for r in rows if r.sandbox_result_accepted_for_review == "true")
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_SAFETY_GATE] "
            f"rows={len(rows)} statuses={status_text} review_accepted={review_count} "
            "simulated_result_only=true real_qualification_allowed=false "
            "tws_connection_allowed=false ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_safety_gate_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox safety gate only. "
            "Sandbox results are accepted for review only; safety gate remains CLOSED. "
            "No TWS connection / no IBKR connection / no reqMktData / no reqHistoricalData / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_result_pack is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_result_pack import (
            build_ibkr_readonly_qualification_sandbox_result_pack_rows,
            write_ibkr_readonly_qualification_sandbox_result_pack_csv,
            write_ibkr_readonly_qualification_sandbox_result_pack_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_result_pack
            if args.ibkr_readonly_qualification_sandbox_result_pack
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_result_pack_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_result_pack_csv",
                "ibkr_readonly_qualification_sandbox_result_pack.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_result_pack_report",
                "reports/ibkr_readonly_qualification_sandbox_result_pack_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_result_pack_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_result_pack_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_result_pack_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        simulated_count = sum(1 for r in rows if r.sandbox_qualification_status == "SIMULATED")
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_RESULT_PACK] "
            f"rows={len(rows)} statuses={status_text} simulated_results={simulated_count} "
            "simulated_result_only=true real_qualification_allowed=false "
            "tws_connection_allowed=false ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_result_pack_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox result pack only. "
            "Simulated results are not real IBKR qualification. "
            "No TWS connection / no IBKR connection / no reqMktData / no reqHistoricalData / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_qualification_simulator is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_qualification_simulator import (
            build_ibkr_readonly_qualification_sandbox_qualification_simulator_rows,
            write_ibkr_readonly_qualification_sandbox_qualification_simulator_csv,
            write_ibkr_readonly_qualification_sandbox_qualification_simulator_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_qualification_simulator
            if args.ibkr_readonly_qualification_sandbox_qualification_simulator
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_qualification_simulator_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_qualification_simulator_csv",
                "ibkr_readonly_qualification_sandbox_qualification_simulator.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_qualification_simulator_report",
                "reports/ibkr_readonly_qualification_sandbox_qualification_simulator_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_qualification_simulator_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_qualification_simulator_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_qualification_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        simulated_count = sum(1 for r in rows if r.sandbox_qualification_status == "SIMULATED")
        not_simulated_count = sum(1 for r in rows if r.sandbox_qualification_status == "NOT_SIMULATED")
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_QUALIFICATION_SIMULATOR] "
            f"rows={len(rows)} statuses={status_text} simulated={simulated_count} not_simulated={not_simulated_count} "
            "real_qualification_allowed=false tws_connection_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_qualification_simulator_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox qualification simulator only. "
            "No real qualification / no TWS connection / no IBKR connection / "
            "no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_input_validator is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_input_validator import (
            build_ibkr_readonly_qualification_sandbox_input_validator_rows,
            write_ibkr_readonly_qualification_sandbox_input_validator_csv,
            write_ibkr_readonly_qualification_sandbox_input_validator_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_input_validator
            if args.ibkr_readonly_qualification_sandbox_input_validator
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_input_validator_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_input_validator_csv",
                "ibkr_readonly_qualification_sandbox_input_validator.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_input_validator_report",
                "reports/ibkr_readonly_qualification_sandbox_input_validator_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_input_validator_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_input_validator_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_input_validation_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        allowed_count = sum(1 for r in rows if r.input_allowed == "true")
        rejected_count = sum(1 for r in rows if r.rejection_required == "true")
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_INPUT_VALIDATOR] "
            f"rows={len(rows)} statuses={status_text} allowed_inputs={allowed_count} rejected_inputs={rejected_count} "
            "sandbox_execution_allowed=false tws_connection_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_input_validator_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox input validator only. "
            "No real TWS input / no real IBKR runtime input / no TWS connection / no IBKR connection / "
            "no real contract qualification / no reqMktData / no reqHistoricalData / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_input_contract is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_input_contract import (
            build_ibkr_readonly_qualification_sandbox_input_contract_rows,
            write_ibkr_readonly_qualification_sandbox_input_contract_csv,
            write_ibkr_readonly_qualification_sandbox_input_contract_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_input_contract
            if args.ibkr_readonly_qualification_sandbox_input_contract
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_input_contract_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_input_contract_csv",
                "ibkr_readonly_qualification_sandbox_input_contract.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_input_contract_report",
                "reports/ibkr_readonly_qualification_sandbox_input_contract_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_input_contract_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_input_contract_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_input_contract_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_INPUT_CONTRACT] "
            f"rows={len(rows)} statuses={status_text} "
            "requires_explicit_sandbox_input=true accepts_real_tws_input=false "
            "accepts_real_ibkr_runtime_input=false sandbox_execution_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_input_contract_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox input contract only. "
            "No real TWS input / no real IBKR runtime input / no TWS connection / no IBKR connection / "
            "no real contract qualification / no reqMktData / no reqHistoricalData / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_design is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_design import (
            build_ibkr_readonly_qualification_sandbox_design_rows,
            write_ibkr_readonly_qualification_sandbox_design_csv,
            write_ibkr_readonly_qualification_sandbox_design_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_design
            if args.ibkr_readonly_qualification_sandbox_design
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_design_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_design_csv",
                "ibkr_readonly_qualification_sandbox_design.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_design_report",
                "reports/ibkr_readonly_qualification_sandbox_design_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_design_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_design_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_design_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_DESIGN] "
            f"rows={len(rows)} statuses={status_text} "
            "sandbox_execution_allowed=false real_ibkr_connection_allowed=false "
            "tws_connection_allowed=false ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_design_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox design only. "
            "No TWS connection / no IBKR connection / no real contract qualification / "
            "no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_phase12_closure_report is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_phase12_closure_report import (
            build_ibkr_readonly_qualification_phase12_closure_report_rows,
            write_ibkr_readonly_qualification_phase12_closure_report_csv,
            write_ibkr_readonly_qualification_phase12_closure_report_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_phase12_closure_report
            if args.ibkr_readonly_qualification_phase12_closure_report
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_phase12_closure_report_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_phase12_closure_report_csv",
                "ibkr_readonly_qualification_phase12_closure_report.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_phase12_closure_report",
                "reports/ibkr_readonly_qualification_phase12_closure_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_phase12_closure_report_csv(csv_path, rows)
        write_ibkr_readonly_qualification_phase12_closure_report_report(md_path, rows, input_source)

        statuses = sorted({r.phase12_closure_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_QUALIFICATION_PHASE12_CLOSURE_REPORT] "
            f"rows={len(rows)} statuses={status_text} "
            "final_authorization_status=BLOCKED final_authorization_allowed=false "
            "effective_approval_gate_status=CLOSED approval_effective=false "
            "qualification_allowed=false tws_connection_allowed=false "
            "api_request_allowed=false action_allowed=false"
        )
        print(f"phase12_closure_report_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification Phase 12 closure report only. "
            "Phase 12 is complete but final authorization remains BLOCKED. "
            "No TWS connection / no IBKR connection / no real contract qualification / "
            "no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_final_authorization_packet is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_final_authorization_packet import (
            build_ibkr_readonly_qualification_final_authorization_packet_rows,
            write_ibkr_readonly_qualification_final_authorization_packet_csv,
            write_ibkr_readonly_qualification_final_authorization_packet_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_final_authorization_packet
            if args.ibkr_readonly_qualification_final_authorization_packet
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_final_authorization_packet_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_final_authorization_packet_csv",
                "ibkr_readonly_qualification_final_authorization_packet.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_final_authorization_packet_report",
                "reports/ibkr_readonly_qualification_final_authorization_packet_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_final_authorization_packet_csv(csv_path, rows)
        write_ibkr_readonly_qualification_final_authorization_packet_report(md_path, rows, input_source)

        statuses = sorted({r.final_authorization_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_QUALIFICATION_FINAL_AUTHORIZATION_PACKET] "
            f"rows={len(rows)} statuses={status_text} "
            "final_authorization_allowed=false effective_approval_gate_status=CLOSED "
            "approval_effective=false qualification_allowed=false tws_connection_allowed=false "
            "api_request_allowed=false action_allowed=false"
        )
        print(f"final_authorization_packet_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification final authorization packet only. "
            "Final authorization remains BLOCKED. "
            "No TWS connection / no IBKR connection / no real contract qualification / "
            "no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_effective_approval_gate is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_effective_approval_gate import (
            build_ibkr_readonly_qualification_effective_approval_gate_rows,
            write_ibkr_readonly_qualification_effective_approval_gate_csv,
            write_ibkr_readonly_qualification_effective_approval_gate_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_effective_approval_gate
            if args.ibkr_readonly_qualification_effective_approval_gate
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_effective_approval_gate_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_effective_approval_gate_csv",
                "ibkr_readonly_qualification_effective_approval_gate.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_effective_approval_gate_report",
                "reports/ibkr_readonly_qualification_effective_approval_gate_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_effective_approval_gate_csv(csv_path, rows)
        write_ibkr_readonly_qualification_effective_approval_gate_report(md_path, rows, input_source)

        gate_statuses = sorted({r.effective_approval_gate_status for r in rows})
        gate_text = ",".join(gate_statuses) if gate_statuses else "none"
        print(
            "[IBKR_READONLY_QUALIFICATION_EFFECTIVE_APPROVAL_GATE] "
            f"rows={len(rows)} gate_statuses={gate_text} "
            "approval_effective=false effective_approval_allowed=false "
            "candidate_final_gate_status=CLOSED candidate_safety_status=BLOCKED "
            "qualification_allowed=false tws_connection_allowed=false "
            "api_request_allowed=false action_allowed=false"
        )
        print(f"effective_approval_gate_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification effective approval gate only. "
            "Gate remains CLOSED and approval_effective=false. "
            "No TWS connection / no IBKR connection / no real contract qualification / "
            "no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_operator_approval_stub is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_operator_approval_stub import (
            build_ibkr_readonly_qualification_operator_approval_stub_rows,
            write_ibkr_readonly_qualification_operator_approval_stub_csv,
            write_ibkr_readonly_qualification_operator_approval_stub_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_operator_approval_stub
            if args.ibkr_readonly_qualification_operator_approval_stub
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_operator_approval_stub_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_operator_approval_stub_csv",
                "ibkr_readonly_qualification_operator_approval_stub.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_operator_approval_stub_report",
                "reports/ibkr_readonly_qualification_operator_approval_stub_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_operator_approval_stub_csv(csv_path, rows)
        write_ibkr_readonly_qualification_operator_approval_stub_report(md_path, rows, input_source)

        statuses = sorted({r.operator_approval_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_QUALIFICATION_OPERATOR_APPROVAL_STUB] "
            f"rows={len(rows)} statuses={status_text} "
            "approval_effective=false candidate_final_gate_status=CLOSED candidate_safety_status=BLOCKED "
            "qualification_allowed=false tws_connection_allowed=false "
            "api_request_allowed=false action_allowed=false"
        )
        print(f"operator_approval_stub_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification operator approval stub only. "
            "Operator approval remains PENDING and approval_effective=false. "
            "No TWS connection / no IBKR connection / no real contract qualification / "
            "no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_operator_decision_ledger is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_operator_decision_ledger import (
            build_ibkr_readonly_qualification_operator_decision_ledger_rows,
            write_ibkr_readonly_qualification_operator_decision_ledger_csv,
            write_ibkr_readonly_qualification_operator_decision_ledger_report,
        )

        input_path = (
            args.ibkr_readonly_qualification_operator_decision_ledger
            if args.ibkr_readonly_qualification_operator_decision_ledger
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_operator_decision_ledger_rows(input_path)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_operator_decision_ledger_csv",
                "ibkr_readonly_qualification_operator_decision_ledger.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_operator_decision_ledger_report",
                "reports/ibkr_readonly_qualification_operator_decision_ledger_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_operator_decision_ledger_csv(csv_path, rows)
        write_ibkr_readonly_qualification_operator_decision_ledger_report(md_path, rows, input_path)

        statuses = sorted({r.operator_decision_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_QUALIFICATION_OPERATOR_DECISION_LEDGER] "
            f"rows={len(rows)} statuses={status_text} "
            "candidate_final_gate_status=CLOSED candidate_safety_status=BLOCKED "
            "qualification_allowed=false tws_connection_allowed=false "
            "api_request_allowed=false action_allowed=false"
        )
        print(f"operator_decision_ledger_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification operator decision ledger only. "
            "Operator decision remains PENDING and candidate safety remains BLOCKED. "
            "No TWS connection / no IBKR connection / no real contract qualification / "
            "no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_candidate_safety_summary is not None:
        from pathlib import Path
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
        from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
        from src.ibkr_readonly_qualification_safety_summary import IBKRReadOnlyQualificationSafetySummaryRow
        from src.ibkr_readonly_qualification_candidate_resolver import build_ibkr_readonly_qualification_candidate_resolver_rows
        from src.ibkr_readonly_qualification_candidate_review_pack import build_ibkr_readonly_qualification_candidate_review_pack_rows
        from src.ibkr_readonly_qualification_candidate_final_gate import build_ibkr_readonly_qualification_candidate_final_gate_rows
        from src.ibkr_readonly_qualification_candidate_safety_summary import (
            build_ibkr_readonly_qualification_candidate_safety_summary_rows,
            write_ibkr_readonly_qualification_candidate_safety_summary_csv,
            write_ibkr_readonly_qualification_candidate_safety_summary_report,
        )

        input_path = args.ibkr_readonly_qualification_candidate_safety_summary if args.ibkr_readonly_qualification_candidate_safety_summary else "data/market_data_provider_config.yaml"

        mapping_config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        dry_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])
        guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_rows, monitor.config["runtime"]["timezone"])

        safety_rows = [
            IBKRReadOnlyQualificationSafetySummaryRow(
                section_id="FINAL",
                section_name="Final IBKR read-only qualification full safety summary",
                source_layer="Phase 10G-10M + Phase 11A-11D",
                input_row_count="0",
                blocked_or_closed_count="0",
                pass_or_ready_count="0",
                summary_status="BLOCKED",
                overall_status="BLOCKED",
                apply_allowed="false",
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                blocking_summary="overall_status_blocked_until_explicit_future_phase_design_and_manual_operator_review",
                warning_flags="overall_blocked_by_default",
                notes="synthetic safety summary row for candidate safety summary",
                timestamp_jst="",
                timestamp_et="",
            )
        ]

        resolver_rows = build_ibkr_readonly_qualification_candidate_resolver_rows(
            mapping_rows,
            dry_rows,
            guard_rows,
            safety_rows,
            monitor.config["runtime"]["timezone"],
        )
        review_rows = build_ibkr_readonly_qualification_candidate_review_pack_rows(
            resolver_rows,
            monitor.config["runtime"]["timezone"],
        )
        gate_rows = build_ibkr_readonly_qualification_candidate_final_gate_rows(
            resolver_rows,
            review_rows,
            monitor.config["runtime"]["timezone"],
        )
        rows = build_ibkr_readonly_qualification_candidate_safety_summary_rows(
            resolver_rows,
            review_rows,
            gate_rows,
            monitor.config["runtime"]["timezone"],
        )

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_safety_summary_csv", "ibkr_readonly_qualification_candidate_safety_summary.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_safety_summary_report", "reports/ibkr_readonly_qualification_candidate_safety_summary_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_candidate_safety_summary_csv(csv_path, rows)
        write_ibkr_readonly_qualification_candidate_safety_summary_report(md_path, rows, input_path)

        statuses = sorted({r.candidate_safety_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CANDIDATE_SAFETY_SUMMARY] rows={len(rows)} statuses={status_text} candidate_final_gate_status=CLOSED qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"candidate_safety_summary_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification candidate safety summary only. Candidate safety status remains BLOCKED and candidate final gate remains CLOSED. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_candidate_final_gate is not None:
        from pathlib import Path
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
        from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
        from src.ibkr_readonly_qualification_safety_summary import IBKRReadOnlyQualificationSafetySummaryRow
        from src.ibkr_readonly_qualification_candidate_resolver import build_ibkr_readonly_qualification_candidate_resolver_rows
        from src.ibkr_readonly_qualification_candidate_review_pack import build_ibkr_readonly_qualification_candidate_review_pack_rows
        from src.ibkr_readonly_qualification_candidate_final_gate import (
            build_ibkr_readonly_qualification_candidate_final_gate_rows,
            write_ibkr_readonly_qualification_candidate_final_gate_csv,
            write_ibkr_readonly_qualification_candidate_final_gate_report,
        )

        input_path = args.ibkr_readonly_qualification_candidate_final_gate if args.ibkr_readonly_qualification_candidate_final_gate else "data/market_data_provider_config.yaml"

        mapping_config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        dry_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])
        guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_rows, monitor.config["runtime"]["timezone"])

        safety_rows = [
            IBKRReadOnlyQualificationSafetySummaryRow(
                section_id="FINAL",
                section_name="Final IBKR read-only qualification full safety summary",
                source_layer="Phase 10G-10M + Phase 11A-11D",
                input_row_count="0",
                blocked_or_closed_count="0",
                pass_or_ready_count="0",
                summary_status="BLOCKED",
                overall_status="BLOCKED",
                apply_allowed="false",
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                blocking_summary="overall_status_blocked_until_explicit_future_phase_design_and_manual_operator_review",
                warning_flags="overall_blocked_by_default",
                notes="synthetic safety summary row for candidate final gate",
                timestamp_jst="",
                timestamp_et="",
            )
        ]

        resolver_rows = build_ibkr_readonly_qualification_candidate_resolver_rows(
            mapping_rows,
            dry_rows,
            guard_rows,
            safety_rows,
            monitor.config["runtime"]["timezone"],
        )
        review_rows = build_ibkr_readonly_qualification_candidate_review_pack_rows(
            resolver_rows,
            monitor.config["runtime"]["timezone"],
        )
        rows = build_ibkr_readonly_qualification_candidate_final_gate_rows(
            resolver_rows,
            review_rows,
            monitor.config["runtime"]["timezone"],
        )

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_final_gate_csv", "ibkr_readonly_qualification_candidate_final_gate.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_final_gate_report", "reports/ibkr_readonly_qualification_candidate_final_gate_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_candidate_final_gate_csv(csv_path, rows)
        write_ibkr_readonly_qualification_candidate_final_gate_report(md_path, rows, input_path)

        statuses = sorted({r.candidate_final_gate_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CANDIDATE_FINAL_GATE] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"candidate_final_gate_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification candidate final gate only. Candidate final gate remains CLOSED. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_candidate_review_pack is not None:
        from pathlib import Path
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
        from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
        from src.ibkr_readonly_qualification_safety_summary import IBKRReadOnlyQualificationSafetySummaryRow
        from src.ibkr_readonly_qualification_candidate_resolver import build_ibkr_readonly_qualification_candidate_resolver_rows
        from src.ibkr_readonly_qualification_candidate_review_pack import (
            build_ibkr_readonly_qualification_candidate_review_pack_rows,
            write_ibkr_readonly_qualification_candidate_review_pack_csv,
            write_ibkr_readonly_qualification_candidate_review_pack_report,
        )

        input_path = args.ibkr_readonly_qualification_candidate_review_pack if args.ibkr_readonly_qualification_candidate_review_pack else "data/market_data_provider_config.yaml"

        mapping_config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        dry_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])
        guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_rows, monitor.config["runtime"]["timezone"])

        safety_rows = [
            IBKRReadOnlyQualificationSafetySummaryRow(
                section_id="FINAL",
                section_name="Final IBKR read-only qualification full safety summary",
                source_layer="Phase 10G-10M + Phase 11A-11D",
                input_row_count="0",
                blocked_or_closed_count="0",
                pass_or_ready_count="0",
                summary_status="BLOCKED",
                overall_status="BLOCKED",
                apply_allowed="false",
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                blocking_summary="overall_status_blocked_until_explicit_future_phase_design_and_manual_operator_review",
                warning_flags="overall_blocked_by_default",
                notes="synthetic safety summary row for candidate review pack",
                timestamp_jst="",
                timestamp_et="",
            )
        ]

        resolver_rows = build_ibkr_readonly_qualification_candidate_resolver_rows(
            mapping_rows,
            dry_rows,
            guard_rows,
            safety_rows,
            monitor.config["runtime"]["timezone"],
        )
        rows = build_ibkr_readonly_qualification_candidate_review_pack_rows(
            resolver_rows,
            monitor.config["runtime"]["timezone"],
        )

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_review_pack_csv", "ibkr_readonly_qualification_candidate_review_pack.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_review_pack_report", "reports/ibkr_readonly_qualification_candidate_review_pack_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_candidate_review_pack_csv(csv_path, rows)
        write_ibkr_readonly_qualification_candidate_review_pack_report(md_path, rows, input_path)

        statuses = sorted({r.review_pack_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CANDIDATE_REVIEW_PACK] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"candidate_review_pack_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification candidate review pack only. Operator review required. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_candidate_resolver is not None:
        from pathlib import Path
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
        from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
        from src.ibkr_readonly_qualification_safety_summary import IBKRReadOnlyQualificationSafetySummaryRow
        from src.ibkr_readonly_qualification_candidate_resolver import (
            build_ibkr_readonly_qualification_candidate_resolver_rows,
            write_ibkr_readonly_qualification_candidate_resolver_csv,
            write_ibkr_readonly_qualification_candidate_resolver_report,
        )

        input_path = args.ibkr_readonly_qualification_candidate_resolver if args.ibkr_readonly_qualification_candidate_resolver else "data/market_data_provider_config.yaml"

        mapping_config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        dry_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])
        guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_rows, monitor.config["runtime"]["timezone"])

        safety_rows = [
            IBKRReadOnlyQualificationSafetySummaryRow(
                section_id="FINAL",
                section_name="Final IBKR read-only qualification full safety summary",
                source_layer="Phase 10G-10M + Phase 11A-11D",
                input_row_count="0",
                blocked_or_closed_count="0",
                pass_or_ready_count="0",
                summary_status="BLOCKED",
                overall_status="BLOCKED",
                apply_allowed="false",
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                blocking_summary="overall_status_blocked_until_explicit_future_phase_design_and_manual_operator_review",
                warning_flags="overall_blocked_by_default",
                notes="synthetic safety summary row for candidate resolver",
                timestamp_jst="",
                timestamp_et="",
            )
        ]

        rows = build_ibkr_readonly_qualification_candidate_resolver_rows(
            mapping_rows,
            dry_rows,
            guard_rows,
            safety_rows,
            monitor.config["runtime"]["timezone"],
        )

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_resolver_csv", "ibkr_readonly_qualification_candidate_resolver.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_resolver_report", "reports/ibkr_readonly_qualification_candidate_resolver_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_candidate_resolver_csv(csv_path, rows)
        write_ibkr_readonly_qualification_candidate_resolver_report(md_path, rows, input_path)

        statuses = sorted({r.candidate_resolver_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CANDIDATE_RESOLVER] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"candidate_resolver_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification candidate resolver only. Overall status remains BLOCKED. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_safety_summary is not None:
        from pathlib import Path
        from src.ibkr_live_provider_adapter_check import (
            build_ibkr_live_provider_adapter_check_rows,
            load_ibkr_live_provider_adapter_config,
        )
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
        from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
        from src.ibkr_readonly_qualification_precheck import build_ibkr_readonly_qualification_precheck_rows
        from src.ibkr_readonly_qualification_runbook import build_ibkr_readonly_qualification_runbook_rows
        from src.ibkr_readonly_qualification_go_no_go import build_ibkr_readonly_qualification_go_no_go_rows
        from src.ibkr_readonly_qualification_config_template import (
            build_ibkr_readonly_qualification_config_template_rows,
            default_ibkr_readonly_qualification_template,
        )
        from src.ibkr_readonly_qualification_config_audit import build_ibkr_readonly_qualification_config_audit_rows
        from src.ibkr_readonly_qualification_config_apply_plan import build_ibkr_readonly_qualification_config_apply_plan_rows
        from src.ibkr_readonly_qualification_config_final_gate import build_ibkr_readonly_qualification_config_final_gate_rows
        from src.ibkr_readonly_qualification_safety_summary import (
            build_ibkr_readonly_qualification_safety_summary_rows,
            write_ibkr_readonly_qualification_safety_summary_csv,
            write_ibkr_readonly_qualification_safety_summary_report,
        )

        input_path = args.ibkr_readonly_qualification_safety_summary if args.ibkr_readonly_qualification_safety_summary else "config.yaml"

        provider_config = load_ibkr_live_provider_adapter_config("data/market_data_provider_config.yaml")
        mapping_config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")

        adapter_rows = build_ibkr_live_provider_adapter_check_rows(provider_config, monitor.config["runtime"]["timezone"])
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        dry_run_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])
        guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_run_rows, monitor.config["runtime"]["timezone"])
        precheck_rows = build_ibkr_readonly_qualification_precheck_rows({}, monitor.config["runtime"]["timezone"])
        runbook_rows = build_ibkr_readonly_qualification_runbook_rows(precheck_rows, monitor.config["runtime"]["timezone"])
        go_no_go_rows = build_ibkr_readonly_qualification_go_no_go_rows(
            adapter_rows,
            mapping_rows,
            dry_run_rows,
            guard_rows,
            precheck_rows,
            runbook_rows,
            monitor.config["runtime"]["timezone"],
        )

        template_rows = build_ibkr_readonly_qualification_config_template_rows(monitor.config["runtime"]["timezone"])
        audit_config = default_ibkr_readonly_qualification_template()
        audit_rows = build_ibkr_readonly_qualification_config_audit_rows(audit_config, monitor.config["runtime"]["timezone"])
        apply_rows = build_ibkr_readonly_qualification_config_apply_plan_rows(audit_rows, monitor.config["runtime"]["timezone"])
        gate_rows = build_ibkr_readonly_qualification_config_final_gate_rows(
            template_rows,
            audit_rows,
            apply_rows,
            monitor.config["runtime"]["timezone"],
        )

        rows = build_ibkr_readonly_qualification_safety_summary_rows(
            go_no_go_rows,
            gate_rows,
            monitor.config["runtime"]["timezone"],
        )

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_safety_summary_csv", "ibkr_readonly_qualification_safety_summary.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_safety_summary_report", "reports/ibkr_readonly_qualification_safety_summary_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_safety_summary_csv(csv_path, rows)
        write_ibkr_readonly_qualification_safety_summary_report(md_path, rows, input_path)

        statuses = sorted({r.overall_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_SAFETY_SUMMARY] rows={len(rows)} statuses={status_text} apply_allowed=false qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"safety_summary_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification full safety summary only. Overall status remains BLOCKED. No config mutation / no TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_config_final_gate is not None:
        from pathlib import Path
        from src.ibkr_readonly_qualification_config_template import (
            build_ibkr_readonly_qualification_config_template_rows,
            default_ibkr_readonly_qualification_template,
        )
        from src.ibkr_readonly_qualification_config_audit import build_ibkr_readonly_qualification_config_audit_rows
        from src.ibkr_readonly_qualification_config_apply_plan import build_ibkr_readonly_qualification_config_apply_plan_rows
        from src.ibkr_readonly_qualification_config_final_gate import (
            build_ibkr_readonly_qualification_config_final_gate_rows,
            write_ibkr_readonly_qualification_config_final_gate_csv,
            write_ibkr_readonly_qualification_config_final_gate_report,
        )

        input_path = args.ibkr_readonly_qualification_config_final_gate if args.ibkr_readonly_qualification_config_final_gate else monitor.config["runtime"].get(
            "ibkr_readonly_qualification_config_template_yaml",
            "data/ibkr_readonly_qualification_config_template.yaml",
        )

        template_rows = build_ibkr_readonly_qualification_config_template_rows(monitor.config["runtime"]["timezone"])
        audit_config = default_ibkr_readonly_qualification_template()
        audit_rows = build_ibkr_readonly_qualification_config_audit_rows(audit_config, monitor.config["runtime"]["timezone"])
        apply_rows = build_ibkr_readonly_qualification_config_apply_plan_rows(audit_rows, monitor.config["runtime"]["timezone"])
        rows = build_ibkr_readonly_qualification_config_final_gate_rows(
            template_rows,
            audit_rows,
            apply_rows,
            monitor.config["runtime"]["timezone"],
        )

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_final_gate_csv", "ibkr_readonly_qualification_config_final_gate.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_final_gate_report", "reports/ibkr_readonly_qualification_config_final_gate_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_config_final_gate_csv(csv_path, rows)
        write_ibkr_readonly_qualification_config_final_gate_report(md_path, rows, input_path)

        statuses = sorted({r.final_gate_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CONFIG_FINAL_GATE] rows={len(rows)} statuses={status_text} apply_allowed=false qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"config_final_gate_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification config final gate only. Final gate remains CLOSED. No config mutation / no TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_config_apply_plan is not None:
        from pathlib import Path
        from src.ibkr_readonly_qualification_config_audit import (
            build_ibkr_readonly_qualification_config_audit_rows,
            load_ibkr_readonly_qualification_config_audit_config,
        )
        from src.ibkr_readonly_qualification_config_apply_plan import (
            build_ibkr_readonly_qualification_config_apply_plan_rows,
            write_ibkr_readonly_qualification_config_apply_plan_csv,
            write_ibkr_readonly_qualification_config_apply_plan_report,
        )

        input_path = args.ibkr_readonly_qualification_config_apply_plan if args.ibkr_readonly_qualification_config_apply_plan else monitor.config["runtime"].get(
            "ibkr_readonly_qualification_config_template_yaml",
            "data/ibkr_readonly_qualification_config_template.yaml",
        )
        audit_config = load_ibkr_readonly_qualification_config_audit_config(input_path)
        audit_rows = build_ibkr_readonly_qualification_config_audit_rows(audit_config, monitor.config["runtime"]["timezone"])
        rows = build_ibkr_readonly_qualification_config_apply_plan_rows(audit_rows, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_apply_plan_csv", "ibkr_readonly_qualification_config_apply_plan.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_apply_plan_report", "reports/ibkr_readonly_qualification_config_apply_plan_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_config_apply_plan_csv(csv_path, rows)
        write_ibkr_readonly_qualification_config_apply_plan_report(md_path, rows, input_path)

        statuses = sorted({r.apply_plan_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CONFIG_APPLY_PLAN] rows={len(rows)} statuses={status_text} apply_allowed=false qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"config_apply_plan_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification config apply plan only. No config mutation / no TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_config_audit is not None:
        from pathlib import Path
        from src.ibkr_readonly_qualification_config_audit import (
            build_ibkr_readonly_qualification_config_audit_rows,
            load_ibkr_readonly_qualification_config_audit_config,
            write_ibkr_readonly_qualification_config_audit_csv,
            write_ibkr_readonly_qualification_config_audit_report,
        )

        input_path = args.ibkr_readonly_qualification_config_audit if args.ibkr_readonly_qualification_config_audit else monitor.config["runtime"].get(
            "ibkr_readonly_qualification_config_template_yaml",
            "data/ibkr_readonly_qualification_config_template.yaml",
        )
        audit_config = load_ibkr_readonly_qualification_config_audit_config(input_path)
        rows = build_ibkr_readonly_qualification_config_audit_rows(audit_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_audit_csv", "ibkr_readonly_qualification_config_audit.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_audit_report", "reports/ibkr_readonly_qualification_config_audit_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_config_audit_csv(csv_path, rows)
        write_ibkr_readonly_qualification_config_audit_report(md_path, rows, input_path)

        statuses = sorted({r.config_audit_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CONFIG_AUDIT] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"config_audit_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification config audit only. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_config_template is not None:
        from pathlib import Path
        from src.ibkr_readonly_qualification_config_template import (
            build_ibkr_readonly_qualification_config_template_rows,
            write_ibkr_readonly_qualification_config_template_csv,
            write_ibkr_readonly_qualification_config_template_report,
            write_ibkr_readonly_qualification_template_yaml,
        )

        template_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_config_template_yaml",
                "data/ibkr_readonly_qualification_config_template.yaml",
            )
        )
        rows = build_ibkr_readonly_qualification_config_template_rows(monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_template_csv", "ibkr_readonly_qualification_config_template.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_template_report", "reports/ibkr_readonly_qualification_config_template_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_config_template_csv(csv_path, rows)
        write_ibkr_readonly_qualification_config_template_report(md_path, rows, str(template_path))
        write_ibkr_readonly_qualification_template_yaml(template_path)

        statuses = sorted({r.template_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CONFIG_TEMPLATE] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"config_template_csv={csv_path}")
        print(f"config_template_yaml={template_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification config template only. Template remains disabled by default. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_go_no_go is not None:
        from pathlib import Path
        from src.ibkr_live_provider_adapter_check import (
            build_ibkr_live_provider_adapter_check_rows,
            load_ibkr_live_provider_adapter_config,
        )
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
        from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
        from src.ibkr_readonly_qualification_precheck import build_ibkr_readonly_qualification_precheck_rows
        from src.ibkr_readonly_qualification_runbook import build_ibkr_readonly_qualification_runbook_rows
        from src.ibkr_readonly_qualification_go_no_go import (
            build_ibkr_readonly_qualification_go_no_go_rows,
            write_ibkr_readonly_qualification_go_no_go_csv,
            write_ibkr_readonly_qualification_go_no_go_report,
        )

        input_path = args.ibkr_readonly_qualification_go_no_go if args.ibkr_readonly_qualification_go_no_go else "config.yaml"
        provider_config = load_ibkr_live_provider_adapter_config("data/market_data_provider_config.yaml")
        mapping_config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")

        adapter_rows = build_ibkr_live_provider_adapter_check_rows(provider_config, monitor.config["runtime"]["timezone"])
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        dry_run_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])
        guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_run_rows, monitor.config["runtime"]["timezone"])
        precheck_rows = build_ibkr_readonly_qualification_precheck_rows({}, monitor.config["runtime"]["timezone"])
        runbook_rows = build_ibkr_readonly_qualification_runbook_rows(precheck_rows, monitor.config["runtime"]["timezone"])
        rows = build_ibkr_readonly_qualification_go_no_go_rows(
            adapter_rows,
            mapping_rows,
            dry_run_rows,
            guard_rows,
            precheck_rows,
            runbook_rows,
            monitor.config["runtime"]["timezone"],
        )

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_go_no_go_csv", "ibkr_readonly_qualification_go_no_go.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_go_no_go_report", "reports/ibkr_readonly_qualification_go_no_go_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_go_no_go_csv(csv_path, rows)
        write_ibkr_readonly_qualification_go_no_go_report(md_path, rows, input_path)

        statuses = sorted({r.go_no_go_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_GO_NO_GO] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"go_no_go_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification go/no-go summary only. Final status remains NO_GO. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_runbook is not None:
        from pathlib import Path
        from src.ibkr_readonly_qualification_precheck import (
            build_ibkr_readonly_qualification_precheck_rows,
            load_ibkr_readonly_qualification_precheck_config,
        )
        from src.ibkr_readonly_qualification_runbook import (
            build_ibkr_readonly_qualification_runbook_rows,
            write_ibkr_readonly_qualification_runbook_csv,
            write_ibkr_readonly_qualification_runbook_report,
        )

        input_path = args.ibkr_readonly_qualification_runbook if args.ibkr_readonly_qualification_runbook else "config.yaml"
        precheck_config = load_ibkr_readonly_qualification_precheck_config(input_path)
        precheck_rows = build_ibkr_readonly_qualification_precheck_rows(precheck_config, monitor.config["runtime"]["timezone"])
        rows = build_ibkr_readonly_qualification_runbook_rows(precheck_rows, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_runbook_csv", "ibkr_readonly_qualification_runbook.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_runbook_report", "reports/ibkr_readonly_qualification_runbook_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_runbook_csv(csv_path, rows)
        write_ibkr_readonly_qualification_runbook_report(md_path, rows, input_path)

        statuses = sorted({r.runbook_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_RUNBOOK] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"runbook_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification runbook only. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_precheck is not None:
        from pathlib import Path
        from src.ibkr_readonly_qualification_precheck import (
            build_ibkr_readonly_qualification_precheck_rows,
            load_ibkr_readonly_qualification_precheck_config,
            write_ibkr_readonly_qualification_precheck_csv,
            write_ibkr_readonly_qualification_precheck_report,
        )

        input_path = args.ibkr_readonly_qualification_precheck if args.ibkr_readonly_qualification_precheck else "config.yaml"
        precheck_config = load_ibkr_readonly_qualification_precheck_config(input_path)
        rows = build_ibkr_readonly_qualification_precheck_rows(precheck_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_precheck_csv", "ibkr_readonly_qualification_precheck.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_precheck_report", "reports/ibkr_readonly_qualification_precheck_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_precheck_csv(csv_path, rows)
        write_ibkr_readonly_qualification_precheck_report(md_path, rows, input_path)

        statuses = sorted({r.precheck_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_PRECHECK] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"precheck_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification precheck only. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_contract_qualification_execution_guard is not None:
        from pathlib import Path
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
        from src.ibkr_contract_qualification_execution_guard import (
            build_ibkr_contract_qualification_execution_guard_rows,
            write_ibkr_contract_qualification_execution_guard_csv,
            write_ibkr_contract_qualification_execution_guard_report,
        )

        input_path = args.ibkr_contract_qualification_execution_guard if args.ibkr_contract_qualification_execution_guard else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        mapping_config = load_ibkr_contract_mapping_config(input_path)
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        dry_run_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])
        rows = build_ibkr_contract_qualification_execution_guard_rows(dry_run_rows, monitor.config["runtime"]["timezone"], explicit_execution_flag=False)

        csv_path = Path(monitor.config["runtime"].get("ibkr_contract_qualification_execution_guard_csv", "ibkr_contract_qualification_execution_guard.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_contract_qualification_execution_guard_report", "reports/ibkr_contract_qualification_execution_guard_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_contract_qualification_execution_guard_csv(csv_path, rows)
        write_ibkr_contract_qualification_execution_guard_report(md_path, rows, input_path)

        statuses = sorted({r.execution_guard_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_CONTRACT_QUALIFICATION_EXECUTION_GUARD] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"execution_guard_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR contract qualification execution guard only. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_contract_qualification_dry_run is not None:
        from pathlib import Path
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import (
            build_ibkr_contract_qualification_dry_run_rows,
            write_ibkr_contract_qualification_dry_run_csv,
            write_ibkr_contract_qualification_dry_run_report,
        )

        input_path = args.ibkr_contract_qualification_dry_run if args.ibkr_contract_qualification_dry_run else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        mapping_config = load_ibkr_contract_mapping_config(input_path)
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_contract_qualification_dry_run_csv", "ibkr_contract_qualification_dry_run.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_contract_qualification_dry_run_report", "reports/ibkr_contract_qualification_dry_run_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_contract_qualification_dry_run_csv(csv_path, rows)
        write_ibkr_contract_qualification_dry_run_report(md_path, rows, input_path)

        statuses = sorted({r.qualification_dry_run_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_CONTRACT_QUALIFICATION_DRY_RUN] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"qualification_dry_run_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR contract qualification dry-run only. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_contract_mapping_plan is not None:
        from pathlib import Path
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
            write_ibkr_contract_mapping_plan_csv,
            write_ibkr_contract_mapping_plan_report,
        )

        input_path = args.ibkr_contract_mapping_plan if args.ibkr_contract_mapping_plan else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        mapping_config = load_ibkr_contract_mapping_config(input_path)
        rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_contract_mapping_plan_csv", "ibkr_contract_mapping_plan.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_contract_mapping_plan_report", "reports/ibkr_contract_mapping_plan_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_contract_mapping_plan_csv(csv_path, rows)
        write_ibkr_contract_mapping_plan_report(md_path, rows, input_path)

        statuses = sorted({r.mapping_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_CONTRACT_MAPPING_PLAN] rows={len(rows)} statuses={status_text} tws_connection_allowed=false market_data_request_allowed=false api_request_allowed=false action_allowed=false")
        print(f"contract_mapping_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR contract mapping plan only. No TWS connection / no IBKR connection / no contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_live_provider_adapter_check is not None:
        from pathlib import Path
        from src.ibkr_live_provider_adapter_check import (
            build_ibkr_live_provider_adapter_check_rows,
            load_ibkr_live_provider_adapter_config,
            write_ibkr_live_provider_adapter_check_csv,
            write_ibkr_live_provider_adapter_check_report,
        )

        input_path = args.ibkr_live_provider_adapter_check if args.ibkr_live_provider_adapter_check else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_ibkr_live_provider_adapter_config(input_path)
        rows = build_ibkr_live_provider_adapter_check_rows(provider_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_live_provider_adapter_check_csv", "ibkr_live_provider_adapter_check.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_live_provider_adapter_check_report", "reports/ibkr_live_provider_adapter_check_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_live_provider_adapter_check_csv(csv_path, rows)
        write_ibkr_live_provider_adapter_check_report(md_path, rows, input_path)

        statuses = sorted({r.adapter_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_LIVE_PROVIDER_ADAPTER_CHECK] rows={len(rows)} statuses={status_text} tws_connection_allowed=false market_data_request_allowed=false api_request_allowed=false action_allowed=false")
        print(f"ibkr_adapter_check_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR live provider adapter skeleton only. No TWS connection / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.live_final_research_review_pack is not None:
        from pathlib import Path
        from src.live_provider_mock_adapter import (
            build_live_provider_mock_adapter_rows,
            load_live_provider_mock_adapter_config,
        )
        from src.live_data_quality_gate import build_live_data_quality_gate_rows
        from src.live_research_review_pack import build_live_research_review_pack_rows
        from src.live_final_research_review_pack import (
            build_live_final_research_review_pack_rows,
            write_live_final_research_review_pack_csv,
            write_live_final_research_review_pack_report,
        )

        input_path = args.live_final_research_review_pack if args.live_final_research_review_pack else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_live_provider_mock_adapter_config(input_path)
        mock_rows = build_live_provider_mock_adapter_rows(provider_config, monitor.config["runtime"]["timezone"])
        mock_rows_by_target = {row.target_id: row.__dict__ for row in mock_rows}
        quality_rows = build_live_data_quality_gate_rows(mock_rows_by_target, monitor.config["runtime"]["timezone"])
        research_rows = build_live_research_review_pack_rows(quality_rows, monitor.config["runtime"]["timezone"])
        research_rows_by_target = {row.target_id: row.__dict__ for row in research_rows}
        rows = build_live_final_research_review_pack_rows(research_rows_by_target, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("live_final_research_review_pack_csv", "live_final_research_review_pack.csv"))
        md_path = Path(monitor.config["runtime"].get("live_final_research_review_pack_report", "reports/live_final_research_review_pack_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_live_final_research_review_pack_csv(csv_path, rows)
        write_live_final_research_review_pack_report(md_path, rows, input_path)

        statuses = sorted({r.final_plan_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[LIVE_FINAL_RESEARCH_REVIEW_PACK] rows={len(rows)} statuses={status_text} api_request_allowed=false action_allowed=false")
        print(f"live_final_research_review_pack_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Live/mock final research review pack only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.live_research_review_pack is not None:
        from pathlib import Path
        from src.live_provider_mock_adapter import (
            build_live_provider_mock_adapter_rows,
            load_live_provider_mock_adapter_config,
        )
        from src.live_data_quality_gate import build_live_data_quality_gate_rows
        from src.live_research_review_pack import (
            build_live_research_review_pack_rows,
            write_live_research_review_pack_csv,
            write_live_research_review_pack_report,
        )

        input_path = args.live_research_review_pack if args.live_research_review_pack else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_live_provider_mock_adapter_config(input_path)
        mock_rows = build_live_provider_mock_adapter_rows(provider_config, monitor.config["runtime"]["timezone"])
        mock_rows_by_target = {row.target_id: row.__dict__ for row in mock_rows}
        quality_rows = build_live_data_quality_gate_rows(mock_rows_by_target, monitor.config["runtime"]["timezone"])
        rows = build_live_research_review_pack_rows(quality_rows, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("live_research_review_pack_csv", "live_research_review_pack.csv"))
        md_path = Path(monitor.config["runtime"].get("live_research_review_pack_report", "reports/live_research_review_pack_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_live_research_review_pack_csv(csv_path, rows)
        write_live_research_review_pack_report(md_path, rows, input_path)

        statuses = sorted({r.research_pack_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[LIVE_RESEARCH_REVIEW_PACK] rows={len(rows)} statuses={status_text} api_request_allowed=false action_allowed=false")
        print(f"live_research_review_pack_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Live/mock research review pack bridge only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.live_data_quality_gate is not None:
        from pathlib import Path
        from src.live_provider_mock_adapter import (
            build_live_provider_mock_adapter_rows,
            load_live_provider_mock_adapter_config,
        )
        from src.live_data_quality_gate import (
            build_live_data_quality_gate_rows,
            write_live_data_quality_gate_csv,
            write_live_data_quality_gate_report,
        )

        input_path = args.live_data_quality_gate if args.live_data_quality_gate else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_live_provider_mock_adapter_config(input_path)
        mock_rows = build_live_provider_mock_adapter_rows(provider_config, monitor.config["runtime"]["timezone"])
        mock_rows_by_target = {row.target_id: row.__dict__ for row in mock_rows}
        rows = build_live_data_quality_gate_rows(mock_rows_by_target, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("live_data_quality_gate_csv", "live_data_quality_gate.csv"))
        md_path = Path(monitor.config["runtime"].get("live_data_quality_gate_report", "reports/live_data_quality_gate_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_live_data_quality_gate_csv(csv_path, rows)
        write_live_data_quality_gate_report(md_path, rows, input_path)

        statuses = sorted({r.quality_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[LIVE_DATA_QUALITY_GATE] rows={len(rows)} statuses={status_text} api_request_allowed=false action_allowed=false")
        print(f"quality_gate_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Live/mock data quality gate only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.live_provider_mock_adapter is not None:
        from pathlib import Path
        from src.live_provider_mock_adapter import (
            build_live_provider_mock_adapter_rows,
            load_live_provider_mock_adapter_config,
            write_live_provider_mock_adapter_csv,
            write_live_provider_mock_adapter_report,
        )

        input_path = args.live_provider_mock_adapter if args.live_provider_mock_adapter else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_live_provider_mock_adapter_config(input_path)
        rows = build_live_provider_mock_adapter_rows(provider_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("live_provider_mock_adapter_csv", "live_provider_mock_adapter.csv"))
        md_path = Path(monitor.config["runtime"].get("live_provider_mock_adapter_report", "reports/live_provider_mock_adapter_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_live_provider_mock_adapter_csv(csv_path, rows)
        write_live_provider_mock_adapter_report(md_path, rows, input_path)

        statuses = sorted({r.data_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[LIVE_PROVIDER_MOCK_ADAPTER] rows={len(rows)} statuses={status_text} api_request_allowed=false action_allowed=false")
        print(f"mock_adapter_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Live provider mock adapter only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.live_provider_request_gate is not None:
        from pathlib import Path
        from src.live_provider_request_gate import (
            build_live_provider_request_gate_rows,
            load_live_provider_request_gate_config,
            write_live_provider_request_gate_csv,
            write_live_provider_request_gate_report,
        )

        input_path = args.live_provider_request_gate if args.live_provider_request_gate else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_live_provider_request_gate_config(input_path)
        rows = build_live_provider_request_gate_rows(provider_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("live_provider_request_gate_csv", "live_provider_request_gate.csv"))
        md_path = Path(monitor.config["runtime"].get("live_provider_request_gate_report", "reports/live_provider_request_gate_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_live_provider_request_gate_csv(csv_path, rows)
        write_live_provider_request_gate_report(md_path, rows, input_path)

        statuses = sorted({r.gate_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[LIVE_PROVIDER_REQUEST_GATE] rows={len(rows)} statuses={status_text} api_request_allowed=false action_allowed=false")
        print(f"request_gate_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Live provider request gate safety check only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.live_provider_interface_check is not None:
        from pathlib import Path
        from src.live_market_data_provider_interface import (
            build_live_provider_interface_check_rows,
            load_live_provider_interface_config,
            write_live_provider_interface_check_csv,
            write_live_provider_interface_check_report,
        )

        input_path = args.live_provider_interface_check if args.live_provider_interface_check else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_live_provider_interface_config(input_path)
        rows = build_live_provider_interface_check_rows(provider_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("live_provider_interface_check_csv", "live_provider_interface_check.csv"))
        md_path = Path(monitor.config["runtime"].get("live_provider_interface_check_report", "reports/live_provider_interface_check_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_live_provider_interface_check_csv(csv_path, rows)
        write_live_provider_interface_check_report(md_path, rows, input_path)

        statuses = sorted({r.interface_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[LIVE_PROVIDER_INTERFACE_CHECK] rows={len(rows)} statuses={status_text} api_request_allowed=false action_allowed=false")
        print(f"interface_check_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Live provider interface safety check only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.market_data_provider_selector is not None:
        from pathlib import Path
        from src.market_data_provider_selector import (
            build_market_data_provider_selector_rows,
            load_market_data_provider_selector_config,
            write_market_data_provider_selector_csv,
            write_market_data_provider_selector_report,
        )

        input_path = args.market_data_provider_selector if args.market_data_provider_selector else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_market_data_provider_selector_config(input_path)
        rows = build_market_data_provider_selector_rows(provider_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("market_data_provider_selector_csv", "market_data_provider_selector.csv"))
        md_path = Path(monitor.config["runtime"].get("market_data_provider_selector_report", "reports/market_data_provider_selector_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_market_data_provider_selector_csv(csv_path, rows)
        write_market_data_provider_selector_report(md_path, rows, input_path)

        statuses = sorted({r.selection_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[MARKET_DATA_PROVIDER_SELECTOR] rows={len(rows)} statuses={status_text} live_request_allowed=false action_allowed=false")
        print(f"selector_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Provider selector planning only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.market_data_provider_config_audit is not None:
        from pathlib import Path
        from src.market_data_provider_config_audit import (
            build_market_data_provider_config_audit_rows,
            load_market_data_provider_config,
            write_market_data_provider_config_audit_csv,
            write_market_data_provider_config_audit_report,
        )

        input_path = args.market_data_provider_config_audit if args.market_data_provider_config_audit else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_market_data_provider_config(input_path)
        rows = build_market_data_provider_config_audit_rows(provider_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("market_data_provider_config_audit_csv", "market_data_provider_config_audit.csv"))
        md_path = Path(monitor.config["runtime"].get("market_data_provider_config_audit_report", "reports/market_data_provider_config_audit_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_market_data_provider_config_audit_csv(csv_path, rows)
        write_market_data_provider_config_audit_report(md_path, rows, input_path)

        statuses = sorted({r.config_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[MARKET_DATA_PROVIDER_CONFIG_AUDIT] providers={len(rows)} statuses={status_text} action_allowed=false")
        print(f"config_audit_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Provider config audit only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.market_data_provider_readiness:
        from pathlib import Path
        from src.market_data_provider_readiness import (
            build_market_data_provider_readiness_rows,
            load_market_data_provider_readiness_config,
            write_market_data_provider_readiness_csv,
            write_market_data_provider_readiness_report,
        )

        config_path = monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_market_data_provider_readiness_config(config_path)
        rows = build_market_data_provider_readiness_rows(monitor.config["runtime"]["timezone"], provider_config)

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
