#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 447-449 real quote signal report check started"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
mkdir -p .pycache
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-$REPO_ROOT/.pycache}"

python3 -m py_compile main.py src/*.py
if command -v pytest >/dev/null 2>&1; then
  PYTHONPATH=. pytest -q
elif [[ -x ".venv/bin/python" ]]; then
  echo "[INFO] pytest not found on PATH; using .venv/bin/python -m pytest"
  PYTHONPATH=. .venv/bin/python -m pytest -q
else
  echo "[FAIL] pytest is not available"
  exit 1
fi

for path in \
  src/operator_real_quote_normalization.py \
  scripts/operator_real_quote_normalization.sh \
  operator_real_quote_normalization.csv \
  reports/operator_real_quote_normalization_report.md \
  tests/test_operator_real_quote_normalization.py \
  src/operator_real_quote_signal_bridge.py \
  scripts/operator_real_quote_signal_bridge.sh \
  operator_real_quote_signal_bridge.csv \
  reports/operator_real_quote_signal_bridge_report.md \
  tests/test_operator_real_quote_signal_bridge.py \
  src/operator_daily_real_market_report.py \
  scripts/operator_daily_real_market_report.sh \
  operator_daily_real_market_report.csv \
  reports/operator_daily_real_market_report.md \
  scripts/phase447_449_real_quote_signal_report_check.sh \
  tests/test_operator_daily_real_market_report.py; do
  [[ -f "$path" ]] || { echo "[FAIL] missing Phase 447-449 artifact: $path"; exit 1; }
done

if git diff --cached --name-only | rg -n '^config\.yaml$' >/dev/null; then
  echo "[FAIL] config.yaml is staged"
  exit 1
fi

if git diff --cached --name-only | rg -n '^ibkr_market_data_api_errors\.csv$' >/dev/null; then
  echo "[FAIL] ibkr_market_data_api_errors.csv is staged"
  exit 1
fi

PYTHONPATH="$REPO_ROOT" python3 - <<'PY'
from pathlib import Path
import re

paths = [
    Path("src/operator_real_quote_normalization.py"),
    Path("src/operator_real_quote_signal_bridge.py"),
    Path("src/operator_daily_real_market_report.py"),
    Path("scripts/operator_real_quote_normalization.sh"),
    Path("scripts/operator_real_quote_signal_bridge.sh"),
    Path("scripts/operator_daily_real_market_report.sh"),
    Path("scripts/phase447_449_real_quote_signal_report_check.sh"),
    Path("tests/test_operator_real_quote_normalization.py"),
    Path("tests/test_operator_real_quote_signal_bridge.py"),
    Path("tests/test_operator_daily_real_market_report.py"),
]

patterns = {
    "placeOrder": re.compile(r"\bplaceOrder\s*\("),
    "cancelOrder": re.compile(r"\bcancelOrder\s*\("),
    "reqHistoricalData": re.compile(r"\breqHistoricalData\s*\("),
    "rebalance": re.compile(r"(?<!_)\brebalance\s*\("),
    "accountSummary": re.compile(r"\baccountSummary\s*\("),
    "reqAccount": re.compile(r"\breqAccount\w*\s*\("),
    "reqPositions": re.compile(r"\breqPositions\s*\("),
    "position read path": re.compile(r"\bpositions?\s*\("),
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
  "normalized_status=SAFE_UNAVAILABLE" \
  "operator_next_step=review_real_marketdata_connection" \
  "signal_bridge_status=HOLD_NO_REAL_QUOTE" \
  "observation_signal=NO_REAL_QUOTE_REVIEW_ONLY" \
  "no auto trading" \
  "no account reads" \
  "no position reads" \
  "no historical data requests" \
  "no Telegram real send" \
  "no order/cancel/rebalance"; do
  if ! rg -n "$marker" reports/operator_real_quote_normalization_report.md reports/operator_real_quote_signal_bridge_report.md reports/operator_daily_real_market_report.md >/dev/null; then
    echo "[FAIL] missing Phase 447-449 report marker: $marker"
    exit 1
  fi
done

echo "[PASS] Phase 447-449 real quote signal report check completed"
