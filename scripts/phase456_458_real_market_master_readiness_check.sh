#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 456-458 real-market master readiness check started"

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

bash scripts/operator_daily_master_run.sh
bash scripts/operator_continuity_archive_index.sh
bash scripts/operator_mvp_readiness_report.sh

for path in \
  src/operator_daily_master_run.py \
  scripts/operator_daily_master_run.sh \
  operator_daily_master_run_summary.csv \
  reports/operator_daily_master_run_report.md \
  tests/test_operator_daily_master_run.py \
  src/operator_continuity_archive_index.py \
  scripts/operator_continuity_archive_index.sh \
  operator_continuity_archive_index.csv \
  reports/operator_continuity_archive_index_report.md \
  tests/test_operator_continuity_archive_index.py \
  src/operator_mvp_readiness_report.py \
  scripts/operator_mvp_readiness_report.sh \
  operator_mvp_readiness_report.csv \
  reports/operator_mvp_readiness_report.md \
  tests/test_operator_mvp_readiness_report.py \
  scripts/phase456_458_real_market_master_readiness_check.sh; do
  [[ -f "$path" ]] || { echo "[FAIL] missing Phase 456-458 artifact: $path"; exit 1; }
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
    Path("src/operator_daily_master_run.py"),
    Path("src/operator_continuity_archive_index.py"),
    Path("src/operator_mvp_readiness_report.py"),
    Path("scripts/operator_daily_master_run.sh"),
    Path("scripts/operator_continuity_archive_index.sh"),
    Path("scripts/operator_mvp_readiness_report.sh"),
    Path("scripts/phase456_458_real_market_master_readiness_check.sh"),
    Path("tests/test_operator_daily_master_run.py"),
    Path("tests/test_operator_continuity_archive_index.py"),
    Path("tests/test_operator_mvp_readiness_report.py"),
]

patterns = {
    "place" + "Order": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?placeOrder\s*\("),
    "cancel" + "Order": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?cancelOrder\s*\("),
    "req" + "HistoricalData": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?reqHistoricalData\s*\("),
    "re" + "balance": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?rebalance\s*\("),
    "account" + "Summary": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?accountSummary\s*\("),
    "req" + "Account": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?reqAccount\w*\s*\("),
    "req" + "Positions": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?reqPositions\s*\("),
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
  "master_status=" \
  "continuity_status=" \
  "readiness_status=" \
  "no auto trading" \
  "no account reads" \
  "no position reads" \
  "no historical data requests" \
  "no Telegram real send" \
  "no order/cancel/rebalance"; do
  if ! rg -n "$marker" reports/operator_daily_master_run_report.md reports/operator_continuity_archive_index_report.md reports/operator_mvp_readiness_report.md >/dev/null; then
    echo "[FAIL] missing Phase 456-458 report marker: $marker"
    exit 1
  fi
done

echo "[PASS] Phase 456-458 real-market master readiness check completed"
