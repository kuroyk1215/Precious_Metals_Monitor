#!/usr/bin/env bash
set -euo pipefail

NOTIFICATION_PACKET="ibkr_telegram_notification_packet.csv"
MESSAGE_PREVIEW="reports/ibkr_telegram_message_preview.md"
OUTPUT_CSV="ibkr_telegram_send_gate_decision.csv"
OUTPUT_REPORT="reports/ibkr_telegram_send_gate_report.md"
SEND_TELEGRAM="false"
APPROVAL_FILE=".telegram_send_approval.local"

for arg in "$@"; do
  case "$arg" in
    --notification-packet=*)
      NOTIFICATION_PACKET="${arg#--notification-packet=}"
      ;;
    --message-preview=*)
      MESSAGE_PREVIEW="${arg#--message-preview=}"
      ;;
    --output-csv=*)
      OUTPUT_CSV="${arg#--output-csv=}"
      ;;
    --output-report=*)
      OUTPUT_REPORT="${arg#--output-report=}"
      ;;
    --send-telegram)
      SEND_TELEGRAM="true"
      ;;
    --approval-file=*)
      APPROVAL_FILE="${arg#--approval-file=}"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

BOT_TOKEN_VALUE=""
CHAT_ID_VALUE=""
if [[ "$SEND_TELEGRAM" == "true" ]]; then
  BOT_TOKEN_VALUE="${TELEGRAM_BOT_TOKEN:-}"
  CHAT_ID_VALUE="${TELEGRAM_CHAT_ID:-}"
fi

export NOTIFICATION_PACKET MESSAGE_PREVIEW OUTPUT_CSV OUTPUT_REPORT SEND_TELEGRAM APPROVAL_FILE
export BOT_TOKEN_VALUE CHAT_ID_VALUE
export RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"

mkdir -p "$(dirname "$OUTPUT_REPORT")"

echo "[INFO] IBKR Telegram send gate started: ${RUN_TS}"

python3 - <<'PY'
from pathlib import Path
import os

from src.ibkr_telegram_send_gate import (
    evaluate_send_gate,
    write_send_gate_csv,
    write_send_gate_report,
)

send_telegram = os.environ["SEND_TELEGRAM"] == "true"
decision = evaluate_send_gate(
    send_telegram=send_telegram,
    approval_file=os.environ["APPROVAL_FILE"],
    notification_packet=os.environ["NOTIFICATION_PACKET"],
    message_preview=os.environ["MESSAGE_PREVIEW"],
    bot_token=os.environ["BOT_TOKEN_VALUE"] if send_telegram else None,
    chat_id=os.environ["CHAT_ID_VALUE"] if send_telegram else None,
)

write_send_gate_csv(Path(os.environ["OUTPUT_CSV"]), decision)
write_send_gate_report(
    Path(os.environ["OUTPUT_REPORT"]),
    decision,
    os.environ["NOTIFICATION_PACKET"],
    os.environ["MESSAGE_PREVIEW"],
    os.environ["APPROVAL_FILE"],
)

print("[PASS] IBKR Telegram send gate decision generated")
print(f"send_gate_status={decision.send_gate_status}")
print(f"send_gate_reason={decision.send_gate_reason}")
print(f"send_mode={decision.send_mode}")
print(f"approval_file_status={decision.approval_file_status}")
print(f"token_status={decision.token_status}")
print(f"chat_id_status={decision.chat_id_status}")
print(f"notification_packet_status={decision.notification_packet_status}")
print(f"message_preview_status={decision.message_preview_status}")
print(f"telegram_send_triggered={decision.telegram_send_triggered}")
print(f"telegram_send_status={decision.telegram_send_status}")
print("action_allowed=false")
print("broker_execution_triggered=false")
print("historical_data_request_triggered=false")
print("account_read_triggered=false")
print("position_read_triggered=false")
print("manual_review_required=true")
print(f"csv={os.environ['OUTPUT_CSV']}")
print(f"report={os.environ['OUTPUT_REPORT']}")
PY
