#!/usr/bin/env bash
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$REPO_ROOT"
SCRIPT_DIR="$REPO_ROOT/scripts"
OUTPUT_CSV="operator_daily_mvp_run_summary.csv"
OUTPUT_REPORT="reports/operator_daily_mvp_run_summary.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root=*) ROOT="${1#--root=}"; shift ;;
    --root) ROOT="${2:?--root requires a path}"; shift 2 ;;
    --script-dir=*) SCRIPT_DIR="${1#--script-dir=}"; shift ;;
    --script-dir) SCRIPT_DIR="${2:?--script-dir requires a path}"; shift 2 ;;
    --output-csv=*) OUTPUT_CSV="${1#--output-csv=}"; shift ;;
    --output-csv) OUTPUT_CSV="${2:?--output-csv requires a path}"; shift 2 ;;
    --output-report=*) OUTPUT_REPORT="${1#--output-report=}"; shift ;;
    --output-report) OUTPUT_REPORT="${2:?--output-report requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

mkdir -p "$ROOT/reports"
STEP_RESULTS="$(mktemp /tmp/phase441_daily_mvp_steps.XXXXXX)"

run_step() {
  local step_name="$1"
  local script_path="$2"
  shift 2
  echo "[INFO] Running ${step_name}: ${script_path}"
  bash "$script_path" "$@"
  local exit_code=$?
  if [[ "$exit_code" -eq 0 ]]; then
    echo "[PASS] ${step_name}"
  else
    echo "[FAIL] ${step_name} exit_code=${exit_code}"
  fi
  printf '%s\t%s\t%s\t%s\n' "$step_name" "$script_path" "$exit_code" "exit_code=${exit_code}" >> "$STEP_RESULTS"
}

run_step "daily_operator_handoff_summary" "$SCRIPT_DIR/daily_operator_handoff_summary.sh" \
  --contract-map-csv "$ROOT/ibkr_verified_contract_map_gld_slv.csv" \
  --snapshot-csv "$ROOT/ibkr_market_data_snapshot.csv" \
  --api-errors-csv "$ROOT/ibkr_market_data_api_errors.csv" \
  --execution-c-packet "$ROOT/ibkr_execution_c_validation_packet.csv" \
  --operator-packet "$ROOT/ibkr_daily_operator_packet.csv" \
  --post-analysis-csv "$ROOT/first_operator_run_post_analysis.csv" \
  --telegram-notification-packet "$ROOT/ibkr_telegram_notification_packet.csv" \
  --output-csv "$ROOT/daily_operator_handoff_summary.csv" \
  --output-report "$ROOT/reports/daily_operator_handoff_summary.md"

run_step "latest_artifact_entrypoint" "$SCRIPT_DIR/latest_artifact_entrypoint.sh" --root "$ROOT"

run_step "research_trading_plan" "$SCRIPT_DIR/research_trading_plan.sh" \
  --root "$ROOT" \
  --output-csv "$ROOT/research_trading_plan.csv" \
  --output-report "$ROOT/reports/research_trading_plan_report.md"

run_step "watchlist_universe" "$SCRIPT_DIR/watchlist_universe.sh" \
  --root "$ROOT" \
  --output-csv "$ROOT/watchlist_universe.csv" \
  --output-report "$ROOT/reports/watchlist_universe_report.md"

run_step "telegram_notification_gate" "$SCRIPT_DIR/telegram_notification_gate.sh" \
  --root "$ROOT" \
  --output-csv "$ROOT/telegram_notification_gate.csv" \
  --output-report "$ROOT/reports/telegram_notification_gate_report.md" \
  --preview-report "$ROOT/reports/telegram_notification_approval_preview.md"

run_step "local_dashboard" "$SCRIPT_DIR/local_dashboard.sh" \
  --root "$ROOT" \
  --output-html "reports/dashboard.html"

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" python3 -m src.operator_daily_mvp_run_summary \
  --root "$ROOT" \
  --step-results "$STEP_RESULTS" \
  --output-csv "$OUTPUT_CSV" \
  --output-report "$OUTPUT_REPORT"
SUMMARY_EXIT=$?

rm -f "$STEP_RESULTS"
exit "$SUMMARY_EXIT"
