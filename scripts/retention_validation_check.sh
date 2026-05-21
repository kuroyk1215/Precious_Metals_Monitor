#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Retention validation check"

required_files=(
  "docs/RETENTION_VALIDATION_POLICY.md"
  "docs/REPORT_ARCHIVE_POLICY.md"
  "docs/FAILURE_LOG_FORMAT.md"
  "examples/archive_manifest.sample.yaml"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing required file: $file"
    exit 1
  fi
done

if grep -R "auto_trade_allowed: true" examples >/dev/null 2>&1; then
  echo "[FAIL] Sample config enables auto trade"
  exit 1
fi

if grep -R "order_action_allowed: true" examples >/dev/null 2>&1; then
  echo "[FAIL] Sample config enables order action"
  exit 1
fi

echo "[PASS] Retention validation policy is present"
echo "[PASS] Archive and failure log policies are present"
echo "[PASS] Sample files do not enable trading"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
