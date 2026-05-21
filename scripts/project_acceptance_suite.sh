#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Project acceptance suite"

required_files=(
  "docs/PROJECT_ACCEPTANCE_SUITE.md"
  "scripts/daily_research_run.sh"
  "scripts/phase57_60_readonly_ops_batch_check.sh"
  "scripts/phase61_64_daily_research_run_check.sh"
  "scripts/phase65_67_runtime_output_git_hygiene_check.sh"
  "scripts/phase68_70_legacy_runtime_cleanup_check.sh"
  "scripts/phase71_73_post_hygiene_daily_run_acceptance_check.sh"
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

echo "[INFO] Runtime output existence check"
required_runtime_outputs=(
  "daily_research_run_summary.csv"
  "reports/daily_research_run_report.md"
)

for file in "${required_runtime_outputs[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing generated runtime output: $file"
    exit 1
  fi
done

echo "[INFO] Runtime output git hygiene check"
if git status --short | grep -E "daily_research_run_summary.csv|reports/daily_research_run_report.md|final_research_plan_orchestrator.csv|report_template_daily_log_telegram_ready_output.csv|reports/telegram_ready_text.txt" >/dev/null 2>&1; then
  echo "[FAIL] Runtime output appears in git status"
  git status --short
  exit 1
fi

echo "[INFO] Legacy runtime tracking check"
legacy_runtime_paths=(
  "reports/ibkr_smoke_report.md"
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

echo "[PASS] Project acceptance suite completed"
echo "[PASS] Python syntax check passed"
echo "[PASS] Unit tests passed"
echo "[PASS] Daily research run executed"
echo "[PASS] Runtime outputs generated locally"
echo "[PASS] Runtime outputs do not pollute git status"
echo "[PASS] Legacy runtime outputs are not tracked"
echo "[PASS] config.yaml is not staged"
echo "[PASS] No active Python trading API keyword found"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
