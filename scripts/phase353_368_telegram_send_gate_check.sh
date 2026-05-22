#!/usr/bin/env bash
set -euo pipefail

CHECK_LOG_ROOT="/tmp/ibkr_telegram_send_gate_check_logs"
DEFAULT_OUT="/tmp/phase353_368_send_gate_default.out"
BLOCKED_OUT="/tmp/phase353_368_send_gate_blocked.out"
RUNNER_OUT="/tmp/phase353_368_runner.out"
MISSING_APPROVAL="/tmp/nonexistent_telegram_approval_file"

rm -rf "$CHECK_LOG_ROOT"
rm -f "$DEFAULT_OUT" "$BLOCKED_OUT" "$RUNNER_OUT" "$MISSING_APPROVAL"

PATH=.venv/bin:$PATH python -m py_compile main.py src/*.py
PATH=.venv/bin:$PATH PYTHONPATH=. python -m pytest -q

PATH=.venv/bin:$PATH bash scripts/ibkr_telegram_send_gate.sh > "$DEFAULT_OUT"
PATH=.venv/bin:$PATH bash scripts/ibkr_telegram_send_gate.sh --send-telegram --approval-file="$MISSING_APPROVAL" > "$BLOCKED_OUT"
PATH=.venv/bin:$PATH bash scripts/ibkr_local_daily_runner.sh \
  --telegram-send \
  --log-root="$CHECK_LOG_ROOT" \
  --retention-days=7 > "$RUNNER_OUT"

if ! rg -n "send_gate_status=DRY_RUN_ONLY" "$DEFAULT_OUT" >/dev/null 2>&1; then
  echo "[FAIL] default send gate was not DRY_RUN_ONLY"
  exit 1
fi

if ! rg -n "telegram_send_triggered=false" "$DEFAULT_OUT" >/dev/null 2>&1; then
  echo "[FAIL] default send gate triggered Telegram send"
  exit 1
fi

if ! rg -n "send_gate_status=SEND_BLOCKED" "$BLOCKED_OUT" "$RUNNER_OUT" >/dev/null 2>&1; then
  echo "[FAIL] missing approval/token/chat_id path did not block"
  exit 1
fi

if ! rg -n "telegram_send_status=blocked" "$BLOCKED_OUT" "$RUNNER_OUT" >/dev/null 2>&1; then
  echo "[FAIL] blocked send gate did not report blocked status"
  exit 1
fi

python3 - <<'PY'
from pathlib import Path
import csv

root = Path("/tmp/ibkr_telegram_send_gate_check_logs")
decisions = sorted(root.glob("*/*/ibkr_telegram_send_gate_decision.csv"))
reports = sorted(root.glob("*/*/ibkr_telegram_send_gate_report.md"))
if not decisions:
    raise SystemExit("[FAIL] send gate decision was not archived")
if not reports:
    raise SystemExit("[FAIL] send gate report was not archived")
with decisions[-1].open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
if not rows:
    raise SystemExit("[FAIL] send gate decision csv is empty")
decision = rows[-1]
if decision.get("send_gate_status") != "SEND_BLOCKED":
    raise SystemExit("[FAIL] runner send gate was not blocked without approval/token/chat_id")
if decision.get("telegram_send_triggered") != "false":
    raise SystemExit("[FAIL] runner blocked send gate triggered send")
for marker in [
    "action_allowed=false",
    "broker_execution_triggered=false",
    "historical_data_request_triggered=false",
    "account_read_triggered=false",
    "position_read_triggered=false",
]:
    if marker not in reports[-1].read_text(encoding="utf-8"):
        raise SystemExit(f"[FAIL] missing report marker: {marker}")
PY

if rg -n "replace_with_bot_token|replace_with_chat_id|dummy-token-for-redaction|dummy-chat-for-redaction" "$DEFAULT_OUT" "$BLOCKED_OUT" "$RUNNER_OUT" >/dev/null 2>&1; then
  echo "[FAIL] token/chat_id-like value leaked into validation output"
  exit 1
fi

SCAN_FILES=(
  src/ibkr_telegram_send_gate.py
  scripts/ibkr_telegram_send_gate.sh
  scripts/ibkr_local_daily_runner.sh
)

if rg -n "\.(placeOrder|cancelOrder|whatIfOrder|bracketOrder|exerciseOptions|reqGlobalCancel)\s*\(" "${SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] broker execution function found in Telegram send gate executable path"
  exit 1
fi

if rg -n "\.(reqAccount|reqPositions|accountSummary|managedAccounts)\s*\(" "${SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] account or position read found in Telegram send gate executable path"
  exit 1
fi

NETWORK_SCAN_FILES=()
while IFS= read -r scan_file; do
  NETWORK_SCAN_FILES+=("$scan_file")
done < <(rg --files scripts src | rg -v "scripts/phase.*_check\.sh|src/ibkr_telegram_send_gate\.py|scripts/ibkr_telegram_send_gate\.sh")
if rg -n "curl|requests\.post|api\.telegram\.org" "${NETWORK_SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] disallowed Telegram/network send reference found outside send gate"
  exit 1
fi

for marker in \
  "action_allowed=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false"; do
  if ! rg -n "$marker" "$DEFAULT_OUT" "$BLOCKED_OUT" "$RUNNER_OUT" >/dev/null 2>&1; then
    echo "[FAIL] missing output marker: $marker"
    exit 1
  fi
done

echo "[PASS] Phase 353-368 Telegram send gate check completed"
