#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 435 daily operator handoff summary check started"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_DIR="$(mktemp -d /tmp/phase435_handoff.XXXXXX)"
export FIXTURE_DIR

PYTHONPATH="$REPO_ROOT" python3 - <<'PY'
from pathlib import Path
import csv
import os

root = Path(os.environ["FIXTURE_DIR"])
fixtures = {
    "map.csv": [
        {"run_id": "fixture_run", "run_timestamp": "2026-05-24T12:00:00+0900", "display_symbol": "GLD", "symbol": "GLD", "data_source_route": "SYMBOL_BASED_FIRST_VALIDATION", "action_allowed": "false"},
        {"run_id": "fixture_run", "run_timestamp": "2026-05-24T12:00:00+0900", "display_symbol": "SLV", "symbol": "SLV", "data_source_route": "SYMBOL_BASED_FIRST_VALIDATION", "action_allowed": "false"},
    ],
    "snapshot.csv": [
        {"display_symbol": "GLD", "symbol": "GLD", "snapshot_status": "DELAYED_SNAPSHOT_RETURNED", "effective_market_data_type": "delayed", "data_delay_flag": "delayed", "market_price": "221.10", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false"},
        {"display_symbol": "SLV", "symbol": "SLV", "snapshot_status": "DELAYED_SNAPSHOT_RETURNED", "effective_market_data_type": "delayed", "data_delay_flag": "delayed", "market_price": "68.31", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false"},
    ],
    "api_errors.csv": [
        {"display_symbol": "GLD", "symbol": "GLD", "error_code": "10089", "raw_error_message": "Requested market data is not subscribed. Delayed market data available.", "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false", "account_read_triggered": "false", "position_read_triggered": "false", "telegram_send_triggered": "false"},
        {"display_symbol": "GLD", "symbol": "GLD", "error_code": "10089", "raw_error_message": "duplicate persisted error row should not affect delayed_reference_count", "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false", "account_read_triggered": "false", "position_read_triggered": "false", "telegram_send_triggered": "false"},
        {"display_symbol": "SLV", "symbol": "SLV", "error_code": "10089", "raw_error_message": "Requested market data is not subscribed. Delayed market data available.", "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false", "account_read_triggered": "false", "position_read_triggered": "false", "telegram_send_triggered": "false"},
    ],
    "execution.csv": [
        {"execution_c_status": "EXECUTION_C_VALIDATION_READY", "validation_decision": "REVIEW_READY_REFERENCE_ONLY", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false", "account_read_triggered": "false", "position_read_triggered": "false", "telegram_send_triggered": "false"},
    ],
    "operator.csv": [
        {"display_symbol": "GLD", "operator_packet_status": "OPERATOR_REVIEW_READY", "final_research_bucket": "delayed_reference", "usable_reference_price": "221.10", "manual_review_required": "true", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false", "account_read_triggered": "false", "position_read_triggered": "false", "telegram_send_triggered": "false"},
        {"display_symbol": "SLV", "operator_packet_status": "OPERATOR_REVIEW_READY", "final_research_bucket": "delayed_reference", "usable_reference_price": "68.31", "manual_review_required": "true", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false", "account_read_triggered": "false", "position_read_triggered": "false", "telegram_send_triggered": "false"},
    ],
    "post.csv": [
        {"delayed_reference_count": "2", "error_codes_detected": "10089", "error_10089_detected": "true", "error_354_detected": "false", "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE", "action_allowed": "false", "broker_execution_triggered": "false", "historical_data_request_triggered": "false", "account_read_triggered": "false", "position_read_triggered": "false", "telegram_send_triggered": "false"},
    ],
    "telegram.csv": [
        {"display_symbol": "GLD", "notification_status": "READY_TO_NOTIFY", "action_allowed": "false", "telegram_send_triggered": "false"},
        {"display_symbol": "SLV", "notification_status": "READY_TO_NOTIFY", "action_allowed": "false", "telegram_send_triggered": "false"},
    ],
}

for name, rows in fixtures.items():
    with (root / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
PY

OUT="$(PYTHONPATH="$REPO_ROOT" bash "$REPO_ROOT/scripts/daily_operator_handoff_summary.sh" \
  --contract-map-csv "$FIXTURE_DIR/map.csv" \
  --snapshot-csv "$FIXTURE_DIR/snapshot.csv" \
  --api-errors-csv "$FIXTURE_DIR/api_errors.csv" \
  --execution-c-packet "$FIXTURE_DIR/execution.csv" \
  --operator-packet "$FIXTURE_DIR/operator.csv" \
  --post-analysis-csv "$FIXTURE_DIR/post.csv" \
  --telegram-notification-packet "$FIXTURE_DIR/telegram.csv" \
  --output-csv "$FIXTURE_DIR/daily_operator_handoff_summary.csv" \
  --output-report "$FIXTURE_DIR/daily_operator_handoff_summary.md")"
printf '%s\n' "$OUT"

[[ -f "$FIXTURE_DIR/daily_operator_handoff_summary.csv" ]] || { echo "[FAIL] summary csv missing"; exit 1; }
[[ -f "$FIXTURE_DIR/daily_operator_handoff_summary.md" ]] || { echo "[FAIL] summary report missing"; exit 1; }

PYTHONPATH="$REPO_ROOT" python3 - <<'PY'
from pathlib import Path
import csv
import os

root = Path(os.environ["FIXTURE_DIR"])
rows = list(csv.DictReader((root / "daily_operator_handoff_summary.csv").open(newline="", encoding="utf-8")))
assert rows, "missing rows"
assert {row["display_symbol"] for row in rows} == {"GLD", "SLV"}, rows
for row in rows:
    assert row["top_level_status"] == "OPERATOR_HANDOFF_REFERENCE_READY", row
    assert row["error_10089_detected"] == "true", row
    assert "10089" in row["api_error_codes"], row
    assert row["live_subscription_status"] == "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE", row
    assert row["delayed_reference_count"] == "2", row
    assert row["action_allowed"] == "false", row
    assert row["broker_execution_triggered"] == "false", row
    assert row["historical_data_request_triggered"] == "false", row
    assert row["account_read_triggered"] == "false", row
    assert row["position_read_triggered"] == "false", row
    assert row["telegram_send_triggered"] == "false", row
    assert row["recommended_operator_action"] == "MANUAL_REFERENCE_REVIEW_ONLY", row
    assert not any(word in row["recommended_operator_action"].upper() for word in ("TRADE", "BUY", "SELL", "ORDER", "CANCEL", "REBALANCE")), row

report = (root / "daily_operator_handoff_summary.md").read_text(encoding="utf-8")
assert "top_level_status=OPERATOR_HANDOFF_REFERENCE_READY" in report, report
PY

for marker in \
  "top_level_status=OPERATOR_HANDOFF_REFERENCE_READY" \
  "delayed_reference_count=2" \
  "live_subscription_status=LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE" \
  "action_allowed=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false" \
  "telegram_send_triggered=false"
do
  if ! grep -F "$marker" <<<"$OUT" >/dev/null; then
    echo "[FAIL] Missing marker: $marker"
    exit 1
  fi
done

echo "[PASS] Phase 435 daily operator handoff summary check completed"
