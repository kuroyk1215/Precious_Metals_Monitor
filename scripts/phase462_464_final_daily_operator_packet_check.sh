#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 462-464 final daily operator packet check started"

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

bash scripts/operator_final_daily_packet.sh
bash scripts/operator_latest_strategy_decision.sh
bash scripts/operator_real_market_mvp_completion_gate.sh

for path in \
  src/operator_final_daily_packet.py \
  scripts/operator_final_daily_packet.sh \
  operator_final_daily_packet.csv \
  reports/operator_final_daily_packet.md \
  tests/test_operator_final_daily_packet.py \
  src/operator_latest_strategy_decision.py \
  scripts/operator_latest_strategy_decision.sh \
  operator_latest_strategy_decision.csv \
  reports/operator_latest_strategy_decision_report.md \
  tests/test_operator_latest_strategy_decision.py \
  src/operator_real_market_mvp_completion_gate.py \
  scripts/operator_real_market_mvp_completion_gate.sh \
  operator_real_market_mvp_completion_gate.csv \
  reports/operator_real_market_mvp_completion_gate_report.md \
  tests/test_operator_real_market_mvp_completion_gate.py \
  scripts/phase462_464_final_daily_operator_packet_check.sh; do
  [[ -f "$path" ]] || { echo "[FAIL] missing Phase 462-464 artifact: $path"; exit 1; }
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
    Path("src/operator_final_daily_packet.py"),
    Path("src/operator_latest_strategy_decision.py"),
    Path("src/operator_real_market_mvp_completion_gate.py"),
    Path("scripts/operator_final_daily_packet.sh"),
    Path("scripts/operator_latest_strategy_decision.sh"),
    Path("scripts/operator_real_market_mvp_completion_gate.sh"),
    Path("scripts/phase462_464_final_daily_operator_packet_check.sh"),
    Path("tests/test_operator_final_daily_packet.py"),
    Path("tests/test_operator_latest_strategy_decision.py"),
    Path("tests/test_operator_real_market_mvp_completion_gate.py"),
]

patterns = {
    "place" + "Order": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?placeOrder\s*\("),
    "cancel" + "Order": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?cancelOrder\s*\("),
    "req" + "HistoricalData": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?reqHistoricalData\s*\("),
    "re" + "balance": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?rebalance\s*\("),
    "account" + "Summary": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?accountSummary\s*\("),
    "req" + "Account": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?reqAccount\w*\s*\("),
    "req" + "Positions": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?reqPositions\s*\("),
    "position " + "read path": re.compile(r"(?<![A-Za-z0-9_.'\"])\.?positions?\s*\("),
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

PYTHONPATH="$REPO_ROOT" "$PYTHON_BIN" - <<'PY'
from pathlib import Path
import re

paths = [
    Path("operator_final_daily_packet.csv"),
    Path("operator_latest_strategy_decision.csv"),
    Path("operator_real_market_mvp_completion_gate.csv"),
    Path("reports/operator_final_daily_packet.md"),
    Path("reports/operator_latest_strategy_decision_report.md"),
    Path("reports/operator_real_market_mvp_completion_gate_report.md"),
]

word_pattern = re.compile(r"\b(" + "|".join(["B" + "UY", "S" + "ELL", "O" + "RDER", "E" + "XECUTE"]) + r")\b")
hits = []
allowed_fragments = ("forbidden wording", "no execution")
for path in paths:
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        if word_pattern.search(line) and not any(fragment in line for fragment in allowed_fragments):
            hits.append(f"{path}:{lineno}:{line}")

if hits:
    raise SystemExit("[FAIL] trade execution word emitted outside allowed safety wording\n" + "\n".join(hits))
PY

for marker in \
  "current readiness" \
  "strategy explanation" \
  "quote availability" \
  "safety status" \
  "manual review status" \
  "operator next step" \
  "latest_decision_status=" \
  "completion_gate_status=" \
  "no auto trading" \
  "no account reads" \
  "no position reads" \
  "no historical data requests" \
  "no Telegram real send" \
  "no order/cancel/rebalance"; do
  if ! rg -n "$marker" reports/operator_final_daily_packet.md reports/operator_latest_strategy_decision_report.md reports/operator_real_market_mvp_completion_gate_report.md >/dev/null; then
    echo "[FAIL] missing Phase 462-464 report marker: $marker"
    exit 1
  fi
done

echo "[PASS] Phase 462-464 final daily operator packet check completed"
