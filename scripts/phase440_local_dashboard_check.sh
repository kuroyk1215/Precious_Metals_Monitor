#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 440 local dashboard check started"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="$REPO_ROOT/reports/dashboard.html"
RUN_OUT="$(mktemp /tmp/phase440_local_dashboard.XXXXXX)"

PYTHONPATH="$REPO_ROOT" bash "$REPO_ROOT/scripts/local_dashboard.sh" \
  --root "$REPO_ROOT" \
  --output-html "reports/dashboard.html" > "$RUN_OUT"
cat "$RUN_OUT"

[[ -f "$OUTPUT" ]] || { echo "[FAIL] reports/dashboard.html missing"; exit 1; }

if ! rg -n "dashboard_status=(DASHBOARD_READY|DASHBOARD_PARTIAL)" "$RUN_OUT" "$OUTPUT" >/dev/null; then
  echo "[FAIL] dashboard_status is not ready or partial"
  exit 1
fi

for marker in \
  "Operator Handoff Summary" \
  "Research Trading Plan Summary" \
  "Watchlist Universe Summary" \
  "Telegram Gate Summary" \
  "Safety Summary"; do
  if ! rg -n "$marker" "$OUTPUT" >/dev/null; then
    echo "[FAIL] missing dashboard section: $marker"
    exit 1
  fi
done

if [[ -f "$REPO_ROOT/latest_daily_operator_handoff_summary.csv" ]]; then
  for symbol in GLD SLV; do
    if ! rg -n "<td>${symbol}</td>" "$OUTPUT" >/dev/null; then
      echo "[FAIL] missing symbol row: $symbol"
      exit 1
    fi
  done
fi

if [[ -f "$REPO_ROOT/watchlist_universe.csv" ]]; then
  for symbol in 1540 1542 518880; do
    if ! rg -n "<td>${symbol}</td>" "$OUTPUT" >/dev/null; then
      echo "[FAIL] missing watchlist symbol row: $symbol"
      exit 1
    fi
  done
fi

for marker in \
  "action_allowed</th><td>false" \
  "broker_execution_triggered</th><td>false" \
  "historical_data_request_triggered</th><td>false" \
  "account_read_triggered</th><td>false" \
  "position_read_triggered</th><td>false" \
  "telegram_send_triggered</th><td>false"; do
  if ! rg -n "$marker" "$OUTPUT" >/dev/null; then
    echo "[FAIL] missing safety marker: $marker"
    exit 1
  fi
done

python3 - "$OUTPUT" <<'PY'
from pathlib import Path
import re
import sys

html = Path(sys.argv[1]).read_text(encoding="utf-8")
rows = re.findall(r"<tr>(.*?)</tr>", html, flags=re.S)
for row in rows:
    if "recommended_operator_action" in row:
        continue
    cells = re.findall(r"<td>(.*?)</td>", row, flags=re.S)
    if len(cells) >= 5:
        action = re.sub(r"<.*?>", "", cells[4]).upper()
        for word in ("BUY", "SELL", "ORDER", "CANCEL", "REBALANCE", "AUTO_TRADE", "EXECUTE"):
            assert word not in action, (word, action)
PY

if rg -n "urllib|requests|api\.telegram\.org|sendMessage|connect\(|reqMktData|reqHistoricalData|reqAccount|accountSummary|positions\(|reqPositions|placeOrder|cancelOrder|real_connection_allowed: true|market_data_request_allowed: true|historical_data_request_allowed: true|trading_actions_allowed: true" \
  "$REPO_ROOT/src/local_dashboard.py" "$REPO_ROOT/scripts/local_dashboard.sh" >/tmp/phase440_forbidden_scan.txt
then
  cat /tmp/phase440_forbidden_scan.txt
  echo "[FAIL] Forbidden live/network/account/historical/trading call introduced"
  exit 1
fi

echo "[PASS] Phase 440 local dashboard check completed"
