#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Operation handoff check"

required_files=(
  "docs/OPERATION_HANDOFF_PACK.md"
  "docs/MVP_V1_MANUAL_CLOSURE_ACCEPTANCE.md"
  "scripts/check_mvp_v1_acceptance.sh"
  "scripts/daily_manual_check.sh"
  "scripts/local_automation_dryrun.sh"
  "scripts/deployment_decision_check.sh"
  "scripts/local_run_archive_check.sh"
  "scripts/report_archive_dryrun.sh"
  "scripts/retention_validation_check.sh"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing required file: $file"
    exit 1
  fi
done

./scripts/check_mvp_v1_acceptance.sh
./scripts/daily_manual_check.sh
./scripts/local_automation_dryrun.sh
./scripts/deployment_decision_check.sh
./scripts/local_run_archive_check.sh
./scripts/report_archive_dryrun.sh
./scripts/retention_validation_check.sh

echo "[PASS] Operation handoff pack is present"
echo "[PASS] MVP v1.0 manual closure criteria are present"
echo "[PASS] Archive dry-run and retention checks pass"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
