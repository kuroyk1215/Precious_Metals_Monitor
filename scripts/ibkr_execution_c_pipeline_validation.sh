#!/usr/bin/env bash
set -euo pipefail

EXECUTE_MARKET_DATA="false"
MARKET_DATA_TYPE="auto"
TELEGRAM_DRY_RUN="false"
TELEGRAM_SEND="false"
TELEGRAM_APPROVAL_FILE=".telegram_send_approval.local"
CONFIG_PATH="config.yaml"
CONTRACT_MAP_CSV="ibkr_verified_contract_map.csv"
LOG_ROOT="logs/ibkr_daily"
RETENTION_DAYS="30"
OUTPUT_CSV="ibkr_execution_c_validation_packet.csv"
OUTPUT_REPORT="reports/ibkr_execution_c_validation_report.md"

for arg in "$@"; do
  case "$arg" in
    --execute-market-data)
      EXECUTE_MARKET_DATA="true"
      ;;
    --market-data-type=*)
      MARKET_DATA_TYPE="${arg#--market-data-type=}"
      ;;
    --telegram-dry-run)
      TELEGRAM_DRY_RUN="true"
      ;;
    --telegram-send)
      TELEGRAM_SEND="true"
      TELEGRAM_DRY_RUN="true"
      ;;
    --telegram-approval-file=*)
      TELEGRAM_APPROVAL_FILE="${arg#--telegram-approval-file=}"
      ;;
    --config=*)
      CONFIG_PATH="${arg#--config=}"
      ;;
    --contract-map=*)
      CONTRACT_MAP_CSV="${arg#--contract-map=}"
      ;;
    --log-root=*)
      LOG_ROOT="${arg#--log-root=}"
      ;;
    --retention-days=*)
      RETENTION_DAYS="${arg#--retention-days=}"
      ;;
    --output-csv=*)
      OUTPUT_CSV="${arg#--output-csv=}"
      ;;
    --output-report=*)
      OUTPUT_REPORT="${arg#--output-report=}"
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

RUNNER_EXIT_CODE="0"
if [[ "$EXECUTE_MARKET_DATA" == "true" ]]; then
  RUNNER_ARGS=(
    "--execute-market-data"
    "--market-data-type=${MARKET_DATA_TYPE}"
    "--config=${CONFIG_PATH}"
    "--contract-map=${CONTRACT_MAP_CSV}"
    "--log-root=${LOG_ROOT}"
    "--retention-days=${RETENTION_DAYS}"
  )
  if [[ "$TELEGRAM_DRY_RUN" == "true" ]]; then
    RUNNER_ARGS+=("--telegram-dry-run")
  fi
  if [[ "$TELEGRAM_SEND" == "true" ]]; then
    RUNNER_ARGS+=("--telegram-send" "--telegram-approval-file=${TELEGRAM_APPROVAL_FILE}")
  fi
  set +e
  PATH=.venv/bin:$PATH bash scripts/ibkr_local_daily_runner.sh "${RUNNER_ARGS[@]}"
  RUNNER_EXIT_CODE="$?"
  set -e
fi

export EXECUTE_MARKET_DATA MARKET_DATA_TYPE LOG_ROOT OUTPUT_CSV OUTPUT_REPORT RUNNER_EXIT_CODE
mkdir -p "$(dirname "$OUTPUT_REPORT")"

echo "[INFO] IBKR Execution C validation started"

python3 - <<'PY'
from pathlib import Path
import os

from src.ibkr_execution_c_validation import (
    build_execution_c_validation_decision,
    read_csv_rows,
    write_validation_csv,
    write_validation_report,
)


def latest_run_dir(log_root: str):
    root = Path(log_root)
    if not root.exists():
        return None
    candidates = [path for path in root.glob("*/*") if path.is_dir()]
    if not candidates:
        return None
    return sorted(candidates)[-1]


execute_market_data = os.environ["EXECUTE_MARKET_DATA"] == "true"
run_dir = latest_run_dir(os.environ["LOG_ROOT"]) if execute_market_data else None

def choose_path(name: str) -> Path:
    if run_dir is not None and (run_dir / name).exists():
        return run_dir / name
    return Path(name)

runner_status, runner_rows = read_csv_rows(choose_path("ibkr_local_daily_runner_summary.csv"))
pipeline_status, pipeline_rows = read_csv_rows(choose_path("ibkr_daily_research_pipeline_summary.csv"))
snapshot_status, snapshot_rows = read_csv_rows(choose_path("ibkr_market_data_snapshot.csv"))
operator_status, operator_rows = read_csv_rows(choose_path("ibkr_daily_operator_packet.csv"))
notification_status, notification_rows = read_csv_rows(choose_path("ibkr_telegram_notification_packet.csv"))
send_gate_status, send_gate_rows = read_csv_rows(choose_path("ibkr_telegram_send_gate_decision.csv"))

decision = build_execution_c_validation_decision(
    execute_market_data=execute_market_data,
    runner_rows=runner_rows,
    pipeline_rows=pipeline_rows,
    snapshot_rows=snapshot_rows,
    operator_rows=operator_rows,
    notification_rows=notification_rows,
    send_gate_rows=send_gate_rows,
    runner_input_status=runner_status,
    pipeline_input_status=pipeline_status,
    snapshot_input_status=snapshot_status,
    operator_input_status=operator_status,
    notification_input_status=notification_status,
    send_gate_input_status=send_gate_status,
)
if os.environ["RUNNER_EXIT_CODE"] != "0" and execute_market_data:
    decision = build_execution_c_validation_decision(
        execute_market_data=True,
        runner_rows=[{"pipeline_exit_code": os.environ["RUNNER_EXIT_CODE"], "action_allowed": "false"}],
        pipeline_rows=pipeline_rows,
        snapshot_rows=snapshot_rows,
        operator_rows=operator_rows,
        notification_rows=notification_rows,
        send_gate_rows=send_gate_rows,
        runner_input_status=runner_status,
        pipeline_input_status=pipeline_status,
        snapshot_input_status=snapshot_status,
        operator_input_status=operator_status,
        notification_input_status=notification_status,
        send_gate_input_status=send_gate_status,
    )

write_validation_csv(Path(os.environ["OUTPUT_CSV"]), decision)
write_validation_report(Path(os.environ["OUTPUT_REPORT"]), decision)

print("[PASS] IBKR Execution C validation packet generated")
print(f"execution_c_status={decision.execution_c_status}")
print(f"execution_c_mode={decision.execution_c_mode}")
print(f"market_data_execution_requested={decision.market_data_execution_requested}")
print(f"validation_decision={decision.validation_decision}")
print(f"validation_reason={decision.validation_reason}")
print(f"snapshot_status={decision.snapshot_status}")
print(f"effective_market_data_type={decision.effective_market_data_type}")
print(f"data_delay_flag={decision.data_delay_flag}")
print(f"telegram_send_triggered={decision.telegram_send_triggered}")
print("action_allowed=false")
print("broker_execution_triggered=false")
print("historical_data_request_triggered=false")
print("account_read_triggered=false")
print("position_read_triggered=false")
print("manual_review_required=true")
print(f"csv={os.environ['OUTPUT_CSV']}")
print(f"report={os.environ['OUTPUT_REPORT']}")
PY
