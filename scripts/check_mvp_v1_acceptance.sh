#!/usr/bin/env bash
set -euo pipefail

# MVP v1.0 lightweight acceptance check.
#
# This script does not run trading logic.
# It does not place orders, cancel orders, rebalance, or call broker execution.
# It only checks documentation, sample configs, and local hygiene support.

required_files=(
  "docs/MVP_V1_RELEASE_NOTES.md"
  "docs/MVP_V1_ACCEPTANCE_CHECKLIST.md"
  "docs/MVP_V1_OPERATION_INDEX.md"
  "docs/MVP_V1_NEXT_PHASE_DECISION.md"
  "docs/ONE_COMMAND_ACCEPTANCE_PACK.md"
  "docs/MVP_V1_COMMAND_REFERENCE.md"
  "docs/OUTPUT_ACCEPTANCE_CRITERIA.md"
  "docs/NO_TRADE_ASSERTION_GATE.md"
  "docs/GIT_HYGIENE_GUIDE.md"
  "docs/GENERATED_ARTIFACT_CLEANUP.md"
  "examples/primary_metals_config.sample.yaml"
  "examples/telegram_config.sample.yaml"
  "examples/scheduler_config.sample.yaml"
  "examples/data_source_policy.sample.yaml"
  "examples/ibkr_read_only_admission.sample.yaml"
  "examples/ui_config.sample.yaml"
  "scripts/cleanup_generated_artifacts.sh"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing required file: $file"
    exit 1
  fi
done

if [[ ! -x "scripts/cleanup_generated_artifacts.sh" ]]; then
  echo "[FAIL] cleanup script is not executable"
  exit 1
fi

if ! grep -q -- "--report-template-daily-log-telegram-ready-output" docs/MVP_V1_COMMAND_REFERENCE.md docs/ONE_COMMAND_ACCEPTANCE_PACK.md; then
  echo "[FAIL] Core MVP command is not documented"
  exit 1
fi

if ! grep -q "Phase 42: generated runtime artifacts and local environment" .gitignore; then
  echo "[FAIL] Phase 42 generated artifact .gitignore block is missing"
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

echo "[PASS] MVP v1.0 acceptance files are present"
echo "[PASS] cleanup script is executable"
echo "[PASS] core command is documented"
echo "[PASS] sample configs do not enable auto trade or order action"
echo "[PASS] project remains research-only / read-only / manual-only / no auto trade"
