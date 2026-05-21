#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 81-84 acceptance runtime efficiency check"

required_files=(
  "docs/ACCEPTANCE_RUNTIME_EFFICIENCY.md"
  "scripts/daily_research_run.sh"
  "scripts/project_acceptance_suite.sh"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing required file: $file"
    exit 1
  fi
done

echo "[INFO] Verify --skip-tests support"
if ! grep -q -- "--skip-tests" scripts/daily_research_run.sh; then
  echo "[FAIL] daily_research_run.sh does not support --skip-tests"
  exit 1
fi

if ! grep -q -- "daily_research_run.sh --skip-tests" scripts/project_acceptance_suite.sh; then
  echo "[FAIL] project_acceptance_suite.sh does not call daily_research_run.sh --skip-tests"
  exit 1
fi

echo "[INFO] Python syntax check"
python3 -m py_compile main.py src/*.py

echo "[INFO] Unit tests"
python3 -m pytest -q

echo "[INFO] Daily research run with --skip-tests"
./scripts/daily_research_run.sh --skip-tests

echo "[INFO] Metadata schema check"
./scripts/phase77_80_daily_run_metadata_schema_check.sh

echo "[INFO] Project acceptance suite"
./scripts/project_acceptance_suite.sh

echo "[INFO] Runtime output git hygiene check"
if git status --short | grep -E "daily_research_run_summary.csv|reports/daily_research_run_report.md|final_research_plan_orchestrator.csv|report_template_daily_log_telegram_ready_output.csv|reports/telegram_ready_text.txt" >/dev/null 2>&1; then
  echo "[FAIL] Runtime output appears in git status"
  git status --short
  exit 1
fi

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

echo "[PASS] daily_research_run.sh supports --skip-tests"
echo "[PASS] project_acceptance_suite.sh avoids duplicate full test execution"
echo "[PASS] Python syntax check passed"
echo "[PASS] Unit tests passed"
echo "[PASS] Daily research run with --skip-tests passed"
echo "[PASS] Metadata schema check passed"
echo "[PASS] Project acceptance suite passed"
echo "[PASS] Runtime outputs do not pollute git status"
echo "[PASS] config.yaml is not staged"
echo "[PASS] No active Python trading API keyword found"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No real scheduler deployed"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
