#!/usr/bin/env bash
set -euo pipefail

FINAL_PACK_CSV="ibkr_final_research_review_pack.csv"
CSV_PATH="ibkr_daily_operator_packet.csv"
REPORT_PATH="reports/ibkr_daily_operator_packet_report.md"
EXECUTION_C_MODE="dry_run"

for arg in "$@"; do
  case "$arg" in
    --final-pack=*)
      FINAL_PACK_CSV="${arg#--final-pack=}"
      ;;
    --operator-packet=*)
      CSV_PATH="${arg#--operator-packet=}"
      ;;
    --execution-c-mode=*)
      EXECUTION_C_MODE="${arg#--execution-c-mode=}"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

case "$EXECUTION_C_MODE" in
  dry_run|execute_market_data) ;;
  *) echo "[FAIL] Invalid --execution-c-mode: $EXECUTION_C_MODE"; exit 2 ;;
esac

export FINAL_PACK_CSV CSV_PATH REPORT_PATH EXECUTION_C_MODE
export RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
export RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
export BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
export COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"

mkdir -p reports

echo "[INFO] IBKR daily operator packet started: ${RUN_TS}"

python3 - <<'PY'
from pathlib import Path
import os

from src.ibkr_daily_operator_packet import (
    build_operator_packet_rows,
    missing_input_operator_packet_row,
    read_final_pack_rows,
    summarize_operator_statuses,
    write_operator_packet_csv,
    write_operator_packet_report,
)

input_path = Path(os.environ["FINAL_PACK_CSV"])
input_status, input_rows = read_final_pack_rows(input_path)
execution_c_mode = os.environ["EXECUTION_C_MODE"]

if input_rows:
    rows = build_operator_packet_rows(input_rows, execution_c_mode)
else:
    rows = [missing_input_operator_packet_row(str(input_path), execution_c_mode)]

csv_path = Path(os.environ["CSV_PATH"])
report_path = Path(os.environ["REPORT_PATH"])

write_operator_packet_csv(csv_path, rows)
write_operator_packet_report(report_path, rows, str(input_path), input_status, execution_c_mode)

statuses = sorted({row.operator_packet_status for row in rows})
buckets = sorted({row.final_research_bucket for row in rows})
status_counts = summarize_operator_statuses(rows)

print("[PASS] IBKR daily operator packet generated")
print(f"final_pack_input_status={input_status}")
print("operator_packet_status=NO_GO")
print(f"execution_c_mode={execution_c_mode}")
print("action_allowed=false")
print("manual_review_required=true")
print("broker_execution_triggered=false")
print("historical_data_request_triggered=false")
print("account_read_triggered=false")
print("position_read_triggered=false")
print("operator_packet_statuses=" + ",".join(statuses))
print("final_research_buckets=" + ",".join(buckets))
print("operator_packet_counts=" + ",".join(f"{k}:{v}" for k, v in sorted(status_counts.items())))
print(f"csv={csv_path}")
print(f"report={report_path}")
PY
