#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Local run logging and archive policy check"

required_files=(
  "docs/LOCAL_RUN_LOGGING_POLICY.md"
  "docs/REPORT_ARCHIVE_POLICY.md"
  "docs/FAILURE_LOG_FORMAT.md"
  "docs/MANUAL_ARCHIVE_ACCEPTANCE_PACK.md"
  "examples/failure_log.sample.yaml"
  "scripts/check_mvp_v1_acceptance.sh"
  "scripts/daily_manual_check.sh"
  "scripts/local_automation_dryrun.sh"
  "scripts/deployment_decision_check.sh"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing required file: $file"
    exit 1
  fi
done

if grep -R "auto_trade_allowed: true" examples >/dev/null 2>&1; then
  echo "[FAIL] Sample config enables auto_trade_allowed"
  exit 1
fi

if grep -R "order_action_allowed: true" examples >/dev/null 2>&1; then
  echo "[FAIL] Sample config enables order_action_allowed"
  exit 1
fi

if grep -R "telegram_real_send_triggered: true" examples >/dev/null 2>&1; then
  echo "[FAIL] Sample failure log indicates real Telegram send"
  exit 1
fi

if grep -R "broker_execution_triggered: true" examples >/dev/null 2>&1; then
  echo "[FAIL] Sample failure log indicates broker execution"
  exit 1
fi

./scripts/check_mvp_v1_acceptance.sh
./scripts/daily_manual_check.sh
./scripts/local_automation_dryrun.sh
./scripts/deployment_decision_check.sh

echo "[PASS] Local run logging docs are present"
echo "[PASS] Archive policy docs are present"
echo "[PASS] Failure log format is present"
echo "[PASS] Failure log sample is non-execution"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
