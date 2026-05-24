#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 441 daily MVP run wrapper check started"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_OUT="$(mktemp /tmp/phase441_daily_mvp_run.XXXXXX)"

PYTHONPATH="$REPO_ROOT" bash "$REPO_ROOT/scripts/operator_daily_mvp_run.sh" > "$RUN_OUT"
cat "$RUN_OUT"

for path in \
  "$REPO_ROOT/operator_daily_mvp_run_summary.csv" \
  "$REPO_ROOT/reports/operator_daily_mvp_run_summary.md" \
  "$REPO_ROOT/reports/dashboard.html" \
  "$REPO_ROOT/reports/latest_operator_handoff_summary.md" \
  "$REPO_ROOT/reports/research_trading_plan_report.md" \
  "$REPO_ROOT/reports/watchlist_universe_report.md" \
  "$REPO_ROOT/reports/telegram_notification_gate_report.md"; do
  [[ -f "$path" ]] || { echo "[FAIL] missing artifact: $path"; exit 1; }
done

if ! rg -n "top_level_status=(DAILY_MVP_RUN_READY|DAILY_MVP_RUN_PARTIAL)" "$RUN_OUT" "$REPO_ROOT/reports/operator_daily_mvp_run_summary.md" >/dev/null; then
  echo "[FAIL] top-level status is not READY or PARTIAL"
  exit 1
fi

for marker in \
  "action_allowed=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false" \
  "telegram_send_triggered=false" \
  "offline_only=true"; do
  if ! rg -n "$marker" "$RUN_OUT" "$REPO_ROOT/reports/operator_daily_mvp_run_summary.md" >/dev/null; then
    echo "[FAIL] missing safety marker: $marker"
    exit 1
  fi
done

PYTHONPATH="$REPO_ROOT" python3 - <<'PY'
from pathlib import Path
import csv
import re

root = Path(".")
rows = list(csv.DictReader((root / "operator_daily_mvp_run_summary.csv").open(newline="", encoding="utf-8")))
assert rows, "empty summary"
required = {
    "daily_operator_handoff_summary",
    "latest_artifact_entrypoint",
    "research_trading_plan",
    "watchlist_universe",
    "telegram_notification_gate",
    "local_dashboard",
}
assert {row["step_name"] for row in rows} == required, rows
for row in rows:
    assert row["offline_only"] == "true", row
    for field in (
        "action_allowed",
        "broker_execution_triggered",
        "historical_data_request_triggered",
        "account_read_triggered",
        "position_read_triggered",
        "telegram_send_triggered",
    ):
        assert row[field] == "false", (field, row)

for relative in [
    "operator_daily_mvp_run_summary.csv",
    "reports/operator_daily_mvp_run_summary.md",
    "reports/dashboard.html",
]:
    text = (root / relative).read_text(encoding="utf-8")
    for line in text.splitlines():
        if "recommended_operator_action" not in line and "Next Manual Operator Step" not in line:
            continue
        upper = line.upper()
        for word in ("BUY", "SELL", "ORDER", "CANCEL", "REBALANCE", "AUTO_TRADE", "EXECUTE"):
            assert not re.search(rf"(?<![A-Z0-9_]){word}(?![A-Z0-9_])", upper), (word, line)
PY

if rg -n "urllib|requests|api\.telegram\.org|sendMessage|connect\(|reqMktData|reqHistoricalData|reqAccount|accountSummary|positions\(|reqPositions|placeOrder|cancelOrder|real_connection_allowed: true|market_data_request_allowed: true|historical_data_request_allowed: true|trading_actions_allowed: true" \
  "$REPO_ROOT/src/operator_daily_mvp_run_summary.py" "$REPO_ROOT/scripts/operator_daily_mvp_run.sh" >/tmp/phase441_forbidden_scan.txt
then
  cat /tmp/phase441_forbidden_scan.txt
  echo "[FAIL] Forbidden live/network/account/historical/trading call introduced"
  exit 1
fi

echo "[PASS] Phase 441 daily MVP run wrapper check completed"
