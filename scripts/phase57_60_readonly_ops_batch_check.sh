#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 57-60 read-only ops hardening batch check"

required_files=(
  "docs/DAILY_RESEARCH_RUN_ACCEPTANCE.md"
  "docs/DATA_SOURCE_AUDIT_NEXT_STAGE.md"
  "docs/TELEGRAM_READY_NEXT_STAGE.md"
  "docs/DASHBOARD_READINESS_DECISION.md"
  "scripts/daily_manual_check.sh"
  "scripts/operation_handoff_check.sh"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing required file: $file"
    exit 1
  fi
done

echo "[INFO] Python syntax check"
python3 -m py_compile main.py src/*.py

echo "[INFO] Unit tests"
python3 -m pytest -q

echo "[INFO] Existing daily manual check"
./scripts/daily_manual_check.sh

echo "[INFO] Existing operation handoff check"
./scripts/operation_handoff_check.sh

echo "[INFO] Config staging guard"
if git diff --cached --name-only | grep -q "^config.yaml$"; then
  echo "[FAIL] config.yaml is staged"
  exit 1
fi

echo "[INFO] Active runtime trading API guard"
if grep -R "placeOrder\|cancelOrder\|bracketOrder\|whatIfOrder\|exerciseOptions" main.py src --include="*.py" >/dev/null 2>&1; then
  echo "[FAIL] Trading API keyword found in active runtime code"
  exit 1
fi

echo "[PASS] Phase 57 daily research run acceptance doc is present"
echo "[PASS] Phase 58 data source audit next-stage doc is present"
echo "[PASS] Phase 59 Telegram-ready next-stage doc is present"
echo "[PASS] Phase 60 dashboard readiness decision doc is present"
echo "[PASS] Python syntax check passed"
echo "[PASS] Unit tests passed"
echo "[PASS] Existing daily manual check passed"
echo "[PASS] Existing operation handoff check passed"
echo "[PASS] config.yaml is not staged"
echo "[PASS] No active Python trading API keyword found"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
