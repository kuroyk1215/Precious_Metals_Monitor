#!/usr/bin/env bash
set -euo pipefail

EXECUTE_MARKET_DATA="false"
MARKET_DATA_TYPE="auto"
CONFIG_PATH="config.yaml"
CONTRACT_MAP_CSV="ibkr_verified_contract_map.csv"
SNAPSHOT_CSV="ibkr_market_data_snapshot.csv"
DAILY_INTEGRATION_CSV="ibkr_daily_integration_preflight.csv"
REVIEW_PACK_CSV="ibkr_daily_integration_review_pack.csv"
FINAL_PACK_CSV="ibkr_final_research_review_pack.csv"
OPERATOR_PACKET_CSV="ibkr_daily_operator_packet.csv"
SUMMARY_CSV="ibkr_daily_research_pipeline_summary.csv"
REPORT_PATH="reports/ibkr_daily_research_pipeline_report.md"

for arg in "$@"; do
  case "$arg" in
    --execute-market-data)
      EXECUTE_MARKET_DATA="true"
      ;;
    --market-data-type=*)
      MARKET_DATA_TYPE="${arg#--market-data-type=}"
      ;;
    --config=*)
      CONFIG_PATH="${arg#--config=}"
      ;;
    --contract-map=*)
      CONTRACT_MAP_CSV="${arg#--contract-map=}"
      ;;
    --snapshot=*)
      SNAPSHOT_CSV="${arg#--snapshot=}"
      ;;
    --daily-integration=*)
      DAILY_INTEGRATION_CSV="${arg#--daily-integration=}"
      ;;
    --review-pack=*)
      REVIEW_PACK_CSV="${arg#--review-pack=}"
      ;;
    --final-pack=*)
      FINAL_PACK_CSV="${arg#--final-pack=}"
      ;;
    --operator-packet=*)
      OPERATOR_PACKET_CSV="${arg#--operator-packet=}"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

case "$MARKET_DATA_TYPE" in
  auto|live|frozen|delayed|delayed_frozen) ;;
  *) echo "[FAIL] Invalid --market-data-type: $MARKET_DATA_TYPE"; exit 2 ;;
esac

EXECUTION_C_MODE="dry_run"
if [[ "$EXECUTE_MARKET_DATA" == "true" ]]; then
  EXECUTION_C_MODE="execute_market_data"
fi

export RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
export RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
export BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
export COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"
export SUMMARY_CSV REPORT_PATH

mkdir -p reports
SUMMARY_TMP="$(mktemp /tmp/ibkr_daily_pipeline_summary.XXXXXX)"
export SUMMARY_TMP

python3 - <<'PY'
import csv
import os

fields = [
    "run_id",
    "run_timestamp",
    "pipeline_status",
    "execution_c_mode",
    "step_name",
    "step_status",
    "output_csv",
    "output_report",
    "action_allowed",
    "broker_execution_triggered",
    "historical_data_request_triggered",
    "account_read_triggered",
    "position_read_triggered",
    "notes",
]
with open(os.environ["SUMMARY_TMP"], "w", newline="", encoding="utf-8") as f:
    csv.DictWriter(f, fieldnames=fields).writeheader()
PY

append_step() {
  local pipeline_status="$1"
  local step_name="$2"
  local step_status="$3"
  local output_csv="$4"
  local output_report="$5"
  local notes="$6"
  PIPELINE_STATUS="$pipeline_status" STEP_NAME="$step_name" STEP_STATUS="$step_status" OUTPUT_CSV="$output_csv" OUTPUT_REPORT="$output_report" NOTES="$notes" EXECUTION_C_MODE="$EXECUTION_C_MODE" python3 - <<'PY'
import csv
import os

row = {
    "run_id": os.environ["RUN_ID"],
    "run_timestamp": os.environ["RUN_TS"],
    "pipeline_status": os.environ["PIPELINE_STATUS"],
    "execution_c_mode": os.environ["EXECUTION_C_MODE"],
    "step_name": os.environ["STEP_NAME"],
    "step_status": os.environ["STEP_STATUS"],
    "output_csv": os.environ["OUTPUT_CSV"],
    "output_report": os.environ["OUTPUT_REPORT"],
    "action_allowed": "false",
    "broker_execution_triggered": "false",
    "historical_data_request_triggered": "false",
    "account_read_triggered": "false",
    "position_read_triggered": "false",
    "notes": os.environ["NOTES"],
}
with open(os.environ["SUMMARY_TMP"], "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(row.keys()))
    writer.writerow(row)
PY
}

write_report() {
  local pipeline_status="$1"
  PIPELINE_STATUS="$pipeline_status" EXECUTION_C_MODE="$EXECUTION_C_MODE" python3 - <<'PY'
from pathlib import Path
import csv
import os

summary_path = Path(os.environ["SUMMARY_CSV"])
tmp_path = Path(os.environ["SUMMARY_TMP"])
report_path = Path(os.environ["REPORT_PATH"])
summary_path.write_text(tmp_path.read_text(encoding="utf-8"), encoding="utf-8")

rows = list(csv.DictReader(summary_path.open(newline="", encoding="utf-8")))
row_lines = "\n".join(
    f"| {r['step_name']} | {r['step_status']} | {r['output_csv']} | {r['output_report']} | {r['notes']} |"
    for r in rows
)

report_path.write_text(
    "\n".join(
        [
            "# IBKR Daily Research Pipeline Report",
            "",
            "## Pipeline Decision",
            "",
            "| field | value |",
            "|---|---|",
            f"| pipeline_status | {os.environ['PIPELINE_STATUS']} |",
            f"| execution_c_mode | {os.environ['EXECUTION_C_MODE']} |",
            "| action_allowed | false |",
            "",
            "## Pipeline Steps",
            "",
            "| step_name | step_status | output_csv | output_report | notes |",
            "|---|---|---|---|---|",
            row_lines,
            "",
            "## Safety Confirmation",
            "",
            "- action_allowed=false",
            "- broker_execution_triggered=false",
            "- historical_data_request_triggered=false",
            "- account_read_triggered=false",
            "- position_read_triggered=false",
            "- manual_review_required=true",
            "",
            "## Operator Packet",
            "",
            "- operator_packet_csv=ibkr_daily_operator_packet.csv",
            "- operator_packet_report=reports/ibkr_daily_operator_packet_report.md",
        ]
    )
    + "\n",
    encoding="utf-8",
)
PY
}

fail_safe() {
  local step_name="$1"
  local notes="$2"
  append_step "FAILED_SAFE" "$step_name" "FAILED" "" "" "$notes"
  write_report "FAILED_SAFE"
  echo "pipeline_status=FAILED_SAFE"
  echo "action_allowed=false"
  exit 1
}

echo "[INFO] IBKR daily research pipeline started: ${RUN_TS}"

if [[ "$EXECUTE_MARKET_DATA" == "true" ]]; then
  if bash scripts/ibkr_market_data_snapshot_oneshot.sh --execute --config="$CONFIG_PATH" --contract-map="$CONTRACT_MAP_CSV" --market-data-type="$MARKET_DATA_TYPE"; then
    [[ -f "$SNAPSHOT_CSV" ]] || fail_safe "market_data_snapshot" "snapshot csv missing after execute_market_data"
    append_step "NO_GO" "market_data_snapshot" "PASS" "$SNAPSHOT_CSV" "reports/ibkr_market_data_snapshot_report.md" "execute_market_data requested; existing snapshot script handled config gate"
  else
    fail_safe "market_data_snapshot" "market data snapshot step failed"
  fi
else
  if [[ -f "$SNAPSHOT_CSV" ]]; then
    append_step "NO_GO" "market_data_snapshot" "SKIPPED_EXISTING_INPUT" "$SNAPSHOT_CSV" "" "dry_run did not call IBKR; existing snapshot file may be consumed"
  else
    append_step "NO_GO" "market_data_snapshot" "SKIPPED_MISSING_INPUT" "$SNAPSHOT_CSV" "" "dry_run did not call IBKR; missing snapshot will produce NO_GO downstream"
  fi
fi

if bash scripts/ibkr_daily_integration_preflight.sh --market-data-snapshot="$SNAPSHOT_CSV"; then
  [[ -f "ibkr_daily_integration_preflight.csv" ]] || fail_safe "daily_integration_preflight" "daily integration csv missing"
  if [[ "$DAILY_INTEGRATION_CSV" != "ibkr_daily_integration_preflight.csv" ]]; then
    cp ibkr_daily_integration_preflight.csv "$DAILY_INTEGRATION_CSV"
  fi
  append_step "NO_GO" "daily_integration_preflight" "PASS" "$DAILY_INTEGRATION_CSV" "reports/ibkr_daily_integration_preflight_report.md" "daily integration preflight completed"
else
  fail_safe "daily_integration_preflight" "daily integration preflight failed"
fi

if bash scripts/ibkr_daily_integration_review_pack.sh --daily-integration="$DAILY_INTEGRATION_CSV"; then
  [[ -f "ibkr_daily_integration_review_pack.csv" ]] || fail_safe "daily_integration_review_pack" "review pack csv missing"
  if [[ "$REVIEW_PACK_CSV" != "ibkr_daily_integration_review_pack.csv" ]]; then
    cp ibkr_daily_integration_review_pack.csv "$REVIEW_PACK_CSV"
  fi
  append_step "NO_GO" "daily_integration_review_pack" "PASS" "$REVIEW_PACK_CSV" "reports/ibkr_daily_integration_review_pack_report.md" "daily integration review pack completed"
else
  fail_safe "daily_integration_review_pack" "daily integration review pack failed"
fi

if bash scripts/ibkr_final_research_review_pack.sh --review-pack="$REVIEW_PACK_CSV"; then
  [[ -f "ibkr_final_research_review_pack.csv" ]] || fail_safe "final_research_review_pack" "final pack csv missing"
  if [[ "$FINAL_PACK_CSV" != "ibkr_final_research_review_pack.csv" ]]; then
    cp ibkr_final_research_review_pack.csv "$FINAL_PACK_CSV"
  fi
  append_step "NO_GO" "final_research_review_pack" "PASS" "$FINAL_PACK_CSV" "reports/ibkr_final_research_review_pack_report.md" "final research review pack completed"
else
  fail_safe "final_research_review_pack" "final research review pack failed"
fi

if bash scripts/ibkr_daily_operator_packet.sh --final-pack="$FINAL_PACK_CSV" --operator-packet="$OPERATOR_PACKET_CSV" --execution-c-mode="$EXECUTION_C_MODE"; then
  [[ -f "$OPERATOR_PACKET_CSV" ]] || fail_safe "daily_operator_packet" "operator packet csv missing"
  append_step "NO_GO" "daily_operator_packet" "PASS" "$OPERATOR_PACKET_CSV" "reports/ibkr_daily_operator_packet_report.md" "operator packet completed"
else
  fail_safe "daily_operator_packet" "operator packet failed"
fi

write_report "NO_GO"

echo "[PASS] IBKR daily research pipeline completed"
echo "pipeline_status=NO_GO"
echo "execution_c_mode=$EXECUTION_C_MODE"
echo "action_allowed=false"
echo "broker_execution_triggered=false"
echo "historical_data_request_triggered=false"
echo "account_read_triggered=false"
echo "position_read_triggered=false"
echo "summary_csv=$SUMMARY_CSV"
echo "report=$REPORT_PATH"
