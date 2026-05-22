#!/usr/bin/env bash
set -euo pipefail

REVIEW_PACK_CSV="ibkr_daily_integration_review_pack.csv"
CSV_PATH="ibkr_final_research_review_pack.csv"
REPORT_PATH="reports/ibkr_final_research_review_pack_report.md"

for arg in "$@"; do
  case "$arg" in
    --review-pack=*)
      REVIEW_PACK_CSV="${arg#--review-pack=}"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

export REVIEW_PACK_CSV CSV_PATH REPORT_PATH
export RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
export RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
export BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
export COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"

mkdir -p reports

echo "[INFO] IBKR final research review pack bridge started: ${RUN_TS}"

python3 - <<'PY'
from pathlib import Path
import os

from src.ibkr_final_research_review_pack import (
    build_final_review_rows,
    missing_input_final_review_row,
    read_review_pack_rows,
    summarize_research_buckets,
    write_final_review_csv,
    write_final_review_report,
)

input_path = Path(os.environ["REVIEW_PACK_CSV"])
input_status, input_rows = read_review_pack_rows(input_path)

if input_rows:
    rows = build_final_review_rows(input_rows)
else:
    rows = [missing_input_final_review_row(str(input_path))]

csv_path = Path(os.environ["CSV_PATH"])
report_path = Path(os.environ["REPORT_PATH"])

write_final_review_csv(csv_path, rows)
write_final_review_report(report_path, rows, str(input_path), input_status)

statuses = sorted({row.final_review_status for row in rows})
labels = sorted({row.final_decision_label for row in rows})
buckets = summarize_research_buckets(rows)

print("[PASS] IBKR final research review pack bridge generated")
print(f"review_pack_input_status={input_status}")
print("final_research_review_status=NO_GO")
print("action_allowed=false")
print("manual_review_required=true")
print("broker_execution_triggered=false")
print("historical_data_request_triggered=false")
print("account_read_triggered=false")
print("position_read_triggered=false")
print("final_review_statuses=" + ",".join(statuses))
print("final_decision_labels=" + ",".join(labels))
print("final_research_buckets=" + ",".join(f"{k}:{v}" for k, v in sorted(buckets.items())))
print(f"csv={csv_path}")
print(f"report={report_path}")
PY
