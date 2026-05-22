#!/usr/bin/env bash
set -euo pipefail

CHECK_LOG_ROOT="/tmp/ibkr_telegram_dry_run_check_logs"
MISSING_OPERATOR_PACKET="/tmp/nonexistent_phase337_operator_packet.csv"
NOTIFICATION_OUT="/tmp/phase337_352_notification.out"
RUNNER_OUT="/tmp/phase337_352_runner.out"

rm -rf "$CHECK_LOG_ROOT"
rm -f "$MISSING_OPERATOR_PACKET" "$NOTIFICATION_OUT" "$RUNNER_OUT"

PATH=.venv/bin:$PATH python -m py_compile main.py src/*.py
PATH=.venv/bin:$PATH PYTHONPATH=. python -m pytest -q

PATH=.venv/bin:$PATH bash scripts/ibkr_telegram_notification_packet.sh \
  --operator-packet="$MISSING_OPERATOR_PACKET" > "$NOTIFICATION_OUT"

PATH=.venv/bin:$PATH bash scripts/ibkr_local_daily_runner.sh \
  --telegram-dry-run \
  --log-root="$CHECK_LOG_ROOT" \
  --retention-days=7 > "$RUNNER_OUT"

python3 - <<'PY'
from pathlib import Path
import csv

root = Path("/tmp/ibkr_telegram_dry_run_check_logs")
previews = sorted(root.glob("*/*/ibkr_telegram_message_preview.md"))
packets = sorted(root.glob("*/*/ibkr_telegram_notification_packet.csv"))
reports = sorted(root.glob("*/*/ibkr_telegram_notification_packet_report.md"))
summaries = sorted(root.glob("*/*/ibkr_local_daily_runner_summary.csv"))
if not previews:
    raise SystemExit("[FAIL] Telegram message preview was not archived")
if not packets:
    raise SystemExit("[FAIL] Telegram notification packet was not archived")
if not reports:
    raise SystemExit("[FAIL] Telegram notification report was not archived")
if not summaries:
    raise SystemExit("[FAIL] local runner summary was not archived")

packet_text = packets[-1].read_text(encoding="utf-8")
report_text = reports[-1].read_text(encoding="utf-8")
preview_text = previews[-1].read_text(encoding="utf-8")
required = [
    "action_allowed=false",
    "telegram_send_triggered=false",
    "broker_execution_triggered=false",
    "historical_data_request_triggered=false",
    "account_read_triggered=false",
    "position_read_triggered=false",
]
for needle in required:
    if needle not in packet_text and needle not in report_text and needle not in preview_text:
        raise SystemExit(f"[FAIL] missing safety marker: {needle}")

with summaries[-1].open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
if not rows:
    raise SystemExit("[FAIL] runner summary is empty")
summary = rows[-1]
if summary.get("telegram_dry_run_enabled") != "true":
    raise SystemExit("[FAIL] telegram_dry_run_enabled was not true")
if summary.get("telegram_send_triggered") != "false":
    raise SystemExit("[FAIL] telegram_send_triggered was not false")
PY

SCAN_FILES=(
  src/ibkr_telegram_notification_packet.py
  scripts/ibkr_telegram_notification_packet.sh
  scripts/ibkr_local_daily_runner.sh
)

if rg -nE "\.(placeOrder|cancelOrder|whatIfOrder|bracketOrder|exerciseOptions|reqGlobalCancel)\s*\(" "${SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] broker execution function found in Telegram dry-run executable path"
  exit 1
fi

if rg -nE "\.(reqAccount|reqPositions|accountSummary|managedAccounts)\s*\(" "${SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] account or position read found in Telegram dry-run executable path"
  exit 1
fi

if rg -nE "curl|requests\.post|urllib\.request|sendMessage|api\.telegram\.org|TELEGRAM_.*TOKEN|chat_id" "${SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] real Telegram send, token read, or network call found in Telegram dry-run executable path"
  exit 1
fi

for marker in \
  "action_allowed=false" \
  "telegram_send_triggered=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false"; do
  if ! rg -n "$marker" "$NOTIFICATION_OUT" "$RUNNER_OUT" >/dev/null 2>&1; then
    echo "[FAIL] missing output marker: $marker"
    exit 1
  fi
done

echo "[PASS] Phase 337-352 Telegram dry-run notification packet check completed"
