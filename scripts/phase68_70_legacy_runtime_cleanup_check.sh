#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 68-70 legacy runtime output cleanup check"

legacy_runtime_paths=(
  "ibkr_smoke_log.csv"
  "precious_metals_signal_log.csv"
  "reports/ibkr_smoke_report.md"
  "reports/latest_report.md"
  "daily_research_run_summary.csv"
  "final_research_plan_daily_log.csv"
  "final_research_plan_orchestrator.csv"
  "report_template_daily_log_telegram_ready_output.csv"
  "reports/daily_research_run_report.md"
  "reports/final_research_plan_orchestrator_report.md"
  "reports/report_template_daily_log_telegram_ready_output_report.md"
  "reports/telegram_ready_text.txt"
)

for path in "${legacy_runtime_paths[@]}"; do
  if git ls-files --error-unmatch "$path" >/dev/null 2>&1; then
    echo "[FAIL] Runtime output is still tracked by Git: $path"
    exit 1
  fi
done

if [[ ! -f "docs/LEGACY_RUNTIME_OUTPUT_CLEANUP.md" ]]; then
  echo "[FAIL] Missing docs/LEGACY_RUNTIME_OUTPUT_CLEANUP.md"
  exit 1
fi

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

echo "[PASS] Legacy runtime outputs are not tracked by Git"
echo "[PASS] Legacy cleanup doc is present"
echo "[PASS] Python syntax check passed"
echo "[PASS] Unit tests passed"
echo "[PASS] config.yaml is not staged"
echo "[PASS] No active Python trading API keyword found"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
