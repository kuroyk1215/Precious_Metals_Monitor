#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 453-455 real-market strategy quality check started"

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

bash scripts/operator_real_market_archive_compare.sh
bash scripts/operator_signal_threshold_explainer.sh
bash scripts/operator_strategy_quality_report.sh

for path in \
  src/operator_real_market_archive_compare.py \
  scripts/operator_real_market_archive_compare.sh \
  operator_real_market_archive_compare.csv \
  reports/operator_real_market_archive_compare_report.md \
  tests/test_operator_real_market_archive_compare.py \
  src/operator_signal_threshold_explainer.py \
  scripts/operator_signal_threshold_explainer.sh \
  operator_signal_threshold_explainer.csv \
  reports/operator_signal_threshold_explainer_report.md \
  tests/test_operator_signal_threshold_explainer.py \
  src/operator_strategy_quality_report.py \
  scripts/operator_strategy_quality_report.sh \
  operator_strategy_quality_report.csv \
  reports/operator_strategy_quality_report.md \
  tests/test_operator_strategy_quality_report.py \
  scripts/phase453_455_real_market_strategy_quality_check.sh; do
  [[ -f "$path" ]] || { echo "[FAIL] missing Phase 453-455 artifact: $path"; exit 1; }
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
    Path("src/operator_real_market_archive_compare.py"),
    Path("src/operator_signal_threshold_explainer.py"),
    Path("src/operator_strategy_quality_report.py"),
    Path("scripts/operator_real_market_archive_compare.sh"),
    Path("scripts/operator_signal_threshold_explainer.sh"),
    Path("scripts/operator_strategy_quality_report.sh"),
    Path("scripts/phase453_455_real_market_strategy_quality_check.sh"),
    Path("tests/test_operator_real_market_archive_compare.py"),
    Path("tests/test_operator_signal_threshold_explainer.py"),
    Path("tests/test_operator_strategy_quality_report.py"),
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
  "comparison_window=" \
  "status_consistency=" \
  "threshold_status=" \
  "manual_review_required=true" \
  "quality_status=" \
  "data available=" \
  "data unavailable but safe=" \
  "insufficient history=" \
  "signal insufficient=" \
  "manual review only=" \
  "no auto trading" \
  "no account reads" \
  "no position reads" \
  "no historical data requests" \
  "no Telegram real send" \
  "no order/cancel/rebalance"; do
  if ! rg -n "$marker" reports/operator_real_market_archive_compare_report.md reports/operator_signal_threshold_explainer_report.md reports/operator_strategy_quality_report.md >/dev/null; then
    echo "[FAIL] missing Phase 453-455 report marker: $marker"
    exit 1
  fi
done

echo "[PASS] Phase 453-455 real-market strategy quality check completed"
