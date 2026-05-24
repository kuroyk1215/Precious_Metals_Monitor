#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 432B persist Error 10089 normalize counts check started"

PATH=.venv/bin:$PATH python -m py_compile main.py src/*.py
PATH=.venv/bin:$PATH PYTHONPATH=. python -m pytest -q

FIXTURE_DIR="$(mktemp -d /tmp/phase432b_api_errors.XXXXXX)"
export FIXTURE_DIR
PATH=.venv/bin:$PATH PYTHONPATH=. python - <<'PY'
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
    "api_errors.csv": [
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

POST_OUT="$(PATH=.venv/bin:$PATH bash scripts/first_operator_run_post_analysis.sh \
  --execution-c-packet="$FIXTURE_DIR/execution.csv" \
  --snapshot-csv="$FIXTURE_DIR/snapshot.csv" \
  --api-errors-csv="$FIXTURE_DIR/api_errors.csv" \
  --operator-packet="$FIXTURE_DIR/operator.csv" \
  --telegram-notification-packet="$FIXTURE_DIR/telegram.csv" \
  --output-csv="$FIXTURE_DIR/first_operator_run_post_analysis.csv" \
  --output-report="$FIXTURE_DIR/first_operator_run_post_analysis_report.md" \
  --summary-md="$FIXTURE_DIR/first_operator_run_summary.md")"
printf '%s\n' "$POST_OUT"

for marker in \
  "action_allowed=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false" \
  "telegram_send_triggered=false"
do
  if ! grep -F "$marker" <<<"$POST_OUT" >/dev/null; then
    echo "[FAIL] Missing safety marker: $marker"
    exit 1
  fi
done

for marker in \
  "post_run_status=POST_RUN_REFERENCE_READY" \
  "analysis_decision=ACCEPT_REFERENCE_ONLY_RUN" \
  "semantic_status=GLOBAL_NO_TRADE_BUT_OPERATOR_REVIEW_READY" \
  "error_10089_detected=true" \
  "live_subscription_status=LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE"
do
  if ! grep -F "$marker" <<<"$POST_OUT" >/dev/null; then
    echo "[FAIL] Missing acceptance marker: $marker"
    exit 1
  fi
done

PATH=.venv/bin:$PATH PYTHONPATH=. python - <<'PY'
from pathlib import Path
import csv
import os

row = next(csv.DictReader((Path(os.environ["FIXTURE_DIR"]) / "first_operator_run_post_analysis.csv").open(newline="", encoding="utf-8")))
assert row["delayed_reference_count"] == "2", row
assert row["error_codes_detected"] == "10089", row
assert row["error_10089_detected"] == "true", row
assert row["live_subscription_status"] == "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE", row
PY

if ! rg -n "10089" tests/test_ibkr_market_data_fallback.py tests/test_first_operator_run_post_analysis.py >/dev/null; then
  echo "[FAIL] Missing Error 10089 test coverage"
  exit 1
fi

if ! rg -n "354" tests/test_ibkr_market_data_fallback.py tests/test_first_operator_run_post_analysis.py >/dev/null; then
  echo "[FAIL] Missing Error 354 test coverage"
  exit 1
fi

SCAN_FILES=(
  main.py
  src/ibkr_market_data_fallback.py
  src/ibkr_market_data_error_capture.py
  src/first_operator_run_post_analysis.py
  scripts/ibkr_market_data_snapshot_oneshot.sh
  scripts/first_operator_run_post_analysis.sh
  scripts/phase432b_persist_error_10089_normalize_counts_check.sh
)

if rg -n "\.(placeOrder|cancelOrder|whatIfOrder|bracketOrder|exerciseOptions|reqGlobalCancel)\s*\(" "${SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] Broker trading function call detected in Phase 432B execution path"
  exit 1
fi

if rg -n "\.(reqAccount|reqPositions|accountSummary|managedAccounts)\s*\(" "${SCAN_FILES[@]}" >/dev/null 2>&1; then
  echo "[FAIL] Account or position read call detected in Phase 432B execution path"
  exit 1
fi

needle_exec="--execute-market"
needle_exec="${needle_exec}-data"
needle_pipeline="ibkr_execution_c_pipeline_validation"
needle_pipeline="${needle_pipeline}.sh"

if rg -n -- "$needle_exec" scripts/phase432b_persist_error_10089_normalize_counts_check.sh >/dev/null 2>&1; then
  echo "[FAIL] Phase 432B check script contains real market-data execution flag"
  exit 1
fi

if rg -n -- "$needle_pipeline" scripts/phase432b_persist_error_10089_normalize_counts_check.sh >/dev/null 2>&1; then
  echo "[FAIL] Phase 432B check script references Execution C pipeline validation"
  exit 1
fi

echo "[PASS] Phase 432B persist Error 10089 normalize counts check completed"
