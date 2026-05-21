#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 61-64 daily research run runtime output check"

required_files=(
  "docs/DAILY_RESEARCH_RUN_RUNTIME_OUTPUTS.md"
  "scripts/daily_research_run.sh"
  "scripts/phase61_64_daily_research_run_check.sh"
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

echo "[INFO] Daily research run"
./scripts/daily_research_run.sh

echo "[INFO] Runtime output check"
required_outputs=(
  "daily_research_run_summary.csv"
  "reports/daily_research_run_report.md"
)

for file in "${required_outputs[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing runtime output: $file"
    exit 1
  fi
done

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

echo "[INFO] Runtime safety text guard"
if grep -R "telegram_api_called=true\|scheduler_deployed=true\|broker_execution_triggered=true\|final_action_allowed=true" daily_research_run_summary.csv reports/daily_research_run_report.md >/dev/null 2>&1; then
  echo "[FAIL] Runtime output contains unsafe true flag"
  exit 1
fi

echo "[PASS] Phase 61-64 daily research run runtime output docs are present"
echo "[PASS] Daily research run script is present"
echo "[PASS] Python syntax check passed"
echo "[PASS] Unit tests passed"
echo "[PASS] Runtime outputs generated"
echo "[PASS] config.yaml is not staged"
echo "[PASS] No active Python trading API keyword found"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
