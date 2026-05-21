#!/usr/bin/env bash
set -euo pipefail

# Daily manual check for Precious_Metals_Monitor.
#
# This script does not run broker execution.
# It does not place orders, cancel orders, rebalance, or send Telegram messages.

echo "[INFO] Branch:"
git branch --show-current

echo "[INFO] Local status:"
git status --short

required_files=(
  "docs/DAILY_OPERATION_CHECKLIST.md"
  "docs/DAILY_REVIEW_WORKFLOW.md"
  "docs/MANUAL_TRADE_REVIEW_BOUNDARY.md"
  "docs/SCHEDULER_DRY_RUN_OPERATION_PLAN.md"
  "docs/TELEGRAM_DRY_RUN_OPERATION_PLAN.md"
  "scripts/check_mvp_v1_acceptance.sh"
  "scripts/cleanup_generated_artifacts.sh"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing required file: $file"
    exit 1
  fi
done

if [[ ! -x "scripts/check_mvp_v1_acceptance.sh" ]]; then
  echo "[FAIL] scripts/check_mvp_v1_acceptance.sh is not executable"
  exit 1
fi

if [[ ! -x "scripts/cleanup_generated_artifacts.sh" ]]; then
  echo "[FAIL] scripts/cleanup_generated_artifacts.sh is not executable"
  exit 1
fi

if grep -R "auto_trade_allowed: true" examples >/dev/null 2>&1; then
  echo "[FAIL] Sample config enables auto_trade_allowed"
  exit 1
fi

if grep -R "order_action_allowed: true" examples >/dev/null 2>&1; then
  echo "[FAIL] Sample config enables order_action_allowed"
  exit 1
fi

echo "[PASS] Daily manual operation docs are present"
echo "[PASS] Required local scripts are executable"
echo "[PASS] Sample configs do not enable auto trade or order action"
echo "[PASS] No broker execution is triggered by this check"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
