#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 443 real marketdata smoke diagnostics archive check started"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

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
  src/operator_real_marketdata_smoke_archive.py \
  scripts/operator_real_marketdata_smoke_archive.sh \
  operator_real_marketdata_smoke_archive.csv \
  reports/operator_real_marketdata_smoke_archive_report.md \
  scripts/phase443_real_marketdata_smoke_archive_check.sh \
  tests/test_operator_real_marketdata_smoke_archive.py; do
  [[ -f "$path" ]] || { echo "[FAIL] missing Phase 443 artifact: $path"; exit 1; }
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
    Path("src/operator_real_marketdata_smoke_archive.py"),
    Path("scripts/operator_real_marketdata_smoke_archive.sh"),
    Path("scripts/phase443_real_marketdata_smoke_archive_check.sh"),
    Path("tests/test_operator_real_marketdata_smoke_archive.py"),
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
  "source_exists=" \
  "top_level_status=" \
  "final_safety_status=" \
  "config_restored=" \
  "config_file_modified=" \
  "real_connection_allowed_during_run=" \
  "market_data_request_allowed_during_run=" \
  "contract_qualification_allowed=false" \
  "historical_data_request_allowed=false" \
  "trading_actions_allowed=false" \
  "account_read_allowed=false" \
  "position_read_allowed=false" \
  "telegram_send_allowed=false" \
  "req_mkt_data_allowed=" \
  "req_historical_data_allowed=false" \
  "order_action_allowed=false" \
  "cancel_action_allowed=false" \
  "rebalance_action_allowed=false" \
  "diagnostic_category=" \
  "diagnostic_reason=" \
  "operator_next_step="; do
  if ! rg -n "$marker" reports/operator_real_marketdata_smoke_archive_report.md >/dev/null; then
    echo "[FAIL] missing Phase 443 archive report marker: $marker"
    exit 1
  fi
done

echo "[PASS] Phase 443 real marketdata smoke diagnostics archive check completed"
