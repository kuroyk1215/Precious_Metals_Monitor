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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    monitor = PreciousMetalsMonitor(args.config, args.watchlist, mock_mode=(args.mock or args.ibkr_smoke or bool(args.contract_search) or args.calibrate_model or args.pricing_mock or bool(args.calibration_csv) or bool(args.validate_history) or bool(args.build_history) or bool(args.source_audit) or args.ibkr_historical_plan or args.ibkr_historical_fetch))

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
