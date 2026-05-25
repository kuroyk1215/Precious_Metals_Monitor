#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 444-446 real marketdata operator chain check started"

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
  src/operator_real_marketdata_decision_gate.py \
  scripts/operator_real_marketdata_decision_gate.sh \
  operator_real_marketdata_decision_gate.csv \
  reports/operator_real_marketdata_decision_gate_report.md \
  tests/test_operator_real_marketdata_decision_gate.py \
  src/operator_real_marketdata_latest.py \
  scripts/operator_real_marketdata_latest.sh \
  operator_real_marketdata_latest.csv \
  reports/operator_real_marketdata_latest_report.md \
  tests/test_operator_real_marketdata_latest.py \
  scripts/operator_real_marketdata_daily_run.sh \
  operator_real_marketdata_daily_run_summary.csv \
  reports/operator_real_marketdata_daily_run_report.md \
  scripts/phase444_446_real_marketdata_operator_chain_check.sh \
  tests/test_operator_real_marketdata_daily_run.py; do
  [[ -f "$path" ]] || { echo "[FAIL] missing Phase 444-446 artifact: $path"; exit 1; }
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
    Path("src/operator_real_marketdata_decision_gate.py"),
    Path("src/operator_real_marketdata_latest.py"),
    Path("src/operator_real_marketdata_daily_run.py"),
    Path("scripts/operator_real_marketdata_decision_gate.sh"),
    Path("scripts/operator_real_marketdata_latest.sh"),
    Path("scripts/operator_real_marketdata_daily_run.sh"),
    Path("scripts/phase444_446_real_marketdata_operator_chain_check.sh"),
    Path("tests/test_operator_real_marketdata_decision_gate.py"),
    Path("tests/test_operator_real_marketdata_latest.py"),
    Path("tests/test_operator_real_marketdata_daily_run.py"),
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
  "operator_decision=" \
  "config_restored=" \
  "config_file_modified=" \
  "contract_qualification_allowed=false" \
  "historical_data_request_allowed=false" \
  "trading_actions_allowed=false" \
  "account_read_allowed=false" \
  "position_read_allowed=false" \
  "telegram_send_allowed=false" \
  "req_historical_data_allowed=false" \
  "order_action_allowed=false" \
  "cancel_action_allowed=false" \
  "rebalance_action_allowed=false"; do
  if ! rg -n "$marker" reports/operator_real_marketdata_decision_gate_report.md reports/operator_real_marketdata_latest_report.md reports/operator_real_marketdata_daily_run_report.md >/dev/null; then
    echo "[FAIL] missing Phase 444-446 report marker: $marker"
    exit 1
  fi
done

echo "[PASS] Phase 444-446 real marketdata operator chain check completed"
