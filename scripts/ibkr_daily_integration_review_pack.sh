#!/usr/bin/env bash
set -euo pipefail

DAILY_INTEGRATION_CSV="ibkr_daily_integration_preflight.csv"
CSV_PATH="ibkr_daily_integration_review_pack.csv"
REPORT_PATH="reports/ibkr_daily_integration_review_pack_report.md"

for arg in "$@"; do
  case "$arg" in
    --daily-integration=*)
      DAILY_INTEGRATION_CSV="${arg#--daily-integration=}"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

export DAILY_INTEGRATION_CSV CSV_PATH REPORT_PATH
export RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
export RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
export BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
export COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"

mkdir -p reports

echo "[INFO] IBKR daily integration review pack bridge started: ${RUN_TS}"

python3 - <<'PY'
from pathlib import Path
import os

from src.ibkr_daily_integration_review_pack import (
    build_review_rows,
    missing_input_review_row,
    read_daily_integration_rows,
    summarize_data_quality_tiers,
    write_review_pack_csv,
    write_review_pack_report,
)

input_path = Path(os.environ["DAILY_INTEGRATION_CSV"])
input_status, input_rows = read_daily_integration_rows(input_path)

if input_rows:
    rows = build_review_rows(input_rows)
else:
    rows = [missing_input_review_row(str(input_path))]

csv_path = Path(os.environ["CSV_PATH"])
report_path = Path(os.environ["REPORT_PATH"])

write_review_pack_csv(csv_path, rows)
write_review_pack_report(report_path, rows, str(input_path), input_status)

review_statuses = sorted({row.review_status for row in rows})
decision_labels = sorted({row.decision_label for row in rows})
tiers = summarize_data_quality_tiers(rows)

print("[PASS] IBKR daily integration review pack bridge generated")
print(f"daily_integration_input_status={input_status}")
print("review_pack_status=NO_GO")
print("action_allowed=false")
print("manual_review_required=true")
print("review_statuses=" + ",".join(review_statuses))
print("decision_labels=" + ",".join(decision_labels))
print("data_quality_tiers=" + ",".join(f"{k}:{v}" for k, v in sorted(tiers.items())))
print(f"csv={csv_path}")
print(f"report={report_path}")
PY
