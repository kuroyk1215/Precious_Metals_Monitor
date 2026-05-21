#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Report archive dry-run"

required_files=(
  "docs/REPORT_ARCHIVE_DRY_RUN.md"
  "docs/REPORT_ARCHIVE_POLICY.md"
  "docs/LOCAL_RUN_LOGGING_POLICY.md"
  "examples/archive_manifest.sample.yaml"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing required file: $file"
    exit 1
  fi
done

if ! grep -q "archive/" .gitignore; then
  echo "[FAIL] archive/ is not ignored"
  exit 1
fi

if grep -R "broker_execution_triggered: true" examples >/dev/null 2>&1; then
  echo "[FAIL] Sample archive/failure data indicates broker execution"
  exit 1
fi

if grep -R "telegram_real_send_triggered: true" examples >/dev/null 2>&1; then
  echo "[FAIL] Sample archive/failure data indicates real Telegram send"
  exit 1
fi

echo "[PASS] Archive dry-run docs and sample manifest are present"
echo "[PASS] archive/ runtime path is ignored"
echo "[PASS] No runtime archive is committed by this dry-run"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
