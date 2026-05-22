#!/usr/bin/env bash
set -euo pipefail

EXECUTE_MARKET_DATA="false"
MARKET_DATA_TYPE="auto"
CONFIG_PATH="config.yaml"
CONTRACT_MAP_CSV="ibkr_verified_contract_map.csv"
LOG_ROOT="logs/ibkr_daily"
RETENTION_DAYS="30"
ROTATE_ENABLED="true"
TELEGRAM_DRY_RUN_ENABLED="false"
TELEGRAM_SEND_ENABLED="false"
TELEGRAM_APPROVAL_FILE=".telegram_send_approval.local"

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
    --log-root=*)
      LOG_ROOT="${arg#--log-root=}"
      ;;
    --retention-days=*)
      RETENTION_DAYS="${arg#--retention-days=}"
      ;;
    --dry-run)
      EXECUTE_MARKET_DATA="false"
      ;;
    --no-rotate)
      ROTATE_ENABLED="false"
      ;;
    --telegram-dry-run)
      TELEGRAM_DRY_RUN_ENABLED="true"
      ;;
    --telegram-send)
      TELEGRAM_SEND_ENABLED="true"
      TELEGRAM_DRY_RUN_ENABLED="true"
      ;;
    --telegram-approval-file=*)
      TELEGRAM_APPROVAL_FILE="${arg#--telegram-approval-file=}"
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

if ! [[ "$RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
  RETENTION_DAYS="30"
fi

EXECUTION_C_MODE="dry_run"
if [[ "$EXECUTE_MARKET_DATA" == "true" ]]; then
  EXECUTION_C_MODE="execute_market_data"
fi

export LOG_ROOT RETENTION_DAYS ROTATE_ENABLED EXECUTION_C_MODE
eval "$(
python3 - <<'PY'
import os
from src.ibkr_local_daily_runner import build_run_id, ensure_run_dir, normalize_retention_days

run_date, run_id, run_ts = build_run_id()
retention_days = normalize_retention_days(int(os.environ["RETENTION_DAYS"]))
run_dir = ensure_run_dir(os.environ["LOG_ROOT"], run_date, run_id)
print(f"RUN_DATE={run_date!r}")
print(f"RUN_ID={run_id!r}")
print(f"RUN_TS={run_ts!r}")
print(f"RUN_DIR={str(run_dir)!r}")
print(f"RETENTION_DAYS={str(retention_days)!r}")
PY
)"
export RUN_DATE RUN_ID RUN_TS RUN_DIR
export TELEGRAM_DRY_RUN_ENABLED TELEGRAM_SEND_ENABLED TELEGRAM_APPROVAL_FILE

echo "[INFO] IBKR local daily runner started: ${RUN_TS}"
echo "run_dir=${RUN_DIR}"
echo "execution_c_mode=${EXECUTION_C_MODE}"
echo "telegram_dry_run_enabled=${TELEGRAM_DRY_RUN_ENABLED}"
echo "telegram_send_gate_enabled=${TELEGRAM_SEND_ENABLED}"

PIPELINE_ARGS=(
  "--market-data-type=${MARKET_DATA_TYPE}"
  "--config=${CONFIG_PATH}"
  "--contract-map=${CONTRACT_MAP_CSV}"
)
if [[ "$EXECUTE_MARKET_DATA" == "true" ]]; then
  PIPELINE_ARGS+=("--execute-market-data")
fi

set +e
PATH=.venv/bin:$PATH bash scripts/ibkr_daily_research_pipeline.sh "${PIPELINE_ARGS[@]}"
PIPELINE_EXIT_CODE="$?"
set -e

TELEGRAM_DRY_RUN_EXIT_CODE="0"
if [[ "$TELEGRAM_DRY_RUN_ENABLED" == "true" ]]; then
  set +e
  PATH=.venv/bin:$PATH bash scripts/ibkr_telegram_notification_packet.sh \
    --operator-packet=ibkr_daily_operator_packet.csv \
    --pipeline-summary=ibkr_daily_research_pipeline_summary.csv \
    --runner-summary=ibkr_local_daily_runner_summary.csv \
    --output-csv=ibkr_telegram_notification_packet.csv \
    --output-report=reports/ibkr_telegram_notification_packet_report.md \
    --message-preview=reports/ibkr_telegram_message_preview.md
  TELEGRAM_DRY_RUN_EXIT_CODE="$?"
  set -e
fi

TELEGRAM_SEND_GATE_EXIT_CODE="0"
if [[ "$TELEGRAM_SEND_ENABLED" == "true" ]]; then
  set +e
  PATH=.venv/bin:$PATH bash scripts/ibkr_telegram_send_gate.sh \
    --notification-packet=ibkr_telegram_notification_packet.csv \
    --message-preview=reports/ibkr_telegram_message_preview.md \
    --output-csv=ibkr_telegram_send_gate_decision.csv \
    --output-report=reports/ibkr_telegram_send_gate_report.md \
    --send-telegram \
    --approval-file="$TELEGRAM_APPROVAL_FILE"
  TELEGRAM_SEND_GATE_EXIT_CODE="$?"
  set -e
fi

export PIPELINE_EXIT_CODE TELEGRAM_DRY_RUN_EXIT_CODE TELEGRAM_SEND_GATE_EXIT_CODE
python3 - <<'PY'
import os
from pathlib import Path
import csv
from src.ibkr_local_daily_runner import (
    build_runner_summary,
    copy_outputs_to_run_dir,
    rotate_old_run_dirs,
    write_runner_report,
    write_runner_summary_csv,
)

outputs = [
    "ibkr_market_data_snapshot.csv",
    "reports/ibkr_market_data_snapshot_report.md",
    "ibkr_daily_integration_preflight.csv",
    "reports/ibkr_daily_integration_preflight_report.md",
    "ibkr_daily_integration_review_pack.csv",
    "reports/ibkr_daily_integration_review_pack_report.md",
    "ibkr_final_research_review_pack.csv",
    "reports/ibkr_final_research_review_pack_report.md",
    "ibkr_daily_operator_packet.csv",
    "reports/ibkr_daily_operator_packet_report.md",
    "ibkr_daily_research_pipeline_summary.csv",
    "reports/ibkr_daily_research_pipeline_report.md",
]
if os.environ["TELEGRAM_DRY_RUN_ENABLED"] == "true":
    outputs.extend(
        [
            "ibkr_telegram_notification_packet.csv",
            "reports/ibkr_telegram_notification_packet_report.md",
            "reports/ibkr_telegram_message_preview.md",
        ]
    )
if os.environ["TELEGRAM_SEND_ENABLED"] == "true":
    outputs.extend(
        [
            "ibkr_telegram_send_gate_decision.csv",
            "reports/ibkr_telegram_send_gate_report.md",
        ]
    )

run_dir = Path(os.environ["RUN_DIR"])
copied = copy_outputs_to_run_dir(outputs, run_dir)
rotation_enabled = os.environ["ROTATE_ENABLED"] == "true"
removed = rotate_old_run_dirs(
    os.environ["LOG_ROOT"],
    int(os.environ["RETENTION_DAYS"]),
    enabled=rotation_enabled,
)
pipeline_exit_code = int(os.environ["PIPELINE_EXIT_CODE"])
telegram_dry_run_exit_code = int(os.environ["TELEGRAM_DRY_RUN_EXIT_CODE"])
telegram_send_gate_exit_code = int(os.environ["TELEGRAM_SEND_GATE_EXIT_CODE"])
telegram_send_triggered = "false"
telegram_send_status = "not_attempted"
gate_decision_path = Path("ibkr_telegram_send_gate_decision.csv")
if gate_decision_path.exists():
    with gate_decision_path.open(newline="", encoding="utf-8") as f:
        gate_rows = list(csv.DictReader(f))
    if gate_rows:
        telegram_send_triggered = gate_rows[-1].get("telegram_send_triggered", "false")
        telegram_send_status = gate_rows[-1].get("telegram_send_status", "not_attempted")
archive_status = "ARCHIVED" if copied else "NO_OUTPUTS_FOUND"
notes = (
    f"pipeline_exit_code={pipeline_exit_code};"
    f"telegram_dry_run_enabled={os.environ['TELEGRAM_DRY_RUN_ENABLED']};"
    f"telegram_dry_run_exit_code={telegram_dry_run_exit_code};"
    f"telegram_send_gate_enabled={os.environ['TELEGRAM_SEND_ENABLED']};"
    f"telegram_send_gate_exit_code={telegram_send_gate_exit_code};"
    f"telegram_send_triggered={telegram_send_triggered};"
    f"telegram_send_status={telegram_send_status};"
    f"rotation_removed_count={len(removed)};"
    f"runner_status={'FAILED_SAFE' if pipeline_exit_code or telegram_dry_run_exit_code or telegram_send_gate_exit_code else 'NO_GO'}"
)
summary = build_runner_summary(
    run_id=os.environ["RUN_ID"],
    run_timestamp=os.environ["RUN_TS"],
    run_date=os.environ["RUN_DATE"],
    run_dir=run_dir,
    execution_c_mode=os.environ["EXECUTION_C_MODE"],
    pipeline_exit_code=pipeline_exit_code,
    archive_status=archive_status,
    copied_file_count=len(copied),
    rotation_enabled=rotation_enabled,
    retention_days=int(os.environ["RETENTION_DAYS"]),
    notes=notes,
    telegram_dry_run_enabled=os.environ["TELEGRAM_DRY_RUN_ENABLED"] == "true",
    telegram_send_gate_enabled=os.environ["TELEGRAM_SEND_ENABLED"] == "true",
    telegram_send_triggered=telegram_send_triggered == "true",
    telegram_send_status=telegram_send_status,
)
summary_path = run_dir / "ibkr_local_daily_runner_summary.csv"
report_path = run_dir / "ibkr_local_daily_runner_report.md"
write_runner_summary_csv(summary_path, summary)
write_runner_report(report_path, summary, copied)
print(f"runner_status={'FAILED_SAFE' if pipeline_exit_code or telegram_dry_run_exit_code or telegram_send_gate_exit_code else 'NO_GO'}")
print(f"summary_csv={summary_path}")
print(f"report={report_path}")
print(f"copied_file_count={len(copied)}")
print(f"rotation_enabled={str(rotation_enabled).lower()}")
print(f"retention_days={summary.retention_days}")
print(f"telegram_dry_run_enabled={os.environ['TELEGRAM_DRY_RUN_ENABLED']}")
print(f"telegram_send_gate_enabled={os.environ['TELEGRAM_SEND_ENABLED']}")
print(f"telegram_send_triggered={telegram_send_triggered}")
print(f"telegram_send_status={telegram_send_status}")
print("action_allowed=false")
print("broker_execution_triggered=false")
print("historical_data_request_triggered=false")
print("account_read_triggered=false")
print("position_read_triggered=false")
print("manual_review_required=true")
PY

if [[ "$PIPELINE_EXIT_CODE" != "0" ]]; then
  exit "$PIPELINE_EXIT_CODE"
fi
if [[ "$TELEGRAM_DRY_RUN_EXIT_CODE" != "0" ]]; then
  exit "$TELEGRAM_DRY_RUN_EXIT_CODE"
fi
if [[ "$TELEGRAM_SEND_GATE_EXIT_CODE" != "0" ]]; then
  exit "$TELEGRAM_SEND_GATE_EXIT_CODE"
fi

echo "[PASS] IBKR local daily runner completed"
