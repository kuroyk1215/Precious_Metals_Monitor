#!/usr/bin/env bash
set -euo pipefail

EXECUTION_C_PACKET="ibkr_execution_c_validation_packet.csv"
SNAPSHOT_CSV="ibkr_market_data_snapshot.csv"
SNAPSHOT_REPORT="reports/ibkr_market_data_snapshot_report.md"
OPERATOR_PACKET="ibkr_daily_operator_packet.csv"
TELEGRAM_NOTIFICATION_PACKET="ibkr_telegram_notification_packet.csv"
OUTPUT_CSV="first_operator_run_post_analysis.csv"
OUTPUT_REPORT="reports/first_operator_run_post_analysis_report.md"
SUMMARY_MD="reports/first_operator_run_summary.md"

for arg in "$@"; do
  case "$arg" in
    --execution-c-packet=*)
      EXECUTION_C_PACKET="${arg#--execution-c-packet=}"
      ;;
    --snapshot-csv=*)
      SNAPSHOT_CSV="${arg#--snapshot-csv=}"
      ;;
    --snapshot-report=*)
      SNAPSHOT_REPORT="${arg#--snapshot-report=}"
      ;;
    --operator-packet=*)
      OPERATOR_PACKET="${arg#--operator-packet=}"
      ;;
    --telegram-notification-packet=*)
      TELEGRAM_NOTIFICATION_PACKET="${arg#--telegram-notification-packet=}"
      ;;
    --output-csv=*)
      OUTPUT_CSV="${arg#--output-csv=}"
      ;;
    --output-report=*)
      OUTPUT_REPORT="${arg#--output-report=}"
      ;;
    --summary-md=*)
      SUMMARY_MD="${arg#--summary-md=}"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

export EXECUTION_C_PACKET SNAPSHOT_CSV SNAPSHOT_REPORT OPERATOR_PACKET TELEGRAM_NOTIFICATION_PACKET
export OUTPUT_CSV OUTPUT_REPORT SUMMARY_MD

mkdir -p "$(dirname "$OUTPUT_REPORT")" "$(dirname "$SUMMARY_MD")"

echo "[INFO] First operator-run post analysis started"

python3 - <<'PY'
from pathlib import Path
import os

from src.first_operator_run_post_analysis import (
    build_first_operator_run_post_analysis_decision,
    read_csv_rows,
    write_first_operator_run_summary,
    write_post_analysis_csv,
    write_post_analysis_report,
)

execution_status, execution_rows = read_csv_rows(Path(os.environ["EXECUTION_C_PACKET"]))
snapshot_status, snapshot_rows = read_csv_rows(Path(os.environ["SNAPSHOT_CSV"]))
operator_status, operator_rows = read_csv_rows(Path(os.environ["OPERATOR_PACKET"]))
telegram_status, telegram_rows = read_csv_rows(Path(os.environ["TELEGRAM_NOTIFICATION_PACKET"]))

snapshot_report = Path(os.environ["SNAPSHOT_REPORT"])
if snapshot_report.exists():
    report_rows = []
    for line in snapshot_report.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        cells = [cell.strip() for cell in stripped.strip("|").split("|")] if stripped.startswith("|") else []
        table_code = next((cell for cell in cells if cell in {"10089", "354"}), "")
        if table_code:
            report_rows.append({"error_code": table_code, "error_message": stripped, "action_allowed": "false"})
        elif (
            ("error 10089" in lowered or "error 354" in lowered)
            and ("delayed market data available" in lowered or "延迟市场数据可用" in stripped)
        ):
            report_rows.append({"report_text": stripped, "action_allowed": "false"})
    snapshot_rows = list(snapshot_rows) + report_rows

decision = build_first_operator_run_post_analysis_decision(
    execution_c_rows=execution_rows,
    snapshot_rows=snapshot_rows,
    operator_rows=operator_rows,
    telegram_notification_rows=telegram_rows,
    execution_c_input_status=execution_status,
    snapshot_input_status=snapshot_status,
    operator_packet_input_status=operator_status,
    telegram_notification_input_status=telegram_status,
)

write_post_analysis_csv(Path(os.environ["OUTPUT_CSV"]), decision)
write_post_analysis_report(Path(os.environ["OUTPUT_REPORT"]), decision)
write_first_operator_run_summary(Path(os.environ["SUMMARY_MD"]), decision)

print("[PASS] First operator-run post analysis generated")
print(f"post_run_status={decision.post_run_status}")
print(f"analysis_decision={decision.analysis_decision}")
print(f"semantic_status={decision.semantic_status}")
print(f"execution_c_status={decision.execution_c_status}")
print(f"validation_decision={decision.validation_decision}")
print(f"snapshot_status={decision.snapshot_status}")
print(f"effective_market_data_type={decision.effective_market_data_type}")
print(f"data_delay_flag={decision.data_delay_flag}")
print(f"operator_review_ready_count={decision.operator_review_ready_count}")
print(f"error_10089_detected={decision.error_10089_detected}")
print(f"error_354_detected={decision.error_354_detected}")
print(f"live_subscription_status={decision.live_subscription_status}")
print("action_allowed=false")
print("broker_execution_triggered=false")
print("historical_data_request_triggered=false")
print("account_read_triggered=false")
print("position_read_triggered=false")
print("telegram_send_triggered=false")
print(f"csv={os.environ['OUTPUT_CSV']}")
print(f"report={os.environ['OUTPUT_REPORT']}")
print(f"summary={os.environ['SUMMARY_MD']}")
PY
