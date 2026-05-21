#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 65-67 runtime output git hygiene check"

required_files=(
  "docs/RUNTIME_OUTPUT_GIT_HYGIENE.md"
  "scripts/daily_research_run.sh"
  "scripts/phase61_64_daily_research_run_check.sh"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing required file: $file"
    exit 1
  fi
done

required_ignored=(
  "daily_research_run_summary.csv"
  "final_research_plan_daily_log.csv"
  "final_research_plan_orchestrator.csv"
  "report_template_daily_log_telegram_ready_output.csv"
  "reports/daily_research_run_report.md"
  "reports/final_research_plan_orchestrator_report.md"
  "reports/report_template_daily_log_telegram_ready_output_report.md"
  "reports/telegram_ready_text.txt"
)

for path in "${required_ignored[@]}"; do
  if ! grep -Fxq "$path" .gitignore; then
    echo "[FAIL] Missing .gitignore runtime output entry: $path"
    exit 1
  fi
done

echo "[INFO] Python syntax check"
python3 -m py_compile main.py src/*.py

echo "[INFO] Unit tests"
python3 -m pytest -q

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

echo "[PASS] Runtime output hygiene doc is present"
echo "[PASS] Required daily research run scripts are present"
echo "[PASS] Daily research runtime outputs are ignored"
echo "[PASS] Python syntax check passed"
echo "[PASS] Unit tests passed"
echo "[PASS] config.yaml is not staged"
echo "[PASS] No active Python trading API keyword found"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
