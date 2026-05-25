#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 450-452 real-market MVP hardening check started"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
mkdir -p .pycache
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-$REPO_ROOT/.pycache}"

PYTHON_BIN="${PYTHON:-python3}"
if [[ -x "$REPO_ROOT/.venv/bin/python" && "${PYTHON:-}" == "" ]]; then
  PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
fi

"$PYTHON_BIN" -m py_compile main.py src/*.py
PYTHONPATH=. "$PYTHON_BIN" -m pytest -q

bash scripts/operator_real_market_mvp_status.sh
bash scripts/operator_daily_checklist.sh
bash scripts/operator_real_market_mvp_regression_check.sh

for path in \
  src/operator_real_market_mvp_status.py \
  scripts/operator_real_market_mvp_status.sh \
  operator_real_market_mvp_status.csv \
  reports/operator_real_market_mvp_status_report.md \
  tests/test_operator_real_market_mvp_status.py \
  src/operator_daily_checklist.py \
  scripts/operator_daily_checklist.sh \
  operator_daily_checklist.csv \
  reports/operator_daily_checklist.md \
  tests/test_operator_daily_checklist.py \
  src/operator_real_market_mvp_regression.py \
  scripts/operator_real_market_mvp_regression_check.sh \
  scripts/phase450_452_real_market_mvp_hardening_check.sh \
  tests/test_operator_real_market_mvp_regression.py \
  reports/operator_real_market_mvp_regression_report.md \
  operator_real_market_mvp_regression.csv; do
  [[ -f "$path" ]] || { echo "[FAIL] missing Phase 450-452 artifact: $path"; exit 1; }
done

if git diff --cached --name-only | rg -n '^config\.yaml$' >/dev/null; then
  echo "[FAIL] config.yaml is staged"
  exit 1
fi

if git diff --cached --name-only | rg -n '^ibkr_market_data_api_errors\.csv$' >/dev/null; then
  echo "[FAIL] ibkr_market_data_api_errors.csv is staged"
  exit 1
fi

PYTHONPATH="$REPO_ROOT" "$PYTHON_BIN" - <<'PY'
from pathlib import Path
import re

paths = [
    Path("src/operator_real_market_mvp_status.py"),
    Path("src/operator_daily_checklist.py"),
    Path("src/operator_real_market_mvp_regression.py"),
    Path("scripts/operator_real_market_mvp_status.sh"),
    Path("scripts/operator_daily_checklist.sh"),
    Path("scripts/operator_real_market_mvp_regression_check.sh"),
    Path("scripts/phase450_452_real_market_mvp_hardening_check.sh"),
    Path("tests/test_operator_real_market_mvp_status.py"),
    Path("tests/test_operator_daily_checklist.py"),
    Path("tests/test_operator_real_market_mvp_regression.py"),
]

patterns = {
    "placeOrder": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?placeOrder\s*\("),
    "cancelOrder": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?cancelOrder\s*\("),
    "reqHistoricalData": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?reqHistoricalData\s*\("),
    "rebalance": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?rebalance\s*\("),
    "accountSummary": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?accountSummary\s*\("),
    "reqAccount": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?reqAccount\w*\s*\("),
    "reqPositions": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?reqPositions\s*\("),
    "position read path": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?positions?\s*\("),
    "Telegram real send path": re.compile(r"(api\.telegram\.org|send" + r"Message|requests\.post|urllib\.request)"),
}

hits = []
for path in paths:
    text = path.read_text(encoding="utf-8")
    for label, pattern in patterns.items():
        for match in pattern.finditer(text):
            hits.append(f"{path}:{label}:{match.group(0)}")

if hits:
    raise SystemExit("[FAIL] forbidden live/account/historical/trading/send path introduced\n" + "\n".join(hits))
PY

for marker in \
  "mvp_status=" \
  "safety_clean=true" \
  "manual_review_only=true" \
  "no auto trading" \
  "no account reads" \
  "no position reads" \
  "no historical data requests" \
  "no Telegram real send" \
  "no order/cancel/rebalance"; do
  if ! rg -n "$marker" reports/operator_real_market_mvp_status_report.md reports/operator_daily_checklist.md reports/operator_real_market_mvp_regression_report.md >/dev/null; then
    echo "[FAIL] missing Phase 450-452 report marker: $marker"
    exit 1
  fi
done

echo "[PASS] Phase 450-452 real-market MVP hardening check completed"
