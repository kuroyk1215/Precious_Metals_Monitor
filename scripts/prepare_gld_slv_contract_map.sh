#!/usr/bin/env bash
set -euo pipefail

export RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
export RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
export BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
export COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"
export CSV_PATH="ibkr_verified_contract_map_gld_slv.csv"

echo "[INFO] GLD/SLV first-validation contract map preparation started: ${RUN_TS}"

python3 - <<'PY'
from pathlib import Path
import csv
import os

rows = []
for display_symbol in ("GLD", "SLV"):
    rows.append(
        {
            "run_id": os.environ["RUN_ID"],
            "run_timestamp": os.environ["RUN_TS"],
            "timezone": "Asia/Tokyo",
            "branch": os.environ["BRANCH"],
            "commit": os.environ["COMMIT"],
            "workflow": "prepare_gld_slv_contract_map",
            "display_symbol": display_symbol,
            "status": "MAP_READY",
            "symbol": display_symbol,
            "sec_type": "STK",
            "exchange": "SMART",
            "primary_exchange": "ARCA",
            "currency": "USD",
            "conid": "",
            "local_symbol": "",
            "trading_class": "",
            "data_source_route": "SYMBOL_BASED_FIRST_VALIDATION",
            "market_data_allowed": "false",
            "historical_data_allowed": "false",
            "broker_execution_allowed": "false",
            "manual_review_required": "true",
            "action_allowed": "false",
            "notes": "symbol-based first validation map; no broker execution.",
        }
    )

csv_path = Path(os.environ["CSV_PATH"])
with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print("[PASS] GLD/SLV first-validation contract map generated")
print("first_validation_universe=GLD_SLV")
print("ibkr_excluded_symbol_status=518880_EXCLUDED_FROM_IBKR")
print("action_allowed=false")
print(f"csv={csv_path}")
PY
