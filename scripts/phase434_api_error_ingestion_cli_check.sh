#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 434 API error ingestion CLI check started"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_DIR="$(mktemp -d /tmp/phase434_api_errors.XXXXXX)"
export FIXTURE_DIR

PYTHONPATH="$REPO_ROOT" python3 - <<'PY'
from pathlib import Path
import csv
import os

root = Path(os.environ["FIXTURE_DIR"])
fixtures = {
    "execution.csv": [
        {
            "execution_c_status": "EXECUTION_C_VALIDATION_READY",
            "validation_decision": "REVIEW_READY_REFERENCE_ONLY",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
            "telegram_send_triggered": "false",
        }
    ],
    "snapshot.csv": [
        {
            "display_symbol": "GLD",
            "snapshot_status": "DELAYED_SNAPSHOT_RETURNED",
            "effective_market_data_type": "delayed",
            "data_delay_flag": "delayed",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
        },
        {
            "display_symbol": "SLV",
            "snapshot_status": "DELAYED_SNAPSHOT_RETURNED",
            "effective_market_data_type": "delayed",
            "data_delay_flag": "delayed",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
        },
    ],
    "ibkr_market_data_api_errors.csv": [
        {
            "run_id": "fixture_run",
            "timestamp": "2026-05-24T12:00:00+0900",
            "reqId": "11",
            "display_symbol": "GLD",
            "symbol": "GLD",
            "error_code": "10089",
            "raw_error_message": "Requested market data is not subscribed. Delayed market data available.",
            "normalized_error_class": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE",
            "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
            "telegram_send_triggered": "false",
        },
        {
            "run_id": "fixture_run",
            "timestamp": "2026-05-24T12:00:01+0900",
            "reqId": "12",
            "display_symbol": "SLV",
            "symbol": "SLV",
            "error_code": "10089",
            "raw_error_message": "Requested market data is not subscribed. Delayed market data available.",
            "normalized_error_class": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE",
            "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
            "telegram_send_triggered": "false",
        },
    ],
    "operator.csv": [
        {
            "display_symbol": "GLD",
            "operator_packet_status": "OPERATOR_REVIEW_READY",
            "final_research_bucket": "delayed_reference",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
        },
        {
            "display_symbol": "SLV",
            "operator_packet_status": "OPERATOR_REVIEW_READY",
            "final_research_bucket": "delayed_reference",
            "action_allowed": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
        },
    ],
    "telegram.csv": [
        {
            "display_symbol": "GLD",
            "notification_status": "READY_TO_NOTIFY",
            "action_allowed": "false",
            "telegram_send_triggered": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
        },
        {
            "display_symbol": "SLV",
            "notification_status": "READY_TO_NOTIFY",
            "action_allowed": "false",
            "telegram_send_triggered": "false",
            "broker_execution_triggered": "false",
            "historical_data_request_triggered": "false",
            "account_read_triggered": "false",
            "position_read_triggered": "false",
        },
    ],
}

for name, rows in fixtures.items():
    with (root / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
PY

POST_OUT="$(PYTHONPATH="$REPO_ROOT" bash "$REPO_ROOT/scripts/first_operator_run_post_analysis.sh" \
  --execution-c-packet "$FIXTURE_DIR/execution.csv" \
  --snapshot-csv "$FIXTURE_DIR/snapshot.csv" \
  --api-errors-csv "$FIXTURE_DIR/ibkr_market_data_api_errors.csv" \
  --operator-packet "$FIXTURE_DIR/operator.csv" \
  --telegram-notification-packet "$FIXTURE_DIR/telegram.csv" \
  --output-csv "$FIXTURE_DIR/first_operator_run_post_analysis.csv" \
  --output-report "$FIXTURE_DIR/first_operator_run_post_analysis_report.md" \
  --summary-md "$FIXTURE_DIR/first_operator_run_summary.md")"
printf '%s\n' "$POST_OUT"

for marker in \
  "post_run_status=POST_RUN_REFERENCE_READY" \
  "analysis_decision=ACCEPT_REFERENCE_ONLY_RUN" \
  "semantic_status=GLOBAL_NO_TRADE_BUT_OPERATOR_REVIEW_READY" \
  "error_codes_detected=10089" \
  "error_10089_detected=true" \
  "live_subscription_status=LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE" \
  "delayed_reference_count=2" \
  "action_allowed=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false" \
  "telegram_send_triggered=false"
do
  if ! grep -F "$marker" <<<"$POST_OUT" >/dev/null; then
    echo "[FAIL] Missing Phase 434 marker: $marker"
    exit 1
  fi
done

(
  cd "$FIXTURE_DIR"
  DEFAULT_OUT="$(PYTHONPATH="$REPO_ROOT" bash "$REPO_ROOT/scripts/first_operator_run_post_analysis.sh" \
    --execution-c-packet execution.csv \
    --snapshot-csv snapshot.csv \
    --operator-packet operator.csv \
    --telegram-notification-packet telegram.csv \
    --output-csv default_first_operator_run_post_analysis.csv \
    --output-report default_first_operator_run_post_analysis_report.md \
    --summary-md default_first_operator_run_summary.md)"
  printf '%s\n' "$DEFAULT_OUT"
  if ! grep -F "error_10089_detected=true" <<<"$DEFAULT_OUT" >/dev/null; then
    echo "[FAIL] Default ibkr_market_data_api_errors.csv was not consumed"
    exit 1
  fi
  if ! grep -F "delayed_reference_count=2" <<<"$DEFAULT_OUT" >/dev/null; then
    echo "[FAIL] Default ingestion changed delayed reference counting"
    exit 1
  fi
)

PYTHONPATH="$REPO_ROOT" python3 - <<'PY'
from pathlib import Path
import csv
import os

root = Path(os.environ["FIXTURE_DIR"])
for name in ("first_operator_run_post_analysis.csv", "default_first_operator_run_post_analysis.csv"):
    row = next(csv.DictReader((root / name).open(newline="", encoding="utf-8")))
    assert row["post_run_status"] == "POST_RUN_REFERENCE_READY", row
    assert row["analysis_decision"] == "ACCEPT_REFERENCE_ONLY_RUN", row
    assert row["semantic_status"] == "GLOBAL_NO_TRADE_BUT_OPERATOR_REVIEW_READY", row
    assert "10089" in row["error_codes_detected"], row
    assert row["error_10089_detected"] == "true", row
    assert row["live_subscription_status"] == "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE", row
    assert row["delayed_reference_count"] == "2", row
    assert row["action_allowed"] == "false", row
    assert row["broker_execution_triggered"] == "false", row
    assert row["historical_data_request_triggered"] == "false", row
    assert row["account_read_triggered"] == "false", row
    assert row["position_read_triggered"] == "false", row
    assert row["telegram_send_triggered"] == "false", row
    assert row["manual_review_required"] == "true", row
PY

echo "[PASS] Phase 434 API error ingestion CLI check completed"
