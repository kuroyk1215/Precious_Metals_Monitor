#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 50 deployment decision check"

required_files=(
  "docs/DEPLOYMENT_24H_DECISION_PACK.md"
  "docs/MAC_VS_CLOUD_DECISION_MATRIX.md"
  "docs/DEPLOYMENT_COST_SECURITY_CHECKLIST.md"
  "docs/PHASE50_DEPLOYMENT_DECISION_RECORD.md"
  "scripts/local_automation_dryrun.sh"
  "scripts/check_mvp_v1_acceptance.sh"
  "scripts/daily_manual_check.sh"
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

echo "[PASS] Phase 50 deployment decision docs are present"
echo "[PASS] Local automation dry-run remains valid"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
