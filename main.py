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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    monitor = PreciousMetalsMonitor(args.config, args.watchlist, mock_mode=(args.mock or args.ibkr_smoke or bool(args.contract_search)))

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
