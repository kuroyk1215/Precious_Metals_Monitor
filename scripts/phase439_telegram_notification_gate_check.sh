#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 439 Telegram notification gate check started"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_DIR="$(mktemp -d /tmp/phase439_telegram_gate.XXXXXX)"
export FIXTURE_DIR

mkdir -p "$FIXTURE_DIR/reports"

cp "$REPO_ROOT/latest_daily_operator_handoff_summary.csv" "$FIXTURE_DIR/latest_daily_operator_handoff_summary.csv"
cp "$REPO_ROOT/research_trading_plan.csv" "$FIXTURE_DIR/research_trading_plan.csv"
cp "$REPO_ROOT/watchlist_universe.csv" "$FIXTURE_DIR/watchlist_universe.csv"
[[ -f "$REPO_ROOT/reports/latest_operator_handoff_summary.md" ]] && cp "$REPO_ROOT/reports/latest_operator_handoff_summary.md" "$FIXTURE_DIR/reports/latest_operator_handoff_summary.md"
[[ -f "$REPO_ROOT/reports/research_trading_plan_report.md" ]] && cp "$REPO_ROOT/reports/research_trading_plan_report.md" "$FIXTURE_DIR/reports/research_trading_plan_report.md"
[[ -f "$REPO_ROOT/reports/watchlist_universe_report.md" ]] && cp "$REPO_ROOT/reports/watchlist_universe_report.md" "$FIXTURE_DIR/reports/watchlist_universe_report.md"

DEFAULT_OUT="$FIXTURE_DIR/default.out"
APPROVED_OUT="$FIXTURE_DIR/approved.out"

PYTHONPATH="$REPO_ROOT" bash "$REPO_ROOT/scripts/telegram_notification_gate.sh" \
  --root "$FIXTURE_DIR" \
  --output-csv "$FIXTURE_DIR/telegram_notification_gate.csv" \
  --output-report "$FIXTURE_DIR/reports/telegram_notification_gate_report.md" \
  --preview-report "$FIXTURE_DIR/reports/telegram_notification_approval_preview.md" > "$DEFAULT_OUT"
cat "$DEFAULT_OUT"

[[ -f "$FIXTURE_DIR/telegram_notification_gate.csv" ]] || { echo "[FAIL] telegram_notification_gate.csv missing"; exit 1; }
[[ -f "$FIXTURE_DIR/reports/telegram_notification_gate_report.md" ]] || { echo "[FAIL] telegram_notification_gate_report.md missing"; exit 1; }
[[ -f "$FIXTURE_DIR/reports/telegram_notification_approval_preview.md" ]] || { echo "[FAIL] telegram_notification_approval_preview.md missing"; exit 1; }

PYTHONPATH="$REPO_ROOT" bash "$REPO_ROOT/scripts/telegram_notification_gate.sh" \
  --root "$FIXTURE_DIR" \
  --send-approved \
  --approval-note "manual approval smoke test" \
  --output-csv "$FIXTURE_DIR/telegram_notification_gate_approved.csv" \
  --output-report "$FIXTURE_DIR/reports/telegram_notification_gate_report_approved.md" \
  --preview-report "$FIXTURE_DIR/reports/telegram_notification_approval_preview_approved.md" > "$APPROVED_OUT"
cat "$APPROVED_OUT"

PYTHONPATH="$REPO_ROOT" python3 - <<'PY'
from pathlib import Path
import csv
import os

root = Path(os.environ["FIXTURE_DIR"])

def row(path):
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows, path
    return rows[0]

default = row(root / "telegram_notification_gate.csv")
approved = row(root / "telegram_notification_gate_approved.csv")

for current in (default, approved):
    assert current["telegram_send_triggered"] == "false", current
    assert current["action_allowed"] == "false", current
    assert current["broker_execution_triggered"] == "false", current
    assert current["historical_data_request_triggered"] == "false", current
    assert current["account_read_triggered"] == "false", current
    assert current["position_read_triggered"] == "false", current
    assert current["telegram_send_gate_enabled"] == "false", current

assert default["approval_required"] == "true", default
assert default["send_approved"] == "false", default
assert approved["send_approved"] == "true", approved
assert approved["telegram_send_status"] == "APPROVED_BUT_SEND_NOT_IMPLEMENTED", approved

for path in [
    root / "reports/telegram_notification_approval_preview.md",
    root / "reports/telegram_notification_approval_preview_approved.md",
]:
    text = path.read_text(encoding="utf-8").upper()
    for word in ("BUY", "SELL", "ORDER", "CANCEL", "REBALANCE", "AUTO_TRADE", "EXECUTE"):
        assert word not in text, (word, path)

for current in (default, approved):
    joined = (current["recommended_notification_action"] + " " + current["telegram_send_status"]).upper()
    for word in ("BUY", "SELL", "ORDER", "CANCEL", "REBALANCE", "AUTO_TRADE", "EXECUTE"):
        assert word not in joined, (word, current)
PY

if rg -n "urllib|requests|api\.telegram\.org|sendMessage|connect\(|reqMktData|reqHistoricalData|reqAccount|accountSummary|positions\(|reqPositions|placeOrder|cancelOrder|real_connection_allowed: true|market_data_request_allowed: true|historical_data_request_allowed: true|trading_actions_allowed: true" \
  "$REPO_ROOT/src/telegram_notification_gate.py" "$REPO_ROOT/scripts/telegram_notification_gate.sh" >/tmp/phase439_forbidden_scan.txt
then
  cat /tmp/phase439_forbidden_scan.txt
  echo "[FAIL] Forbidden live/network/account/historical/trading call introduced"
  exit 1
fi

for marker in \
  "telegram_send_triggered=false" \
  "action_allowed=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false"; do
  if ! rg -n "$marker" "$DEFAULT_OUT" "$APPROVED_OUT" >/dev/null; then
    echo "[FAIL] missing output marker: $marker"
    exit 1
  fi
done

echo "[PASS] Phase 439 Telegram notification gate check completed"
